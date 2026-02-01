"""
Integration tests for Vidhi - end-to-end workflows.

These tests verify that all components work together correctly.
"""

import sys
import tempfile
from dataclasses import field
from enum import Enum
from pathlib import Path
from typing import List, Optional
from unittest.mock import patch

import pytest

from vidhi import (
    BasePolyConfig,
)
from vidhi import (
    _create_flat_dataclass as create_flat_dataclass,  # Internal API for testing
)
from vidhi import (
    create_class_from_dict,
    dataclass_to_dict,
    frozen_dataclass,
    load_yaml_config,
)


# Complex integration test fixtures
class StorageType(Enum):
    LOCAL = "local"
    S3 = "s3"
    GCS = "gcs"


@frozen_dataclass
class BaseStorageConfig(BasePolyConfig):
    @classmethod
    def get_type(cls) -> StorageType:
        raise NotImplementedError()


@frozen_dataclass
class LocalStorageConfig(BaseStorageConfig):
    path: str = "/var/data"

    @classmethod
    def get_type(cls) -> StorageType:
        return StorageType.LOCAL


@frozen_dataclass
class S3StorageConfig(BaseStorageConfig):
    bucket: str  # Required field - should not be required in CLI for non-S3 variants
    region: str = "us-east-1"

    @classmethod
    def get_type(cls) -> StorageType:
        return StorageType.S3


@frozen_dataclass
class DatabaseConfig:
    host: str = "localhost"
    port: int = 5432
    database: str = "mydb"
    pool_size: int = 10


@frozen_dataclass
class CacheConfig:
    host: str = "localhost"
    port: int = 6379
    ttl: int = 3600


@frozen_dataclass
class ApplicationConfig:
    app_name: str  # Required field - but can be loaded from file
    database: DatabaseConfig  # Required field - but can be loaded from file
    version: str = "1.0.0"
    debug: bool = False
    cache: Optional[CacheConfig] = None
    storage: BaseStorageConfig = field(default_factory=LocalStorageConfig)
    allowed_hosts: List[str] = field(default_factory=lambda: ["localhost"])


class TestEndToEndYAML:
    def test_yaml_to_dataclass_simple(self):
        """Test complete flow: YAML → dict → dataclass."""
        yaml_content = """
host: "db.production.com"
port: 5433
database: "production_db"
pool_size: 50
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            # Load YAML
            config_dict = load_yaml_config(yaml_path)

            # Create dataclass
            config = create_class_from_dict(DatabaseConfig, config_dict)

            # Verify
            assert config.host == "db.production.com"
            assert config.port == 5433
            assert config.database == "production_db"
            assert config.pool_size == 50
        finally:
            Path(yaml_path).unlink()

    def test_yaml_to_dataclass_nested(self):
        """Test complete flow with nested configs."""
        yaml_content = """
app_name: "MyApp"
version: "2.0.0"
debug: true
database:
  host: "db.example.com"
  port: 5432
  database: "app_db"
  pool_size: 20
cache:
  host: "cache.example.com"
  port: 6380
  ttl: 7200
