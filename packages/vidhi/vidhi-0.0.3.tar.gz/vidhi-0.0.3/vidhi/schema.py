"""Config schema introspection and export system.

This module provides tools for introspecting dataclass configurations and
exporting them to various formats:

- JSON Schema (for IDE autocomplete and validation)
- YAML (for documentation)
- Markdown (for documentation sites)

Example:
    >>> from vidhi.schema import ConfigSchema
    >>> schema = ConfigSchema(MyConfig)
    >>> json_schema = schema.to_json_schema()
    >>> yaml_doc = schema.to_yaml()
"""

from __future__ import annotations

import json
from dataclasses import MISSING, fields, is_dataclass
from enum import Enum
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Set,
    Type,
    Union,
    cast,
    get_args,
    get_origin,
)

from vidhi.base_poly_config import BasePolyConfig
from vidhi.constants import METADATA_KEY_HELP
from vidhi.utils import get_all_subclasses, is_subclass


class FieldSchema:
    """Schema representation of a single field."""

    def __init__(
        self,
        name: str,
        field_type: Any,
        default: Any = MISSING,
        default_factory: Any = MISSING,
        help_text: str = "",
        choices: Optional[List[Any]] = None,
        is_required: bool = False,
        is_polymorphic: bool = False,
        variants: Optional[Dict[str, Type]] = None,
        nested_schema: Optional["ConfigSchema"] = None,
        parent_path: str = "",
    ):
        self.name = name
        self.field_type = field_type
        self.default = default
        self.default_factory = default_factory
        self.help_text = help_text
        self.choices = choices
        self.is_required = is_required
        self.is_polymorphic = is_polymorphic
        self.variants = variants or {}
        self.nested_schema = nested_schema
        self.parent_path = parent_path

    @property
    def full_path(self) -> str:
        """Get the full dot-separated path to this field."""
        if self.parent_path:
            return f"{self.parent_path}.{self.name}"
        return self.name

    @property
    def type_str(self) -> str:
        """Get a human-readable type string."""
        return _type_to_str(self.field_type)

    @property
    def default_str(self) -> str:
        """Get a string representation of the default value."""
        if self.default is not MISSING:
            if isinstance(self.default, Enum):
                return self.default.value
            return repr(self.default)
        if self.default_factory is not MISSING:
            return f"<factory: {self.default_factory.__name__}>"
        return "<required>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = {
            "name": self.name,
            "type": self.type_str,
            "required": self.is_required,
        }
        if self.help_text:
            result["description"] = self.help_text
        if self.default is not MISSING:
            result["default"] = _serialize_default(self.default)
        elif self.default_factory is not MISSING:
            try:
                result["default"] = _serialize_default(self.default_factory())
            except Exception:
                result["default"] = None
        if self.choices:
            result["choices"] = [_serialize_default(c) for c in self.choices]
        if self.is_polymorphic:
            result["polymorphic"] = True
            result["variants"] = list(self.variants.keys())
        if self.nested_schema:
            result["properties"] = self.nested_schema.to_dict()["properties"]
        return result

    def to_json_schema(self) -> Dict[str, Any]:
        """Convert to JSON Schema format."""
        schema: Dict[str, Any] = {}

        # Handle polymorphic types
        if self.is_polymorphic:
            return self._polymorphic_json_schema()

        # Handle nested dataclasses
        if self.nested_schema:
            schema = self.nested_schema.to_json_schema()
            if self.help_text:
                schema["description"] = self.help_text
            return schema

        # Handle basic types
        schema = _type_to_json_schema(self.field_type)

        if self.help_text:
            schema["description"] = self.help_text

        if self.default is not MISSING:
            schema["default"] = _serialize_default(self.default)
        elif self.default_factory is not MISSING:
            try:
                schema["default"] = _serialize_default(self.default_factory())
            except Exception:
                pass

        if self.choices:
            schema["enum"] = [_serialize_default(c) for c in self.choices]

        return schema

    def _polymorphic_json_schema(self) -> Dict[str, Any]:
        """Generate JSON Schema for a polymorphic field using oneOf."""
        variant_schemas = []

        for type_key, variant_class in self.variants.items():
            variant_schema = ConfigSchema(variant_class, parent_path=self.full_path)
            schema = variant_schema.to_json_schema()
            schema["properties"] = schema.get("properties", {})
            schema["properties"]["type"] = {
                "type": "string",
                "const": type_key,
                "description": f"Select '{type_key}' variant",
            }
            schema["required"] = schema.get("required", []) + ["type"]
            schema["title"] = variant_class.__name__
            variant_schemas.append(schema)

        result: Dict[str, Any] = {
            "oneOf": variant_schemas,
        }
        if self.help_text:
            result["description"] = self.help_text

        return result


