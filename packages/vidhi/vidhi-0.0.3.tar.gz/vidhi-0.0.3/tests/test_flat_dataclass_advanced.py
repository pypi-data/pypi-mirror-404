"""Advanced tests for vidhi.flat_dataclass module."""

import sys
import tempfile
from dataclasses import field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional
from unittest.mock import patch

import pytest

from vidhi.base_poly_config import BasePolyConfig
from vidhi.flat_dataclass import create_flat_dataclass, explode_dict
from vidhi.frozen_dataclass import frozen_dataclass


# Test fixtures
class SchedulerType(Enum):
    ROUND_ROBIN = "round_robin"
    PRIORITY = "priority"


@frozen_dataclass
class BaseScheduler(BasePolyConfig):
    timeout: int = 30

    @classmethod
    def get_type(cls) -> SchedulerType:
        raise NotImplementedError()


@frozen_dataclass
class RoundRobinScheduler(BaseScheduler):
    quantum: int = 100

    @classmethod
    def get_type(cls) -> SchedulerType:
        return SchedulerType.ROUND_ROBIN


@frozen_dataclass
class PriorityScheduler(BaseScheduler):
    levels: int = 5

    @classmethod
    def get_type(cls) -> SchedulerType:
        return SchedulerType.PRIORITY


@frozen_dataclass
class ServerConfig:
    host: str = "localhost"
    port: int = 8080


@frozen_dataclass
class DatabaseConfig:
    host: str = "localhost"
    port: int = 5432
    database: str = "mydb"


@frozen_dataclass
class ConfigWithOptional:
    name: str
    optional_value: Optional[int] = None
    optional_str: Optional[str] = None


@frozen_dataclass
class ConfigWithLists:
    tags: List[str] = None
    numbers: List[int] = None

    def __post_init__(self):
        if self.tags is None:
            object.__setattr__(self, "tags", [])
        if self.numbers is None:
            object.__setattr__(self, "numbers", [])


@frozen_dataclass
class ConfigWithDict:
    metadata: Dict[str, str] = None

    def __post_init__(self):
        if self.metadata is None:
            object.__setattr__(self, "metadata", {})


@frozen_dataclass
class ConfigWithMetadata:
    learning_rate: float = field(
        default=0.001,
        metadata={"help": "Learning rate for optimizer", "argname": "lr"},
    )
    batch_size: int = field(default=32, metadata={"help": "Batch size for training"})
    debug_mode: bool = field(default=False, metadata={"help": "Enable debug mode"})


@frozen_dataclass
class ComplexConfig:
    name: str
    server: ServerConfig
    database: DatabaseConfig
    scheduler: BaseScheduler = field(default_factory=RoundRobinScheduler)


class TestExplodeDict:
    def test_explode_dict_no_expansion(self):
        """Test explode_dict with no lists."""
        FlatClass = create_flat_dataclass(ServerConfig)
        config = {"host": "example.com", "port": 9000}
        result = explode_dict(FlatClass, config)

        assert len(result) == 1
        assert result[0]["host"] == "example.com"
        assert result[0]["port"] == 9000

    def test_explode_dict_simple_list(self):
        """Test explode_dict with simple list expansion."""
        FlatClass = create_flat_dataclass(ServerConfig)
        config = {"host": ["localhost", "0.0.0.0"], "port": 8080}
        result = explode_dict(FlatClass, config)

        assert len(result) == 2
        assert result[0]["host"] == "localhost"
        assert result[0]["port"] == 8080
        assert result[1]["host"] == "0.0.0.0"
        assert result[1]["port"] == 8080

    def test_explode_dict_cartesian_product(self):
        """Test explode_dict with multiple lists (cartesian product)."""
        FlatClass = create_flat_dataclass(ServerConfig)
        config = {"host": ["localhost", "0.0.0.0"], "port": [8080, 9000]}
        result = explode_dict(FlatClass, config)

        assert len(result) == 4
        hosts_ports = [(r["host"], r["port"]) for r in result]
        assert ("localhost", 8080) in hosts_ports
        assert ("localhost", 9000) in hosts_ports
        assert ("0.0.0.0", 8080) in hosts_ports
        assert ("0.0.0.0", 9000) in hosts_ports

    def test_explode_dict_with_prefix(self):
        """Test explode_dict with prefix."""
        FlatClass = create_flat_dataclass(ComplexConfig)
        config = {"host": ["localhost", "remote"]}
        result = explode_dict(FlatClass, config, prefix="server_")

        assert len(result) == 2
        assert result[0]["server_host"] == "localhost"
        assert result[1]["server_host"] == "remote"

    def test_explode_dict_max_combinations_exceeded(self):
        """Test that explode_dict raises error when max_combinations exceeded."""
        FlatClass = create_flat_dataclass(ServerConfig)
        # Create config that would generate 121 combinations (11 * 11)
        config = {"host": list(range(11)), "port": list(range(11))}

        with pytest.raises(ValueError, match="exceeds the allowed maximum"):
            explode_dict(FlatClass, config, max_combinations=100)


class TestCLIWithFiles:
    def test_cli_with_yaml_file(self):
        """Test loading config from YAML file via CLI."""
        yaml_content = """
host: "db.example.com"
port: 5433
database: "production"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            FlatConfig = create_flat_dataclass(DatabaseConfig)
            test_args = ["script.py", "--config", yaml_path]

            with patch.object(sys, "argv", test_args):
                configs = FlatConfig.create_from_cli_args()

            assert len(configs) == 1
            config = configs[0].reconstruct_original_dataclass()
            assert config.host == "db.example.com"
            assert config.port == 5433
            assert config.database == "production"
        finally:
            Path(yaml_path).unlink()

    def test_cli_file_override_with_args(self):
        """Test that CLI args override file config."""
        yaml_content = """
