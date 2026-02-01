"""CLI argument parsing and file loading logic.

This module handles:
- Building CLI parser from dataclass fields
- Loading configuration files
- Creating config combinations
- Merging CLI args with file-loaded configs
"""

from __future__ import annotations

import copy
import json
import logging
import os
import sys
from dataclasses import MISSING, fields
from itertools import product
from typing import Any, Dict, List, Optional, Tuple, get_args

from vidhi.cli_parser import VidhiArgumentParser
from vidhi.constants import (
    FIELD_NAME_SEPARATOR,
    METADATA_KEY_ALIASES,
    METADATA_KEY_ARGNAME,
    METADATA_KEY_CHOICES,
    METADATA_KEY_HELP,
    to_cli_arg_name,
)
from vidhi.flat_dataclass.explosion import explode_dict
from vidhi.flat_dataclass.reconstruction import (
    init_iterable_args,
    instantiate_from_args,
)
from vidhi.flat_dataclass.validation import (
    overwrite_args_with_config,
)
from vidhi.utils import (
    get_inner_type,
    is_bool,
    is_dict,
    is_list,
    is_optional,
    is_primitive_type,
    load_yaml_config,
)

logger = logging.getLogger(__name__)


def create_from_cli_args(flat_dataclass_type) -> List[Any]:
    """Create dataclass instances from CLI arguments and configuration files.

    This method parses command-line arguments, loads configurations from files
    (if specified), and creates all combinations of dataclass instances.

    Args:
        flat_dataclass_type: The flat dataclass type (created by create_flat_dataclass)

    Returns:
        A list of dataclass instances.

    Raises:
        SystemExit: If required CLI arguments are missing or invalid
    """
    # Handle built-in flags before regular parsing
    # Check for --install-shell-completions with optional shell argument
    for i, arg in enumerate(sys.argv):
        if arg == "--install-shell-completions":
            # Check if next arg is a shell name
            shell_arg = None
            if i + 1 < len(sys.argv) and sys.argv[i + 1] in ("bash", "zsh", "fish"):
                shell_arg = sys.argv[i + 1]
            _handle_install_completions(flat_dataclass_type, shell_arg)
        elif arg.startswith("--install-shell-completions="):
            shell_arg = arg.split("=", 1)[1]
            _handle_install_completions(flat_dataclass_type, shell_arg)

    if "--export-json-schema" in sys.argv:
        _handle_export_schema(flat_dataclass_type)

    # Handle --config flag for loading YAML config
    config_file = _extract_config_file_arg(sys.argv)

    parser = _build_parser(flat_dataclass_type)
    parsed_args, provided_arg_names = parser.parse_args()

    # Convert parsed dict to namespace-like object for compatibility
    class Namespace:
        pass

    args_ns = Namespace()
    for key, value in parsed_args.items():
        setattr(args_ns, key, value)

    # Track which args were provided by CLI (only those explicitly passed)
    cli_provided_args = {
        k: v for k, v in parsed_args.items() if k in provided_arg_names
    }

    # Load config from --config flag
    loaded_configs: Dict[str, List[Dict[str, Any]]] = {}
    if config_file:
        file_config = load_yaml_config(config_file)
        loaded_configs["__config__"] = explode_dict(
            flat_dataclass_type, file_config, ""
        )
        # Track which fields came from the config file
        for config_dict in loaded_configs["__config__"]:
            for key in config_dict:
                provided_arg_names.add(key)

    # Get default values for merging
    all_default_values = _get_all_defaults(flat_dataclass_type)

    # Process list fields
    final_loaded_configs, final_cli_args = init_iterable_args(
        loaded_configs, cli_provided_args, flat_dataclass_type.list_fields
    )

    # Update args with processed CLI values
    for key, value in final_cli_args.items():
        setattr(args_ns, key, value)

    # Create all combinations of configs
    all_config_combinations, all_keys_to_file_field_names = _create_config_combinations(
        final_loaded_configs
    )

    # Merge CLI args with config combinations
    final_args, all_provided_args = _merge_args_with_configs(
        args_ns,
        all_config_combinations,
        all_keys_to_file_field_names,
        all_default_values,
        final_cli_args,
    )

    # Validate variant fields against the final merged types
    _validate_variant_fields(flat_dataclass_type, final_args, final_cli_args)

    dataclass_instances = instantiate_from_args(
        flat_dataclass_type, final_args, all_provided_args
    )

    return dataclass_instances


