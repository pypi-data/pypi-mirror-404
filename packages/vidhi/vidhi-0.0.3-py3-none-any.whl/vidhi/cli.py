"""Public CLI API for Vidhi configuration management.

This module provides the user-facing API for CLI-based configuration:
- field(): Enhanced dataclass field with CLI options
- parse_cli_args(): Parse CLI arguments into a single config instance
- parse_cli_sweep(): Parse CLI arguments into multiple configs (for sweeps)
- with_cli_overrides(): Override a manually constructed config from CLI
"""

from __future__ import annotations

import sys
from dataclasses import MISSING
from dataclasses import field as dataclass_field
from typing import Any, Dict, List, Type, TypeVar

from vidhi.constants import FIELD_NAME_SEPARATOR
from vidhi.flat_dataclass import create_flat_dataclass
from vidhi.flat_dataclass.cli import _build_parser, _extract_config_file_arg
from vidhi.utils import create_class_from_dict, dataclass_to_dict

T = TypeVar("T")


def field(
    default: Any = MISSING,
    *,
    default_factory: Any = MISSING,
    help: str | None = None,
    name: str | None = None,
    aliases: list[str] | None = None,
    choices: list | None = None,
    # Standard dataclass field parameters
    repr: bool = True,
    hash: bool | None = None,
    init: bool = True,
    compare: bool = True,
    metadata: dict | None = None,
    kw_only: bool = False,
) -> Any:
    """Define a dataclass field with optional CLI configuration.

    This is a drop-in replacement for dataclasses.field() that adds
    convenient CLI argument configuration.

    Args:
        default: Default value for the field
        default_factory: Factory function for default value
        help: Help text shown in --help output
        name: Custom CLI argument name (e.g., "lr" instead of "learning_rate")
        aliases: Alternative CLI names for backwards compatibility (e.g., ["learning-rate"])
        choices: List of valid values for this argument
        repr: Include in repr output
        hash: Include in hash
        init: Include in __init__
        compare: Include in comparison
        metadata: Additional metadata dict
        kw_only: Keyword-only argument

    Returns:
        A dataclass field descriptor

    Example:
        >>> @frozen_dataclass
        >>> class Config:
        >>>     learning_rate: float = field(
        >>>         0.001,
        >>>         help="Learning rate",
        >>>         name="lr",
        >>>         aliases=["learning-rate"]  # For backwards compatibility
        >>>     )
        >>>     batch_size: int = field(32, help="Training batch size")
        >>>     debug: bool = False  # Regular default also works
        >>>     optimizer: str = field("adam", choices=["adam", "sgd", "rmsprop"])
    """
    # Build CLI metadata
    cli_metadata = {}
    if help is not None:
        cli_metadata["help"] = help
    if name is not None:
        cli_metadata["argname"] = name
    if aliases is not None:
        cli_metadata["aliases"] = aliases
    if choices is not None:
        cli_metadata["choices"] = choices

    # Merge with user-provided metadata
    final_metadata = {**(metadata or {}), **cli_metadata}

    # Handle default vs default_factory
    field_kwargs = {
        "repr": repr,
        "hash": hash,
        "init": init,
        "compare": compare,
        "metadata": final_metadata if final_metadata else None,
        "kw_only": kw_only,
    }

    if default is not MISSING:
        field_kwargs["default"] = default
    if default_factory is not MISSING:
        field_kwargs["default_factory"] = default_factory

    return dataclass_field(**field_kwargs)


def parse_cli_args(
    config_class: Type[T],
    *,
    args: list[str] | None = None,
    description: str | None = None,
) -> T:
    """Parse CLI arguments and return a single configuration instance.

    This is the main entry point for CLI-based configuration. It automatically
    generates an argument parser from the config class structure and returns
    a fully instantiated config object.

    Args:
        config_class: The dataclass type to parse arguments for
        args: Optional list of arguments (defaults to sys.argv)
        description: Optional program description for --help

    Returns:
        A single config instance.

    Raises:
        ValueError: If the CLI arguments would produce multiple configs
            (e.g., from a sweep file). Use parse_cli_sweep() for sweeps.

    Example:
        >>> @frozen_dataclass
        >>> class TrainingConfig:
        >>>     learning_rate: float = field(0.001, help="Learning rate")
        >>>     batch_size: int = field(32, help="Batch size")
        >>>
        >>> config = parse_cli_args(TrainingConfig)
        >>> print(config.learning_rate)

        Command line:
        $ python train.py --learning_rate 0.01 --batch_size 64
    """
    configs = parse_cli_sweep(config_class, args=args, description=description)

    if len(configs) > 1:
        raise ValueError(
            f"CLI arguments produced {len(configs)} configs. "
            "Use parse_cli_sweep() for sweep configurations."
        )

    return configs[0]