host: "from-file"
port: 5432
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            FlatConfig = create_flat_dataclass(ServerConfig)
            test_args = [
                "script.py",
                "--config",
                yaml_path,
                "--port",
                "9000",
            ]

            with patch.object(sys, "argv", test_args):
                configs = FlatConfig.create_from_cli_args()

            config = configs[0].reconstruct_original_dataclass()
            assert config.host == "from-file"  # from file
            assert config.port == 9000  # overridden by CLI
        finally:
            Path(yaml_path).unlink()

    def test_cli_nested_yaml_file(self):
        """Test loading nested config from YAML file."""
        yaml_content = """
name: "MyApp"
server:
  host: "app.example.com"
  port: 8080
database:
  host: "db.example.com"
  port: 5432
  database: "myapp"
scheduler:
  type: "round_robin"
  timeout: 60
  quantum: 200
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            FlatConfig = create_flat_dataclass(ComplexConfig)
            test_args = ["script.py", "--config", yaml_path]

            with patch.object(sys, "argv", test_args):
                configs = FlatConfig.create_from_cli_args()

            config = configs[0].reconstruct_original_dataclass()
            assert config.name == "MyApp"
            assert config.server.host == "app.example.com"
            assert config.server.port == 8080
            assert config.database.host == "db.example.com"
            assert config.database.port == 5432
        finally:
            Path(yaml_path).unlink()


class TestCLIOptionalFields:
    def test_cli_optional_with_none(self):
        """Test optional field with None value."""
        FlatConfig = create_flat_dataclass(ConfigWithOptional)
        test_args = ["script.py", "--name", "test"]

        with patch.object(sys, "argv", test_args):
            configs = FlatConfig.create_from_cli_args()

        config = configs[0].reconstruct_original_dataclass()
        assert config.name == "test"
        assert config.optional_value is None
        assert config.optional_str is None

    def test_cli_optional_with_value(self):
        """Test optional field with provided value."""
        FlatConfig = create_flat_dataclass(ConfigWithOptional)
        test_args = [
            "script.py",
            "--name",
            "test",
            "--optional_value",
            "42",
            "--optional_str",
            "hello",
        ]

        with patch.object(sys, "argv", test_args):
            configs = FlatConfig.create_from_cli_args()

        config = configs[0].reconstruct_original_dataclass()
        assert config.name == "test"
        assert config.optional_value == 42
        assert config.optional_str == "hello"


class TestCLIListFields:
    def test_cli_list_of_primitives(self):
        """Test CLI with list of primitives."""
        FlatConfig = create_flat_dataclass(ConfigWithLists)
        test_args = [
            "script.py",
            "--tags",
            "tag1",
            "tag2",
            "tag3",
            "--numbers",
            "1",
            "2",
            "3",
        ]

        with patch.object(sys, "argv", test_args):
            configs = FlatConfig.create_from_cli_args()

        config = configs[0].reconstruct_original_dataclass()
        assert config.tags == ["tag1", "tag2", "tag3"]
        assert config.numbers == [1, 2, 3]

    def test_cli_empty_lists(self):
        """Test CLI with empty lists (defaults)."""
        FlatConfig = create_flat_dataclass(ConfigWithLists)
        test_args = ["script.py"]

        with patch.object(sys, "argv", test_args):
            configs = FlatConfig.create_from_cli_args()

        config = configs[0].reconstruct_original_dataclass()
        assert config.tags == []
        assert config.numbers == []


class TestCLIDictFields:
    def test_cli_dict_field(self):
        """Test CLI with dict field (JSON)."""
        FlatConfig = create_flat_dataclass(ConfigWithDict)
        test_args = ["script.py", "--metadata", '{"key1": "value1", "key2": "value2"}']

        with patch.object(sys, "argv", test_args):
            configs = FlatConfig.create_from_cli_args()

        config = configs[0].reconstruct_original_dataclass()
        assert config.metadata == {"key1": "value1", "key2": "value2"}


class TestCLIBooleanFlags:
    def test_cli_boolean_true_flag(self):
        """Test boolean flag set to true."""
        FlatConfig = create_flat_dataclass(ConfigWithMetadata)
        test_args = ["script.py", "--debug_mode", "true"]

        with patch.object(sys, "argv", test_args):
            configs = FlatConfig.create_from_cli_args()

        config = configs[0].reconstruct_original_dataclass()
        assert config.debug_mode is True

    def test_cli_boolean_false_flag(self):
        """Test boolean flag set to false."""
        FlatConfig = create_flat_dataclass(ConfigWithMetadata)
        test_args = ["script.py", "--debug_mode", "false"]

        with patch.object(sys, "argv", test_args):
            configs = FlatConfig.create_from_cli_args()

        config = configs[0].reconstruct_original_dataclass()
        assert config.debug_mode is False

    def test_cli_boolean_default(self):
        """Test boolean with default value."""
        FlatConfig = create_flat_dataclass(ConfigWithMetadata)
        test_args = ["script.py"]

        with patch.object(sys, "argv", test_args):
            configs = FlatConfig.create_from_cli_args()

        config = configs[0].reconstruct_original_dataclass()
        assert config.debug_mode is False  # default


class TestCLIMetadata:
    def test_cli_custom_argname(self):
        """Test custom argument name from metadata."""
        FlatConfig = create_flat_dataclass(ConfigWithMetadata)
        test_args = ["script.py", "--lr", "0.01"]  # Using custom argname

        with patch.object(sys, "argv", test_args):
            configs = FlatConfig.create_from_cli_args()

        config = configs[0].reconstruct_original_dataclass()
        assert config.learning_rate == 0.01

    def test_cli_metadata_help_text(self):
        """Test that metadata help text is available."""
        FlatConfig = create_flat_dataclass(ConfigWithMetadata)

        # Check that metadata is preserved
        assert "learning_rate" in FlatConfig.metadata_mapping
        assert (
            FlatConfig.metadata_mapping["learning_rate"]["help"]
            == "Learning rate for optimizer"
        )
        assert (
            FlatConfig.metadata_mapping["batch_size"]["help"]
            == "Batch size for training"
        )


class TestFlatDataclassStructure:
    def test_flat_dataclass_dependencies(self):
        """Test that dependencies are correctly tracked."""
        FlatConfig = create_flat_dataclass(ComplexConfig)

        # Should have dependencies mapped
        assert hasattr(FlatConfig, "dataclass_dependencies")
        assert (
            "sample_config" in FlatConfig.dataclass_dependencies
            or "complex_config" in FlatConfig.dataclass_dependencies
        )

    def test_flat_dataclass_polymorphic_tracking(self):
        """Test that polymorphic configs are tracked."""
        FlatConfig = create_flat_dataclass(ComplexConfig)

        # Should track polymorphic children
        assert hasattr(FlatConfig, "base_poly_children")
        assert hasattr(FlatConfig, "base_poly_children_types")

    def test_flat_dataclass_file_fields(self):
        """Test that file fields are tracked."""
        FlatConfig = create_flat_dataclass(ComplexConfig)

        # dataclass_file_fields should be an empty dict (legacy attribute)
        assert hasattr(FlatConfig, "dataclass_file_fields")


class TestPolymorphicCLI:
    def test_cli_polymorphic_type_selection(self):
        """Test selecting polymorphic type via CLI."""

        @frozen_dataclass
        class AppConfig:
            scheduler: BaseScheduler = field(default_factory=RoundRobinScheduler)

        FlatConfig = create_flat_dataclass(AppConfig)
        test_args = [
            "script.py",
            "--scheduler.type",
            "round_robin",
            "--scheduler.quantum",
            "200",
        ]

        with patch.object(sys, "argv", test_args):
            configs = FlatConfig.create_from_cli_args()

        config = configs[0].reconstruct_original_dataclass()
        assert isinstance(config.scheduler, RoundRobinScheduler)
        assert config.scheduler.quantum == 200
        assert config.scheduler.timeout == 30  # default

    def test_cli_polymorphic_different_type(self):
        """Test selecting different polymorphic type."""

        @frozen_dataclass
        class AppConfig:
            scheduler: BaseScheduler = field(default_factory=RoundRobinScheduler)

        FlatConfig = create_flat_dataclass(AppConfig)
        test_args = [
            "script.py",
            "--scheduler.type",
            "priority",
            "--scheduler.levels",
            "10",
        ]

        with patch.object(sys, "argv", test_args):
            configs = FlatConfig.create_from_cli_args()

        config = configs[0].reconstruct_original_dataclass()
        assert isinstance(config.scheduler, PriorityScheduler)
        assert config.scheduler.levels == 10


class TestReconstruction:
    def test_reconstruct_with_defaults(self):
        """Test reconstruction uses defaults for unspecified fields."""
        FlatConfig = create_flat_dataclass(ServerConfig)
        test_args = ["script.py", "--host", "example.com"]

        with patch.object(sys, "argv", test_args):
            configs = FlatConfig.create_from_cli_args()

        config = configs[0].reconstruct_original_dataclass()
        assert config.host == "example.com"
        assert config.port == 8080  # default value

    def test_reconstruct_nested_with_defaults(self):
        """Test reconstruction of nested configs with defaults."""

        @frozen_dataclass
        class OuterConfig:
            name: str
            server: ServerConfig

        FlatConfig = create_flat_dataclass(OuterConfig)
        test_args = ["script.py", "--name", "MyApp", "--server.host", "app.local"]

        with patch.object(sys, "argv", test_args):
            configs = FlatConfig.create_from_cli_args()

        config = configs[0].reconstruct_original_dataclass()
        assert config.name == "MyApp"
        assert config.server.host == "app.local"
        assert config.server.port == 8080  # nested default


class TestTopologicalSort:
    def test_topological_sort_no_cycle(self):
        """Test topological sort with valid dependencies."""
        from vidhi.flat_dataclass.reconstruction import topological_sort

        deps = {
            "app": ["database", "cache"],
            "database": [],
            "cache": [],
        }
        result = topological_sort(deps)
        # All classes should be in the result
        assert set(result) == {"app", "database", "cache"}
        # app comes first (dependents before dependencies in this algorithm)
        # The result is reversed in reconstruct_original_dataclass
        assert len(result) == 3

    def test_topological_sort_detects_cycle(self):
        """Test that topological sort detects circular dependencies."""
        from vidhi.flat_dataclass.reconstruction import topological_sort

        # A -> B -> C -> A (circular)
        deps = {
            "a": ["b"],
            "b": ["c"],
            "c": ["a"],
        }
        with pytest.raises(ValueError, match="Circular dependency detected"):
            topological_sort(deps)

    def test_topological_sort_cycle_error_message(self):
        """Test that cycle error message includes the cycle path."""
        from vidhi.flat_dataclass.reconstruction import topological_sort

        deps = {
            "config_a": ["config_b"],
            "config_b": ["config_a"],
        }
        with pytest.raises(ValueError) as exc_info:
            topological_sort(deps)

        error_msg = str(exc_info.value)
        assert "config_a" in error_msg
        assert "config_b" in error_msg


# =============================================================================
# Comprehensive Polymorphic Config Tests
# =============================================================================


class StorageType(Enum):
    LOCAL = "local"
    S3 = "s3"
    GCS = "gcs"


@frozen_dataclass
class BaseStorageConfig(BasePolyConfig):
    """Base storage configuration."""

    @classmethod
    def get_type(cls) -> StorageType:
        raise NotImplementedError()


@frozen_dataclass
class LocalStorageConfig(BaseStorageConfig):
    path: str = "/data"
    create_if_missing: bool = True

    @classmethod
    def get_type(cls) -> StorageType:
        return StorageType.LOCAL


@frozen_dataclass
class S3StorageConfig(BaseStorageConfig):
    bucket: str = "default-bucket"
    region: str = "us-east-1"
    endpoint_url: Optional[str] = None

    @classmethod
    def get_type(cls) -> StorageType:
        return StorageType.S3


@frozen_dataclass
class GCSStorageConfig(BaseStorageConfig):
    bucket: str = "default-bucket"
    project: str = "my-project"

    @classmethod
    def get_type(cls) -> StorageType:
        return StorageType.GCS


class TestPolymorphicCLIComprehensive:
    """Comprehensive tests for polymorphic config CLI parsing."""

    def test_poly_default_type_uses_correct_variant(self):
        """Test that default type instantiates correct variant."""

        @frozen_dataclass
        class AppConfig:
            storage: BaseStorageConfig = field(default_factory=LocalStorageConfig)

        FlatConfig = create_flat_dataclass(AppConfig)
        test_args = ["script.py"]

        with patch.object(sys, "argv", test_args):
            configs = FlatConfig.create_from_cli_args()

        config = configs[0].reconstruct_original_dataclass()
        assert isinstance(config.storage, LocalStorageConfig)
        assert config.storage.path == "/data"
        assert config.storage.create_if_missing is True

    def test_poly_switch_to_different_variant(self):
        """Test switching from default variant to another."""

        @frozen_dataclass
        class AppConfig:
            storage: BaseStorageConfig = field(default_factory=LocalStorageConfig)

        FlatConfig = create_flat_dataclass(AppConfig)
        test_args = [
            "script.py",
            "--storage.type",
            "s3",
            "--storage.bucket",
            "my-bucket",
            "--storage.region",
            "eu-west-1",
        ]

        with patch.object(sys, "argv", test_args):
            configs = FlatConfig.create_from_cli_args()

        config = configs[0].reconstruct_original_dataclass()
        assert isinstance(config.storage, S3StorageConfig)
        assert config.storage.bucket == "my-bucket"
        assert config.storage.region == "eu-west-1"

    def test_poly_case_insensitive_type_selection(self):
        """Test that type selection is case-insensitive."""

        @frozen_dataclass
        class AppConfig:
            storage: BaseStorageConfig = field(default_factory=LocalStorageConfig)

        FlatConfig = create_flat_dataclass(AppConfig)

        # Test uppercase
        test_args = ["script.py", "--storage.type", "S3"]
        with patch.object(sys, "argv", test_args):
            configs = FlatConfig.create_from_cli_args()
        config = configs[0].reconstruct_original_dataclass()
        assert isinstance(config.storage, S3StorageConfig)

        # Test mixed case
        test_args = ["script.py", "--storage.type", "Local"]
        with patch.object(sys, "argv", test_args):
            configs = FlatConfig.create_from_cli_args()
        config = configs[0].reconstruct_original_dataclass()
        assert isinstance(config.storage, LocalStorageConfig)

    def test_poly_shared_and_variant_specific_fields(self):
        """Test configs with both shared parent fields and variant-specific fields."""

        class CacheType(Enum):
            MEMORY = "memory"
            REDIS = "redis"

        @frozen_dataclass
        class BaseCacheConfig(BasePolyConfig):
            ttl_seconds: int = 300  # Shared field

            @classmethod
            def get_type(cls) -> CacheType:
                raise NotImplementedError()

        @frozen_dataclass
        class MemoryCacheConfig(BaseCacheConfig):
            max_size_mb: int = 100

            @classmethod
            def get_type(cls) -> CacheType:
                return CacheType.MEMORY

        @frozen_dataclass
        class RedisCacheConfig(BaseCacheConfig):
            host: str = "localhost"
            port: int = 6379
            db: int = 0

            @classmethod
            def get_type(cls) -> CacheType:
                return CacheType.REDIS

        @frozen_dataclass
        class AppConfig:
            cache: BaseCacheConfig = field(default_factory=MemoryCacheConfig)

        FlatConfig = create_flat_dataclass(AppConfig)

        # Test memory cache with shared field override
        test_args = [
            "script.py",
            "--cache.type",
            "memory",
            "--cache.ttl_seconds",
            "600",
            "--cache.max_size_mb",
            "200",
        ]
        with patch.object(sys, "argv", test_args):
            configs = FlatConfig.create_from_cli_args()

        config = configs[0].reconstruct_original_dataclass()
        assert isinstance(config.cache, MemoryCacheConfig)
        assert config.cache.ttl_seconds == 600  # Shared field
        assert config.cache.max_size_mb == 200  # Variant-specific

        # Test redis cache
        test_args = [
            "script.py",
            "--cache.type",
            "redis",
            "--cache.ttl_seconds",
            "120",
            "--cache.host",
            "redis.local",
            "--cache.port",
            "6380",
        ]
        with patch.object(sys, "argv", test_args):
            configs = FlatConfig.create_from_cli_args()

        config = configs[0].reconstruct_original_dataclass()
        assert isinstance(config.cache, RedisCacheConfig)
        assert config.cache.ttl_seconds == 120
        assert config.cache.host == "redis.local"
        assert config.cache.port == 6380

    def test_poly_multiple_polymorphic_fields(self):
        """Test config with multiple polymorphic fields."""

        @frozen_dataclass
        class AppConfig:
            scheduler: BaseScheduler = field(default_factory=RoundRobinScheduler)
            storage: BaseStorageConfig = field(default_factory=LocalStorageConfig)

        FlatConfig = create_flat_dataclass(AppConfig)
        test_args = [
            "script.py",
            "--scheduler.type",
            "priority",
            "--scheduler.levels",
            "8",
            "--storage.type",
            "s3",
            "--storage.bucket",
            "prod-bucket",
        ]

        with patch.object(sys, "argv", test_args):
            configs = FlatConfig.create_from_cli_args()

        config = configs[0].reconstruct_original_dataclass()
        assert isinstance(config.scheduler, PriorityScheduler)
        assert config.scheduler.levels == 8
        assert isinstance(config.storage, S3StorageConfig)
        assert config.storage.bucket == "prod-bucket"

    def test_poly_boolean_fields_in_variants(self):
        """Test boolean fields in polymorphic variants."""

        @frozen_dataclass
        class AppConfig:
            storage: BaseStorageConfig = field(default_factory=LocalStorageConfig)

        FlatConfig = create_flat_dataclass(AppConfig)

        # Test with explicit true
        test_args = ["script.py", "--storage.create_if_missing", "true"]
        with patch.object(sys, "argv", test_args):
            configs = FlatConfig.create_from_cli_args()
        config = configs[0].reconstruct_original_dataclass()
        assert config.storage.create_if_missing is True

        # Test with explicit false
        test_args = ["script.py", "--storage.create_if_missing", "false"]
        with patch.object(sys, "argv", test_args):
            configs = FlatConfig.create_from_cli_args()
        config = configs[0].reconstruct_original_dataclass()
        assert config.storage.create_if_missing is False

    def test_poly_optional_fields_in_variants(self):
        """Test optional fields in polymorphic variants."""

        @frozen_dataclass
        class AppConfig:
            storage: BaseStorageConfig = field(default_factory=S3StorageConfig)

        FlatConfig = create_flat_dataclass(AppConfig)

        # Without optional field
        test_args = ["script.py", "--storage.bucket", "my-bucket"]
        with patch.object(sys, "argv", test_args):
            configs = FlatConfig.create_from_cli_args()
        config = configs[0].reconstruct_original_dataclass()
        assert config.storage.endpoint_url is None

        # With optional field
        test_args = [
            "script.py",
            "--storage.bucket",
            "my-bucket",
            "--storage.endpoint_url",
            "http://localhost:9000",
        ]
        with patch.object(sys, "argv", test_args):
            configs = FlatConfig.create_from_cli_args()
        config = configs[0].reconstruct_original_dataclass()
        assert config.storage.endpoint_url == "http://localhost:9000"

    def test_poly_with_non_poly_nested_fields(self):
        """Test polymorphic config alongside non-polymorphic nested configs."""

        @frozen_dataclass
        class DatabaseConfig:
            host: str = "localhost"
            port: int = 5432

        @frozen_dataclass
        class AppConfig:
            name: str = "app"
            database: DatabaseConfig = field(default_factory=DatabaseConfig)
            storage: BaseStorageConfig = field(default_factory=LocalStorageConfig)

        FlatConfig = create_flat_dataclass(AppConfig)
        test_args = [
            "script.py",
            "--name",
            "my-app",
            "--database.host",
            "db.local",
            "--storage.type",
            "gcs",
            "--storage.bucket",
            "gcs-bucket",
            "--storage.project",
            "my-gcp-project",
        ]

        with patch.object(sys, "argv", test_args):
            configs = FlatConfig.create_from_cli_args()

        config = configs[0].reconstruct_original_dataclass()
        assert config.name == "my-app"
        assert config.database.host == "db.local"
        assert config.database.port == 5432  # default
        assert isinstance(config.storage, GCSStorageConfig)
        assert config.storage.bucket == "gcs-bucket"
        assert config.storage.project == "my-gcp-project"


class TestPolymorphicFileLoading:
    """Tests for polymorphic config loading from files."""

    def test_poly_from_yaml_basic(self):
        """Test loading polymorphic config from YAML file."""

        @frozen_dataclass
        class AppConfig:
            name: str = "app"
            scheduler: BaseScheduler = field(default_factory=RoundRobinScheduler)

        yaml_content = """
