"""Custom CLI argument parser for Vidhi configuration.

This module provides a CLI parser designed specifically for dataclass-based
configurations with support for:
- Polymorphic configs with variant-specific defaults
- Clean nested field naming (--scheduler.timeout)
- Grouped help output with colors
- Type validation
"""

from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

from vidhi.constants import to_cli_arg_name

# =============================================================================
# ANSI Color Support
# =============================================================================


class Colors:
    """ANSI color codes for terminal output."""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    # Colors
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Bright colors
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_CYAN = "\033[96m"


def _format_config_name(name: str) -> str:
    """Format a config name for display.

    Converts snake_case names like "resource_allocator_config" to
    title case "Resource Allocator Config".

    Args:
        name: The snake_case config name

    Returns:
        Properly formatted title case name
    """
    # Remove trailing _config suffix for cleaner display
    display_name = name
    if display_name.endswith("_config"):
        display_name = display_name[:-7]

    # Split by underscores and capitalize each word
    words = display_name.split("_")
    return " ".join(word.capitalize() for word in words)


def _supports_color() -> bool:
    """Check if the terminal supports colors."""
    # Check for NO_COLOR environment variable (https://no-color.org/)
    if os.environ.get("NO_COLOR"):
        return False

    # Check for FORCE_COLOR environment variable
    if os.environ.get("FORCE_COLOR"):
        return True

    # Check if stdout is a TTY
    if not hasattr(sys.stdout, "isatty") or not sys.stdout.isatty():
        return False

    # Check TERM environment variable
    term = os.environ.get("TERM", "")
    if term == "dumb":
        return False

    return True


class ColorFormatter:
    """Formatter that applies colors when supported."""

    def __init__(self, use_colors: Optional[bool] = None):
        if use_colors is None:
            use_colors = _supports_color()
        self.use_colors = use_colors

    def _c(self, text: str, *colors: str) -> str:
        """Apply colors to text if colors are enabled."""
        if not self.use_colors:
            return text
        color_code = "".join(colors)
        return f"{color_code}{text}{Colors.RESET}"

    def bold(self, text: str) -> str:
        return self._c(text, Colors.BOLD)

    def dim(self, text: str) -> str:
        return self._c(text, Colors.DIM)

    def option(self, text: str) -> str:
        """Format CLI option (e.g., --host)."""
        return self._c(text, Colors.CYAN)

    def type_hint(self, text: str) -> str:
        """Format type hint (e.g., <int>)."""
        return self._c(text, Colors.YELLOW)

    def default(self, text: str) -> str:
        """Format default value."""
        return self._c(text, Colors.GREEN)

    def required(self, text: str) -> str:
        """Format required marker."""
        return self._c(text, Colors.BRIGHT_RED, Colors.BOLD)

    def choices(self, text: str) -> str:
        """Format choices."""
        return self._c(text, Colors.MAGENTA)

    def header(self, text: str) -> str:
        """Format section header."""
        return self._c(text, Colors.BOLD, Colors.WHITE)

    def variant(self, text: str) -> str:
        """Format variant name."""
        return self._c(text, Colors.BRIGHT_CYAN, Colors.BOLD)

    def yaml_key(self, text: str) -> str:
        """Format YAML key."""
        return self._c(text, Colors.CYAN)

    def yaml_value(self, text: str) -> str:
        """Format YAML value."""
        return self._c(text, Colors.GREEN)

    def yaml_comment(self, text: str) -> str:
        """Format YAML comment."""
        return self._c(text, Colors.DIM)


# =============================================================================
# Argument Data Classes
# =============================================================================


@dataclass
class Argument:
    """Definition of a CLI argument."""

    name: str  # Internal name (e.g., "scheduler__timeout")
    cli_name: str  # CLI name (e.g., "scheduler.timeout")
    arg_type: Union[type, Callable[[str], Any]]  # Expected type or converter function
    default: Any  # Default value (or dict of variant -> default)
    help_text: str  # Help description
    required: bool = False
    is_boolean: bool = False
    is_list: bool = False  # Whether this argument accepts multiple values
    variants: Optional[Set[str]] = None  # Which variants this field belongs to
    type_field: Optional[str] = None  # The type selector field (e.g., "scheduler_type")
    group: Optional[str] = None  # Argument group for help display
    choices: Optional[List[str]] = None  # Valid choices for this argument
    aliases: Optional[List[str]] = None  # Alternative CLI names for this argument


@dataclass
class ArgumentGroup:
    """A group of related arguments for help display."""

    name: str
    title: str
    arguments: List[Argument]


# =============================================================================
# Main Parser Class
# =============================================================================


