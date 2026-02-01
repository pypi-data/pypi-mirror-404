"""Validation framework for polymorphic and configuration arguments.

This module provides comprehensive validation at multiple stages:

1. Schema Validation (during flat dataclass creation):
   - Detects type conflicts (same field name, different types across variants)
   - Validates variant inheritance structure
   - Ensures all variants have valid get_type() implementations

2. Argument Validation (during CLI parsing):
   - Validates polymorphic type requirements
   - Checks required fields for selected variants
   - Warns about fields that won't be used by selected variant

3. Reconstruction Validation (before building final config):
   - Ensures required fields have values
   - Validates field types match expectations

All validation errors include detailed messages to help users fix issues.
"""

from __future__ import annotations

import logging
from dataclasses import MISSING
from dataclasses import fields as get_fields
from typing import Any, Dict, List, Set, Type

from vidhi.constants import (
    CLI_ARG_SEPARATOR,
    FIELD_NAME_SEPARATOR,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Validation Exceptions
# =============================================================================


class ValidationError(Exception):
    """Base class for validation errors."""


class SchemaValidationError(ValidationError):
    """Raised when the schema definition has conflicts or issues.

    This is raised during flat dataclass creation when there are problems
    with the polymorphic config structure, such as type conflicts.
    """


class ArgumentValidationError(ValidationError):
    """Raised when CLI arguments are invalid for the selected variant."""


class ReconstructionValidationError(ValidationError):
    """Raised when the configuration cannot be reconstructed properly."""


# =============================================================================
# Validation Result Classes
# =============================================================================


class ValidationResult:
    """Base class for validation results."""

    def __init__(self, context: str):
        self.context = context
        self.errors: List[Dict[str, Any]] = []
        self.warnings: List[str] = []

    def add_error(self, error_type: str, message: str, **details):
        """Add an error to the result."""
        self.errors.append(
            {
                "type": error_type,
                "message": message,
                **details,
            }
        )

    def add_warning(self, message: str):
        """Add a warning to the result."""
        self.warnings.append(message)

    @property
    def is_valid(self) -> bool:
        """Return True if there are no errors."""
        return len(self.errors) == 0

    def raise_if_invalid(
        self, exception_class: Type[ValidationError] = ValidationError
    ):
        """Raise an exception if there are validation errors."""
        if not self.is_valid:
            messages = [e["message"] for e in self.errors]
            raise exception_class(
                f"Validation failed for '{self.context}':\n"
                + "\n".join(f"  - {msg}" for msg in messages)
            )

    def format_errors(self) -> str:
        """Format errors as a readable string."""
        if not self.errors:
            return "No errors"
        return "\n".join(f"  - {e['message']}" for e in self.errors)

    def format_warnings(self) -> str:
        """Format warnings as a readable string."""
        if not self.warnings:
            return "No warnings"
        return "\n".join(f"  - {w}" for w in self.warnings)


class SchemaValidationResult(ValidationResult):
    """Result of schema validation for a polymorphic config field."""

    def __init__(self, poly_field_name: str):
        super().__init__(poly_field_name)
        self.field_info: Dict[str, Dict[str, Any]] = {}
        self.variant_types: Dict[str, Type] = {}

    def raise_if_invalid(
        self, exception_class: Type[ValidationError] = SchemaValidationError
    ):
        """Raise SchemaValidationError if there are errors."""
        super().raise_if_invalid(exception_class)

    def get_type_conflicts(self) -> List[Dict[str, Any]]:
        """Get all type conflict errors."""
        return [e for e in self.errors if e["type"] == "type_conflict"]

    def has_type_conflicts(self) -> bool:
        """Check if there are any type conflicts."""
        return len(self.get_type_conflicts()) > 0


# =============================================================================
# Schema Validation
# =============================================================================


def _normalize_type(t: Any) -> str:
    """Normalize a type for comparison.

    This handles generic types, optional types, and regular types to produce
    a consistent string representation for comparison.
    """
    # Handle None type
    if t is type(None):
        return "NoneType"

    # Handle generic types (List[X], Dict[K, V], Optional[X], etc.)
    origin = getattr(t, "__origin__", None)
    if origin is not None:
        args = getattr(t, "__args__", ())
        # Filter out NoneType for Optional comparison
        non_none_args = [a for a in args if a is not type(None)]
        if len(non_none_args) != len(args):
            # This was an Optional type, normalize without NoneType
            if len(non_none_args) == 1:
                return f"Optional[{_normalize_type(non_none_args[0])}]"
        args_str = ", ".join(_normalize_type(a) for a in args)
        origin_name = getattr(origin, "__name__", str(origin))
        return f"{origin_name}[{args_str}]"

    # Handle regular types
    if isinstance(t, type):
        return t.__name__

    return str(t)


def _type_repr(t: Any) -> str:
    """Get a human-readable representation of a type."""
    if isinstance(t, type):
        return t.__name__
    origin = getattr(t, "__origin__", None)
    if origin is not None:
        args = getattr(t, "__args__", ())
        args_str = ", ".join(_type_repr(a) for a in args)
        origin_name = getattr(origin, "__name__", str(origin))
        return f"{origin_name}[{args_str}]"
    return str(t)


def validate_poly_schema(
    poly_field_name: str,
    subclasses: List[Type],
    base_class: Type,
    raise_on_error: bool = True,
) -> SchemaValidationResult:
    """Validate the schema of a polymorphic config field.

    This should be called during flat dataclass creation to detect issues
    like type conflicts early, before any CLI parsing happens.

    Checks performed:
    - All variants implement get_type()
    - No duplicate type keys across variants
    - No type conflicts (same field name with different types)

    Args:
        poly_field_name: Name of the polymorphic field (e.g., "scheduler")
        subclasses: List of variant subclasses
        base_class: The base polymorphic config class
        raise_on_error: If True, raise SchemaValidationError on errors

    Returns:
        SchemaValidationResult with any errors or warnings

    Raises:
        SchemaValidationError: If raise_on_error is True and there are errors

    Example:
        >>> result = validate_poly_schema("scheduler", [GreedyScheduler, BeamScheduler], BaseScheduler)
        >>> if not result.is_valid:
        ...     print(result.format_errors())
    """
    result = SchemaValidationResult(poly_field_name)

    # Collect field info from all variants
    field_info: Dict[str, Dict[str, Any]] = {}
    variant_types: Dict[str, Type] = {}

    for subclass in subclasses:
        # Get variant type key
        try:
            variant_type = subclass.get_type()
            # Handle enums with integer values (e.g., pybind11 C++ enums)
            if hasattr(variant_type, "value"):
                if isinstance(variant_type.value, str):
                    type_key = variant_type.value.lower()
                elif hasattr(variant_type, "name"):
                    type_key = variant_type.name.lower()
                else:
                    type_key = str(variant_type.value).lower()
            elif hasattr(variant_type, "name"):
                type_key = variant_type.name.lower()
            else:
                type_key = str(variant_type).lower()
        except NotImplementedError:
            result.add_error(
                "missing_type",
                f"Variant '{subclass.__name__}' does not implement get_type(). "
                f"All variants of '{base_class.__name__}' must implement get_type() "
                f"to return their type discriminator.",
                subclass=subclass.__name__,
                base_class=base_class.__name__,
            )
            continue

        # Check for duplicate type keys
        if type_key in variant_types:
            result.add_error(
                "duplicate_type",
                f"Multiple variants have the same type key '{type_key}': "
                f"'{variant_types[type_key].__name__}' and '{subclass.__name__}'. "
                f"Each variant must have a unique type value.",
                type_key=type_key,
                variants=[variant_types[type_key].__name__, subclass.__name__],
            )
        variant_types[type_key] = subclass

        # Collect fields from this variant
        for field in get_fields(subclass):
            field_name = field.name
            field_type = field.type

            # Get default value
            if field.default is not MISSING:
                default = field.default
            elif field.default_factory is not MISSING:
                default = field.default_factory
            else:
                default = MISSING

            if field_name not in field_info:
                field_info[field_name] = {
                    "types": {},
                    "variants": [],
                    "defaults": {},
                }

            field_info[field_name]["types"][type_key] = field_type
            field_info[field_name]["variants"].append(type_key)
            field_info[field_name]["defaults"][type_key] = default

    # Check for type conflicts
    for field_name, info in field_info.items():
        unique_types: Dict[str, List[str]] = {}  # normalized_type -> [variants]

        for variant_key, field_type in info["types"].items():
            type_str = _normalize_type(field_type)
            if type_str not in unique_types:
                unique_types[type_str] = []
            unique_types[type_str].append(variant_key)

        if len(unique_types) > 1:
            type_details = {k: _type_repr(v) for k, v in info["types"].items()}
            conflicting_types = list(unique_types.keys())
            result.add_error(
                "type_conflict",
                f"Field '{field_name}' has incompatible types across variants:\n"
                + "\n".join(
                    f"    - {variant}: {_type_repr(info['types'][variant])}"
                    for variant in info["variants"]
                )
                + f"\n  Solution: Use unique field names for fields with different types "
                f"(e.g., '{field_name}_v1' and '{field_name}_v2').",
                field=field_name,
                types=type_details,
                variants=info["variants"],
                conflicting_types=conflicting_types,
            )

    # Store validated schema info for later use
    result.field_info = field_info
    result.variant_types = variant_types

    if raise_on_error:
        result.raise_if_invalid()

    return result


def validate_variant_field_access(
    poly_field_name: str,
    selected_type: str,
    provided_args: Set[str],
    field_info: Dict[str, Dict[str, Any]],
    variant_types: Dict[str, Type],
) -> List[str]:
    """Check for fields provided for wrong variants and return warnings.

    Args:
        poly_field_name: Name of the polymorphic field
        selected_type: The selected variant type
        provided_args: Set of argument names that were provided
        field_info: Field information from schema validation
        variant_types: Mapping of type keys to variant classes

    Returns:
        List of warning messages for unused fields
    """
    warnings = []
    type_key = selected_type.lower()

    if type_key not in variant_types:
        return warnings  # Invalid type handled elsewhere

    prefix = f"{poly_field_name}{FIELD_NAME_SEPARATOR}"
    for arg in provided_args:
        if arg.startswith(prefix):
            # Extract the immediate field name (not nested)
            remainder = arg[len(prefix) :]
            field_name = remainder.split(FIELD_NAME_SEPARATOR)[0]

            if field_name in field_info:
                info = field_info[field_name]
                if type_key not in info["variants"]:
                    valid_variants = info["variants"]
                    cli_arg = arg.replace(FIELD_NAME_SEPARATOR, CLI_ARG_SEPARATOR)
                    warnings.append(
                        f"Argument '--{cli_arg}' is not used by variant '{selected_type}'. "
                        f"This field is only valid for: {', '.join(valid_variants)}"
                    )

    return warnings


def overwrite_args_with_config(
    args_namespace: Any,
    config_dict: Dict[str, Any],
    keys_to_file_field_names: Dict[str, str],
    default_values: Dict[str, Any],
    cli_provided_args: Set[str],
) -> None:
    """Overwrite args with values from config, respecting CLI precedence.

    This function recursively merges configuration values from files into the
    argument namespace, skipping any values that were explicitly provided via
    CLI (CLI takes precedence).

    Args:
        args_namespace: The argument namespace to overwrite. Must be flat.
        config_dict: The configuration dictionary to merge. Can be nested.
        keys_to_file_field_names: Maps config keys to the file field names that provided them.
        default_values: Default values for arguments.
        cli_provided_args: Set of argument names explicitly provided via CLI.
    """
    for key, value in config_dict.items():
        if isinstance(value, dict):
            # Recursively process nested config objects
            overwrite_args_with_config(
                args_namespace,
                value,
                keys_to_file_field_names,
                default_values,
                cli_provided_args,
            )
            continue

        # Skip unrecognized keys
        if not hasattr(args_namespace, key):
            source = keys_to_file_field_names.get(key, "unknown")
            logger.warning(
                f"Arg {key} provided by {source} not found in supported args."
            )
            continue

        # Apply config value if not overridden by CLI
        if key not in cli_provided_args:
            logger.debug(f"Setting {key} from config file to {value}")
            setattr(args_namespace, key, value)
        else:
            source = keys_to_file_field_names.get(key, "unknown")
            logger.debug(
                f"Arg {key} provided by {source} skipped (CLI takes precedence)"
            )