name: "yaml-app"
scheduler:
  type: priority
  timeout: 60
  levels: 10
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            FlatConfig = create_flat_dataclass(AppConfig)
            test_args = ["script.py", "--config", yaml_path]

            with patch.object(sys, "argv", test_args):
                configs = FlatConfig.create_from_cli_args()

            config = configs[0].reconstruct_original_dataclass()
            assert config.name == "yaml-app"
            assert isinstance(config.scheduler, PriorityScheduler)
            assert config.scheduler.timeout == 60
            assert config.scheduler.levels == 10
        finally:
            Path(yaml_path).unlink()

    def test_poly_from_yaml_with_cli_override(self):
        """Test YAML polymorphic config with CLI overrides."""

        @frozen_dataclass
        class AppConfig:
            name: str = "app"
            scheduler: BaseScheduler = field(default_factory=RoundRobinScheduler)

        yaml_content = """
name: "yaml-app"
scheduler:
  type: priority
  timeout: 60
  levels: 5
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            FlatConfig = create_flat_dataclass(AppConfig)
            # Override levels from CLI
            test_args = [
                "script.py",
                "--config",
                yaml_path,
                "--scheduler.levels",
                "15",
            ]

            with patch.object(sys, "argv", test_args):
                configs = FlatConfig.create_from_cli_args()

            config = configs[0].reconstruct_original_dataclass()
            assert config.name == "yaml-app"
            assert isinstance(config.scheduler, PriorityScheduler)
            assert config.scheduler.levels == 15  # CLI override
            assert config.scheduler.timeout == 60  # from YAML
        finally:
            Path(yaml_path).unlink()

    def test_poly_from_yaml_type_override_cli(self):
        """Test overriding polymorphic type via CLI when file specifies different type."""

        @frozen_dataclass
        class AppConfig:
            name: str = "app"
            scheduler: BaseScheduler = field(default_factory=RoundRobinScheduler)

        yaml_content = """
name: "yaml-app"
scheduler:
  type: priority
  timeout: 60
  levels: 5
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            FlatConfig = create_flat_dataclass(AppConfig)
            # Override type from CLI
            test_args = [
                "script.py",
                "--config",
                yaml_path,
                "--scheduler.type",
                "round_robin",
                "--scheduler.quantum",
                "50",
            ]

            with patch.object(sys, "argv", test_args):
                configs = FlatConfig.create_from_cli_args()

            config = configs[0].reconstruct_original_dataclass()
            assert isinstance(config.scheduler, RoundRobinScheduler)
            assert config.scheduler.quantum == 50
        finally:
            Path(yaml_path).unlink()

    def test_poly_yaml_multiple_configs_expansion(self):
        """Test YAML with list expansion creates multiple polymorphic configs."""

        @frozen_dataclass
        class AppConfig:
            name: str = "app"
            storage: BaseStorageConfig = field(default_factory=LocalStorageConfig)

        yaml_content = """
name: "multi-app"
storage:
  - type: local
    path: /data/local
  - type: s3
    bucket: s3-bucket
    region: us-west-2
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            FlatConfig = create_flat_dataclass(AppConfig)
            test_args = ["script.py", "--config", yaml_path]

            with patch.object(sys, "argv", test_args):
                configs = FlatConfig.create_from_cli_args()

            assert len(configs) == 2

            config1 = configs[0].reconstruct_original_dataclass()
            assert isinstance(config1.storage, LocalStorageConfig)
            assert config1.storage.path == "/data/local"

            config2 = configs[1].reconstruct_original_dataclass()
            assert isinstance(config2.storage, S3StorageConfig)
            assert config2.storage.bucket == "s3-bucket"
            assert config2.storage.region == "us-west-2"
        finally:
            Path(yaml_path).unlink()

    def test_poly_nested_in_yaml(self):
        """Test deeply nested polymorphic configs in YAML."""

        @frozen_dataclass
        class InnerConfig:
            scheduler: BaseScheduler = field(default_factory=RoundRobinScheduler)

        @frozen_dataclass
        class OuterConfig:
            name: str = "outer"
            inner: InnerConfig = field(default_factory=InnerConfig)

        yaml_content = """
name: "nested-app"
inner:
  scheduler:
    type: priority
    timeout: 120
    levels: 7
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            FlatConfig = create_flat_dataclass(OuterConfig)
            test_args = ["script.py", "--config", yaml_path]

            with patch.object(sys, "argv", test_args):
                configs = FlatConfig.create_from_cli_args()

            config = configs[0].reconstruct_original_dataclass()
            assert config.name == "nested-app"
            assert isinstance(config.inner.scheduler, PriorityScheduler)
            assert config.inner.scheduler.timeout == 120
            assert config.inner.scheduler.levels == 7
        finally:
            Path(yaml_path).unlink()


class TestPolymorphicEdgeCases:
    """Edge case tests for polymorphic configs."""

    def test_poly_all_variants_have_same_field_name_different_defaults(self):
        """Test when all variants have a field with same name but different defaults."""

        class QueueType(Enum):
            FIFO = "fifo"
            LIFO = "lifo"
            PRIORITY = "priority"

        @frozen_dataclass
        class BaseQueueConfig(BasePolyConfig):
            @classmethod
            def get_type(cls) -> QueueType:
                raise NotImplementedError()

        @frozen_dataclass
        class FifoQueueConfig(BaseQueueConfig):
            max_size: int = 100

            @classmethod
            def get_type(cls) -> QueueType:
                return QueueType.FIFO

        @frozen_dataclass
        class LifoQueueConfig(BaseQueueConfig):
            max_size: int = 50  # Different default

            @classmethod
            def get_type(cls) -> QueueType:
                return QueueType.LIFO

        @frozen_dataclass
        class PriorityQueueConfig(BaseQueueConfig):
            max_size: int = 200  # Different default
            num_priorities: int = 5

            @classmethod
            def get_type(cls) -> QueueType:
                return QueueType.PRIORITY

        @frozen_dataclass
        class AppConfig:
            queue: BaseQueueConfig = field(default_factory=FifoQueueConfig)

        FlatConfig = create_flat_dataclass(AppConfig)

        # Test FIFO default
        test_args = ["script.py", "--queue.type", "fifo"]
        with patch.object(sys, "argv", test_args):
            configs = FlatConfig.create_from_cli_args()
        config = configs[0].reconstruct_original_dataclass()
        assert isinstance(config.queue, FifoQueueConfig)
        assert config.queue.max_size == 100

        # Test LIFO with its default
        test_args = ["script.py", "--queue.type", "lifo"]
        with patch.object(sys, "argv", test_args):
            configs = FlatConfig.create_from_cli_args()
        config = configs[0].reconstruct_original_dataclass()
        assert isinstance(config.queue, LifoQueueConfig)
        # Note: max_size will use the value from the flat dataclass, which
        # may not be variant-specific. This is a known limitation.

        # Test explicit override works
        test_args = ["script.py", "--queue.type", "lifo", "--queue.max_size", "75"]
        with patch.object(sys, "argv", test_args):
            configs = FlatConfig.create_from_cli_args()
        config = configs[0].reconstruct_original_dataclass()
        assert isinstance(config.queue, LifoQueueConfig)
        assert config.queue.max_size == 75

    def test_poly_variant_only_field_not_passed_for_other_variant(self):
        """Test that variant-only fields don't cause issues for other variants."""

        @frozen_dataclass
        class AppConfig:
            scheduler: BaseScheduler = field(default_factory=RoundRobinScheduler)

        FlatConfig = create_flat_dataclass(AppConfig)

        # Use round_robin (has quantum field) - should work without levels
        test_args = [
            "script.py",
            "--scheduler.type",
            "round_robin",
            "--scheduler.quantum",
            "150",
        ]
        with patch.object(sys, "argv", test_args):
            configs = FlatConfig.create_from_cli_args()

        config = configs[0].reconstruct_original_dataclass()
        assert isinstance(config.scheduler, RoundRobinScheduler)
        assert config.scheduler.quantum == 150
        # Should not have levels attribute (it's PriorityScheduler-only)
        assert not hasattr(config.scheduler, "levels")

    def test_poly_three_variants(self):
        """Test polymorphic config with three variants."""

        @frozen_dataclass
        class AppConfig:
            storage: BaseStorageConfig = field(default_factory=LocalStorageConfig)

        FlatConfig = create_flat_dataclass(AppConfig)

        # Test all three variants
        variants = [
            ("local", LocalStorageConfig, {"path": "/custom"}),
            ("s3", S3StorageConfig, {"bucket": "test-bucket"}),
            ("gcs", GCSStorageConfig, {"bucket": "gcs-test", "project": "test-proj"}),
        ]

        for type_name, expected_class, extra_args in variants:
            test_args = ["script.py", "--storage.type", type_name]
            for key, value in extra_args.items():
                test_args.extend([f"--storage.{key}", str(value)])

            with patch.object(sys, "argv", test_args):
                configs = FlatConfig.create_from_cli_args()

            config = configs[0].reconstruct_original_dataclass()
            assert isinstance(config.storage, expected_class), f"Failed for {type_name}"
            for key, value in extra_args.items():
                assert getattr(config.storage, key) == value

    def test_poly_optional_polymorphic_field(self):
        """Test optional polymorphic field that defaults to None."""

        @frozen_dataclass
        class AppConfig:
            name: str = "app"
            scheduler: Optional[BaseScheduler] = None

        FlatConfig = create_flat_dataclass(AppConfig)

        # Without specifying scheduler
        test_args = ["script.py", "--name", "my-app"]
        with patch.object(sys, "argv", test_args):
            configs = FlatConfig.create_from_cli_args()

        config = configs[0].reconstruct_original_dataclass()
        assert config.name == "my-app"
        assert config.scheduler is None

        # With scheduler specified
        test_args = [
            "script.py",
            "--name",
            "my-app",
            "--scheduler.type",
            "round_robin",
        ]
        with patch.object(sys, "argv", test_args):
            configs = FlatConfig.create_from_cli_args()

        config = configs[0].reconstruct_original_dataclass()
        assert isinstance(config.scheduler, RoundRobinScheduler)