def _build_parser(flat_dataclass_type) -> VidhiArgumentParser:
    """Build a VidhiArgumentParser from flat dataclass metadata.

    Args:
        flat_dataclass_type: The flat dataclass type with metadata

    Returns:
        Configured VidhiArgumentParser instance
    """
    # Get description from original dataclass docstring
    description = None
    original_class = getattr(flat_dataclass_type, "_original_dataclass", None)
    if original_class and original_class.__doc__:
        # Use first line of docstring as description
        description = original_class.__doc__.strip().split("\n")[0]

    parser = VidhiArgumentParser(description=description)

    # Add group and variant descriptions from polymorphic class docstrings
    base_poly_children = getattr(flat_dataclass_type, "base_poly_children", {})
    for group_name, variants in base_poly_children.items():
        if variants:
            # Get the first variant class and find its base class docstring
            first_variant_class = next(iter(variants.values()))
            for base in first_variant_class.__bases__:
                if hasattr(base, "__doc__") and base.__doc__:
                    # Use first line of docstring
                    doc = base.__doc__.strip().split("\n")[0]
                    parser.set_group_description(group_name, doc)
                    break

            # Add each variant's docstring
            for variant_name, variant_class in variants.items():
                if variant_class.__doc__:
                    doc = variant_class.__doc__.strip().split("\n")[0]
                    parser.set_variant_description(group_name, variant_name, doc)

    # Add nested dataclass group descriptions (for non-poly nested configs)
    nested_group_docs = getattr(flat_dataclass_type, "nested_group_docs", {})
    for group_path, doc in nested_group_docs.items():
        parser.set_nested_group_description(group_path, doc)

    # Pass nested group mapping to parser
    nested_groups = getattr(flat_dataclass_type, "nested_groups", {})
    parser.set_nested_groups(nested_groups)

    for field in fields(flat_dataclass_type):
        if not field.init:
            continue

        _add_field_to_parser(flat_dataclass_type, field, parser)

    return parser


def _add_field_to_parser(
    flat_dataclass_type,
    field: Any,
    parser: VidhiArgumentParser,
) -> None:
    """Add a single dataclass field to the parser.

    Args:
        flat_dataclass_type: The flat dataclass type containing metadata
        field: Dataclass field to add
        parser: VidhiArgumentParser instance
    """
    from enum import Enum

    # Get metadata
    metadata = flat_dataclass_type.metadata_mapping.get(field.name, {})
    help_text = metadata.get(METADATA_KEY_HELP, "")
    custom_argname = metadata.get(METADATA_KEY_ARGNAME)
    aliases = metadata.get(METADATA_KEY_ALIASES)
    metadata_choices = metadata.get(METADATA_KEY_CHOICES)

    # Determine CLI name
    cli_name = custom_argname if custom_argname else to_cli_arg_name(field.name)

    # Handle Optional types
    is_field_optional = is_optional(field.type)
    field_type = get_inner_type(field.type) if is_field_optional else field.type

    # Get default value
    default = _get_field_default(field)

    # Check if this is a variant-specific field
    poly_info = flat_dataclass_type.poly_field_variants.get(field.name)
    variants = None
    type_field = None

    if poly_info:
        variants = poly_info.get("variants")
        type_field = poly_info.get("type_field")

        # If field has variant-specific defaults, build the default dict
        if variants and len(variants) < len(
            _get_all_variants_for_type_field(flat_dataclass_type, type_field)
        ):
            # This is a variant-specific field - wrap default in dict
            if default is not None:
                default = {v: default for v in variants}

    # Determine argument group
    group = _get_field_group(field.name)

    # Check if boolean
    is_boolean = is_bool(field_type)

    # Detect choices for enum fields or polymorphic type selectors
    choices = None

    # Check if this is a polymorphic type selector field (e.g., scheduler_type, cache__pool_type)
    if field.name.endswith("_type"):
        base_field = field.name[:-5]  # Remove "_type" suffix
        if base_field in getattr(flat_dataclass_type, "base_poly_children_types", {}):
            choices = list(
                flat_dataclass_type.base_poly_children_types[base_field].keys()
            )

            # For nested type selectors (e.g., cache__pool_type), inherit the parent's
            # variant info so the help output knows which parent variant this belongs to
            if variants is None and FIELD_NAME_SEPARATOR in base_field:
                parent_poly_info = flat_dataclass_type.poly_field_variants.get(
                    base_field
                )
                if parent_poly_info:
                    variants = parent_poly_info.get("variants")
                    type_field = parent_poly_info.get("type_field")

    # Check if field type is an Enum
    if (
        choices is None
        and isinstance(field_type, type)
        and issubclass(field_type, Enum)
    ):
        choices = [m.value for m in field_type]

    # Use choices from field metadata if not already set
    if choices is None and metadata_choices:
        choices = metadata_choices

    # Handle list/dict types
    is_list_field = is_list(field_type)
    if is_list_field:
        inner_type = get_args(field_type)[0]
        if is_primitive_type(inner_type):
            field_type = inner_type
        else:
            field_type = json.loads
    elif is_dict(field_type):
        field_type = json.loads

    parser.add_argument(
        name=field.name,
        cli_name=cli_name,
        arg_type=field_type,
        default=default,
        help_text=help_text,
        required=False,  # We handle required validation separately
        is_boolean=is_boolean,
        is_list=is_list_field,
        variants=variants,
        type_field=type_field,
        group=group,
        choices=choices,
        aliases=aliases,
    )