class ConfigSchema:
    """Schema introspection for dataclass configurations.

    Provides methods to:
    - Introspect dataclass structure
    - Get field information by path
    - Export to JSON Schema, YAML, or Markdown

    Example:
        >>> schema = ConfigSchema(MyConfig)
        >>> field = schema.get_field("model.tensor_parallel_size")
        >>> print(field.help_text)
        >>> json_schema = schema.to_json_schema()
    """

    def __init__(
        self,
        config_class: Type,
        parent_path: str = "",
        _visited: Optional[Set[Type]] = None,
    ):
        """Initialize schema from a dataclass type.

        Args:
            config_class: The dataclass type to introspect
            parent_path: Parent path for nested schemas
            _visited: Set of already visited types (for cycle detection)
        """
        self.config_class = config_class
        self.parent_path = parent_path
        self._visited = _visited or set()
        self._fields: Dict[str, FieldSchema] = {}

        if not is_dataclass(config_class):
            raise ValueError(f"{config_class.__name__} is not a dataclass")

        # Prevent infinite recursion
        if config_class in self._visited:
            return
        self._visited.add(config_class)

        self._introspect()

    def _introspect(self) -> None:
        """Introspect the dataclass and build field schemas."""
        for field in fields(self.config_class):
            field_schema = self._create_field_schema(field)
            self._fields[field.name] = field_schema

    def _create_field_schema(self, field: Any) -> FieldSchema:
        """Create a FieldSchema from a dataclass field."""
        field_type = field.type
        help_text = field.metadata.get(METADATA_KEY_HELP, "")
        choices = field.metadata.get("choices")

        # Get default value
        default = field.default if field.default is not MISSING else MISSING
        default_factory = (
            field.default_factory if field.default_factory is not MISSING else MISSING
        )

        is_required = default is MISSING and default_factory is MISSING

        # Check if this is a polymorphic field
        inner_type = _unwrap_optional(field_type)
        is_poly = is_subclass(inner_type, BasePolyConfig)

        variants: Dict[str, Type] = {}
        nested_schema: Optional[ConfigSchema] = None

        if is_poly:
            # Collect all variants
            for subclass in get_all_subclasses(inner_type):
                try:
                    type_val = subclass.get_type()
                    # Handle enums with integer values (e.g., pybind11 C++ enums)
                    if hasattr(type_val, "value"):
                        if isinstance(type_val.value, str):
                            type_key = type_val.value.lower()
                        elif hasattr(type_val, "name"):
                            type_key = type_val.name.lower()
                        else:
                            type_key = str(type_val.value).lower()
                    elif hasattr(type_val, "name"):
                        type_key = type_val.name.lower()
                    else:
                        type_key = str(type_val).lower()
                    variants[type_key] = subclass
                except NotImplementedError:
                    continue
        elif is_dataclass(inner_type) and inner_type not in self._visited:
            # Nested dataclass - inner_type is always a type from field.type annotation
            nested_schema = ConfigSchema(
                cast(Type, inner_type),
                parent_path=(
                    self.parent_path + "." + field.name
                    if self.parent_path
                    else field.name
                ),
                _visited=self._visited.copy(),
            )

        return FieldSchema(
            name=field.name,
            field_type=field_type,
            default=default,
            default_factory=default_factory,
            help_text=help_text,
            choices=choices,
            is_required=is_required,
            is_polymorphic=is_poly,
            variants=variants,
            nested_schema=nested_schema,
            parent_path=self.parent_path,
        )

    @property
    def fields(self) -> Dict[str, FieldSchema]:
        """Get all field schemas."""
        return self._fields

    def get_field(self, path: str) -> Optional[FieldSchema]:
        """Get a field by dot-separated path.

        Args:
            path: Dot-separated path like "model.tensor_parallel_size"

        Returns:
            FieldSchema if found, None otherwise
        """
        parts = path.split(".")
        current_schema = self

        for i, part in enumerate(parts):
            if part not in current_schema._fields:
                return None
            field = current_schema._fields[part]
            if i == len(parts) - 1:
                return field
            if field.nested_schema:
                current_schema = field.nested_schema
            else:
                return None

        return None

    def get_all_fields(self) -> List[FieldSchema]:
        """Get all fields including nested ones (flattened)."""
        result = []
        for field in self._fields.values():
            result.append(field)
            if field.nested_schema:
                result.extend(field.nested_schema.get_all_fields())
        return result

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "class": self.config_class.__name__,
            "properties": {
                name: field.to_dict() for name, field in self._fields.items()
            },
        }

    def to_json_schema(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate JSON Schema (draft-07) for the configuration.

        This can be used with IDEs for YAML/JSON autocomplete.

        Args:
            title: Optional title for the schema
            description: Optional description

        Returns:
            JSON Schema as a dictionary
        """
        schema: Dict[str, Any] = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "title": title or self.config_class.__name__,
            "properties": {},
            "additionalProperties": False,
        }

        if description:
            schema["description"] = description

        required = []
        for name, field in self._fields.items():
            schema["properties"][name] = field.to_json_schema()
            if field.is_required:
                required.append(name)

        if required:
            schema["required"] = required

        return schema

    def to_yaml(self) -> str:
        """Generate YAML documentation string."""
        try:
            import yaml
        except ImportError:
            raise ImportError("PyYAML is required for YAML export: pip install pyyaml")

        doc = self._generate_yaml_doc()
        return yaml.dump(doc, default_flow_style=False, sort_keys=False)

    def _generate_yaml_doc(self) -> Dict[str, Any]:
        """Generate YAML-friendly documentation structure."""
        doc: Dict[str, Any] = {}
        for name, field in self._fields.items():
            entry: Dict[str, Any] = {
                "type": field.type_str,
            }
            if field.help_text:
                entry["description"] = field.help_text
            if field.default is not MISSING:
                entry["default"] = _serialize_default(field.default)
            elif field.default_factory is not MISSING:
                try:
                    entry["default"] = _serialize_default(field.default_factory())
                except Exception:
                    entry["default"] = "<factory>"
            if field.is_required:
                entry["required"] = True
            if field.is_polymorphic:
                entry["variants"] = list(field.variants.keys())
            if field.nested_schema:
                entry["properties"] = field.nested_schema._generate_yaml_doc()
            doc[name] = entry
        return doc

    def to_markdown(self, include_toc: bool = True) -> str:
        """Generate Markdown documentation.

        Args:
            include_toc: Whether to include table of contents

        Returns:
            Markdown formatted documentation
        """
        lines = [f"# {self.config_class.__name__} Configuration\n"]

        if include_toc:
            lines.append("## Table of Contents\n")
            for field in self.get_all_fields():
                indent = "  " * field.full_path.count(".")
                lines.append(
                    f"{indent}- [{field.full_path}](#{field.full_path.replace('.', '')})"
                )
            lines.append("")

        lines.append("## Fields\n")
        lines.extend(self._generate_markdown_fields())

        return "\n".join(lines)

    def _generate_markdown_fields(self, indent: int = 0) -> List[str]:
        """Generate Markdown for fields."""
        lines = []
        prefix = "  " * indent

        for name, field in self._fields.items():
            anchor = field.full_path.replace(".", "")
            lines.append(f"{prefix}### `{field.full_path}` {{#{anchor}}}\n")
            lines.append(f"{prefix}- **Type:** `{field.type_str}`")
            lines.append(
                f"{prefix}- **Required:** {'Yes' if field.is_required else 'No'}"
            )
            lines.append(f"{prefix}- **Default:** `{field.default_str}`")
            if field.help_text:
                lines.append(f"{prefix}- **Description:** {field.help_text}")
            if field.choices:
                choices_str = ", ".join(f"`{c}`" for c in field.choices)
                lines.append(f"{prefix}- **Choices:** {choices_str}")
            if field.is_polymorphic:
                variants_str = ", ".join(f"`{v}`" for v in field.variants.keys())
                lines.append(f"{prefix}- **Variants:** {variants_str}")
            lines.append("")

            if field.nested_schema:
                lines.extend(field.nested_schema._generate_markdown_fields(indent + 1))

        return lines

    def export_json_schema(self, path: str, indent: int = 2) -> None:
        """Export JSON Schema to a file.

        Args:
            path: Output file path
            indent: JSON indentation (default 2)
        """
        schema = self.to_json_schema()
        with open(path, "w") as f:
            json.dump(schema, f, indent=indent)

    def export_yaml(self, path: str) -> None:
        """Export YAML documentation to a file.

        Args:
            path: Output file path
        """
        yaml_str = self.to_yaml()
        with open(path, "w") as f:
            f.write(yaml_str)

    def export_markdown(self, path: str) -> None:
        """Export Markdown documentation to a file.

        Args:
            path: Output file path
        """
        md_str = self.to_markdown()
        with open(path, "w") as f:
            f.write(md_str)


# =============================================================================
# Helper Functions
# =============================================================================


def _unwrap_optional(t: Any) -> Any:
    """Unwrap Optional[X] to get X."""
    origin = get_origin(t)
    if origin is Union:
        args = get_args(t)
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1:
            return non_none[0]
    return t


def _type_to_str(t: Any) -> str:
    """Convert a type to a human-readable string."""
    if t is type(None):
        return "None"

    origin = get_origin(t)
    if origin is not None:
        args = get_args(t)
        if origin is Union:
            # Check for Optional
            non_none = [a for a in args if a is not type(None)]
            if len(non_none) == 1 and len(args) == 2:
                return f"Optional[{_type_to_str(non_none[0])}]"
            return " | ".join(_type_to_str(a) for a in args)
        if origin is list:
            if args:
                return f"List[{_type_to_str(args[0])}]"
            return "List"
        if origin is dict:
            if len(args) == 2:
                return f"Dict[{_type_to_str(args[0])}, {_type_to_str(args[1])}]"
            return "Dict"
        origin_name = getattr(origin, "__name__", str(origin))
        args_str = ", ".join(_type_to_str(a) for a in args)
        return f"{origin_name}[{args_str}]"

    if isinstance(t, type):
        return t.__name__

    return str(t)


def _type_to_json_schema(t: Any) -> Dict[str, Any]:
    """Convert a Python type to JSON Schema type."""
    # Handle None
    if t is type(None):
        return {"type": "null"}

    # Handle Optional and Union
    origin = get_origin(t)
    if origin is Union:
        args = get_args(t)
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1 and len(args) == 2:
            # Optional[X]
            schema = _type_to_json_schema(non_none[0])
            if "type" in schema:
                if isinstance(schema["type"], list):
                    schema["type"].append("null")
                else:
                    schema["type"] = [schema["type"], "null"]
            else:
                schema = {"oneOf": [schema, {"type": "null"}]}
            return schema
        # Union of multiple types
        return {"oneOf": [_type_to_json_schema(a) for a in args]}

    # Handle List
    if origin is list:
        args = get_args(t)
        if args:
            return {"type": "array", "items": _type_to_json_schema(args[0])}
        return {"type": "array"}

    # Handle Dict
    if origin is dict:
        args = get_args(t)
        if len(args) == 2:
            return {
                "type": "object",
                "additionalProperties": _type_to_json_schema(args[1]),
            }
        return {"type": "object"}

    # Handle Enum (both Python Enum and native/pybind11 enums)
    if isinstance(t, type) and issubclass(t, Enum):
        return {
            "type": "string",
            "enum": [
                m.value if isinstance(m.value, (str, int, float, bool)) else m.name
                for m in t
            ],
        }
    # Handle native (pybind11) enums that have __members__ but don't inherit from Enum
    if isinstance(t, type) and hasattr(t, "__members__"):
        members = t.__members__
        return {
            "type": "string",
            "enum": [
                m.value if isinstance(m.value, (str, int, float, bool)) else m.name
                for m in members.values()
            ],
        }

    # Handle basic types
    if t is str:
        return {"type": "string"}
    if t is int:
        return {"type": "integer"}
    if t is float:
        return {"type": "number"}
    if t is bool:
        return {"type": "boolean"}

    # Handle dataclasses - t is a type from field annotations
    if is_dataclass(t):
        schema = ConfigSchema(cast(Type, t))
        return schema.to_json_schema()

    # Fallback
    return {}


def _serialize_default(value: Any) -> Any:
    """Serialize a default value for JSON/YAML output."""
    # Handle Python Enum
    if isinstance(value, Enum):
        return (
            value.value
            if isinstance(value.value, (str, int, float, bool))
            else value.name
        )
    # Handle native (pybind11) enums that have .value and .name but don't inherit from Enum
    if (
        hasattr(value, "value")
        and hasattr(value, "name")
        and not isinstance(value, type)
    ):
        enum_value = value.value
        if isinstance(enum_value, (str, int, float, bool)):
            return enum_value
        return value.name
    if is_dataclass(value):
        return {
            f.name: _serialize_default(getattr(value, f.name)) for f in fields(value)
        }
    if isinstance(value, (list, tuple)):
        return [_serialize_default(v) for v in value]
    if isinstance(value, dict):
        return {k: _serialize_default(v) for k, v in value.items()}
    return value
