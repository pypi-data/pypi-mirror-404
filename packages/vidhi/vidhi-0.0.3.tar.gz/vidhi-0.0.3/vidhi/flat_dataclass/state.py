"""State management for dataclass flattening process.

This module handles the state tracking during the flattening process:
- Field collection (with/without defaults)
- Dependency tracking
- Metadata mapping
- Polymorphic config tracking
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import MISSING, fields, make_dataclass
from typing import Any, Dict, Optional, Type, get_args

from vidhi.base_poly_config import BasePolyConfig
from vidhi.constants import (
    FIELD_NAME_SEPARATOR,
    FIELD_SUFFIX_TYPE,
    METADATA_KEY_HELP,
)
from vidhi.flat_dataclass.validation import validate_poly_schema
from vidhi.utils import (
    get_all_subclasses,
    get_inner_type,
    is_list,
    is_optional,
    is_subclass,
    to_snake_case,
)


def _get_type_key(type_val: Any) -> str:
    """Get a string type key from a polymorphic type value.

    Handles enums (both Python and pybind11 C++ enums) by preferring
    string values, falling back to enum names for integer values.

    Args:
        type_val: The type value from get_type(), typically an enum

    Returns:
        A lowercase string suitable for use as a type key
    """
    if hasattr(type_val, "value"):
        # If value is a string, use it directly
        if isinstance(type_val.value, str):
            return type_val.value.lower()
        # For integer values (e.g., pybind11 C++ enums), use name instead
        elif hasattr(type_val, "name"):
            return type_val.name.lower()
        else:
            return str(type_val.value).lower()
    elif hasattr(type_val, "name"):
        return type_val.name.lower()
    else:
        return str(type_val).lower()


def _initialize_dataclass_state() -> Dict[str, Any]:
    """Initialize collections for tracking dataclass metadata during flattening.

    Returns:
        Dictionary containing all state tracking structures:
        - fields_with_defaults: List of fields that have default values
        - fields_without_defaults: List of required fields
        - dataclass_args: Maps dataclass names to their field definitions
        - dataclass_dependencies: Maps dataclass names to their dependencies
        - metadata_mapping: Maps field names to their metadata
        - names_to_classes: Maps unique dataclass names to classes
        - base_poly_children: Maps poly configs to their child classes
        - base_poly_children_types: Maps poly configs to child type names
        - args_with_default_none: Set of fields with None defaults
        - list_fields: Maps list field names to their inner types
        - poly_variant_fields: Set of polymorphic variant field names
    """
    return {
        "fields_with_defaults": [],
        "fields_without_defaults": [],
        "dataclass_args": defaultdict(list),
        "dataclass_dependencies": defaultdict(
            list
        ),  # maps unique nested dataclass names to their uniquely named dependencies
        "metadata_mapping": {},
        "names_to_classes": {},  # maps unique nested dataclass names to their corresponding dataclass class
        "base_poly_children": {},  # maps unique (by name) base poly configs to {children names: children classes} (Dict[str, Dict[str, Any]])
        "base_poly_children_types": {},  # maps unique (by name) base poly configs to {children types: children names} (Dict[str, Dict[str, str]])
        "args_with_default_none": set(),  # the set of args that have a default value of None
        "list_fields": {},  # maps list field (prefixed) names to their inner types
        "poly_variant_fields": set(),  # set of field names that belong to polymorphic config variants (should not be marked required)
        "poly_field_variants": {},  # maps field names to their valid variants and type field
        "poly_variant_defaults": {},  # maps poly_field_name -> {field_name: {variant: default_value}}
        "poly_default_types": {},  # maps poly_field_name -> default variant type
        "nested_groups": {},  # maps field names to their parent nested dataclass path (e.g., "a__b__c" -> "a__b")
        "nested_group_docs": {},  # maps nested dataclass paths to their docstrings
    }


def _get_field_type_info(field: Any) -> tuple:
    """Extract type information from a dataclass field.

    Args:
        field: Dataclass field to inspect

    Returns:
        Tuple of (field_type, is_optional)
    """
    if is_optional(field.type):
        return get_inner_type(field.type), True
    return field.type, False


def _get_default_value_for_poly_field(field: Any, field_type: Type[Any]) -> str:
    """Get the default value for a polymorphic config field.

    Args:
        field: The dataclass field
        field_type: The field's type

    Returns:
        The default type value as a string (uses enum value if available)

    Raises:
        ValueError: If the field has no default or default_factory, or if get_type() is not implemented
    """
    if field.default_factory is not MISSING:
        default_instance = field.default_factory()
        default_class = type(default_instance)
        try:
            type_val = default_instance.get_type()
        except NotImplementedError:
            subclasses = list(get_all_subclasses(field_type))
            raise ValueError(
                f"Polymorphic config error for field '{field.name}':\n"
                f"  {default_class.__name__}.get_type() is not implemented.\n"
                f"  \n"
                + _get_poly_config_fix_message(field_type, default_class, subclasses)
            ) from None
    elif field.default is not MISSING:
        if field.default is None:
            return "None"
        default_class = type(field.default)
        try:
            type_val = field.default.get_type()
        except NotImplementedError:
            subclasses = list(get_all_subclasses(field_type))
            raise ValueError(
                f"Polymorphic config error for field '{field.name}':\n"
                f"  {default_class.__name__}.get_type() is not implemented.\n"
                f"  \n"
                + _get_poly_config_fix_message(field_type, default_class, subclasses)
            ) from None
    else:
        raise ValueError(
            f"Field {field.name} of type {field_type} must have a default or default_factory"
        )

    # Get the type key using the same logic as elsewhere
    return _get_type_key(type_val)


def _get_poly_config_fix_message(
    field_type: Type[Any], default_class: Type[Any], subclasses: list
) -> str:
    """Generate a helpful error message for polymorphic config issues."""
    if not subclasses:
        # No subclasses - the class itself extends BasePolyConfig directly
        return (
            f"  The class {field_type.__name__} extends BasePolyConfig but has no subclasses.\n"
            f"  BasePolyConfig requires at least one subclass that implements get_type().\n"
            f"  \n"
            f"  To fix this, create an abstract base class:\n"
            f"    @frozen_dataclass\n"
            f"    class Abstract{field_type.__name__}(BasePolyConfig):\n"
            f"        pass\n"
            f"    \n"
            f"    @frozen_dataclass\n"
            f"    class {field_type.__name__}(Abstract{field_type.__name__}):\n"
            f"        # ... fields ...\n"
            f"        \n"
            f"        @staticmethod\n"
            f"        def get_type() -> YourEnumType:\n"
            f"            return YourEnumType.YOUR_VALUE\n"
            f"  \n"
            f"  Or, if polymorphism is not needed, remove BasePolyConfig inheritance."
        )
    else:
        # Has subclasses but one doesn't implement get_type()
        return (
            f"  All concrete subclasses of BasePolyConfig must implement get_type().\n"
            f"  \n"
            f"  To fix this, add get_type() to {default_class.__name__}:\n"
            f"    @staticmethod\n"
            f"    def get_type() -> YourEnumType:\n"
            f"        return YourEnumType.YOUR_VALUE"
        )


def _handle_polymorphic_config_field(
    flattening_state: Dict[str, Any],
    field: Any,
    field_type: Type[Any],
    prefixed_name: str,
    prefixed_input_dataclass: str,
    prefix: str,
) -> None:
    """Process a field that is a BasePolyConfig subclass.

    This uses a unified field naming scheme where all variants share the same
    field names (e.g., --scheduler.max_pending instead of --greedy.scheduler.max_pending).
    Variant-specific fields are validated at parse time based on the selected type.

    Args:
        flattening_state: State dictionary tracking flattening process
        field: The polymorphic field
        field_type: The field's type
        prefixed_name: Prefixed field name
        prefixed_input_dataclass: Name of the parent dataclass
        prefix: Current prefix string
    """
    flattening_state["dataclass_args"][prefixed_input_dataclass].append(
        (prefixed_name, field.name, field_type)
    )
    flattening_state["base_poly_children"][prefixed_name] = {}
    flattening_state["base_poly_children_types"][prefixed_name] = {}

    type_field_name = f"{prefixed_name}{FIELD_SUFFIX_TYPE}"
    default_value = _get_default_value_for_poly_field(field, field_type)

    # Get all valid type choices and collect subclass info
    valid_types = []
    subclasses = list(get_all_subclasses(field_type))

    # Validate: BasePolyConfig must have at least one subclass
    if not subclasses:
        raise ValueError(
            f"Polymorphic config error for field '{field.name}':\n"
            f"  {field_type.__name__} has no subclasses.\n"
            f"  \n" + _get_poly_config_fix_message(field_type, field_type, subclasses)
        )

    # Validate: Each subclass must implement get_type()
    for subclass in subclasses:
        try:
            subclass.get_type()
        except NotImplementedError:
            raise ValueError(
                f"Polymorphic config error for field '{field.name}':\n"
                f"  {subclass.__name__}.get_type() is not implemented.\n"
                f"  \n" + _get_poly_config_fix_message(field_type, subclass, subclasses)
            ) from None

    # Validate the polymorphic schema - this will raise SchemaValidationError
    # if there are type conflicts or other issues
    schema_result = validate_poly_schema(
        prefixed_name, subclasses, field_type, raise_on_error=True
    )

    # Store schema validation result for later use in argument validation
    if "poly_schema_results" not in flattening_state:
        flattening_state["poly_schema_results"] = {}
    flattening_state["poly_schema_results"][prefixed_name] = schema_result

    for subclass in subclasses:
        subclass_type = subclass.get_type()
        valid_types.append(_get_type_key(subclass_type))

    # Create help text for type field with valid choices
    type_help = f"Type of {field.name}. Choices: {', '.join(sorted(valid_types))}"

    flattening_state["fields_with_defaults"].append(
        (type_field_name, type(default_value), default_value)
    )
    flattening_state["metadata_mapping"][type_field_name] = {
        METADATA_KEY_HELP: type_help
    }

    # Store the default variant type for this poly field
    flattening_state["poly_default_types"][prefixed_name] = default_value

    # Collect all fields from all subclasses, tracking which variants have each field
    # Also track variant-specific defaults
    all_variant_fields: Dict[str, Dict[str, Any]] = (
        {}
    )  # field_name -> {type, field, variants, variant_defaults}

    # Initialize variant defaults tracking for this poly field
    flattening_state["poly_variant_defaults"][prefixed_name] = {}

    for subclass in subclasses:
        # Get the type key - use enum value if available, otherwise enum name
        subclass_type = subclass.get_type()
        type_key = _get_type_key(subclass_type)

        # Use the polymorphic field name as the child node (not variant-prefixed)
        child_node_name = prefixed_name

        # map the child node name to the subclass
        flattening_state["base_poly_children"][prefixed_name][type_key] = subclass
        # map type -> child node name (all map to same node now)
        flattening_state["base_poly_children_types"][prefixed_name][
            type_key
        ] = child_node_name

        # Collect fields from this subclass
        for sub_field in fields(subclass):
            field_key = sub_field.name
            sub_field_type, _ = _get_field_type_info(sub_field)

            # Get the default value for this variant
            if sub_field.default is not MISSING:
                variant_default = sub_field.default
            elif sub_field.default_factory is not MISSING:
                variant_default = sub_field.default_factory
            else:
                variant_default = MISSING

            if field_key not in all_variant_fields:
                all_variant_fields[field_key] = {
                    "type": sub_field_type,
                    "field": sub_field,
                    "variants": set(),
                    "variant_defaults": {},
                }
            all_variant_fields[field_key]["variants"].add(type_key)
            all_variant_fields[field_key]["variant_defaults"][
                type_key
            ] = variant_default

            # Store variant-specific default in state
            full_field_name = f"{prefixed_name}{FIELD_NAME_SEPARATOR}{field_key}"
            if (
                full_field_name
                not in flattening_state["poly_variant_defaults"][prefixed_name]
            ):
                flattening_state["poly_variant_defaults"][prefixed_name][
                    full_field_name
                ] = {}
            flattening_state["poly_variant_defaults"][prefixed_name][full_field_name][
                type_key
            ] = variant_default

    # Ensure parent depends on this polymorphic field
    flattening_state["dataclass_dependencies"][prefixed_input_dataclass].append(
        prefixed_name
    )

    # Initialize dependency tracking for the polymorphic config
    _ = flattening_state["dataclass_dependencies"][prefixed_name]
    flattening_state["names_to_classes"][prefixed_name] = field_type

    # Process collected fields - use unified names (scheduler.field, not greedy.scheduler.field)
    poly_field_prefix = f"{prefixed_name}{FIELD_NAME_SEPARATOR}"

    for field_name, field_info in all_variant_fields.items():
        sub_field = field_info["field"]
        sub_field_type = field_info["type"]
        variants = field_info["variants"]
        variant_defaults = field_info["variant_defaults"]

        full_field_name = f"{poly_field_prefix}{field_name}"

        # Determine if this is a common field (all variants) or variant-specific
        is_common = len(variants) == len(subclasses)

        # Check if this is a nested type that will be processed recursively
        is_nested_poly = is_subclass(sub_field_type, BasePolyConfig)
        is_nested_dataclass = (
            hasattr(sub_field_type, "__dataclass_fields__") and not is_nested_poly
        )

        # Only add primitive/list fields to fields_with_defaults
        # Nested types will be handled by recursive calls
        if not is_nested_poly and not is_nested_dataclass:
            # Get default value - use the default variant's default, not just any variant
            # The default_value (from _get_default_value_for_poly_field) tells us which variant is default
            field_default = MISSING
            field_default_factory = MISSING

            # Use the default variant's default value for this field
            if default_value in variant_defaults:
                variant_def = variant_defaults[default_value]
                if variant_def is not MISSING:
                    if callable(variant_def) and not isinstance(variant_def, type):
                        field_default_factory = variant_def
                    else:
                        field_default = variant_def
            else:
                # Fallback: use the first variant's default if field exists
                for variant_key in variant_defaults:
                    variant_def = variant_defaults[variant_key]
                    if variant_def is not MISSING:
                        if callable(variant_def) and not isinstance(variant_def, type):
                            field_default_factory = variant_def
                        else:
                            field_default = variant_def
                        break

            if field_default is not MISSING:
                flattening_state["fields_with_defaults"].append(
                    (full_field_name, sub_field_type, field_default)
                )
            elif field_default_factory is not MISSING:
                flattening_state["fields_with_defaults"].append(
                    (full_field_name, sub_field_type, field_default_factory)
                )
            else:
                # Required field - but for polymorphic variants, treat as optional
                flattening_state["fields_with_defaults"].append(
                    (full_field_name, Optional[sub_field_type], None)
                )

            # Build help text - CLI parser handles variant info display
            help_text = sub_field.metadata.get(METADATA_KEY_HELP, "")

            flattening_state["metadata_mapping"][full_field_name] = {
                **sub_field.metadata,
                METADATA_KEY_HELP: help_text,
            }

        # Track polymorphic variant fields for validation
        flattening_state["poly_variant_fields"].add(full_field_name)

        # Track which variants this field belongs to (for validation)
        if "poly_field_variants" not in flattening_state:
            flattening_state["poly_field_variants"] = {}
        flattening_state["poly_field_variants"][full_field_name] = {
            "variants": variants,
            "type_field": type_field_name,
        }

        # Handle nested types within polymorphic fields
        if is_nested_poly:
            # Nested polymorphic config - process recursively
            flattening_state["dataclass_args"][prefixed_name].append(
                (full_field_name, field_name, sub_field_type)
            )
            _handle_polymorphic_config_field(
                flattening_state,
                sub_field,
                sub_field_type,
                full_field_name,
                prefixed_name,
                f"{full_field_name}{FIELD_NAME_SEPARATOR}",
            )
        elif is_nested_dataclass:
            # Nested regular dataclass - process recursively
            flattening_state["dataclass_args"][prefixed_name].append(
                (full_field_name, field_name, sub_field_type)
            )
            # Track fields before processing to identify new nested fields
            fields_before = set(flattening_state["metadata_mapping"].keys())

            _handle_nested_dataclass_field(
                flattening_state,
                sub_field,
                sub_field_type,
                full_field_name,
                prefixed_name,
            )

            # Propagate poly variant info to all newly created nested fields
            fields_after = set(flattening_state["metadata_mapping"].keys())
            new_nested_fields = fields_after - fields_before
            for nested_field_name in new_nested_fields:
                if "poly_field_variants" not in flattening_state:
                    flattening_state["poly_field_variants"] = {}
                flattening_state["poly_field_variants"][nested_field_name] = {
                    "variants": variants,
                    "type_field": type_field_name,
                }
        elif is_list(sub_field_type):
            # List field
            flattening_state["dataclass_args"][prefixed_name].append(
                (full_field_name, field_name, sub_field_type)
            )
            inner_type = get_args(sub_field_type)[0]
            flattening_state["list_fields"][full_field_name] = inner_type
        else:
            # Primitive field
            flattening_state["dataclass_args"][prefixed_name].append(
                (full_field_name, field_name, sub_field_type)
            )


def _handle_nested_dataclass_field(
    flattening_state: Dict[str, Any],
    field: Any,
    field_type: Type[Any],
    prefixed_name: str,
    prefixed_input_dataclass: str,
) -> None:
    """Process a field that is a nested dataclass.

    Args:
        flattening_state: State dictionary tracking flattening process
        field: The nested dataclass field
        field_type: The field's type
        prefixed_name: Prefixed field name
        prefixed_input_dataclass: Name of the parent dataclass
    """
    dependency_name = prefixed_name
    flattening_state["dataclass_dependencies"][prefixed_input_dataclass].append(
        dependency_name
    )
    flattening_state["dataclass_args"][prefixed_input_dataclass].append(
        (prefixed_name, field.name, field_type)
    )

    # Store the nested dataclass docstring (first line only)
    if field_type.__doc__:
        doc = field_type.__doc__.strip().split("\n")[0]
        flattening_state["nested_group_docs"][prefixed_name] = doc

    _process_single_dataclass(
        flattening_state, field_type, f"{prefixed_name}{FIELD_NAME_SEPARATOR}"
    )


def _handle_primitive_field(
    flattening_state: Dict[str, Any],
    field: Any,
    field_type: Type[Any],
    prefixed_name: str,
    prefixed_input_dataclass: str,
) -> None:
    """Process a field that is a primitive type.

    Args:
        flattening_state: State dictionary tracking flattening process
        field: The primitive field
        field_type: The field's type
        prefixed_name: Prefixed field name
        prefixed_input_dataclass: Name of the parent dataclass
    """
    field_default = field.default if field.default is not MISSING else MISSING
    field_default_factory = (
        field.default_factory if field.default_factory is not MISSING else MISSING
    )

    if field_default is not MISSING:
        flattening_state["fields_with_defaults"].append(
            (prefixed_name, field_type, field_default)
        )
    elif field_default_factory is not MISSING:
        flattening_state["fields_with_defaults"].append(
            (prefixed_name, field_type, field_default_factory)
        )
    else:
        flattening_state["fields_without_defaults"].append((prefixed_name, field_type))

    flattening_state["dataclass_args"][prefixed_input_dataclass].append(
        (prefixed_name, field.name, field_type)
    )
    flattening_state["metadata_mapping"][prefixed_name] = field.metadata

    # Track which nested group this field belongs to
    flattening_state["nested_groups"][prefixed_name] = prefixed_input_dataclass

    # a list can contain poly configs or nested dataclasses
    if is_list(field_type):
        inner_type = get_args(field_type)[0]
        flattening_state["list_fields"][prefixed_name] = inner_type


def _process_single_dataclass(
    flattening_state: Dict[str, Any],
    input_dataclass: Type[Any],
    prefix: str = "",
    is_poly_variant: bool = False,
) -> None:
    """Process a single dataclass, flattening its fields and handling special cases.

    Args:
        flattening_state: The state dictionary tracking all dataclass metadata
        input_dataclass: The dataclass to process
        prefix: Prefix to add to field names
        is_poly_variant: True if this dataclass is a variant of a polymorphic config
    """
    prefixed_class_name = (
        f"{prefix[:-len(FIELD_NAME_SEPARATOR)]}"
        if prefix
        else f"{to_snake_case(input_dataclass.__name__)}"
    )

    # initialize dependency tracking for this dataclass
    _ = flattening_state["dataclass_dependencies"][prefixed_class_name]
    flattening_state["names_to_classes"][prefixed_class_name] = input_dataclass

    # process each field in the dataclass
    for field in fields(input_dataclass):
        prefixed_name = f"{prefix}{field.name}"
        field_type, _ = _get_field_type_info(field)

        if field.default is None:
            flattening_state["args_with_default_none"].add(prefixed_name)

        # Mark this field as belonging to a polymorphic variant
        if is_poly_variant:
            flattening_state["poly_variant_fields"].add(prefixed_name)

        if is_subclass(field_type, BasePolyConfig):
            _handle_polymorphic_config_field(
                flattening_state,
                field,
                field_type,
                prefixed_name,
                prefixed_class_name,
                prefix,
            )
        elif hasattr(field_type, "__dataclass_fields__"):
            _handle_nested_dataclass_field(
                flattening_state, field, field_type, prefixed_name, prefixed_class_name
            )
        else:
            _handle_primitive_field(
                flattening_state, field, field_type, prefixed_name, prefixed_class_name
            )


def _create_flat_class_type(flattening_state: Dict[str, Any]) -> Type[Any]:
    """Create the final flattened dataclass type with all metadata attached.

    Args:
        flattening_state: State dictionary with all collected metadata

    Returns:
        The flattened dataclass type with methods and metadata attached
    """
    all_fields = (
        flattening_state["fields_without_defaults"]
        + flattening_state["fields_with_defaults"]
    )
    flat_dataclass_type = make_dataclass("FlatClass", all_fields)

    # attach metadata to the class
    flat_dataclass_type.dataclass_args = flattening_state["dataclass_args"]
    flat_dataclass_type.dataclass_dependencies = flattening_state[
        "dataclass_dependencies"
    ]
    flat_dataclass_type.dataclass_names_to_classes = flattening_state[
        "names_to_classes"
    ]
    flat_dataclass_type.metadata_mapping = flattening_state["metadata_mapping"]
    flat_dataclass_type.dataclass_file_fields = {}  # Legacy, kept for compatibility
    flat_dataclass_type.base_poly_children = flattening_state["base_poly_children"]
    flat_dataclass_type.base_poly_children_types = flattening_state[
        "base_poly_children_types"
    ]
    flat_dataclass_type.args_with_default_none = flattening_state[
        "args_with_default_none"
    ]
    flat_dataclass_type.list_fields = flattening_state["list_fields"]
    flat_dataclass_type.poly_variant_fields = flattening_state["poly_variant_fields"]
    flat_dataclass_type.poly_field_variants = flattening_state["poly_field_variants"]
    flat_dataclass_type.poly_variant_defaults = flattening_state[
        "poly_variant_defaults"
    ]
    flat_dataclass_type.poly_default_types = flattening_state["poly_default_types"]
    flat_dataclass_type.poly_schema_results = flattening_state.get(
        "poly_schema_results", {}
    )
    flat_dataclass_type.nested_groups = flattening_state["nested_groups"]
    flat_dataclass_type.nested_group_docs = flattening_state["nested_group_docs"]
    return flat_dataclass_type