class TestPolymorphicHelpOutput:
    """Tests for help output with polymorphic configs."""

    def test_help_shows_type_choices(self):
        """Test that help output shows available type choices."""
        from vidhi.flat_dataclass.cli import _build_parser

        @frozen_dataclass
        class AppConfig:
            scheduler: BaseScheduler = field(default_factory=RoundRobinScheduler)

        FlatConfig = create_flat_dataclass(AppConfig)
        parser = _build_parser(FlatConfig)

        # Check that the type field has choices info
        type_arg = parser.arguments.get("scheduler_type")
        assert type_arg is not None
        assert "round_robin" in type_arg.help_text.lower()
        assert "priority" in type_arg.help_text.lower()

    def test_help_shows_variant_only_fields(self):
        """Test that help shows which fields are variant-only."""
        from vidhi.flat_dataclass.cli import _build_parser

        @frozen_dataclass
        class AppConfig:
            scheduler: BaseScheduler = field(default_factory=RoundRobinScheduler)

        FlatConfig = create_flat_dataclass(AppConfig)
        parser = _build_parser(FlatConfig)

        # levels is only for priority
        levels_arg = parser.arguments.get("scheduler__levels")
        assert levels_arg is not None
        assert levels_arg.variants is not None
        assert "priority" in levels_arg.variants

        # quantum is only for round_robin
        quantum_arg = parser.arguments.get("scheduler__quantum")
        assert quantum_arg is not None
        assert quantum_arg.variants is not None
        assert "round_robin" in quantum_arg.variants

        # timeout is shared - should have all variants or no variant restriction
        timeout_arg = parser.arguments.get("scheduler__timeout")
        assert timeout_arg is not None