def _get_field_default(field: Any) -> Any:
    """Get the default value for a field."""
    if field.default is not MISSING:
        value = field.default
        if callable(value) and not isinstance(value, type):
            return value()
        return value
    elif field.default_factory is not MISSING:
        return field.default_factory()
    return None


def _get_field_group(field_name: str) -> str:
    """Determine which argument group a field belongs to."""
    # Type fields go in main options
    if field_name.endswith("_type"):
        return ""

    # Nested fields use first component as group
    if FIELD_NAME_SEPARATOR in field_name:
        return field_name.split(FIELD_NAME_SEPARATOR)[0]

    return ""


def _get_all_variants_for_type_field(flat_dataclass_type, type_field: str) -> set:
    """Get all variant names for a polymorphic type field."""
    # The type field name is like "scheduler_type"
    # The base poly field name is "scheduler"
    base_field = type_field.replace("_type", "")

    if base_field in flat_dataclass_type.base_poly_children_types:
        return set(flat_dataclass_type.base_poly_children_types[base_field].keys())
    return set()


def _get_all_defaults(flat_dataclass_type) -> Dict[str, Any]:
    """Get all default values from flat dataclass."""
    defaults = {}
    for field in fields(flat_dataclass_type):
        defaults[field.name] = _get_field_default(field)
    return defaults


def _create_config_combinations(
    loaded_configs: Dict[str, List[Dict[str, Any]]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, str]]]:
    """Create cartesian product of all loaded configs.

    Args:
        loaded_configs: Dictionary mapping file field names to config lists

    Returns:
        Tuple of (all_config_combinations, all_keys_to_file_field_names)
    """
    all_config_combinations = []
    all_keys_to_file_field_names: List[Dict[str, str]] = []

    if not loaded_configs:
        return all_config_combinations, all_keys_to_file_field_names

    config_lists = list(loaded_configs.values())
    file_field_names = list(loaded_configs.keys())

    for combination in product(*config_lists):
        combined_config = {}
        params_to_files = {}

        for config, current_file_field_name in zip(combination, file_field_names):
            for key, value in config.items():
                if key in combined_config:
                    raise ValueError(
                        f"Arg {key} provided by {current_file_field_name} is also set by {params_to_files[key]}."
                    )
                combined_config[key] = value
                params_to_files[key] = current_file_field_name

        all_config_combinations.append(combined_config)
        all_keys_to_file_field_names.append(params_to_files)

    logger.info(f"Created {len(all_config_combinations)} total config combinations.")

    return all_config_combinations, all_keys_to_file_field_names


def _merge_args_with_configs(
    parsed_args,
    all_config_combinations: List[Dict[str, Any]],
    all_keys_to_file_field_names: List[Dict[str, str]],
    all_default_values: Dict[str, Any],
    cli_provided_args: Dict[str, Any],
) -> Tuple[List[Any], List[Dict[str, Any]]]:
    """Merge CLI arguments with all config combinations.

    Returns:
        Tuple of (list of all flatclass args, list of user-provided args for each config)
    """
    all_provided_args: List[Dict[str, Any]] = []

    if not all_config_combinations:
        return [parsed_args], [cli_provided_args]

    final_args = []
    for config_dict, keys_to_file_field_names in zip(
        all_config_combinations, all_keys_to_file_field_names
    ):
        _provided_args_in_config = {
            **config_dict,
            **cli_provided_args,
        }
        all_provided_args.append(_provided_args_in_config)

        args_copy = copy.deepcopy(parsed_args)
        overwrite_args_with_config(
            args_copy,
            config_dict,
            keys_to_file_field_names,
            all_default_values,
            set(cli_provided_args.keys()),
        )
        final_args.append(args_copy)

    return final_args, all_provided_args