class VidhiArgumentParser:
    """Custom argument parser for Vidhi configurations.

    Unlike argparse, this parser:
    - Handles polymorphic configs with variant-specific defaults
    - Shows all variant defaults in help text
    - Validates fields against selected variant type
    - Produces clean, grouped help output with colors
    """

    def __init__(self, prog: Optional[str] = None, description: Optional[str] = None):
        self.prog = prog or os.path.basename(sys.argv[0])
        self.description = description
        self.arguments: Dict[str, Argument] = {}
        self.groups: Dict[str, ArgumentGroup] = {}
        self._group_order: List[str] = []  # Track insertion order
        self._group_descriptions: Dict[str, str] = {}  # Group docstrings
        self._variant_descriptions: Dict[str, Dict[str, str]] = (
            {}
        )  # group -> {variant -> desc}
        self._nested_group_descriptions: Dict[str, str] = {}  # nested path -> docstring
        self._nested_groups: Dict[str, str] = {}  # field_name -> parent nested path
        self._color = ColorFormatter()

    def set_group_description(self, group: str, description: str) -> None:
        """Set a description for a group (from class docstring)."""
        self._group_descriptions[group] = description

    def set_variant_description(
        self, group: str, variant: str, description: str
    ) -> None:
        """Set a description for a variant (from variant class docstring)."""
        if group not in self._variant_descriptions:
            self._variant_descriptions[group] = {}
        self._variant_descriptions[group][variant] = description

    def set_nested_group_description(self, group_path: str, description: str) -> None:
        """Set a description for a nested dataclass group."""
        self._nested_group_descriptions[group_path] = description

    def set_nested_groups(self, nested_groups: Dict[str, str]) -> None:
        """Set the mapping of field names to their parent nested dataclass paths."""
        self._nested_groups = nested_groups

    def add_argument(
        self,
        name: str,
        cli_name: str,
        arg_type: Union[type, Callable[[str], Any]],
        default: Any = None,
        help_text: str = "",
        required: bool = False,
        is_boolean: bool = False,
        is_list: bool = False,
        variants: Optional[Set[str]] = None,
        type_field: Optional[str] = None,
        group: Optional[str] = None,
        choices: Optional[List[str]] = None,
        aliases: Optional[List[str]] = None,
    ) -> None:
        """Add an argument to the parser."""
        arg = Argument(
            name=name,
            cli_name=cli_name,
            arg_type=arg_type,
            default=default,
            help_text=help_text,
            required=required,
            is_boolean=is_boolean,
            is_list=is_list,
            variants=variants,
            type_field=type_field,
            group=group,
            choices=choices,
            aliases=aliases,
        )
        self.arguments[name] = arg

        # Add to group
        group_key = group or ""
        if group_key not in self.groups:
            # Use proper title case formatting for config names
            if group_key:
                formatted_name = _format_config_name(group_key)
                title = f"{formatted_name} Options"
            else:
                title = "Options"
            self.groups[group_key] = ArgumentGroup(
                name=group_key, title=title, arguments=[]
            )
            self._group_order.append(group_key)
        self.groups[group_key].arguments.append(arg)

    def parse_args(
        self,
        args: Optional[List[str]] = None,
    ) -> Tuple[Dict[str, Any], Set[str]]:
        """Parse command line arguments.

        Args:
            args: List of arguments (defaults to sys.argv[1:])

        Returns:
            Tuple of (parsed_values, provided_args) where:
            - parsed_values: Dictionary mapping argument names to parsed values
            - provided_args: Set of argument names that were explicitly provided
        """
        if args is None:
            args = sys.argv[1:]

        # Check for help
        if "-h" in args or "--help" in args:
            self.print_help()
            sys.exit(0)

        # Parse arguments
        result: Dict[str, Any] = {}
        provided: Set[str] = set()
        i = 0

        while i < len(args):
            arg = args[i]

            if not arg.startswith("--"):
                i += 1
                continue

            # Handle --flag or --flag=value or --flag value
            if "=" in arg:
                cli_name, value = arg[2:].split("=", 1)
            else:
                cli_name = arg[2:]
                value = None

            internal_name = self._find_argument_by_cli_name(cli_name)
            if not internal_name:
                print(f"Error: Unknown argument --{cli_name}", file=sys.stderr)
                sys.exit(1)

            arg_def = self.arguments[internal_name]

            # Get value(s)
            if arg_def.is_list:
                # Collect multiple values until next flag
                values = []
                if value is not None:
                    # Value was provided with = syntax
                    values.append(value)
                    i += 1
                else:
                    i += 1  # Move past the flag
                    # Collect values until next flag or end of args
                    while i < len(args) and not args[i].startswith("--"):
                        values.append(args[i])
                        i += 1

                if not values:
                    print(
                        f"Error: --{cli_name} requires at least one value",
                        file=sys.stderr,
                    )
                    sys.exit(1)

                # Convert each value to the target type
                try:
                    result[internal_name] = [arg_def.arg_type(v) for v in values]
                except (ValueError, TypeError) as e:
                    print(
                        f"Error: Invalid value for --{cli_name}: {e}", file=sys.stderr
                    )
                    sys.exit(1)
            else:
                # Single value argument
                if value is None:
                    if i + 1 >= len(args):
                        print(f"Error: --{cli_name} requires a value", file=sys.stderr)
                        sys.exit(1)
                    value = args[i + 1]
                    i += 2
                else:
                    i += 1

                # Convert type
                try:
                    if arg_def.arg_type == bool:
                        lower_val = value.lower()
                        if lower_val in ("true", "1", "yes"):
                            result[internal_name] = True
                        elif lower_val in ("false", "0", "no"):
                            result[internal_name] = False
                        else:
                            print(
                                f"Error: Invalid boolean value '{value}' for --{cli_name}. "
                                f"Use true/false, yes/no, or 1/0.",
                                file=sys.stderr,
                            )
                            sys.exit(1)
                    elif isinstance(arg_def.arg_type, type) and issubclass(
                        arg_def.arg_type, Enum
                    ):
                        result[internal_name] = value
                    else:
                        result[internal_name] = arg_def.arg_type(value)
                except (ValueError, TypeError) as e:
                    print(
                        f"Error: Invalid value for --{cli_name}: {e}", file=sys.stderr
                    )
                    sys.exit(1)

                # Validate choices if specified (case-insensitive for type selectors)
                if arg_def.choices:
                    value_to_check = result[internal_name]
                    # Check case-insensitively
                    choices_lower = {str(c).lower(): c for c in arg_def.choices}
                    if str(value_to_check).lower() in choices_lower:
                        # Normalize to the canonical case
                        result[internal_name] = choices_lower[
                            str(value_to_check).lower()
                        ]
                    elif value_to_check not in arg_def.choices:
                        print(
                            f"Error: Invalid value '{value_to_check}' for --{cli_name}. "
                            f"Choose from: {', '.join(str(c) for c in arg_def.choices)}",
                            file=sys.stderr,
                        )
                        sys.exit(1)

            provided.add(internal_name)

        # Apply defaults and validate
        self._apply_defaults(result, provided)
        self._validate_required(result, provided)
        # Note: Variant field validation is done after merging with config files
        # in create_from_cli_args() to validate against the final type

        return result, provided

    def _find_argument_by_cli_name(self, cli_name: str) -> Optional[str]:
        """Find internal argument name by CLI name or alias."""
        for name, arg in self.arguments.items():
            if arg.cli_name == cli_name:
                return name
            # Check aliases
            if arg.aliases and cli_name in arg.aliases:
                return name
        return None

    def _apply_defaults(self, result: Dict[str, Any], provided: Set[str]) -> None:
        """Apply default values for unprovided arguments."""
        for name, arg in self.arguments.items():
            if name not in provided:
                if isinstance(arg.default, dict):
                    # Variant-specific default - use default variant's value
                    # Get the selected type
                    if arg.type_field and arg.type_field in result:
                        selected_type = result[arg.type_field]
                        if selected_type in arg.default:
                            result[name] = arg.default[selected_type]
                        else:
                            # Use first available default
                            result[name] = next(iter(arg.default.values()))
                    else:
                        result[name] = next(iter(arg.default.values()))
                else:
                    result[name] = arg.default

    def _validate_required(self, result: Dict[str, Any], provided: Set[str]) -> None:
        """Validate that required arguments are provided."""
        for name, arg in self.arguments.items():
            if arg.required and name not in provided:
                print(f"Error: --{arg.cli_name} is required", file=sys.stderr)
                sys.exit(1)

    def print_help(self) -> None:
        """Print formatted help message with colors."""
        c = self._color
        lines = []

        # Usage line
        lines.append(self._format_usage())
        lines.append("")

        if self.description:
            lines.append(self.description)
            lines.append("")

        # Built-in options
        lines.append(c.header("Built-in Options:"))
        lines.append(
            f"  {c.option('-h')}, {c.option('--help')}"
            f"            show this help message and exit"
        )
        lines.append(
            f"  {c.option('--config')} {c.type_hint('<path>')}"
            f"       load configuration from YAML file"
        )
        lines.append(
            f"  {c.option('--install-shell-completions')} {c.type_hint('[shell]')}"
        )
        lines.append(f"                        install shell completions and exit")
        lines.append(f"  {c.option('--export-json-schema')} {c.type_hint('[path]')}")
        lines.append(f"                        export JSON schema for IDE autocomplete")
        lines.append("")

        # Identify polymorphic groups and their variants
        poly_groups = self._identify_polymorphic_groups()

        # Print groups in order
        for group_key in self._group_order:
            group = self.groups[group_key]
            if not group.arguments:
                continue

            if group_key in poly_groups:
                # This is a polymorphic group - show each variant separately
                lines.extend(
                    self._format_polymorphic_group(group, poly_groups[group_key])
                )
            else:
                # Regular group - filter out nested type selectors
                filtered_args = [
                    arg
                    for arg in group.arguments
                    if not (arg.name.endswith("_type") and "__" in arg.name)
                ]
                if filtered_args:
                    lines.append(c.header(f"{group.title}:"))
                    for arg in filtered_args:
                        lines.extend(self._format_argument_help(arg))
                    lines.append("")

        # Add YAML example
        lines.extend(self._format_yaml_example())

        print("\n".join(lines))

    def _format_usage(self) -> str:
        """Format the usage line."""
        c = self._color
        parts = [c.bold(self.prog)]

        # Show a simplified usage - just indicate options are available
        required_args = [a for a in self.arguments.values() if a.required]
        optional_count = len(self.arguments) - len(required_args)

        for arg in required_args:
            parts.append(f"{c.option('--' + arg.cli_name)} {c.type_hint('<value>')}")

        if optional_count > 0:
            parts.append(c.dim("[options]"))

        return f"usage: {' '.join(parts)}"

    def _identify_polymorphic_groups(self) -> Dict[str, Dict[str, List[Argument]]]:
        """Identify polymorphic groups and organize arguments by variant.

        Handles nested polymorphism by only including top-level variants in the group.
        Nested poly fields (e.g., pool inside redis cache) are grouped under their
        parent variant.

        Returns:
            Dict mapping group_key -> {variant_name -> [arguments]}
        """
        poly_groups: Dict[str, Dict[str, List[Argument]]] = {}

        # First, identify the primary type field for each group
        # For nested groups like "inference_engine_config", type_fields are like
        # "inference_engine_config__controller_config_type" - check relative to group
        primary_type_fields: Dict[str, str] = {}  # group -> primary type_field
        for arg in self.arguments.values():
            if arg.type_field and arg.group:
                group = arg.group
                group_prefix = group + "__" if group else ""
                # Check if this is a top-level type field relative to the group
                relative_type_field = arg.type_field
                if group_prefix and arg.type_field.startswith(group_prefix):
                    relative_type_field = arg.type_field[len(group_prefix) :]
                if "__" not in relative_type_field:
                    if group not in primary_type_fields:
                        primary_type_fields[group] = arg.type_field

        # Now organize arguments
        for arg in self.arguments.values():
            if arg.type_field and arg.group:
                group = arg.group
                primary_tf = primary_type_fields.get(group)

                # Skip if this is a nested poly field (type_field has "__" relative to group)
                # These will be added to their parent variant below
                if primary_tf and arg.type_field != primary_tf:
                    group_prefix = group + "__" if group else ""
                    relative_type_field = arg.type_field
                    if group_prefix and arg.type_field.startswith(group_prefix):
                        relative_type_field = arg.type_field[len(group_prefix) :]
                    if "__" in relative_type_field:
                        continue

                if group not in poly_groups:
                    poly_groups[group] = {}

                if arg.variants:
                    for variant in arg.variants:
                        if variant not in poly_groups[group]:
                            poly_groups[group][variant] = []
                        poly_groups[group][variant].append(arg)

        # Add shared args (no variants) to all variants in their group
        for arg in self.arguments.values():
            if arg.type_field and arg.group and not arg.variants:
                group = arg.group
                primary_tf = primary_type_fields.get(group)

                # Only add if this is a top-level poly field
                if primary_tf and arg.type_field == primary_tf:
                    if group in poly_groups:
                        for variant in poly_groups[group]:
                            poly_groups[group][variant].append(arg)

        # Now add nested poly fields to their parent variants
        # e.g., pool fields go under redis variant
        for arg in self.arguments.values():
            if arg.type_field and arg.group and "__" in arg.type_field:
                group = arg.group
                if group not in poly_groups:
                    continue

                # Find which parent variant this nested field belongs to
                # by checking the field name prefix
                # e.g., cache__pool__max_connections belongs to variants that have "pool"
                parent_variants = self._find_parent_variants_for_nested_field(
                    arg, poly_groups[group]
                )

                for parent_variant in parent_variants:
                    if parent_variant in poly_groups[group]:
                        poly_groups[group][parent_variant].append(arg)

        return poly_groups

    def _find_parent_variants_for_nested_field(
        self, arg: Argument, group_variants: Dict[str, List[Argument]]
    ) -> Set[str]:
        """Find which parent variants a nested poly field belongs to.

        For a field like cache.pool.max_connections with type_field cache__pool_type,
        we find the parent by looking at the cache__pool field which has variants={'redis'}.
        """
        if not arg.type_field or "__" not in arg.type_field:
            return set(group_variants.keys())

        # Get the parent field path from the type_field
        # e.g., "cache__pool_type" -> "cache__pool"
        parent_path = arg.type_field.rsplit("_type", 1)[0]
        parent_cli_name = to_cli_arg_name(parent_path)

        # Look for the parent field argument which has the parent variant info
        # e.g., find "cache.pool" which has variants={'redis'}
        for name, other_arg in self.arguments.items():
            if other_arg.cli_name == parent_cli_name or name == parent_path:
                if other_arg.variants:
                    return other_arg.variants

        # Fallback: look for the parent type selector (e.g., cache.pool.type)
        # and check which top-level variants it belongs to
        parent_type_selector = parent_cli_name + ".type"
        for name, other_arg in self.arguments.items():
            if other_arg.cli_name == parent_type_selector:
                if other_arg.variants:
                    return other_arg.variants

        # Last resort: add to all variants
        return set(group_variants.keys())

    def _format_polymorphic_group(
        self, group: ArgumentGroup, variants: Dict[str, List[Argument]]
    ) -> List[str]:
        """Format a polymorphic group with separate sections per variant.

        Nested poly configs are shown as flattened variants with parent context,
        e.g., [redis.pool: cluster] instead of nested sub-sections.
        """
        c = self._color
        lines = []

        # Find the primary type selector for THIS GROUP ITSELF (not nested fields)
        # A type selector for the group would be named {group_name}_type and exist
        # at the parent level, NOT within the group prefix.
        # Type selectors within the group (like inference_engine_config__controller_config_type)
        # are for NESTED fields, not for the group itself.
        type_arg = None
        type_field_name = None
        group_prefix = group.name + "__" if group.name else ""

        # Look for a type selector for the group itself
        # e.g., for group "inference_engine_config", look for "inference_engine_config_type"
        # This would be set on the parent, not within this group
        group_type_selector = group.name + "_type" if group.name else None
        if group_type_selector and group_type_selector in self.arguments:
            type_field_name = group_type_selector
            type_arg = self.arguments.get(type_field_name)

        # If no group-level type selector, find the first nested one for tracking purposes
        # but we won't show it at the group level
        for arg in group.arguments:
            if arg.type_field:
                relative_type_field = arg.type_field
                if group_prefix and arg.type_field.startswith(group_prefix):
                    relative_type_field = arg.type_field[len(group_prefix) :]
                if "__" not in relative_type_field:
                    arg.type_field
                    break

        # Filter out nested poly variants (those whose args all have nested type_field)
        top_level_variants: Set[str] = set()

        for variant_name, variant_args in variants.items():
            is_top_level = False
            for arg in variant_args:
                if arg.type_field:
                    # Check relative to group prefix
                    relative_type_field = arg.type_field
                    if group_prefix and arg.type_field.startswith(group_prefix):
                        relative_type_field = arg.type_field[len(group_prefix) :]
                    if "__" not in relative_type_field:
                        is_top_level = True
                        break
            if is_top_level:
                top_level_variants.add(variant_name)

        # Header for the polymorphic group
        variant_names = sorted(top_level_variants)
        lines.append(c.header(f"{group.title}:"))

        # Show group description if available
        if group.name in self._group_descriptions:
            lines.append(f"  {self._group_descriptions[group.name]}")

        if type_arg and variant_names:
            choices_str = c.choices("{" + ",".join(variant_names) + "}")
            default_str = ""
            if type_arg.default:
                default_str = f" {c.dim('[' + str(type_arg.default) + ']')}"
            lines.append(
                f"  Select variant with {c.option('--' + type_arg.cli_name)} "
                f"{choices_str}{default_str}"
            )
        lines.append("")

        # Collect nested poly info for flattened display
        # Only collect FIRST-LEVEL nested poly here (e.g., cache__pool_type, not cache__pool__strategy_type)
        # Deeper levels are handled recursively in _format_flattened_nested_variants
        all_nested_poly: Dict[str, Tuple[Set[str], List[Argument]]] = {}

        # Get all nested args for this group
        all_group_nested_args: List[Argument] = []
        for arg in self.arguments.values():
            if arg.type_field and "__" in arg.type_field and arg.group == group.name:
                all_group_nested_args.append(arg)

        # Find first-level nested type fields (one more "__" than the primary type field)
        # If there's no group-level type selector, find the minimum depth of type fields
        if type_field_name:
            primary_depth = type_field_name.count("__")
        else:
            # Find the minimum depth of all type fields in this group
            type_field_depths = set()
            for arg in all_group_nested_args:
                if arg.type_field:
                    type_field_depths.add(arg.type_field.count("__"))
            primary_depth = min(type_field_depths) - 1 if type_field_depths else 0
        first_level_type_fields: Set[str] = set()

        for arg in all_group_nested_args:
            if arg.type_field is None:
                continue
            tf_depth = arg.type_field.count("__")
            if tf_depth == primary_depth + 1:
                first_level_type_fields.add(arg.type_field)

        # Collect args for each first-level nested type field
        for nested_tf in first_level_type_fields:
            # Get parent variants from the type selector itself
            type_selector = self.arguments.get(nested_tf)
            if type_selector and type_selector.variants:
                parent_variants = type_selector.variants
            else:
                # Fallback: find from args
                parent_variants = self._find_parent_variants_for_nested_field(
                    next(
                        (a for a in all_group_nested_args if a.type_field == nested_tf),
                        None,
                    )
                    or all_group_nested_args[0],
                    variants,
                )

            # Get the base path for this nested level (e.g., "cache__pool" from "cache__pool_type")
            base_path = nested_tf.rsplit("_type", 1)[0]

            # Collect ALL nested args (including deeper levels) that fall under this base path
            # e.g., for cache__pool_type, collect cache__pool__* and cache__pool__strategy__*
            nested_args = [
                a
                for a in all_group_nested_args
                if a.type_field is not None
                and (
                    a.type_field == nested_tf  # Direct match
                    or a.type_field.startswith(base_path + "__")  # Deeper nested
                )
            ]
            all_nested_poly[nested_tf] = (parent_variants, nested_args)

        # Show each top-level variant's options
        for variant_name in variant_names:
            variant_args = variants[variant_name]
            if not variant_args:
                continue

            # Separate top-level args from nested poly args
            top_level_args = [
                arg
                for arg in variant_args
                if not (arg.type_field and "__" in arg.type_field)
            ]

            # Sort: shared fields first, then variant-specific
            shared_args = [a for a in top_level_args if not a.variants]
            specific_args = [a for a in top_level_args if a.variants]
            sorted_top_args = shared_args + specific_args

            # Skip variants that have no top-level args (only nested poly)
            if not sorted_top_args:
                continue

            # Variant header showing config context and type
            # Get config name from the type_field of args in this variant
            config_name = "config"
            if sorted_top_args and sorted_top_args[0].type_field:
                # Extract config name from type_field (e.g., "controller_config" from "...__controller_config_type")
                tf = sorted_top_args[0].type_field
                if tf.endswith("_type"):
                    config_name = tf[:-5].split("__")[-1]
            formatted_config = _format_config_name(config_name)
            lines.append(
                f"  {c.dim(formatted_config + ' →')} {c.variant(variant_name)}"
            )

            # Show variant description if available
            if (
                group.name in self._variant_descriptions
                and variant_name in self._variant_descriptions[group.name]
            ):
                lines.append(
                    f"    {c.dim(self._variant_descriptions[group.name][variant_name])}"
                )

            for arg in sorted_top_args:
                lines.extend(
                    self._format_argument_help(
                        arg, show_variants=False, variant=variant_name, indent=2
                    )
                )
            lines.append("")

        # Show flattened nested poly variants after all top-level variants
        # Render each nested poly only once (not per parent variant)
        for nested_tf, (parent_variants, nested_args) in all_nested_poly.items():
            # Find a representative parent variant that's in top_level_variants
            representative_parent = None
            for pv in sorted(parent_variants):
                if pv in top_level_variants:
                    representative_parent = pv
                    break
            if representative_parent:
                lines.extend(
                    self._format_flattened_nested_variants(
                        nested_tf,
                        nested_args,
                        representative_parent,
                        primary_type_field=type_field_name,
                    )
                )

        return lines

    def _format_flattened_nested_variants(
        self,
        nested_type_field: str,
        nested_args: List[Argument],
        parent_variant: str,
        depth: int = 1,
        primary_type_field: Optional[str] = None,
    ) -> List[str]:
        """Format nested poly variants as flattened sections with parent context.

        Shows sections like [redis.pool: cluster] indented under parent,
        with a selector hint. Recursively handles deeper nesting.

        Args:
            nested_type_field: The type field (e.g., "cache__pool_type")
            nested_args: Arguments belonging to this nested poly level
            parent_variant: The parent variant path (e.g., "redis")
            depth: Current nesting depth (1 = first nested level)
            primary_type_field: The parent's primary type field to avoid duplication
        """
        c = self._color
        lines = []

        # Base indentation increases with depth
        base_indent = "    " * depth
        content_indent = base_indent + "  "

        # Get the nested type selector argument
        nested_type_arg = self.arguments.get(nested_type_field)
        if not nested_type_arg:
            return lines

        # Extract the nested field name (e.g., "cache__pool_type" -> "pool")
        parts = nested_type_field.replace("__", ".").split(".")
        nested_name = parts[-1].replace("_type", "") if parts else "nested"

        # Group nested args by their variant, separating direct args from deeper nested
        nested_variants: Dict[str, List[Argument]] = {}
        deeper_nested: Dict[str, Tuple[str, List[Argument]]] = (
            {}
        )  # type_field -> (parent, args)

        for arg in nested_args:
            # Check if this arg belongs to an even deeper nested poly
            if arg.type_field and arg.type_field != nested_type_field:
                # Count depth by number of "__" separators
                arg_depth = arg.type_field.count("__")
                current_depth = nested_type_field.count("__")
                if arg_depth > current_depth:
                    # This belongs to a deeper level - collect for later
                    if arg.type_field not in deeper_nested:
                        deeper_nested[arg.type_field] = (nested_type_field, [])
                    deeper_nested[arg.type_field][1].append(arg)
                    continue

            # Regular arg for this level
            if arg.variants:
                for v in arg.variants:
                    if v not in nested_variants:
                        nested_variants[v] = []
                    nested_variants[v].append(arg)
            else:
                # Shared across all nested variants
                for v in nested_type_arg.choices or []:
                    if v not in nested_variants:
                        nested_variants[v] = []
                    nested_variants[v].append(arg)

        if not nested_variants and not nested_type_arg.choices:
            return lines

        # Ensure all valid type choices are represented, even if they have no unique args
        all_choices = nested_type_arg.choices or []
        for choice in all_choices:
            if choice not in nested_variants:
                nested_variants[choice] = []

        # Show header and selector hint for nested poly
        # Use all choices from the type field, not just those with args
        variant_names = (
            sorted(all_choices) if all_choices else sorted(nested_variants.keys())
        )
        choices_str = c.choices("{" + ",".join(variant_names) + "}")
        default_str = ""
        if nested_type_arg.default:
            default_str = f" {c.dim('[' + str(nested_type_arg.default) + ']')}"

        # Format the config name properly (e.g., "resource_allocator_config" -> "Resource Allocator")
        formatted_name = _format_config_name(nested_name)
        lines.append(f"{base_indent}{c.header(formatted_name + ' Options:')}")

        # Show nested group description if available
        nested_group = nested_type_field.rsplit("_type", 1)[0]
        if nested_group in self._group_descriptions:
            lines.append(f"{content_indent}{self._group_descriptions[nested_group]}")

        # Only show type selector if it's different from the primary type field
        # (avoid redundant display of the same selector shown at parent level)
        if nested_type_field != primary_type_field:
            lines.append(
                f"{content_indent}Select with {c.option('--' + nested_type_arg.cli_name)} "
                f"{choices_str}{default_str}"
            )
        lines.append("")

        # Show each nested variant as an indented section
        for nested_variant in variant_names:
            variant_args = nested_variants[nested_variant]
            if not variant_args:
                continue

            # Variant header showing config context and type
            formatted_nested = _format_config_name(nested_name)
            lines.append(
                f"{content_indent}{c.dim(formatted_nested + ' →')} {c.variant(nested_variant)}"
            )

            # Show variant description if available
            if (
                nested_group in self._variant_descriptions
                and nested_variant in self._variant_descriptions[nested_group]
            ):
                lines.append(
                    f"{content_indent}  {self._variant_descriptions[nested_group][nested_variant]}"
                )

            # Format arguments with nested dataclass grouping
            lines.extend(
                self._format_grouped_arguments(
                    variant_args,
                    parent_context=nested_group,
                    show_variants=False,
                    variant=nested_variant,
                    base_indent=len(content_indent) + 2,
                )
            )

            # Check for even deeper nested poly within this variant
            for deeper_tf, (_, _) in deeper_nested.items():
                # Check if this deeper poly belongs to this variant
                # by looking at the deeper type selector's variants
                deeper_type_selector = self.arguments.get(deeper_tf)
                if deeper_type_selector:
                    parent_variants = deeper_type_selector.variants or set()
                    if nested_variant not in parent_variants:
                        continue  # This deeper poly doesn't belong to this variant

                # Collect ALL args under this deeper type field's base path
                # (including even deeper nested args)
                deeper_base_path = deeper_tf.rsplit("_type", 1)[0]
                all_deeper_args = [
                    a
                    for a in nested_args
                    if a.type_field is not None
                    and (
                        a.type_field == deeper_tf
                        or a.type_field.startswith(deeper_base_path + "__")
                    )
                ]

                # Get the parent variant for deeper level
                deeper_parent = f"{parent_variant}.{nested_name}: {nested_variant}"
                lines.extend(
                    self._format_flattened_nested_variants(
                        deeper_tf,
                        all_deeper_args,  # Pass all args under this path
                        deeper_parent,
                        depth + 1,
                        primary_type_field=primary_type_field,
                    )
                )

            lines.append("")

        return lines

    def _format_argument_help(
        self,
        arg: Argument,
        show_variants: bool = True,
        variant: Optional[str] = None,
        indent: int = 0,
    ) -> List[str]:
        """Format help text for a single argument with colors and type info.

        Format:
          --option <type> [default]
              Help text description
        """
        c = self._color
        lines = []
        prefix = " " * indent

        # Build argument string with type hint
        type_str = self._get_type_string(arg)

        # Build the option names (including aliases)
        option_names = [c.option("--" + arg.cli_name)]
        if arg.aliases:
            for alias in arg.aliases:
                option_names.append(c.dim("--" + alias))

        # Get default value for display
        default_display = self._get_default_display(arg, variant, show_variants)

        if default_display:
            suffix = f" {c.dim('[' + default_display + ']')}"
        else:
            suffix = ""

        if arg.is_boolean:
            bool_choices = c.choices("{true,false}")
            arg_str = f"{prefix}  {', '.join(option_names)} {bool_choices}"
            arg_str += suffix
        elif arg.choices:
            choices_str = c.choices("{" + ",".join(arg.choices) + "}")
            arg_str = f"{prefix}  {', '.join(option_names)} {choices_str}"
            arg_str += suffix
        else:
            arg_str = f"{prefix}  {', '.join(option_names)} {c.type_hint(type_str)}"
            arg_str += suffix

        # Add the argument line
        lines.append(arg_str)

        # Description indent (aligned under the option)
        desc_prefix = prefix + "      "

        # Help text line
        if arg.help_text:
            help_text = arg.help_text
            # Strip any existing "only for" annotations
            if "only for:" in help_text.lower():
                help_text = re.sub(r"\s*\(only for:[^)]+\)", "", help_text).strip()

            lines.append(f"{desc_prefix}{help_text}")

        # Variant info on its own line if applicable
        if show_variants and arg.variants and isinstance(arg.default, dict):
            variant_list = ", ".join(sorted(arg.variants))
            lines.append(f"{desc_prefix}{c.dim('only for: ' + variant_list)}")

        return lines

    def _format_grouped_arguments(
        self,
        args: List[Argument],
        parent_context: str,
        show_variants: bool = False,
        variant: Optional[str] = None,
        base_indent: int = 0,
    ) -> List[str]:
        """Format arguments grouped by their nested dataclass with sub-headers.

        Args:
            args: List of arguments to format
            parent_context: The parent context path (e.g., "inference_engine_config__controller_config__replica_controller_config")
            show_variants: Whether to show variant info
            variant: Current variant if applicable
            base_indent: Base indentation level

        Returns:
            Formatted lines with sub-headers for each nested dataclass group
        """
        c = self._color
        lines = []

        # Group arguments by their immediate nested dataclass parent
        groups: Dict[str, List[Argument]] = {}
        direct_args: List[Argument] = []

        for arg in args:
            nested_group = self._nested_groups.get(arg.name, "")

            if nested_group and nested_group != parent_context:
                # Check if this is a direct child of the parent context
                # by seeing if the nested_group starts with parent_context
                if parent_context and nested_group.startswith(parent_context + "__"):
                    # Extract the immediate child group name
                    remaining = nested_group[len(parent_context) + 2 :]
                    immediate_child = remaining.split("__")[0]
                    full_child_path = f"{parent_context}__{immediate_child}"

                    if full_child_path not in groups:
                        groups[full_child_path] = []
                    groups[full_child_path].append(arg)
                elif not parent_context and "__" in nested_group:
                    # Top level - group by first level
                    parts = nested_group.split("__")
                    if len(parts) >= 2:
                        immediate_child = "__".join(parts[:2])
                        if immediate_child not in groups:
                            groups[immediate_child] = []
                        groups[immediate_child].append(arg)
                    else:
                        direct_args.append(arg)
                else:
                    direct_args.append(arg)
            else:
                direct_args.append(arg)

        # Format direct arguments first
        for arg in direct_args:
            lines.extend(
                self._format_argument_help(
                    arg,
                    show_variants=show_variants,
                    variant=variant,
                    indent=base_indent,
                )
            )

        # Then format each nested group with its header
        for group_path in sorted(groups.keys()):
            group_args = groups[group_path]
            if not group_args:
                continue

            # Extract the group name from the path
            group_name = group_path.split("__")[-1]
            formatted_name = _format_config_name(group_name)

            # Show group header
            indent_str = " " * base_indent
            lines.append(f"{indent_str}{c.header(formatted_name + ':')}")

            # Show group description if available
            if group_path in self._nested_group_descriptions:
                lines.append(
                    f"{indent_str}  {c.dim(self._nested_group_descriptions[group_path])}"
                )

            # Recursively format this group's arguments (they may have sub-groups)
            lines.extend(
                self._format_grouped_arguments(
                    group_args,
                    parent_context=group_path,
                    show_variants=show_variants,
                    variant=variant,
                    base_indent=base_indent + 2,
                )
            )

        return lines

    def _get_default_display(
        self, arg: Argument, variant: Optional[str], show_variants: bool
    ) -> str:
        """Get the default value for inline display."""
        if isinstance(arg.default, dict):
            if variant and variant in arg.default:
                return str(arg.default[variant])
            elif not show_variants:
                return str(next(iter(arg.default.values())))
            else:
                # Multiple defaults - show first one
                return str(next(iter(arg.default.values())))
        elif arg.default is not None:
            return str(arg.default)
        # Show None for optional fields with no default
        elif not arg.required:
            return "None"
        return ""

    def _get_type_string(self, arg: Argument) -> str:
        """Get a human-readable type string for an argument."""
        if arg.is_boolean:
            return ""

        if arg.is_list:
            inner = self._type_name(arg.arg_type)
            return f"<{inner}...>"

        return f"<{self._type_name(arg.arg_type)}>"

    def _type_name(self, t: Union[type, Callable]) -> str:
        """Get the name of a type."""
        if t is int:
            return "int"
        if t is float:
            return "float"
        if t is str:
            return "str"
        if t is bool:
            return "bool"
        if isinstance(t, type) and issubclass(t, Enum):
            return "choice"
        if hasattr(t, "__name__"):
            name = t.__name__
            if name == "loads":  # json.loads
                return "json"
            return name
        return "value"

    def _format_yaml_example(self) -> List[str]:
        """Generate an example YAML configuration snippet."""
        c = self._color
        lines = []

        lines.append(c.header("Example YAML Config:"))
        lines.append(c.dim("  # Save as config.yaml and use with --config config.yaml"))
        lines.append("")

        # Group arguments by their top-level group
        top_level_args = []
        nested_groups: Dict[str, List[Argument]] = {}

        for arg in self.arguments.values():
            if "." in arg.cli_name:
                group_name = arg.cli_name.split(".")[0]
                if group_name not in nested_groups:
                    nested_groups[group_name] = []
                nested_groups[group_name].append(arg)
            else:
                top_level_args.append(arg)

        # Format top-level args
        for arg in top_level_args[:5]:  # Limit to first 5
            lines.append(self._format_yaml_arg(arg, indent=2))

        # Format one nested group as example
        if nested_groups:
            group_name = next(iter(nested_groups.keys()))
            group_args = nested_groups[group_name]

            lines.append(f"  {c.yaml_key(group_name + ':')}")
            for arg in group_args[:3]:  # Limit to first 3 per group
                # Get the field name (after the dot)
                field_name = arg.cli_name.split(".", 1)[1]
                default = self._get_example_value(arg)
                comment = (
                    f"  {c.yaml_comment('# ' + arg.help_text)}" if arg.help_text else ""
                )
                lines.append(
                    f"    {c.yaml_key(field_name + ':')} {c.yaml_value(str(default))}{comment}"
                )

        lines.append("")
        return lines

    def _format_yaml_arg(self, arg: Argument, indent: int = 0) -> str:
        """Format a single argument as YAML."""
        c = self._color
        prefix = " " * indent

        default = self._get_example_value(arg)
        comment = f"  {c.yaml_comment('# ' + arg.help_text)}" if arg.help_text else ""

        return f"{prefix}{c.yaml_key(arg.cli_name + ':')} {c.yaml_value(str(default))}{comment}"

    def _get_example_value(self, arg: Argument) -> Any:
        """Get an example value for YAML output."""
        if isinstance(arg.default, dict):
            return next(iter(arg.default.values()))
        if arg.default is not None:
            return arg.default
        if arg.choices:
            return arg.choices[0]
        if arg.arg_type is int:
            return 0
        if arg.arg_type is float:
            return 0.0
        if arg.arg_type is bool:
            return False
        return '""'