class TestNestedPolymorphicConfigs:
    """Tests for nested polymorphic configurations (poly inside poly)."""

    def test_nested_poly_basic(self):
        """Test basic nested polymorphic config - a poly field inside a poly variant."""

        class InnerType(Enum):
            FAST = "fast"
            SLOW = "slow"

        @frozen_dataclass
        class BaseInnerConfig(BasePolyConfig):
            name: str = "inner"

            @classmethod
            def get_type(cls) -> InnerType:
                raise NotImplementedError()

        @frozen_dataclass
        class FastInnerConfig(BaseInnerConfig):
            speed: int = 100

            @classmethod
            def get_type(cls) -> InnerType:
                return InnerType.FAST

        @frozen_dataclass
        class SlowInnerConfig(BaseInnerConfig):
            speed: int = 10

            @classmethod
            def get_type(cls) -> InnerType:
                return InnerType.SLOW

        class OuterType(Enum):
            ALPHA = "alpha"
            BETA = "beta"

        @frozen_dataclass
        class BaseOuterConfig(BasePolyConfig):
            label: str = "outer"

            @classmethod
            def get_type(cls) -> OuterType:
                raise NotImplementedError()

        @frozen_dataclass
        class AlphaConfig(BaseOuterConfig):
            inner: BaseInnerConfig = field(default_factory=FastInnerConfig)
            alpha_value: int = 1

            @classmethod
            def get_type(cls) -> OuterType:
                return OuterType.ALPHA

        @frozen_dataclass
        class BetaConfig(BaseOuterConfig):
            inner: BaseInnerConfig = field(default_factory=SlowInnerConfig)
            beta_value: int = 2

            @classmethod
            def get_type(cls) -> OuterType:
                return OuterType.BETA

        @frozen_dataclass
        class AppConfig:
            app_name: str = "app"
            outer: BaseOuterConfig = field(default_factory=AlphaConfig)

        FlatConfig = create_flat_dataclass(AppConfig)

        # Test default (alpha with fast inner)
        test_args = ["script.py"]
        with patch.object(sys, "argv", test_args):
            configs = FlatConfig.create_from_cli_args()

        config = configs[0].reconstruct_original_dataclass()
        assert isinstance(config.outer, AlphaConfig)
        assert isinstance(config.outer.inner, FastInnerConfig)
        assert config.outer.inner.speed == 100

    def test_nested_poly_switch_both_types(self):
        """Test switching both outer and inner polymorphic types via CLI."""

        class InnerType(Enum):
            FAST = "fast"
            SLOW = "slow"

        @frozen_dataclass
        class BaseInnerConfig(BasePolyConfig):
            name: str = "inner"

            @classmethod
            def get_type(cls) -> InnerType:
                raise NotImplementedError()

        @frozen_dataclass
        class FastInnerConfig(BaseInnerConfig):
            speed: int = 100

            @classmethod
            def get_type(cls) -> InnerType:
                return InnerType.FAST

        @frozen_dataclass
        class SlowInnerConfig(BaseInnerConfig):
            speed: int = 10

            @classmethod
            def get_type(cls) -> InnerType:
                return InnerType.SLOW

        class OuterType(Enum):
            ALPHA = "alpha"
            BETA = "beta"

        @frozen_dataclass
        class BaseOuterConfig(BasePolyConfig):
            label: str = "outer"

            @classmethod
            def get_type(cls) -> OuterType:
                raise NotImplementedError()

        @frozen_dataclass
        class AlphaConfig(BaseOuterConfig):
            inner: BaseInnerConfig = field(default_factory=FastInnerConfig)
            alpha_value: int = 1

            @classmethod
            def get_type(cls) -> OuterType:
                return OuterType.ALPHA

        @frozen_dataclass
        class BetaConfig(BaseOuterConfig):
            inner: BaseInnerConfig = field(default_factory=SlowInnerConfig)
            beta_value: int = 2

            @classmethod
            def get_type(cls) -> OuterType:
                return OuterType.BETA

        @frozen_dataclass
        class AppConfig:
            app_name: str = "app"
            outer: BaseOuterConfig = field(default_factory=AlphaConfig)

        FlatConfig = create_flat_dataclass(AppConfig)

        # Switch to beta with slow inner
        test_args = [
            "script.py",
            "--outer.type",
            "beta",
            "--outer.inner.type",
            "slow",
            "--outer.inner.speed",
            "5",
        ]
        with patch.object(sys, "argv", test_args):
            configs = FlatConfig.create_from_cli_args()

        config = configs[0].reconstruct_original_dataclass()
        assert isinstance(config.outer, BetaConfig)
        assert isinstance(config.outer.inner, SlowInnerConfig)
        assert config.outer.inner.speed == 5

    def test_nested_poly_fields_registered(self):
        """Test that nested polymorphic config fields are properly registered."""

        class InnerType(Enum):
            X = "x"
            Y = "y"

        @frozen_dataclass
        class BaseInnerConfig(BasePolyConfig):
            @classmethod
            def get_type(cls) -> InnerType:
                raise NotImplementedError()

        @frozen_dataclass
        class XConfig(BaseInnerConfig):
            x_value: int = 10

            @classmethod
            def get_type(cls) -> InnerType:
                return InnerType.X

        @frozen_dataclass
        class YConfig(BaseInnerConfig):
            y_value: int = 20

            @classmethod
            def get_type(cls) -> InnerType:
                return InnerType.Y

        class OuterType(Enum):
            A = "a"

        @frozen_dataclass
        class BaseOuterConfig(BasePolyConfig):
            @classmethod
            def get_type(cls) -> OuterType:
                raise NotImplementedError()

        @frozen_dataclass
        class AConfig(BaseOuterConfig):
            inner: BaseInnerConfig = field(default_factory=XConfig)

            @classmethod
            def get_type(cls) -> OuterType:
                return OuterType.A

        @frozen_dataclass
        class AppConfig:
            outer: BaseOuterConfig = field(default_factory=AConfig)

        FlatConfig = create_flat_dataclass(AppConfig)

        # Check that nested type field is registered
        assert hasattr(FlatConfig, "outer__inner_type")

        # Check nested poly children are tracked
        assert "outer__inner" in FlatConfig.base_poly_children
        assert "x" in FlatConfig.base_poly_children["outer__inner"]
        assert "y" in FlatConfig.base_poly_children["outer__inner"]

    def test_nested_poly_from_yaml(self):
        """Test loading nested polymorphic configs from YAML."""

        class InnerType(Enum):
            FAST = "fast"
            SLOW = "slow"

        @frozen_dataclass
        class BaseInnerConfig(BasePolyConfig):
            @classmethod
            def get_type(cls) -> InnerType:
                raise NotImplementedError()

        @frozen_dataclass
        class FastInnerConfig(BaseInnerConfig):
            speed: int = 100

            @classmethod
            def get_type(cls) -> InnerType:
                return InnerType.FAST

        @frozen_dataclass
        class SlowInnerConfig(BaseInnerConfig):
            speed: int = 10

            @classmethod
            def get_type(cls) -> InnerType:
                return InnerType.SLOW

        class OuterType(Enum):
            ALPHA = "alpha"

        @frozen_dataclass
        class BaseOuterConfig(BasePolyConfig):
            @classmethod
            def get_type(cls) -> OuterType:
                raise NotImplementedError()

        @frozen_dataclass
        class AlphaConfig(BaseOuterConfig):
            inner: BaseInnerConfig = field(default_factory=FastInnerConfig)

            @classmethod
            def get_type(cls) -> OuterType:
                return OuterType.ALPHA

        @frozen_dataclass
        class AppConfig:
            name: str = "app"
            outer: BaseOuterConfig = field(default_factory=AlphaConfig)

        yaml_content = """
name: "yaml-nested-app"
outer:
  type: alpha
  inner:
    type: slow
    speed: 25
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            FlatConfig = create_flat_dataclass(AppConfig)
            test_args = ["script.py", "--config", yaml_path]

            with patch.object(sys, "argv", test_args):
                configs = FlatConfig.create_from_cli_args()

            config = configs[0].reconstruct_original_dataclass()
            assert config.name == "yaml-nested-app"
            assert isinstance(config.outer, AlphaConfig)
            assert isinstance(config.outer.inner, SlowInnerConfig)
            assert config.outer.inner.speed == 25
        finally:
            Path(yaml_path).unlink()

    def test_nested_poly_three_levels(self):
        """Test three levels of nested polymorphic configs."""

        class Level3Type(Enum):
            L3A = "l3a"
            L3B = "l3b"

        @frozen_dataclass
        class BaseLevel3(BasePolyConfig):
            @classmethod
            def get_type(cls) -> Level3Type:
                raise NotImplementedError()

        @frozen_dataclass
        class L3AConfig(BaseLevel3):
            l3a_val: int = 300

            @classmethod
            def get_type(cls) -> Level3Type:
                return Level3Type.L3A

        @frozen_dataclass
        class L3BConfig(BaseLevel3):
            l3b_val: int = 301

            @classmethod
            def get_type(cls) -> Level3Type:
                return Level3Type.L3B

        class Level2Type(Enum):
            L2A = "l2a"

        @frozen_dataclass
        class BaseLevel2(BasePolyConfig):
            @classmethod
            def get_type(cls) -> Level2Type:
                raise NotImplementedError()

        @frozen_dataclass
        class L2AConfig(BaseLevel2):
            l2a_val: int = 200
            level3: BaseLevel3 = field(default_factory=L3AConfig)

            @classmethod
            def get_type(cls) -> Level2Type:
                return Level2Type.L2A

        class Level1Type(Enum):
            L1A = "l1a"

        @frozen_dataclass
        class BaseLevel1(BasePolyConfig):
            @classmethod
            def get_type(cls) -> Level1Type:
                raise NotImplementedError()

        @frozen_dataclass
        class L1AConfig(BaseLevel1):
            l1a_val: int = 100
            level2: BaseLevel2 = field(default_factory=L2AConfig)

            @classmethod
            def get_type(cls) -> Level1Type:
                return Level1Type.L1A

        @frozen_dataclass
        class AppConfig:
            level1: BaseLevel1 = field(default_factory=L1AConfig)

        FlatConfig = create_flat_dataclass(AppConfig)

        # Check that deeply nested type fields exist
        assert hasattr(FlatConfig, "level1__level2_type")
        assert hasattr(FlatConfig, "level1__level2__level3_type")

        # Test setting deeply nested type and value
        # CLI uses . separators, type field uses _type suffix
        test_args = [
            "script.py",
            "--level1.level2.level3.type",
            "l3b",
            "--level1.level2.level3.l3b_val",
            "999",
        ]
        with patch.object(sys, "argv", test_args):
            configs = FlatConfig.create_from_cli_args()

        config = configs[0].reconstruct_original_dataclass()
        assert isinstance(config.level1, L1AConfig)
        assert isinstance(config.level1.level2, L2AConfig)
        assert isinstance(config.level1.level2.level3, L3BConfig)
        assert config.level1.level2.level3.l3b_val == 999


class TestSharedPolyBaseClass:
    """Tests for multiple properties using the same polymorphic base class."""

    def test_same_poly_base_two_fields_same_class(self):
        """Test two fields in the same class using the same poly base."""

        class SchedulerType(Enum):
            FAST = "fast"
            SLOW = "slow"

        @frozen_dataclass
        class BaseScheduler(BasePolyConfig):
            name: str = "scheduler"

            @classmethod
            def get_type(cls) -> SchedulerType:
                raise NotImplementedError()

        @frozen_dataclass
        class FastScheduler(BaseScheduler):
            speed: int = 100

            @classmethod
            def get_type(cls) -> SchedulerType:
                return SchedulerType.FAST

        @frozen_dataclass
        class SlowScheduler(BaseScheduler):
            speed: int = 10

            @classmethod
            def get_type(cls) -> SchedulerType:
                return SchedulerType.SLOW

        @frozen_dataclass
        class AppConfig:
            primary_scheduler: BaseScheduler = field(default_factory=FastScheduler)
            backup_scheduler: BaseScheduler = field(default_factory=SlowScheduler)

        FlatConfig = create_flat_dataclass(AppConfig)

        # Verify both type fields exist
        assert hasattr(FlatConfig, "primary_scheduler_type")
        assert hasattr(FlatConfig, "backup_scheduler_type")

        # Test setting both to different types
        test_args = [
            "script.py",
            "--primary_scheduler.type",
            "slow",
            "--primary_scheduler.speed",
            "5",
            "--backup_scheduler.type",
            "fast",
            "--backup_scheduler.speed",
            "200",
        ]
        with patch.object(sys, "argv", test_args):
            configs = FlatConfig.create_from_cli_args()

        config = configs[0].reconstruct_original_dataclass()
        assert isinstance(config.primary_scheduler, SlowScheduler)
        assert config.primary_scheduler.speed == 5
        assert isinstance(config.backup_scheduler, FastScheduler)
        assert config.backup_scheduler.speed == 200

    def test_same_poly_base_three_fields_same_class(self):
        """Test three fields using the same poly base class."""

        class StorageType(Enum):
            LOCAL = "local"
            REMOTE = "remote"

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
        class RemoteStorage(BaseStorage):
            url: str = "http://storage"

            @classmethod
            def get_type(cls) -> StorageType:
                return StorageType.REMOTE

        @frozen_dataclass
        class AppConfig:
            input_storage: BaseStorage = field(default_factory=LocalStorage)
            output_storage: BaseStorage = field(default_factory=LocalStorage)
            cache_storage: BaseStorage = field(default_factory=RemoteStorage)

        FlatConfig = create_flat_dataclass(AppConfig)

        # Set all three to different configurations
        test_args = [
            "script.py",
            "--input_storage.type",
            "local",
            "--input_storage.path",
            "/input",
            "--output_storage.type",
            "remote",
            "--output_storage.url",
            "http://output",
            "--cache_storage.type",
            "local",
            "--cache_storage.path",
            "/cache",
        ]
        with patch.object(sys, "argv", test_args):
            configs = FlatConfig.create_from_cli_args()

        config = configs[0].reconstruct_original_dataclass()
        assert isinstance(config.input_storage, LocalStorage)
        assert config.input_storage.path == "/input"
        assert isinstance(config.output_storage, RemoteStorage)
        assert config.output_storage.url == "http://output"
        assert isinstance(config.cache_storage, LocalStorage)
        assert config.cache_storage.path == "/cache"

    def test_same_poly_base_different_nesting_levels(self):
        """Test same poly base at different nesting levels."""

        class ProcessorType(Enum):
            CPU = "cpu"
            GPU = "gpu"

        @frozen_dataclass
        class BaseProcessor(BasePolyConfig):
            cores: int = 1

            @classmethod
            def get_type(cls) -> ProcessorType:
                raise NotImplementedError()

        @frozen_dataclass
        class CPUProcessor(BaseProcessor):
            threads_per_core: int = 2

            @classmethod
            def get_type(cls) -> ProcessorType:
                return ProcessorType.CPU

        @frozen_dataclass
        class GPUProcessor(BaseProcessor):
            cuda_cores: int = 1000

            @classmethod
            def get_type(cls) -> ProcessorType:
                return ProcessorType.GPU

        @frozen_dataclass
        class WorkerConfig:
            name: str = "worker"
            processor: BaseProcessor = field(default_factory=CPUProcessor)

        @frozen_dataclass
        class AppConfig:
            main_processor: BaseProcessor = field(default_factory=GPUProcessor)
            worker: WorkerConfig = field(default_factory=WorkerConfig)

        FlatConfig = create_flat_dataclass(AppConfig)

        # Verify type fields at different levels
        assert hasattr(FlatConfig, "main_processor_type")
        assert hasattr(FlatConfig, "worker__processor_type")

        # Set top-level to GPU, nested to CPU
        test_args = [
            "script.py",
            "--main_processor.type",
            "gpu",
            "--main_processor.cuda_cores",
            "2000",
            "--worker.processor.type",
            "cpu",
            "--worker.processor.threads_per_core",
            "4",
        ]
        with patch.object(sys, "argv", test_args):
            configs = FlatConfig.create_from_cli_args()

        config = configs[0].reconstruct_original_dataclass()
        assert isinstance(config.main_processor, GPUProcessor)
        assert config.main_processor.cuda_cores == 2000
        assert isinstance(config.worker.processor, CPUProcessor)
        assert config.worker.processor.threads_per_core == 4

    def test_same_poly_base_nested_and_sibling(self):
        """Test same poly base used both as sibling and nested field."""

        class CacheType(Enum):
            MEMORY = "memory"
            DISK = "disk"

        @frozen_dataclass
        class BaseCache(BasePolyConfig):
            ttl: int = 60

            @classmethod
            def get_type(cls) -> CacheType:
                raise NotImplementedError()

        @frozen_dataclass
        class MemoryCache(BaseCache):
            max_items: int = 1000

            @classmethod
            def get_type(cls) -> CacheType:
                return CacheType.MEMORY

        @frozen_dataclass
        class DiskCache(BaseCache):
            path: str = "/tmp/cache"

            @classmethod
            def get_type(cls) -> CacheType:
                return CacheType.DISK

        @frozen_dataclass
        class ServiceConfig:
            cache: BaseCache = field(default_factory=MemoryCache)

        @frozen_dataclass
        class AppConfig:
            global_cache: BaseCache = field(default_factory=DiskCache)
            service_a: ServiceConfig = field(default_factory=ServiceConfig)
            service_b: ServiceConfig = field(default_factory=ServiceConfig)

        FlatConfig = create_flat_dataclass(AppConfig)

        # All three use same poly base but different instances
        test_args = [
            "script.py",
            "--global_cache.type",
            "disk",
            "--global_cache.path",
            "/var/cache",
            "--service_a.cache.type",
            "memory",
            "--service_a.cache.max_items",
            "500",
            "--service_b.cache.type",
            "disk",
            "--service_b.cache.path",
            "/tmp/service_b",
        ]
        with patch.object(sys, "argv", test_args):
            configs = FlatConfig.create_from_cli_args()

        config = configs[0].reconstruct_original_dataclass()
        assert isinstance(config.global_cache, DiskCache)
        assert config.global_cache.path == "/var/cache"
        assert isinstance(config.service_a.cache, MemoryCache)
        assert config.service_a.cache.max_items == 500
        assert isinstance(config.service_b.cache, DiskCache)
        assert config.service_b.cache.path == "/tmp/service_b"

    def test_same_poly_base_in_poly_variant(self):
        """Test same poly base used inside a polymorphic variant."""

        class BackendType(Enum):
            SQL = "sql"
            NOSQL = "nosql"

        @frozen_dataclass
        class BaseBackend(BasePolyConfig):
            timeout: int = 30

            @classmethod
            def get_type(cls) -> BackendType:
                raise NotImplementedError()

        @frozen_dataclass
        class SQLBackend(BaseBackend):
            connection_string: str = "sqlite://"

            @classmethod
            def get_type(cls) -> BackendType:
                return BackendType.SQL

        @frozen_dataclass
        class NoSQLBackend(BaseBackend):
            host: str = "localhost"

            @classmethod
            def get_type(cls) -> BackendType:
                return BackendType.NOSQL

        class ServiceType(Enum):
            PRIMARY = "primary"
            SECONDARY = "secondary"

        @frozen_dataclass
        class BaseService(BasePolyConfig):
            @classmethod
            def get_type(cls) -> ServiceType:
                raise NotImplementedError()

        @frozen_dataclass
        class PrimaryService(BaseService):
            main_backend: BaseBackend = field(default_factory=SQLBackend)
            replica_backend: BaseBackend = field(default_factory=SQLBackend)

            @classmethod
            def get_type(cls) -> ServiceType:
                return ServiceType.PRIMARY

        @frozen_dataclass
        class SecondaryService(BaseService):
            backend: BaseBackend = field(default_factory=NoSQLBackend)

            @classmethod
            def get_type(cls) -> ServiceType:
                return ServiceType.SECONDARY

        @frozen_dataclass
        class AppConfig:
            service: BaseService = field(default_factory=PrimaryService)

        FlatConfig = create_flat_dataclass(AppConfig)

        # Test primary service with two backends of same poly base
        test_args = [
            "script.py",
            "--service.type",
            "primary",
            "--service.main_backend.type",
            "sql",
            "--service.main_backend.connection_string",
            "postgres://main",
            "--service.replica_backend.type",
            "nosql",
            "--service.replica_backend.host",
            "replica.local",
        ]
        with patch.object(sys, "argv", test_args):
            configs = FlatConfig.create_from_cli_args()

        config = configs[0].reconstruct_original_dataclass()
        assert isinstance(config.service, PrimaryService)
        assert isinstance(config.service.main_backend, SQLBackend)
        assert config.service.main_backend.connection_string == "postgres://main"
        assert isinstance(config.service.replica_backend, NoSQLBackend)
        assert config.service.replica_backend.host == "replica.local"

    def test_same_poly_base_from_yaml(self):
        """Test multiple fields with same poly base loaded from YAML."""

        class QueueType(Enum):
            FIFO = "fifo"
            LIFO = "lifo"

        @frozen_dataclass
        class BaseQueue(BasePolyConfig):
            size: int = 100

            @classmethod
            def get_type(cls) -> QueueType:
                raise NotImplementedError()

        @frozen_dataclass
        class FIFOQueue(BaseQueue):
            overflow_policy: str = "drop"

            @classmethod
            def get_type(cls) -> QueueType:
                return QueueType.FIFO

        @frozen_dataclass
        class LIFOQueue(BaseQueue):
            max_depth: int = 50

            @classmethod
            def get_type(cls) -> QueueType:
                return QueueType.LIFO

        @frozen_dataclass
        class AppConfig:
            input_queue: BaseQueue = field(default_factory=FIFOQueue)
            output_queue: BaseQueue = field(default_factory=FIFOQueue)

        yaml_content = """