def _validate_variant_fields(
    flat_dataclass_type,
    final_args: List[Any],
    cli_provided_args: Dict[str, Any],
) -> None:
    """Validate that CLI-provided variant fields match the final merged type.

    This validation happens after merging CLI args with config files, so we
    validate against the actual final type (which may come from the config file).

    Args:
        flat_dataclass_type: The flat dataclass type with poly_field_variants metadata
        final_args: List of merged argument namespaces
        cli_provided_args: Dict of args explicitly provided via CLI
    """
    poly_field_variants = getattr(flat_dataclass_type, "poly_field_variants", {})

    for args in final_args:
        for field_name, cli_value in cli_provided_args.items():
            # Check if this field has variant restrictions
            poly_info = poly_field_variants.get(field_name)
            if not poly_info:
                continue

            valid_variants = poly_info.get("variants", set())
            type_field = poly_info.get("type_field")

            if not valid_variants or not type_field:
                continue

            # Get the final type from the merged args
            final_type = getattr(args, type_field, None)
            if final_type is None:
                continue

            # Compare case-insensitively since variants are stored lowercase
            if final_type.lower() not in valid_variants:
                valid_list = ", ".join(sorted(valid_variants))
                cli_name = field_name.replace("__", ".")
                print(
                    f"Error: --{cli_name} is only valid for {valid_list}, "
                    f"but {type_field.replace('__', '.')}={final_type}",
                    file=sys.stderr,
                )
                sys.exit(1)


def _extract_config_file_arg(argv: List[str]) -> Optional[str]:
    """Extract and remove --config argument from argv.

    Args:
        argv: Command line arguments (modified in place)

    Returns:
        Config file path if --config was provided, None otherwise
    """
    config_file = None

    i = 0
    while i < len(argv):
        if argv[i] == "--config":
            if i + 1 < len(argv) and not argv[i + 1].startswith("--"):
                config_file = argv[i + 1]
                # Remove both --config and the path from argv
                del argv[i : i + 2]
            else:
                print("Error: --config requires a file path", file=sys.stderr)
                sys.exit(1)
        elif argv[i].startswith("--config="):
            config_file = argv[i].split("=", 1)[1]
            del argv[i]
        else:
            i += 1

    return config_file


def _handle_install_completions(
    flat_dataclass_type, shell_override: Optional[str] = None
) -> None:
    """Handle --install-shell-completions flag.

    Installs shell completions and exits.

    Args:
        flat_dataclass_type: The flat dataclass type
        shell_override: Optional explicit shell name (bash, zsh, fish)
    """
    from vidhi.cli_completion import detect_shell, install_completion

    # Get command name from sys.argv[0]
    command_name = os.path.basename(sys.argv[0])
    if command_name.endswith(".py"):
        command_name = command_name[:-3]

    # Use override or detect shell
    if shell_override:
        if shell_override not in ("bash", "zsh", "fish"):
            print(f"Unknown shell: {shell_override}")
            print("Supported shells: bash, zsh, fish")
            sys.exit(1)
        shell = shell_override
    else:
        shell = detect_shell()
        if shell is None:
            print("Could not detect shell from $SHELL environment variable.")
            print("Please specify shell explicitly:")
            print("  --install-shell-completions bash")
            print("  --install-shell-completions zsh")
            print("  --install-shell-completions fish")
            sys.exit(1)

    # Install completions
    print(f"Installing {shell} completions for '{command_name}'...")
    try:
        result = install_completion(flat_dataclass_type, command_name, shell)
        print(result)
        sys.exit(0)
    except Exception as e:
        print(f"Error installing completions: {e}")
        sys.exit(1)


def _handle_export_schema(flat_dataclass_type) -> None:
    """Handle --export-json-schema flag.

    Exports JSON schema for IDE autocomplete and exits.
    """
    from vidhi.schema import ConfigSchema

    # Find the output path (next argument after --export-json-schema)
    try:
        idx = sys.argv.index("--export-json-schema")
        if idx + 1 >= len(sys.argv) or sys.argv[idx + 1].startswith("--"):
            output_path = "config.schema.json"
        else:
            output_path = sys.argv[idx + 1]
    except ValueError:
        output_path = "config.schema.json"

    # Get the original dataclass
    original_class = flat_dataclass_type._original_dataclass

    # Generate and export schema
    try:
        schema = ConfigSchema(original_class)
        schema.export_json_schema(output_path)
        print(f"JSON Schema exported to: {output_path}")
        print()
        print("To enable IDE autocomplete, add to .vscode/settings.json:")
        print()
        # Use relative path for display if not absolute
        display_path = output_path if os.path.isabs(output_path) else f"./{output_path}"
        print("  {")
        print('    "yaml.schemas": {')
        print(f'      "{display_path}": "*.yaml"')
        print("    }")
        print("  }")
        sys.exit(0)
    except Exception as e:
        print(f"Error exporting schema: {e}")
        sys.exit(1)
