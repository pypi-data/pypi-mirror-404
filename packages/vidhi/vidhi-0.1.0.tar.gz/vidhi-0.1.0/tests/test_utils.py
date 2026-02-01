"""Comprehensive tests for vidhi.utils module."""

import tempfile
from enum import Enum
from pathlib import Path

import pytest

from vidhi.base_poly_config import BasePolyConfig
from vidhi.frozen_dataclass import frozen_dataclass
from vidhi.utils import (
    create_class_from_dict,
    dataclass_to_dict,
    expand_dict,
    get_all_subclasses,
    is_bool,
    is_composed_of_primitives,
    is_dict,
    is_list,
    is_optional,
    is_primitive_type,
    load_yaml_config,
    to_snake_case,
)


# Test fixtures
class ConfigType(Enum):
    TYPE_A = "type_a"
    TYPE_B = "type_b"


@frozen_dataclass
class SimpleConfig:
    name: str
    value: int = 10


@frozen_dataclass
class NestedConfig:
    simple: SimpleConfig
    extra: str = "default"


@frozen_dataclass
class BaseTestConfig(BasePolyConfig):
    common: str = "base"

    @classmethod
    def get_type(cls) -> ConfigType:
        raise NotImplementedError()


@frozen_dataclass
class TypeAConfig(BaseTestConfig):
    field_a: int = 1

    @classmethod
    def get_type(cls) -> ConfigType:
        return ConfigType.TYPE_A


@frozen_dataclass
class TypeBConfig(BaseTestConfig):
    field_b: str = "b"

    @classmethod
    def get_type(cls) -> ConfigType:
        return ConfigType.TYPE_B


class TestGetAllSubclasses:
    def test_get_all_subclasses_single_level(self):
        """Test getting direct subclasses."""
        subclasses = get_all_subclasses(BaseTestConfig)
        assert TypeAConfig in subclasses
        assert TypeBConfig in subclasses
        assert len(subclasses) == 2

    def test_get_all_subclasses_multilevel(self):
        """Test getting subclasses across multiple inheritance levels."""

        class Parent:
            pass

        class Child1(Parent):
            pass

        class Child2(Parent):
            pass

        class GrandChild(Child1):
            pass

        subclasses = get_all_subclasses(Parent)
        assert Child1 in subclasses
        assert Child2 in subclasses
        assert GrandChild in subclasses


class TestTypePredicates:
    def test_is_primitive_type(self):
        """Test primitive type detection."""
        assert is_primitive_type(int)
        assert is_primitive_type(str)
        assert is_primitive_type(float)
        assert is_primitive_type(bool)
        assert is_primitive_type(type(None))
        assert not is_primitive_type(list)
        assert not is_primitive_type(dict)
        assert not is_primitive_type(SimpleConfig)

    def test_is_optional(self):
        """Test Optional type detection."""
        from typing import Optional

        assert is_optional(Optional[int])
        assert is_optional(Optional[str])
        assert not is_optional(int)
        assert not is_optional(str)

    def test_is_list(self):
        """Test List type detection."""
        from typing import List

        assert is_list(List[int])
        assert is_list(List[str])
        assert is_list(list[int])
        assert not is_list(int)
        assert not is_list(dict)

    def test_is_dict(self):
        """Test Dict type detection."""
        from typing import Dict

        assert is_dict(Dict[str, int])
        assert is_dict(dict[str, int])
        assert not is_dict(int)
        assert not is_dict(list)

    def test_is_bool(self):
        """Test bool type detection."""
        assert is_bool(bool)
        assert not is_bool(int)
        assert not is_bool(str)

    def test_is_composed_of_primitives(self):
        """Test composed type detection."""
        from typing import Dict, List, Optional

        assert is_composed_of_primitives(int)
        assert is_composed_of_primitives(str)
        assert is_composed_of_primitives(List[int])
        assert is_composed_of_primitives(Dict[str, int])
        assert is_composed_of_primitives(Optional[int])
        # Nested primitives
        assert is_composed_of_primitives(List[Optional[int]])


class TestToSnakeCase:
    def test_to_snake_case_basic(self):
        """Test basic CamelCase to snake_case conversion."""
        assert to_snake_case("CamelCase") == "camel_case"
        assert to_snake_case("SimpleConfig") == "simple_config"
        assert to_snake_case("HTTPResponse") == "h_t_t_p_response"

    def test_to_snake_case_already_snake(self):
        """Test that snake_case strings are unchanged."""
        assert to_snake_case("snake_case") == "snake_case"
        assert to_snake_case("already_lower") == "already_lower"

    def test_to_snake_case_single_word(self):
        """Test single word conversion."""
        assert to_snake_case("Word") == "word"
        assert to_snake_case("lowercase") == "lowercase"