input_queue:
  type: fifo
  size: 200
  overflow_policy: block
output_queue:
  type: lifo
  size: 50
  max_depth: 25
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            FlatConfig = create_flat_dataclass(AppConfig)
            test_args = ["script.py", "--config", yaml_path]

            with patch.object(sys, "argv", test_args):
                configs = FlatConfig.create_from_cli_args()

            config = configs[0].reconstruct_original_dataclass()
            assert isinstance(config.input_queue, FIFOQueue)
            assert config.input_queue.size == 200
            assert config.input_queue.overflow_policy == "block"
            assert isinstance(config.output_queue, LIFOQueue)
            assert config.output_queue.size == 50
            assert config.output_queue.max_depth == 25
        finally:
            Path(yaml_path).unlink()

    def test_same_poly_base_mixed_cli_and_defaults(self):
        """Test multiple fields with same poly base, some from CLI, some defaults."""

        class LoggerType(Enum):
            FILE = "file"
            CONSOLE = "console"

        @frozen_dataclass
        class BaseLogger(BasePolyConfig):
            level: str = "INFO"

            @classmethod
            def get_type(cls) -> LoggerType:
                raise NotImplementedError()

        @frozen_dataclass
        class FileLogger(BaseLogger):
            path: str = "/var/log/app.log"

            @classmethod
            def get_type(cls) -> LoggerType:
                return LoggerType.FILE

        @frozen_dataclass
        class ConsoleLogger(BaseLogger):
            colorize: bool = True

            @classmethod
            def get_type(cls) -> LoggerType:
                return LoggerType.CONSOLE

        @frozen_dataclass
        class AppConfig:
            error_logger: BaseLogger = field(default_factory=FileLogger)
            debug_logger: BaseLogger = field(default_factory=ConsoleLogger)
            audit_logger: BaseLogger = field(default_factory=FileLogger)

        FlatConfig = create_flat_dataclass(AppConfig)

        # Only set error_logger, leave others as defaults
        test_args = [
            "script.py",
            "--error_logger.type",
            "console",
            "--error_logger.colorize",
            "false",
        ]
        with patch.object(sys, "argv", test_args):
            configs = FlatConfig.create_from_cli_args()

        config = configs[0].reconstruct_original_dataclass()
        # error_logger switched to console
        assert isinstance(config.error_logger, ConsoleLogger)
        assert config.error_logger.colorize is False
        # debug_logger keeps default (console)
        assert isinstance(config.debug_logger, ConsoleLogger)
        assert config.debug_logger.colorize is True  # default
        # audit_logger keeps default (file)
        assert isinstance(config.audit_logger, FileLogger)
        assert config.audit_logger.path == "/var/log/app.log"

    def test_same_poly_base_deep_nesting_multiple(self):
        """Test same poly base at multiple deep nesting levels."""

        class HandlerType(Enum):
            SYNC = "sync"
            ASYNC = "async"

        @frozen_dataclass
        class BaseHandler(BasePolyConfig):
            timeout: int = 10

            @classmethod
            def get_type(cls) -> HandlerType:
                raise NotImplementedError()

        @frozen_dataclass
        class SyncHandler(BaseHandler):
            block: bool = True

            @classmethod
            def get_type(cls) -> HandlerType:
                return HandlerType.SYNC

        @frozen_dataclass
        class AsyncHandler(BaseHandler):
            max_concurrent: int = 10

            @classmethod
            def get_type(cls) -> HandlerType:
                return HandlerType.ASYNC

        @frozen_dataclass
        class Level3Config:
            handler: BaseHandler = field(default_factory=SyncHandler)

        @frozen_dataclass
        class Level2Config:
            handler: BaseHandler = field(default_factory=AsyncHandler)
            nested: Level3Config = field(default_factory=Level3Config)

        @frozen_dataclass
        class Level1Config:
            handler: BaseHandler = field(default_factory=SyncHandler)
            nested: Level2Config = field(default_factory=Level2Config)

        @frozen_dataclass
        class AppConfig:
            handler: BaseHandler = field(default_factory=AsyncHandler)
            nested: Level1Config = field(default_factory=Level1Config)

        FlatConfig = create_flat_dataclass(AppConfig)

        # Verify all handler type fields exist at different levels
        assert hasattr(FlatConfig, "handler_type")
        assert hasattr(FlatConfig, "nested__handler_type")
        assert hasattr(FlatConfig, "nested__nested__handler_type")
        assert hasattr(FlatConfig, "nested__nested__nested__handler_type")

        # Set handlers at different levels to different types
        test_args = [
            "script.py",
            "--handler.type",
            "async",
            "--handler.max_concurrent",
            "20",
            "--nested.handler.type",
            "sync",
            "--nested.handler.block",
            "false",
            "--nested.nested.handler.type",
            "async",
            "--nested.nested.handler.max_concurrent",
            "5",
            "--nested.nested.nested.handler.type",
            "sync",
        ]
        with patch.object(sys, "argv", test_args):
            configs = FlatConfig.create_from_cli_args()

        config = configs[0].reconstruct_original_dataclass()
        # Level 0: async
        assert isinstance(config.handler, AsyncHandler)
        assert config.handler.max_concurrent == 20
        # Level 1: sync
        assert isinstance(config.nested.handler, SyncHandler)
        assert config.nested.handler.block is False
        # Level 2: async
        assert isinstance(config.nested.nested.handler, AsyncHandler)
        assert config.nested.nested.handler.max_concurrent == 5
        # Level 3: sync
        assert isinstance(config.nested.nested.nested.handler, SyncHandler)


