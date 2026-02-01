"""Tests for ConfigSchema and JSON Schema generation."""

import json
import tempfile
from dataclasses import field
from enum import Enum
from pathlib import Path

import pytest

from vidhi.base_poly_config import BasePolyConfig
from vidhi.flat_dataclass import create_flat_dataclass
from vidhi.frozen_dataclass import frozen_dataclass
from vidhi.schema import ConfigSchema


class TestConfigSchema:
    """Tests for ConfigSchema introspection."""

    def test_basic_schema_introspection(self):
        """Test basic dataclass schema introspection."""

        @frozen_dataclass
        class SimpleConfig:
            name: str = "default"
            count: int = 10
            enabled: bool = True

        schema = ConfigSchema(SimpleConfig)

        assert "name" in schema.fields
        assert "count" in schema.fields
        assert "enabled" in schema.fields

        assert schema.fields["name"].type_str == "str"
        assert schema.fields["count"].type_str == "int"
        assert schema.fields["enabled"].type_str == "bool"

    def test_nested_schema_introspection(self):
        """Test nested dataclass schema introspection."""

        @frozen_dataclass
        class DatabaseConfig:
            host: str = "localhost"
            port: int = 5432

        @frozen_dataclass
        class AppConfig:
            name: str = "app"
            database: DatabaseConfig = field(default_factory=DatabaseConfig)

        schema = ConfigSchema(AppConfig)

        assert "database" in schema.fields
        assert schema.fields["database"].nested_schema is not None

        db_schema = schema.fields["database"].nested_schema
        assert "host" in db_schema.fields
        assert "port" in db_schema.fields

    def test_get_field_by_path(self):
        """Test getting fields by dot-separated path."""

        @frozen_dataclass
        class InnerConfig:
            value: int = 42

        @frozen_dataclass
        class MiddleConfig:
            inner: InnerConfig = field(default_factory=InnerConfig)

        @frozen_dataclass
        class OuterConfig:
            middle: MiddleConfig = field(default_factory=MiddleConfig)

        schema = ConfigSchema(OuterConfig)

        found_field = schema.get_field("middle.inner.value")
        assert found_field is not None
        assert found_field.name == "value"
        assert found_field.type_str == "int"

    def test_polymorphic_schema_introspection(self):
        """Test polymorphic config schema introspection."""

        class StorageType(Enum):
            LOCAL = "local"
            S3 = "s3"

        @frozen_dataclass
        class BaseStorage(BasePolyConfig):
            @classmethod
            def get_type(cls) -> StorageType:
                raise NotImplementedError()

        @frozen_dataclass
        class LocalStorage(BaseStorage):
            path: str = "/data"

            @classmethod
            def get_type(cls) -> StorageType:
                return StorageType.LOCAL

        @frozen_dataclass
        class S3Storage(BaseStorage):
            bucket: str = "my-bucket"
            region: str = "us-east-1"

            @classmethod
            def get_type(cls) -> StorageType:
                return StorageType.S3

        @frozen_dataclass
        class AppConfig:
            storage: BaseStorage = field(default_factory=LocalStorage)

        schema = ConfigSchema(AppConfig)

        assert "storage" in schema.fields
        storage_field = schema.fields["storage"]
        assert storage_field.is_polymorphic
        assert "local" in storage_field.variants
        assert "s3" in storage_field.variants

    def test_help_text_extraction(self):
        """Test that help text from metadata is extracted."""
        from vidhi.constants import METADATA_KEY_HELP

        @frozen_dataclass
        class ConfigWithHelp:
            name: str = field(
                default="default",
                metadata={METADATA_KEY_HELP: "The name of the item"},
            )

        schema = ConfigSchema(ConfigWithHelp)
        assert schema.fields["name"].help_text == "The name of the item"