class TestDataclassToDict:
    def test_dataclass_to_dict_simple(self):
        """Test converting simple dataclass to dict."""
        config = SimpleConfig(name="test", value=42)
        result = dataclass_to_dict(config)

        assert isinstance(result, dict)
        assert result["name"] == "test"
        assert result["value"] == 42

    def test_dataclass_to_dict_nested(self):
        """Test converting nested dataclass to dict."""
        simple = SimpleConfig(name="inner", value=20)
        nested = NestedConfig(simple=simple, extra="custom")
        result = dataclass_to_dict(nested)

        assert isinstance(result, dict)
        assert isinstance(result["simple"], dict)
        assert result["simple"]["name"] == "inner"
        assert result["simple"]["value"] == 20
        assert result["extra"] == "custom"

    def test_dataclass_to_dict_with_list(self):
        """Test converting dataclass with list to dict."""

        @frozen_dataclass
        class ConfigWithList:
            items: list[int]

        config = ConfigWithList(items=[1, 2, 3])
        result = dataclass_to_dict(config)

        assert result["items"] == [1, 2, 3]

    def test_dataclass_to_dict_with_enum(self):
        """Test converting dataclass with enum to dict."""

        @frozen_dataclass
        class ConfigWithEnum:
            type_val: ConfigType

        config = ConfigWithEnum(type_val=ConfigType.TYPE_A)
        result = dataclass_to_dict(config)

        assert result["type_val"] == "type_a"

    def test_dataclass_to_dict_polymorphic(self):
        """Test converting polymorphic config to dict."""
        config = TypeAConfig(field_a=99)
        result = dataclass_to_dict(config)

        assert result["common"] == "base"
        assert result["field_a"] == 99
        assert (
            result["type"] == "type_a"
        )  # Uses enum value for YAML/JSON config consistency


class TestCreateClassFromDict:
    def test_create_class_from_dict_simple(self):
        """Test creating simple dataclass from dict."""
        config_dict = {"name": "test", "value": 42}
        config = create_class_from_dict(SimpleConfig, config_dict)

        assert isinstance(config, SimpleConfig)
        assert config.name == "test"
        assert config.value == 42

    def test_create_class_from_dict_with_defaults(self):
        """Test creating dataclass with default values."""
        config_dict = {"name": "test"}
        config = create_class_from_dict(SimpleConfig, config_dict)

        assert config.name == "test"
        assert config.value == 10  # default

    def test_create_class_from_dict_nested(self):
        """Test creating nested dataclass from dict."""
        config_dict = {"simple": {"name": "inner", "value": 20}, "extra": "custom"}
        config = create_class_from_dict(NestedConfig, config_dict)

        assert isinstance(config, NestedConfig)
        assert isinstance(config.simple, SimpleConfig)
        assert config.simple.name == "inner"
        assert config.simple.value == 20
        assert config.extra == "custom"

    def test_create_class_from_dict_polymorphic_as_field(self):
        """Test creating config with polymorphic field."""

        @frozen_dataclass
        class ConfigWithPoly:
            poly_field: BaseTestConfig

        config_dict = {
            "poly_field": {"type": "type_a", "common": "custom", "field_a": 99}
        }
        config = create_class_from_dict(ConfigWithPoly, config_dict)

        assert isinstance(config.poly_field, TypeAConfig)
        assert config.poly_field.common == "custom"
        assert config.poly_field.field_a == 99

    def test_create_class_from_dict_polymorphic_case_insensitive(self):
        """Test polymorphic config with case-insensitive type matching."""

        @frozen_dataclass
        class ConfigWithPoly:
            poly_field: BaseTestConfig

        config_dict = {"poly_field": {"type": "TYPE_A", "field_a": 50}}
        config = create_class_from_dict(ConfigWithPoly, config_dict)

        assert isinstance(config.poly_field, TypeAConfig)
        assert config.poly_field.field_a == 50

    def test_create_class_from_dict_polymorphic_type_b(self):
        """Test creating polymorphic config type B."""

        @frozen_dataclass
        class ConfigWithPoly:
            poly_field: BaseTestConfig

        config_dict = {"poly_field": {"type": "type_b", "field_b": "custom"}}
        config = create_class_from_dict(ConfigWithPoly, config_dict)

        assert isinstance(config.poly_field, TypeBConfig)
        assert config.poly_field.field_b == "custom"

    def test_create_class_from_dict_with_list_of_primitives(self):
        """Test creating config with list of primitives."""
        from typing import List

        @frozen_dataclass
        class ConfigWithList:
            items: List[int]

        config_dict = {"items": [1, 2, 3, 4, 5]}
        config = create_class_from_dict(ConfigWithList, config_dict)

        assert config.items == [1, 2, 3, 4, 5]

    def test_create_class_from_dict_with_list_of_dataclasses(self):
        """Test creating config with list of dataclasses."""
        from typing import List

        @frozen_dataclass
        class ConfigWithList:
            items: List[SimpleConfig]

        config_dict = {"items": [{"name": "a", "value": 1}, {"name": "b", "value": 2}]}
        config = create_class_from_dict(ConfigWithList, config_dict)

        assert len(config.items) == 2
        assert isinstance(config.items[0], SimpleConfig)
        assert config.items[0].name == "a"
        assert config.items[1].value == 2

    def test_create_class_from_dict_invalid_keys(self):
        """Test error on unknown keys in dict."""
        config_dict = {"name": "test", "value": 42, "unknown_key": "bad"}

        with pytest.raises(TypeError, match="Unknown arguments"):
            create_class_from_dict(SimpleConfig, config_dict)

    def test_create_class_from_dict_none(self):
        """Test creating from None returns None."""
        result = create_class_from_dict(SimpleConfig, None)
        assert result is None

    def test_create_class_from_dict_not_dataclass(self):
        """Test with non-dataclass type returns dict as-is."""
        result = create_class_from_dict(int, {"key": "value"})
        assert result == {"key": "value"}