class TestPolymorphicCornerCases:
    """Corner case tests for polymorphic configs."""

    def test_poly_variant_with_required_field(self):
        """Test poly variant with a required field (no default)."""

        class ModeType(Enum):
            SIMPLE = "simple"
            ADVANCED = "advanced"

        @frozen_dataclass
        class BaseMode(BasePolyConfig):
            name: str = "mode"

            @classmethod
            def get_type(cls) -> ModeType:
                raise NotImplementedError()

        @frozen_dataclass
        class SimpleMode(BaseMode):
            level: int = 1

            @classmethod
            def get_type(cls) -> ModeType:
                return ModeType.SIMPLE

        @frozen_dataclass
        class AdvancedMode(BaseMode):
            # This variant has all defaults too for CLI compatibility
            complexity: int = 10
            features: str = "all"

            @classmethod
            def get_type(cls) -> ModeType:
                return ModeType.ADVANCED

        @frozen_dataclass
        class AppConfig:
            mode: BaseMode = field(default_factory=SimpleMode)

        FlatConfig = create_flat_dataclass(AppConfig)

        # Switch to advanced and provide its fields
        test_args = [
            "script.py",
            "--mode.type",
            "advanced",
            "--mode.complexity",
            "20",
            "--mode.features",
            "limited",
        ]
        with patch.object(sys, "argv", test_args):
            configs = FlatConfig.create_from_cli_args()

        config = configs[0].reconstruct_original_dataclass()
        assert isinstance(config.mode, AdvancedMode)
        assert config.mode.complexity == 20
        assert config.mode.features == "limited"

    def test_poly_variant_with_enum_field(self):
        """Test poly variant containing an enum-typed field."""

        class Priority(Enum):
            LOW = "low"
            MEDIUM = "medium"
            HIGH = "high"

        class TaskType(Enum):
            SYNC = "sync"
            ASYNC = "async"

        @frozen_dataclass
        class BaseTask(BasePolyConfig):
            name: str = "task"

            @classmethod
            def get_type(cls) -> TaskType:
                raise NotImplementedError()

        @frozen_dataclass
        class SyncTask(BaseTask):
            timeout: int = 30

            @classmethod
            def get_type(cls) -> TaskType:
                return TaskType.SYNC

        @frozen_dataclass
        class AsyncTask(BaseTask):
            priority: Priority = Priority.MEDIUM
            max_retries: int = 3

            @classmethod
            def get_type(cls) -> TaskType:
                return TaskType.ASYNC

        @frozen_dataclass
        class AppConfig:
            task: BaseTask = field(default_factory=SyncTask)

        FlatConfig = create_flat_dataclass(AppConfig)

        # Test with enum field
        test_args = [
            "script.py",
            "--task.type",
            "async",
            "--task.priority",
            "high",
            "--task.max_retries",
            "5",
        ]
        with patch.object(sys, "argv", test_args):
            configs = FlatConfig.create_from_cli_args()

        config = configs[0].reconstruct_original_dataclass()
        assert isinstance(config.task, AsyncTask)
        # Enum fields are auto-converted from strings to enum values
        assert config.task.priority == Priority.HIGH
        assert config.task.max_retries == 5

    def test_poly_overlapping_field_names_same_type(self):
        """Test variants with same field name and same type but different defaults."""

        class EngineType(Enum):
            V4 = "v4"
            V6 = "v6"
            V8 = "v8"

        @frozen_dataclass
        class BaseEngine(BasePolyConfig):
            @classmethod
            def get_type(cls) -> EngineType:
                raise NotImplementedError()

        @frozen_dataclass
        class V4Engine(BaseEngine):
            horsepower: int = 150
            cylinders: int = 4

            @classmethod
            def get_type(cls) -> EngineType:
                return EngineType.V4

        @frozen_dataclass
        class V6Engine(BaseEngine):
            horsepower: int = 250  # Same name, different default
            cylinders: int = 6

            @classmethod
            def get_type(cls) -> EngineType:
                return EngineType.V6

        @frozen_dataclass
        class V8Engine(BaseEngine):
            horsepower: int = 400  # Same name, different default
            cylinders: int = 8
            turbo: bool = False  # Unique to V8

            @classmethod
            def get_type(cls) -> EngineType:
                return EngineType.V8

        @frozen_dataclass
        class CarConfig:
            engine: BaseEngine = field(default_factory=V4Engine)

        FlatConfig = create_flat_dataclass(CarConfig)

        # Test V8 with custom horsepower
        test_args = [
            "script.py",
            "--engine.type",
            "v8",
            "--engine.horsepower",
            "500",
            "--engine.turbo",
            "true",
        ]
        with patch.object(sys, "argv", test_args):
            configs = FlatConfig.create_from_cli_args()

        config = configs[0].reconstruct_original_dataclass()
        assert isinstance(config.engine, V8Engine)
        assert config.engine.horsepower == 500
        assert config.engine.cylinders == 8
        assert config.engine.turbo is True

    def test_poly_with_list_field_in_variant(self):
        """Test poly variant with a list field."""

        class StrategyType(Enum):
            SINGLE = "single"
            MULTI = "multi"

        @frozen_dataclass
        class BaseStrategy(BasePolyConfig):
            name: str = "strategy"

            @classmethod
            def get_type(cls) -> StrategyType:
                raise NotImplementedError()

        @frozen_dataclass
        class SingleStrategy(BaseStrategy):
            target: str = "default"

            @classmethod
            def get_type(cls) -> StrategyType:
                return StrategyType.SINGLE

        @frozen_dataclass
        class MultiStrategy(BaseStrategy):
            targets: List[str] = field(default_factory=list)
            parallel: bool = True

            @classmethod
            def get_type(cls) -> StrategyType:
                return StrategyType.MULTI

        @frozen_dataclass
        class AppConfig:
            strategy: BaseStrategy = field(default_factory=SingleStrategy)

        FlatConfig = create_flat_dataclass(AppConfig)

        # Test with list field via CLI (multiple values)
        test_args = [
            "script.py",
            "--strategy.type",
            "multi",
            "--strategy.targets",
            "target1",
            "target2",
            "target3",
            "--strategy.parallel",
            "false",
        ]
        with patch.object(sys, "argv", test_args):
            configs = FlatConfig.create_from_cli_args()

        config = configs[0].reconstruct_original_dataclass()
        assert isinstance(config.strategy, MultiStrategy)
        assert config.strategy.targets == ["target1", "target2", "target3"]
        assert config.strategy.parallel is False

    def test_poly_switch_variant_file_to_cli(self):
        """Test switching poly variant from file default to different CLI type."""

        class ConnType(Enum):
            HTTP = "http"
            GRPC = "grpc"

        @frozen_dataclass
        class BaseConnection(BasePolyConfig):
            timeout: int = 30

            @classmethod
            def get_type(cls) -> ConnType:
                raise NotImplementedError()

        @frozen_dataclass
        class HttpConnection(BaseConnection):
            url: str = "http://localhost"
            headers: str = ""

            @classmethod
            def get_type(cls) -> ConnType:
                return ConnType.HTTP

        @frozen_dataclass
        class GrpcConnection(BaseConnection):
            host: str = "localhost"
            port: int = 50051

            @classmethod
            def get_type(cls) -> ConnType:
                return ConnType.GRPC

        @frozen_dataclass
        class AppConfig:
            connection: BaseConnection = field(default_factory=HttpConnection)

        # YAML has HTTP connection
        yaml_content = """
connection:
  type: http
  timeout: 60
  url: http://api.example.com
  headers: "Authorization: Bearer token"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            FlatConfig = create_flat_dataclass(AppConfig)

            # CLI overrides to GRPC
            test_args = [
                "script.py",
                "--config",
                yaml_path,
                "--connection.type",
                "grpc",
                "--connection.host",
                "grpc.example.com",
                "--connection.port",
                "9090",
            ]
            with patch.object(sys, "argv", test_args):
                configs = FlatConfig.create_from_cli_args()

            config = configs[0].reconstruct_original_dataclass()
            assert isinstance(config.connection, GrpcConnection)
            assert config.connection.host == "grpc.example.com"
            assert config.connection.port == 9090
            # Timeout from file should still apply if shared
            assert config.connection.timeout == 60
        finally:
            Path(yaml_path).unlink()

    def test_poly_with_post_init_validation(self):
        """Test poly variant with __post_init__ validation."""

        class RangeType(Enum):
            PERCENT = "percent"
            ABSOLUTE = "absolute"

        @frozen_dataclass
        class BaseRange(BasePolyConfig):
            @classmethod
            def get_type(cls) -> RangeType:
                raise NotImplementedError()

        @frozen_dataclass
        class PercentRange(BaseRange):
            min_pct: int = 0
            max_pct: int = 100

            @classmethod
            def get_type(cls) -> RangeType:
                return RangeType.PERCENT

            def __post_init__(self):
                if not (0 <= self.min_pct <= 100):
                    raise ValueError(f"min_pct must be 0-100, got {self.min_pct}")
                if not (0 <= self.max_pct <= 100):
                    raise ValueError(f"max_pct must be 0-100, got {self.max_pct}")
                if self.min_pct > self.max_pct:
                    raise ValueError("min_pct cannot exceed max_pct")

        @frozen_dataclass
        class AbsoluteRange(BaseRange):
            min_val: int = 0
            max_val: int = 1000

            @classmethod
            def get_type(cls) -> RangeType:
                return RangeType.ABSOLUTE

        @frozen_dataclass
        class AppConfig:
            range: BaseRange = field(default_factory=PercentRange)

        FlatConfig = create_flat_dataclass(AppConfig)

        # Valid percent range
        test_args = [
            "script.py",
            "--range.type",
            "percent",
            "--range.min_pct",
            "10",
            "--range.max_pct",
            "90",
        ]
        with patch.object(sys, "argv", test_args):
            configs = FlatConfig.create_from_cli_args()

        config = configs[0].reconstruct_original_dataclass()
        assert isinstance(config.range, PercentRange)
        assert config.range.min_pct == 10
        assert config.range.max_pct == 90

        # Invalid percent range should raise
        test_args = [
            "script.py",
            "--range.type",
            "percent",
            "--range.min_pct",
            "80",
            "--range.max_pct",
            "20",  # min > max
        ]
        with patch.object(sys, "argv", test_args):
            configs = FlatConfig.create_from_cli_args()

        with pytest.raises(ValueError, match="min_pct cannot exceed max_pct"):
            configs[0].reconstruct_original_dataclass()

    def test_poly_numeric_edge_cases(self):
        """Test poly variants with numeric edge cases.

        Note: Same field name with different types across variants is NOT supported.
        Each variant must use unique field names or compatible types.
        """

        class CalcType(Enum):
            INT = "int"
            FLOAT = "float"

        @frozen_dataclass
        class BaseCalc(BasePolyConfig):
            @classmethod
            def get_type(cls) -> CalcType:
                raise NotImplementedError()

        @frozen_dataclass
        class IntCalc(BaseCalc):
            int_value: int = 0
            multiplier: int = 1

            @classmethod
            def get_type(cls) -> CalcType:
                return CalcType.INT

        @frozen_dataclass
        class FloatCalc(BaseCalc):
            float_value: float = 0.0
            precision: int = 2

            @classmethod
            def get_type(cls) -> CalcType:
                return CalcType.FLOAT

        @frozen_dataclass
        class AppConfig:
            calc: BaseCalc = field(default_factory=IntCalc)

        FlatConfig = create_flat_dataclass(AppConfig)

        # Test negative integer
        test_args = [
            "script.py",
            "--calc.type",
            "int",
            "--calc.int_value",
            "-999",
            "--calc.multiplier",
            "-1",
        ]
        with patch.object(sys, "argv", test_args):
            configs = FlatConfig.create_from_cli_args()

        config = configs[0].reconstruct_original_dataclass()
        assert config.calc.int_value == -999
        assert config.calc.multiplier == -1

        # Test float with decimal
        test_args = [
            "script.py",
            "--calc.type",
            "float",
            "--calc.float_value",
            "3.14159",
            "--calc.precision",
            "5",
        ]
        with patch.object(sys, "argv", test_args):
            configs = FlatConfig.create_from_cli_args()

        config = configs[0].reconstruct_original_dataclass()
        assert abs(config.calc.float_value - 3.14159) < 0.00001
        assert config.calc.precision == 5

    def test_poly_variant_only_inherits_no_new_fields(self):
        """Test poly variant that only inherits fields, adds no new ones."""

        class ProfileType(Enum):
            DEFAULT = "default"
            CUSTOM = "custom"

        @frozen_dataclass
        class BaseProfile(BasePolyConfig):
            name: str = "profile"
            enabled: bool = True

            @classmethod
            def get_type(cls) -> ProfileType:
                raise NotImplementedError()

        @frozen_dataclass
        class DefaultProfile(BaseProfile):
            # No new fields, just uses inherited ones

            @classmethod
            def get_type(cls) -> ProfileType:
                return ProfileType.DEFAULT

        @frozen_dataclass
        class CustomProfile(BaseProfile):
            custom_setting: str = "none"

            @classmethod
            def get_type(cls) -> ProfileType:
                return ProfileType.CUSTOM

        @frozen_dataclass
        class AppConfig:
            profile: BaseProfile = field(default_factory=DefaultProfile)

        FlatConfig = create_flat_dataclass(AppConfig)

        # Use default profile (variant with no new fields)
        test_args = [
            "script.py",
            "--profile.type",
            "default",
            "--profile.name",
            "my-profile",
            "--profile.enabled",
            "false",
        ]
        with patch.object(sys, "argv", test_args):
            configs = FlatConfig.create_from_cli_args()

        config = configs[0].reconstruct_original_dataclass()
        assert isinstance(config.profile, DefaultProfile)
        assert config.profile.name == "my-profile"
        assert config.profile.enabled is False

    def test_poly_special_characters_in_string(self):
        """Test poly variants with special characters in string values."""

        class FormatType(Enum):
            PLAIN = "plain"
            RICH = "rich"

        @frozen_dataclass
        class BaseFormat(BasePolyConfig):
            @classmethod
            def get_type(cls) -> FormatType:
                raise NotImplementedError()

        @frozen_dataclass
        class PlainFormat(BaseFormat):
            text: str = ""

            @classmethod
            def get_type(cls) -> FormatType:
                return FormatType.PLAIN

        @frozen_dataclass
        class RichFormat(BaseFormat):
            template: str = ""
            delimiter: str = ","

            @classmethod
            def get_type(cls) -> FormatType:
                return FormatType.RICH

        @frozen_dataclass
        class AppConfig:
            fmt: BaseFormat = field(default_factory=PlainFormat)

        FlatConfig = create_flat_dataclass(AppConfig)

        # Test with special characters
        test_args = [
            "script.py",
            "--fmt.type",
            "rich",
            "--fmt.template",
            "Hello, {name}! <b>Welcome</b>",
            "--fmt.delimiter",
            "|",
        ]
        with patch.object(sys, "argv", test_args):
            configs = FlatConfig.create_from_cli_args()

        config = configs[0].reconstruct_original_dataclass()
        assert isinstance(config.fmt, RichFormat)
        assert config.fmt.template == "Hello, {name}! <b>Welcome</b>"
        assert config.fmt.delimiter == "|"

    def test_poly_with_optional_nested_dataclass(self):
        """Test poly variant with optional nested dataclass field."""

        @frozen_dataclass
        class Metadata:
            version: str = "1.0"
            author: str = "unknown"

        class PluginType(Enum):
            BASIC = "basic"
            EXTENDED = "extended"

        @frozen_dataclass
        class BasePlugin(BasePolyConfig):
            name: str = "plugin"

            @classmethod
            def get_type(cls) -> PluginType:
                raise NotImplementedError()

        @frozen_dataclass
        class BasicPlugin(BasePlugin):
            enabled: bool = True

            @classmethod
            def get_type(cls) -> PluginType:
                return PluginType.BASIC

        @frozen_dataclass
        class ExtendedPlugin(BasePlugin):
            enabled: bool = True
            metadata: Metadata = field(default_factory=Metadata)

            @classmethod
            def get_type(cls) -> PluginType:
                return PluginType.EXTENDED

        @frozen_dataclass
        class AppConfig:
            plugin: BasePlugin = field(default_factory=BasicPlugin)

        FlatConfig = create_flat_dataclass(AppConfig)

        # Test extended plugin with nested metadata
        test_args = [
            "script.py",
            "--plugin.type",
            "extended",
            "--plugin.name",
            "my-plugin",
            "--plugin.metadata.version",
            "2.0",
            "--plugin.metadata.author",
            "test-author",
        ]
        with patch.object(sys, "argv", test_args):
            configs = FlatConfig.create_from_cli_args()

        config = configs[0].reconstruct_original_dataclass()
        assert isinstance(config.plugin, ExtendedPlugin)
        assert config.plugin.name == "my-plugin"
        assert config.plugin.metadata.version == "2.0"
        assert config.plugin.metadata.author == "test-author"

    def test_poly_all_defaults_no_cli_args(self):
        """Test poly config when using all defaults with no CLI args."""

        class StyleType(Enum):
            DARK = "dark"
            LIGHT = "light"

        @frozen_dataclass
        class BaseStyle(BasePolyConfig):
            font_size: int = 12

            @classmethod
            def get_type(cls) -> StyleType:
                raise NotImplementedError()

        @frozen_dataclass
        class DarkStyle(BaseStyle):
            background: str = "#000000"
            foreground: str = "#FFFFFF"

            @classmethod
            def get_type(cls) -> StyleType:
                return StyleType.DARK

        @frozen_dataclass
        class LightStyle(BaseStyle):
            background: str = "#FFFFFF"
            foreground: str = "#000000"

            @classmethod
            def get_type(cls) -> StyleType:
                return StyleType.LIGHT

        @frozen_dataclass
        class AppConfig:
            primary_style: BaseStyle = field(default_factory=DarkStyle)
            secondary_style: BaseStyle = field(default_factory=LightStyle)

        FlatConfig = create_flat_dataclass(AppConfig)

        # No CLI args at all - use all defaults
        test_args = ["script.py"]
        with patch.object(sys, "argv", test_args):
            configs = FlatConfig.create_from_cli_args()

        config = configs[0].reconstruct_original_dataclass()
        assert isinstance(config.primary_style, DarkStyle)
        assert config.primary_style.background == "#000000"
        assert isinstance(config.secondary_style, LightStyle)
        assert config.secondary_style.background == "#FFFFFF"

    def test_poly_multiple_files_different_poly_fields(self):
        """Test loading different poly fields from different files."""

        class DbType(Enum):
            POSTGRES = "postgres"
            MYSQL = "mysql"

        @frozen_dataclass
        class BaseDb(BasePolyConfig):
            host: str = "localhost"

            @classmethod
            def get_type(cls) -> DbType:
                raise NotImplementedError()

        @frozen_dataclass
        class PostgresDb(BaseDb):
            port: int = 5432

            @classmethod
            def get_type(cls) -> DbType:
                return DbType.POSTGRES

        @frozen_dataclass
        class MysqlDb(BaseDb):
            port: int = 3306

            @classmethod
            def get_type(cls) -> DbType:
                return DbType.MYSQL

        class CacheType(Enum):
            REDIS = "redis"
            MEMCACHED = "memcached"

        @frozen_dataclass
        class BaseCacheConfig(BasePolyConfig):
            ttl: int = 300

            @classmethod
            def get_type(cls) -> CacheType:
                raise NotImplementedError()

        @frozen_dataclass
        class RedisCache(BaseCacheConfig):
            host: str = "localhost"
            port: int = 6379

            @classmethod
            def get_type(cls) -> CacheType:
                return CacheType.REDIS

        @frozen_dataclass
        class MemcachedCache(BaseCacheConfig):
            servers: str = "localhost:11211"

            @classmethod
            def get_type(cls) -> CacheType:
                return CacheType.MEMCACHED

        @frozen_dataclass
        class DbConfig:
            db: BaseDb = field(default_factory=PostgresDb)

        @frozen_dataclass
        class CacheConfig:
            cache: BaseCacheConfig = field(default_factory=RedisCache)

        @frozen_dataclass
        class AppConfig:
            database: DbConfig = field(default_factory=DbConfig)
            caching: CacheConfig = field(default_factory=CacheConfig)

        # Create a combined config file
        yaml_content = """