class TestJSONSchemaGeneration:
    """Tests for JSON Schema generation."""

    def test_basic_json_schema(self):
        """Test basic JSON Schema generation."""

        @frozen_dataclass
        class SimpleConfig:
            name: str = "default"
            count: int = 10
            ratio: float = 0.5
            enabled: bool = True

        schema = ConfigSchema(SimpleConfig)
        json_schema = schema.to_json_schema()

        assert json_schema["$schema"] == "http://json-schema.org/draft-07/schema#"
        assert json_schema["type"] == "object"
        assert "properties" in json_schema

        props = json_schema["properties"]
        assert props["name"]["type"] == "string"
        assert props["count"]["type"] == "integer"
        assert props["ratio"]["type"] == "number"
        assert props["enabled"]["type"] == "boolean"

    def test_json_schema_with_defaults(self):
        """Test that defaults are included in JSON Schema."""

        @frozen_dataclass
        class ConfigWithDefaults:
            name: str = "myapp"
            port: int = 8080

        schema = ConfigSchema(ConfigWithDefaults)
        json_schema = schema.to_json_schema()

        assert json_schema["properties"]["name"]["default"] == "myapp"
        assert json_schema["properties"]["port"]["default"] == 8080

    def test_json_schema_with_enum(self):
        """Test JSON Schema with enum types."""

        class LogLevel(Enum):
            DEBUG = "debug"
            INFO = "info"
            ERROR = "error"

        @frozen_dataclass
        class ConfigWithEnum:
            level: LogLevel = LogLevel.INFO

        schema = ConfigSchema(ConfigWithEnum)
        json_schema = schema.to_json_schema()

        level_schema = json_schema["properties"]["level"]
        assert level_schema["type"] == "string"
        assert "enum" in level_schema
        assert set(level_schema["enum"]) == {"debug", "info", "error"}

    def test_json_schema_with_list(self):
        """Test JSON Schema with list types."""
        from typing import List

        @frozen_dataclass
        class ConfigWithList:
            items: List[str] = field(default_factory=list)
            numbers: List[int] = field(default_factory=list)

        schema = ConfigSchema(ConfigWithList)
        json_schema = schema.to_json_schema()

        assert json_schema["properties"]["items"]["type"] == "array"
        assert json_schema["properties"]["items"]["items"]["type"] == "string"
        assert json_schema["properties"]["numbers"]["items"]["type"] == "integer"

    def test_json_schema_polymorphic_oneof(self):
        """Test that polymorphic fields generate oneOf schemas."""

        class ModeType(Enum):
            FAST = "fast"
            ACCURATE = "accurate"

        @frozen_dataclass
        class BaseMode(BasePolyConfig):
            @classmethod
            def get_type(cls) -> ModeType:
                raise NotImplementedError()

        @frozen_dataclass
        class FastMode(BaseMode):
            speed: int = 10

            @classmethod
            def get_type(cls) -> ModeType:
                return ModeType.FAST

        @frozen_dataclass
        class AccurateMode(BaseMode):
            precision: float = 0.99

            @classmethod
            def get_type(cls) -> ModeType:
                return ModeType.ACCURATE

        @frozen_dataclass
        class AppConfig:
            mode: BaseMode = field(default_factory=FastMode)

        schema = ConfigSchema(AppConfig)
        json_schema = schema.to_json_schema()

        mode_schema = json_schema["properties"]["mode"]
        assert "oneOf" in mode_schema
        assert len(mode_schema["oneOf"]) == 2

    def test_json_schema_export(self):
        """Test exporting JSON Schema to file."""

        @frozen_dataclass
        class SimpleConfig:
            name: str = "test"

        schema = ConfigSchema(SimpleConfig)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            path = f.name

        try:
            schema.export_json_schema(path)
            with open(path) as f:
                loaded = json.load(f)
            assert loaded["properties"]["name"]["type"] == "string"
        finally:
            Path(path).unlink()

    def test_json_schema_valid_for_validation(self):
        """Test that generated JSON Schema can validate configs."""
        try:
            import jsonschema
        except ImportError:
            pytest.skip("jsonschema not installed")

        @frozen_dataclass
        class ValidatedConfig:
            name: str = "default"
            count: int = 10

        schema = ConfigSchema(ValidatedConfig)
        json_schema = schema.to_json_schema()

        # Valid config should pass
        valid_config = {"name": "test", "count": 5}
        jsonschema.validate(valid_config, json_schema)

        # Invalid config should fail
        invalid_config = {"name": 123, "count": "not a number"}
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(invalid_config, json_schema)


class TestFlatDataclassSchemaIntegration:
    """Tests for schema integration with flat dataclass."""

    def test_get_schema_method(self):
        """Test that flat dataclass has get_schema method."""

        @frozen_dataclass
        class SimpleConfig:
            name: str = "test"

        FlatConfig = create_flat_dataclass(SimpleConfig)
        schema = FlatConfig.get_schema()

        assert isinstance(schema, ConfigSchema)
        assert "name" in schema.fields

    def test_export_json_schema_method(self):
        """Test export_json_schema method on flat dataclass."""

        @frozen_dataclass
        class SimpleConfig:
            value: int = 42

        FlatConfig = create_flat_dataclass(SimpleConfig)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            path = f.name

        try:
            FlatConfig.export_json_schema(path)
            with open(path) as f:
                loaded = json.load(f)
            assert "properties" in loaded
        finally:
            Path(path).unlink()


class TestMarkdownGeneration:
    """Tests for Markdown documentation generation."""

    def test_markdown_generation(self):
        """Test Markdown documentation generation."""
        from vidhi.constants import METADATA_KEY_HELP

        @frozen_dataclass
        class DocumentedConfig:
            name: str = field(
                default="myapp",
                metadata={METADATA_KEY_HELP: "Application name"},
            )
            port: int = field(
                default=8080,
                metadata={METADATA_KEY_HELP: "HTTP port number"},
            )

        schema = ConfigSchema(DocumentedConfig)
        markdown = schema.to_markdown()

        assert "# DocumentedConfig Configuration" in markdown
        assert "`name`" in markdown
        assert "Application name" in markdown
        assert "`port`" in markdown
        assert "HTTP port number" in markdown