allowed_hosts:
  - "localhost"
  - "example.com"
  - "*.example.com"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            config_dict = load_yaml_config(yaml_path)
            config = create_class_from_dict(ApplicationConfig, config_dict)

            assert config.app_name == "MyApp"
            assert config.version == "2.0.0"
            assert config.debug is True

            # Nested database
            assert config.database.host == "db.example.com"
            assert config.database.pool_size == 20

            # Optional cache
            assert config.cache is not None
            assert config.cache.host == "cache.example.com"
            assert config.cache.ttl == 7200

            # List field
            assert len(config.allowed_hosts) == 3
            assert "localhost" in config.allowed_hosts
        finally:
            Path(yaml_path).unlink()

    def test_yaml_to_dataclass_polymorphic(self):
        """Test YAML with polymorphic config."""
        yaml_content = """
app_name: "DataPipeline"
database:
  host: "db.local"
storage:
  type: "s3"
  bucket: "my-data-bucket"
  region: "us-west-2"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            config_dict = load_yaml_config(yaml_path)
            config = create_class_from_dict(ApplicationConfig, config_dict)

            assert config.app_name == "DataPipeline"
            assert isinstance(config.storage, S3StorageConfig)
            assert config.storage.bucket == "my-data-bucket"
            assert config.storage.region == "us-west-2"
        finally:
            Path(yaml_path).unlink()


class TestEndToEndCLI:
    def test_cli_args_to_dataclass(self):
        """Test complete flow: CLI args → flat → dataclass."""
        FlatConfig = create_flat_dataclass(DatabaseConfig)
        test_args = [
            "script.py",
            "--host",
            "prod.db.com",
            "--port",
            "5433",
            "--database",
            "prod_db",
        ]

        with patch.object(sys, "argv", test_args):
            flat_configs = FlatConfig.create_from_cli_args()

        config = flat_configs[0].reconstruct_original_dataclass()

        assert config.host == "prod.db.com"
        assert config.port == 5433
        assert config.database == "prod_db"
        assert config.pool_size == 10  # default

    def test_cli_nested_config(self):
        """Test CLI with nested config structures."""
        FlatConfig = create_flat_dataclass(ApplicationConfig)
        test_args = [
            "script.py",
            "--app_name",
            "TestApp",
            "--database.host",
            "db.test.com",  # required field
            "--version",
            "3.0.0",
            "--debug",
            "true",
            "--database.port",
            "5432",
            "--cache.host",
            "cache.test.com",
            "--storage.type",
            "LOCAL",  # Specify storage type to avoid requiring S3 fields
            "--storage.path",
            "/data/test",
        ]

        with patch.object(sys, "argv", test_args):
            flat_configs = FlatConfig.create_from_cli_args()

        config = flat_configs[0].reconstruct_original_dataclass()

        assert config.app_name == "TestApp"
        assert config.version == "3.0.0"
        assert config.debug is True
        assert config.database.host == "db.test.com"
        assert config.cache.host == "cache.test.com"
        assert isinstance(config.storage, LocalStorageConfig)
        assert config.storage.path == "/data/test"


class TestEndToEndMixed:
    def test_yaml_plus_cli_overrides(self):
        """Test loading from YAML and overriding with CLI args."""
        yaml_content = """
app_name: "FromYAML"
version: "1.0.0"
database:
  host: "db.yaml.com"
  port: 5432
cache:
  host: "cache.yaml.com"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            FlatConfig = create_flat_dataclass(ApplicationConfig)
            test_args = [
                "script.py",
                "--config",
                yaml_path,
                "--version",
                "2.0.0",  # Override
                "--database.port",
                "5433",  # Override
            ]

            with patch.object(sys, "argv", test_args):
                flat_configs = FlatConfig.create_from_cli_args()

            config = flat_configs[0].reconstruct_original_dataclass()

            # From YAML
            assert config.app_name == "FromYAML"
            assert config.database.host == "db.yaml.com"
            assert config.cache.host == "cache.yaml.com"

            # Overridden by CLI
            assert config.version == "2.0.0"
            assert config.database.port == 5433
        finally:
            Path(yaml_path).unlink()