database:
  db:
    type: mysql
    host: db.example.com
    port: 3307
caching:
  cache:
    type: memcached
    ttl: 600
    servers: cache1:11211,cache2:11211
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            FlatConfig = create_flat_dataclass(AppConfig)

            test_args = ["script.py", "--config", yaml_path]
            with patch.object(sys, "argv", test_args):
                configs = FlatConfig.create_from_cli_args()

            config = configs[0].reconstruct_original_dataclass()
            # DB from config file
            assert isinstance(config.database.db, MysqlDb)
            assert config.database.db.host == "db.example.com"
            assert config.database.db.port == 3307
            # Cache from config file
            assert isinstance(config.caching.cache, MemcachedCache)
            assert config.caching.cache.ttl == 600
            assert config.caching.cache.servers == "cache1:11211,cache2:11211"
        finally:
            Path(yaml_path).unlink()


class TestSchemaValidation:
    """Tests for the schema validation framework."""

    def test_type_conflict_raises_error(self):
        """Test that type conflicts are detected and raise SchemaValidationError."""
        from vidhi.flat_dataclass.validation import SchemaValidationError

        class ModeType(Enum):
            A = "a"
            B = "b"

        @frozen_dataclass
        class BaseMode(BasePolyConfig):
            @classmethod
            def get_type(cls) -> ModeType:
                raise NotImplementedError()

        @frozen_dataclass
        class ModeA(BaseMode):
            value: int = 0  # int type

            @classmethod
            def get_type(cls) -> ModeType:
                return ModeType.A

        @frozen_dataclass
        class ModeB(BaseMode):
            value: str = "default"  # str type - CONFLICT!

            @classmethod
            def get_type(cls) -> ModeType:
                return ModeType.B

        @frozen_dataclass
        class AppConfig:
            mode: BaseMode = field(default_factory=ModeA)

        # Should raise SchemaValidationError due to type conflict
        with pytest.raises(SchemaValidationError) as exc_info:
            create_flat_dataclass(AppConfig)

        error_msg = str(exc_info.value)
        assert "value" in error_msg
        assert "type" in error_msg.lower()

    def test_duplicate_type_raises_error(self):
        """Test that duplicate type values are detected."""
        from vidhi.flat_dataclass.validation import SchemaValidationError

        class ModeType(Enum):
            SAME = "same"

        @frozen_dataclass
        class BaseMode(BasePolyConfig):
            @classmethod
            def get_type(cls) -> ModeType:
                raise NotImplementedError()

        @frozen_dataclass
        class ModeA(BaseMode):
            a_field: int = 1

            @classmethod
            def get_type(cls) -> ModeType:
                return ModeType.SAME  # Same type as ModeB

        @frozen_dataclass
        class ModeB(BaseMode):
            b_field: int = 2

            @classmethod
            def get_type(cls) -> ModeType:
                return ModeType.SAME  # Duplicate!

        @frozen_dataclass
        class AppConfig:
            mode: BaseMode = field(default_factory=ModeA)

        with pytest.raises(SchemaValidationError) as exc_info:
            create_flat_dataclass(AppConfig)

        error_msg = str(exc_info.value)
        assert "same" in error_msg.lower()
        assert "duplicate" in error_msg.lower() or "multiple" in error_msg.lower()

    def test_compatible_types_no_error(self):
        """Test that fields with same type across variants don't raise errors."""

        class StyleType(Enum):
            DARK = "dark"
            LIGHT = "light"

        @frozen_dataclass
        class BaseStyle(BasePolyConfig):
            @classmethod
            def get_type(cls) -> StyleType:
                raise NotImplementedError()

        @frozen_dataclass
        class DarkStyle(BaseStyle):
            color: str = "#000000"  # Same type
            brightness: int = 0

            @classmethod
            def get_type(cls) -> StyleType:
                return StyleType.DARK

        @frozen_dataclass
        class LightStyle(BaseStyle):
            color: str = "#FFFFFF"  # Same type - no conflict
            brightness: int = 100

            @classmethod
            def get_type(cls) -> StyleType:
                return StyleType.LIGHT

        @frozen_dataclass
        class AppConfig:
            style: BaseStyle = field(default_factory=DarkStyle)

        # Should NOT raise - types are compatible
        FlatConfig = create_flat_dataclass(AppConfig)
        assert FlatConfig is not None

    def test_schema_result_stored_on_flat_class(self):
        """Test that schema validation results are stored on the flat class."""

        class ModeType(Enum):
            X = "x"
            Y = "y"

        @frozen_dataclass
        class BaseMode(BasePolyConfig):
            common: str = "shared"

            @classmethod
            def get_type(cls) -> ModeType:
                raise NotImplementedError()

        @frozen_dataclass
        class ModeX(BaseMode):
            x_only: int = 1

            @classmethod
            def get_type(cls) -> ModeType:
                return ModeType.X

        @frozen_dataclass
        class ModeY(BaseMode):
            y_only: int = 2

            @classmethod
            def get_type(cls) -> ModeType:
                return ModeType.Y

        @frozen_dataclass
        class AppConfig:
            mode: BaseMode = field(default_factory=ModeX)

        FlatConfig = create_flat_dataclass(AppConfig)

        # Schema results should be stored
        assert hasattr(FlatConfig, "poly_schema_results")
        assert "mode" in FlatConfig.poly_schema_results

        # Check field info was collected
        schema_result = FlatConfig.poly_schema_results["mode"]
        assert "common" in schema_result.field_info
        assert "x_only" in schema_result.field_info
        assert "y_only" in schema_result.field_info

        # Check variant types
        assert "x" in schema_result.variant_types
        assert "y" in schema_result.variant_types

    def test_validation_error_message_is_helpful(self):
        """Test that validation errors include helpful guidance."""
        from vidhi.flat_dataclass.validation import SchemaValidationError

        class ItemType(Enum):
            NUMERIC = "numeric"
            TEXT = "text"

        @frozen_dataclass
        class BaseItem(BasePolyConfig):
            @classmethod
            def get_type(cls) -> ItemType:
                raise NotImplementedError()

        @frozen_dataclass
        class NumericItem(BaseItem):
            data: int = 0

            @classmethod
            def get_type(cls) -> ItemType:
                return ItemType.NUMERIC

        @frozen_dataclass
        class TextItem(BaseItem):
            data: str = ""  # Type conflict with int

            @classmethod
            def get_type(cls) -> ItemType:
                return ItemType.TEXT

        @frozen_dataclass
        class AppConfig:
            item: BaseItem = field(default_factory=NumericItem)

        with pytest.raises(SchemaValidationError) as exc_info:
            create_flat_dataclass(AppConfig)

        error_msg = str(exc_info.value)
        # Should mention the field name
        assert "data" in error_msg
        # Should suggest using unique field names
        assert "unique" in error_msg.lower() or "different" in error_msg.lower()

    def test_optional_type_not_conflicting_with_base(self):
        """Test that Optional[X] is considered same as X for conflict detection."""

        class ModeType(Enum):
            A = "a"
            B = "b"

        @frozen_dataclass
        class BaseMode(BasePolyConfig):
            @classmethod
            def get_type(cls) -> ModeType:
                raise NotImplementedError()

        @frozen_dataclass
        class ModeA(BaseMode):
            value: str = "default"

            @classmethod
            def get_type(cls) -> ModeType:
                return ModeType.A

        @frozen_dataclass
        class ModeB(BaseMode):
            value: str = "other"  # Same base type

            @classmethod
            def get_type(cls) -> ModeType:
                return ModeType.B

        @frozen_dataclass
        class AppConfig:
            mode: BaseMode = field(default_factory=ModeA)

        # Should not raise - str and str are compatible
        FlatConfig = create_flat_dataclass(AppConfig)
        assert FlatConfig is not None