def parse_cli_sweep(
    config_class: Type[T],
    *,
    args: list[str] | None = None,
    description: str | None = None,
) -> List[T]:
    """Parse CLI arguments and return multiple configuration instances.

    Use this for sweep/grid configurations where CLI arguments or config
    files can produce multiple config combinations.

    Args:
        config_class: The dataclass type to parse arguments for
        args: Optional list of arguments (defaults to sys.argv)
        description: Optional program description for --help

    Returns:
        List of config instances.

    Example:
        >>> configs = parse_cli_sweep(TrainingConfig)
        >>> for config in configs:
        >>>     train(config)
    """
    # Note: args and description parameters are reserved for future use
    # Currently, arguments are always parsed from sys.argv
    _ = args  # Reserved for future: custom argument list
    _ = description  # Reserved for future: argparse description

    # Create the internal flat representation
    flat_class = create_flat_dataclass(config_class)

    # Parse CLI arguments and create instances
    flat_instances = flat_class.create_from_cli_args()

    # Reconstruct original nested config structure
    return [instance.reconstruct_original_dataclass() for instance in flat_instances]


def with_cli_overrides(config: T) -> T:
    """Override a manually constructed config with CLI arguments.

    This allows you to define defaults programmatically and let users
    override specific values from the command line. Supports YAML file
    loading via --config.

    Priority: CLI args > YAML file > code defaults

    Args:
        config: A dataclass config instance with your default values

    Returns:
        A new config instance with CLI overrides applied.

    Example:
        >>> def create_config():
        >>>     return InferenceEngineConfig(
        >>>         model="gpt-4",
        >>>         temperature=0.7,
        >>>         max_tokens=1000,
        >>>     )
        >>>
        >>> config = with_cli_overrides(create_config())
        >>>
        >>> # Users can now run:
        >>> # python script.py --temperature 0.9 --max_tokens 2000
        >>> # Or with a YAML file:
        >>> # python script.py --config settings.yaml --temperature 0.9
    """
    config_class = type(config)

    # Convert base config to nested dict
    base_dict = dataclass_to_dict(config)

    # Create flat dataclass and use full CLI parsing (handles files, etc.)
    flat_class = create_flat_dataclass(config_class)

    # Check if any CLI args were provided (need to handle --config specially)
    # Make a copy of sys.argv to check without modifying it
    argv_copy = sys.argv.copy()
    has_config_file = _extract_config_file_arg(argv_copy) is not None

    parser = _build_parser(flat_class)
    _, cli_provided = parser.parse_args(argv_copy[1:])

    # If no CLI args provided (and no config file), return original config
    if not cli_provided and not has_config_file:
        return config

    # Use full CLI parsing to get config (handles YAML files, etc.)
    flat_instances = flat_class.create_from_cli_args()

    if len(flat_instances) > 1:
        raise ValueError(
            f"CLI arguments produced {len(flat_instances)} configs. "
            "with_cli_overrides() only supports single configs."
        )

    flat_instance = flat_instances[0]

    # Get the CLI-parsed config as dict
    cli_config = flat_instance.reconstruct_original_dataclass()
    cli_dict = dataclass_to_dict(cli_config)

    # Get the set of fields that were explicitly provided (from CLI or YAML file)
    # This includes fields loaded from YAML files, not just direct CLI args
    provided_fields = _get_provided_fields(flat_instance.provided_args)

    # Merge: start with base, overlay CLI/file-provided values
    merged_dict = _merge_with_provided(base_dict, cli_dict, provided_fields)

    # Reconstruct config from merged dict
    return create_class_from_dict(config_class, merged_dict)


def _get_provided_fields(provided_arg_names: set) -> set:
    """Convert flat arg names to nested field paths.

    Args:
        provided_arg_names: Set of flat arg names like "database__host"

    Returns:
        Set of nested paths like ("database", "host")
    """
    result = set()
    for name in provided_arg_names:
        parts = tuple(name.split(FIELD_NAME_SEPARATOR))
        result.add(parts)
    return result


def _merge_with_provided(
    base: Dict[str, Any],
    cli: Dict[str, Any],
    provided: set,
    path: tuple = (),
) -> Dict[str, Any]:
    """Merge CLI values into base, but only for provided fields.

    For fields that were explicitly provided via CLI or YAML, use CLI values.
    For fields not provided, keep base values.

    Args:
        base: Base config dict
        cli: CLI-parsed config dict
        provided: Set of field paths that were explicitly provided
        path: Current path in the nested structure

    Returns:
        Merged dictionary
    """
    result = {}

    # Get all keys from both dicts
    all_keys = set(base.keys()) | set(cli.keys())

    for key in all_keys:
        current_path = path + (key,)
        base_val = base.get(key)
        cli_val = cli.get(key)

        # Check if this field or any nested field was provided
        field_provided = any(p[: len(current_path)] == current_path for p in provided)

        if isinstance(base_val, dict) and isinstance(cli_val, dict):
            # Recurse into nested dicts
            result[key] = _merge_with_provided(
                base_val, cli_val, provided, current_path
            )
        elif field_provided:
            # Use CLI value for provided fields
            result[key] = cli_val if cli_val is not None else base_val
        else:
            # Use base value for non-provided fields
            result[key] = base_val if base_val is not None else cli_val

    return result
