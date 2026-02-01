"""Constants used throughout the Vidhi configuration library.

This module defines all magic strings, default values, and error messages
to avoid hardcoding throughout the codebase.
"""

# =============================================================================
# Field Naming Conventions
# =============================================================================

# Suffix added to polymorphic field names to store the selected type
FIELD_SUFFIX_TYPE = "_type"

# Separator used for hierarchy in nested field names (e.g., "database__host_name")
# Uses double underscore to distinguish from underscores within field names
FIELD_NAME_SEPARATOR = "__"


# =============================================================================
# Dictionary Keys
# =============================================================================

# Key used to store polymorphic type information in dictionaries
DICT_KEY_TYPE = "type"

# Key used to store alternative name information
DICT_KEY_NAME = "name"

# Internal key used during post-initialization
DICT_KEY_IN_POST_INIT = "_in_post_init"


# =============================================================================
# CLI Argument Formatting
# =============================================================================

# Separator used in CLI argument names (e.g., "--database.host")
CLI_ARG_SEPARATOR = "."

# Prefix for CLI arguments
CLI_ARG_PREFIX = "--"


# =============================================================================
# Default Values
# =============================================================================

# Maximum number of configuration combinations to prevent combinatorial explosion
DEFAULT_MAX_COMBINATIONS = 10_000

# Default nargs value for list arguments
DEFAULT_LIST_NARGS = "+"


# =============================================================================
# Special String Values
# =============================================================================

# String representation of None for type fields
TYPE_VALUE_NONE = "None"


# =============================================================================
# Error Messages
# =============================================================================

MSG_COMBINATORIAL_EXPLOSION = (
    "The number of generated configuration combinations ({count}) "
    "exceeds the allowed maximum of {max}. Reduce list sizes or "
    "increase the limit to avoid combinatorial explosion."
)

MSG_INVALID_TYPE_VALUE = (
    "No subclass of '{parent}' matches type value '{type_val}'. "
    "Valid types are: {valid_types}"
)

MSG_UNKNOWN_ARGUMENTS = "Unknown arguments provided for {class_name}: {extra_keys}"

MSG_MISSING_REQUIRED_FIELD = (
    "--{arg_name} is required when --{type_arg} is '{type_value}'"
)

MSG_FIELD_REQUIRES_DEFAULT = (
    "Field {field_name} of type {field_type} must have a default or default_factory"
)

MSG_ARGNAME_CONFLICT = (
    "Cannot have multiple fields with the same argname: {argname} "
    "already exists for field {existing_field}"
)

MSG_UNSUPPORTED_LIST_TYPE = (
    "Unsupported list element type '{element_type}'. "
    "Only primitives, dataclasses and BasePolyConfig subclasses are allowed."
)


# =============================================================================
# Metadata Keys
# =============================================================================

# Key for help text in field metadata
METADATA_KEY_HELP = "help"

# Key for custom argument name in field metadata
METADATA_KEY_ARGNAME = "argname"

# Key for CLI argument aliases in field metadata
METADATA_KEY_ALIASES = "aliases"

# Key for choices in field metadata
METADATA_KEY_CHOICES = "choices"


# =============================================================================
# Helper Functions for Common Operations
# =============================================================================


def to_cli_arg_name(field_name: str) -> str:
    """Convert a field name to CLI argument format.

    Converts double underscores (hierarchy separators) to dots.
    Single underscores within field names are preserved.
    Type fields (_type suffix) become .type for cleaner CLI.

    Args:
        field_name: The internal field name (e.g., "database__host_name")

    Returns:
        CLI argument name (e.g., "database.host_name")

    Example:
        >>> to_cli_arg_name("database__host_name")
        "database.host_name"
        >>> to_cli_arg_name("simple_field")
        "simple_field"
        >>> to_cli_arg_name("scheduler_type")
        "scheduler.type"
    """
    # Handle _type suffix -> .type
    if field_name.endswith("_type"):
        field_name = field_name[:-5] + "__type"

    # Convert __ to .
    return field_name.replace(FIELD_NAME_SEPARATOR, CLI_ARG_SEPARATOR)


def from_cli_arg_name(cli_arg_name: str) -> str:
    """Convert a CLI argument name to internal field name format.

    Converts dots to double underscores (hierarchy separators).
    This is the inverse of to_cli_arg_name for simple cases.

    Note: For fields with _config suffixes, this may not produce exact
    inverse since _config information is lost. The parser handles this
    via alias matching.

    Args:
        cli_arg_name: The CLI argument name (e.g., "database.host_name")

    Returns:
        Internal field name (e.g., "database__host_name")
    """
    # Handle .type suffix -> _type
    if cli_arg_name.endswith(".type"):
        cli_arg_name = cli_arg_name[:-5] + "_type"

    return cli_arg_name.replace(CLI_ARG_SEPARATOR, FIELD_NAME_SEPARATOR)


def get_type_field_name(field_name: str) -> str:
    """Get the type field name for a polymorphic field.

    Args:
        field_name: The base field name (e.g., "scheduler")

    Returns:
        The type field name (e.g., "scheduler_type")
    """
    return f"{field_name}{FIELD_SUFFIX_TYPE}"