class TestLoadYamlConfig:
    def test_load_yaml_config_valid(self):
        """Test loading valid YAML file."""
        yaml_content = """
name: "test_app"
value: 42
nested:
  key: "value"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            config = load_yaml_config(yaml_path)
            assert config["name"] == "test_app"
            assert config["value"] == 42
            assert config["nested"]["key"] == "value"
        finally:
            Path(yaml_path).unlink()

    def test_load_yaml_config_json_fallback(self):
        """Test JSON fallback when YAML parsing fails."""
        json_content = '{"name": "test", "value": 123}'

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write(json_content)
            json_path = f.name

        try:
            config = load_yaml_config(json_path)
            assert config["name"] == "test"
            assert config["value"] == 123
        finally:
            Path(json_path).unlink()

    def test_load_yaml_config_missing_file(self):
        """Test error handling for missing file."""
        with pytest.raises(FileNotFoundError):
            load_yaml_config("/nonexistent/path/to/config.yaml")

    def test_load_yaml_config_empty_file(self):
        """Test loading empty YAML file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("")
            yaml_path = f.name

        try:
            config = load_yaml_config(yaml_path)
            assert config == {}
        finally:
            Path(yaml_path).unlink()

    def test_load_yaml_config_list_at_top_level(self):
        """Test loading YAML with list at top level."""
        yaml_content = """
- name: "item1"
  value: 1
- name: "item2"
  value: 2
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            config = load_yaml_config(yaml_path)
            assert "_list" in config
            assert len(config["_list"]) == 2
            assert config["_list"][0]["name"] == "item1"
        finally:
            Path(yaml_path).unlink()

    def test_load_yaml_config_invalid_content(self):
        """Test error handling for invalid YAML/JSON."""
        invalid_content = "this is not valid: yaml: or: json {"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(invalid_content)
            yaml_path = f.name

        try:
            with pytest.raises(Exception):  # Will raise YAML error
                load_yaml_config(yaml_path)
        finally:
            Path(yaml_path).unlink()


class TestExpandDict:
    def test_expand_dict_no_lists(self):
        """Test expand_dict with no lists (no expansion)."""
        config = {"a": 1, "b": 2}
        result = expand_dict(config)

        assert len(result) == 1
        assert result[0] == {"a": 1, "b": 2}

    def test_expand_dict_simple_list(self):
        """Test expand_dict with simple list."""
        config = {"a": [1, 2], "b": 3}
        result = expand_dict(config)

        assert len(result) == 2
        assert {"a": 1, "b": 3} in result
        assert {"a": 2, "b": 3} in result

    def test_expand_dict_multiple_lists(self):
        """Test expand_dict with multiple lists (cartesian product)."""
        config = {"a": [1, 2], "b": [3, 4]}
        result = expand_dict(config)

        assert len(result) == 4
        assert {"a": 1, "b": 3} in result
        assert {"a": 1, "b": 4} in result
        assert {"a": 2, "b": 3} in result
        assert {"a": 2, "b": 4} in result

    def test_expand_dict_nested_dict(self):
        """Test expand_dict with nested dictionary."""
        config = {"outer": {"inner": [1, 2]}, "other": 3}
        result = expand_dict(config)

        assert len(result) == 2
        assert result[0]["outer"]["inner"] == 1
        assert result[1]["outer"]["inner"] == 2

    def test_expand_dict_list_of_dicts(self):
        """Test expand_dict with list of dictionaries."""
        config = {"item": [{"name": "a"}, {"name": "b"}]}
        result = expand_dict(config)

        assert len(result) == 2
        assert result[0]["item"]["name"] == "a"
        assert result[1]["item"]["name"] == "b"