class TestRoundTrip:
    def test_dataclass_to_dict_to_dataclass(self):
        """Test round-trip: dataclass → dict → dataclass."""
        # Create original
        original = ApplicationConfig(
            app_name="RoundTrip",
            version="1.2.3",
            debug=True,
            database=DatabaseConfig(host="db.local", port=5432),
            cache=CacheConfig(host="cache.local", ttl=1800),
            storage=S3StorageConfig(bucket="test-bucket", region="eu-west-1"),
            allowed_hosts=["localhost", "*.example.com"],
        )

        # Convert to dict
        config_dict = dataclass_to_dict(original)

        # Verify dict structure
        assert config_dict["app_name"] == "RoundTrip"
        assert config_dict["database"]["host"] == "db.local"
        assert config_dict["cache"]["host"] == "cache.local"

        # Convert back to dataclass
        reconstructed = create_class_from_dict(ApplicationConfig, config_dict)

        # Verify reconstruction
        assert reconstructed.app_name == original.app_name
        assert reconstructed.version == original.version
        assert reconstructed.debug == original.debug
        assert reconstructed.database.host == original.database.host
        assert reconstructed.cache.ttl == original.cache.ttl
        assert isinstance(reconstructed.storage, S3StorageConfig)
        assert reconstructed.storage.bucket == original.storage.bucket
        assert reconstructed.allowed_hosts == original.allowed_hosts

    def test_yaml_round_trip(self):
        """Test round-trip: dataclass → dict → YAML → dict → dataclass."""
        import yaml

        original = DatabaseConfig(
            host="round.trip.com", port=5433, database="round_trip_db", pool_size=25
        )

        # To dict
        config_dict = dataclass_to_dict(original)

        # To YAML string
        yaml_str = yaml.dump(config_dict)

        # Write and read back
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_str)
            yaml_path = f.name

        try:
            # Load from YAML
            loaded_dict = load_yaml_config(yaml_path)

            # Reconstruct
            reconstructed = create_class_from_dict(DatabaseConfig, loaded_dict)

            # Verify
            assert reconstructed.host == original.host
            assert reconstructed.port == original.port
            assert reconstructed.database == original.database
            assert reconstructed.pool_size == original.pool_size
        finally:
            Path(yaml_path).unlink()


class TestComplexScenarios:
    def test_multiple_polymorphic_configs(self):
        """Test config with multiple polymorphic fields."""

        @frozen_dataclass
        class MultiPolyConfig:
            name: str
            primary_storage: BaseStorageConfig = field(
                default_factory=LocalStorageConfig
            )
            backup_storage: BaseStorageConfig = field(
                default_factory=LocalStorageConfig
            )

        yaml_content = """
name: "MultiStorage"
primary_storage:
  type: "s3"
  bucket: "primary-bucket"
backup_storage:
  type: "local"
  path: "/backup"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            config_dict = load_yaml_config(yaml_path)
            config = create_class_from_dict(MultiPolyConfig, config_dict)

            assert isinstance(config.primary_storage, S3StorageConfig)
            assert config.primary_storage.bucket == "primary-bucket"
            assert isinstance(config.backup_storage, LocalStorageConfig)
            assert config.backup_storage.path == "/backup"
        finally:
            Path(yaml_path).unlink()

    def test_deeply_nested_configs(self):
        """Test deeply nested configuration structures."""

        @frozen_dataclass
        class Level3Config:
            value: int = 3

        @frozen_dataclass
        class Level2Config:
            level3: Level3Config
            name: str = "level2"

        @frozen_dataclass
        class Level1Config:
            level2: Level2Config
            name: str = "level1"

        yaml_content = """
name: "root"
level2:
  name: "middle"
  level3:
    value: 42
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            config_dict = load_yaml_config(yaml_path)
            config = create_class_from_dict(Level1Config, config_dict)

            assert config.name == "root"
            assert config.level2.name == "middle"
            assert config.level2.level3.value == 42
        finally:
            Path(yaml_path).unlink()


class TestErrorHandling:
    def test_invalid_yaml_file(self):
        """Test error handling for invalid YAML."""
        invalid_content = "this is: not: valid: yaml: {{"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(invalid_content)
            yaml_path = f.name

        try:
            with pytest.raises(Exception):
                load_yaml_config(yaml_path)
        finally:
            Path(yaml_path).unlink()

    def test_missing_required_field(self):
        """Test error when required field is missing."""
        yaml_content = """
version: "1.0.0"
database:
  host: "db.local"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            config_dict = load_yaml_config(yaml_path)
            # Missing required 'app_name' field
            with pytest.raises(TypeError):
                create_class_from_dict(ApplicationConfig, config_dict)
        finally:
            Path(yaml_path).unlink()

    def test_unknown_config_keys(self):
        """Test error when unknown keys are present."""
        config_dict = {
            "host": "localhost",
            "port": 5432,
            "unknown_key": "should_error",
        }

        with pytest.raises(TypeError, match="Unknown arguments"):
            create_class_from_dict(DatabaseConfig, config_dict)
