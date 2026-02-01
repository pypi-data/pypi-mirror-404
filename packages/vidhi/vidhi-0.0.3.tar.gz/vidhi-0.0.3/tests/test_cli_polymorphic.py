"""Tests for polymorphic CLI argument parsing.

These tests ensure that polymorphic configurations work correctly with CLI parsing,
including nested polymorphic configs (poly inside poly).
"""

import sys
from dataclasses import field
from enum import Enum
from unittest.mock import patch

import pytest

from vidhi import BasePolyConfig, frozen_dataclass, parse_cli_args

# =============================================================================
# Tests: Basic Polymorphic CLI Parsing
# =============================================================================


class TestBasicPolymorphicParsing:
    """Tests for basic polymorphic CLI argument parsing."""

    def test_default_variant(self):
        """Test that default variant is used when no type specified."""

        class CacheType(Enum):
            MEMORY = "memory"
            REDIS = "redis"

        @frozen_dataclass
        class BaseCacheConfig(BasePolyConfig):
            ttl_seconds: int = field(default=3600, metadata={"help": "TTL in seconds"})

            @classmethod
            def get_type(cls) -> CacheType:
                raise NotImplementedError()

        @frozen_dataclass
        class MemoryCacheConfig(BaseCacheConfig):
            max_size: int = field(default=1000, metadata={"help": "Max cache size"})

            @classmethod
            def get_type(cls) -> CacheType:
                return CacheType.MEMORY

        @frozen_dataclass
        class RedisCacheConfig(BaseCacheConfig):
            host: str = field(default="localhost", metadata={"help": "Redis host"})

            @classmethod
            def get_type(cls) -> CacheType:
                return CacheType.REDIS

        @frozen_dataclass
        class AppConfig:
            name: str = field(default="app", metadata={"help": "App name"})
            cache: BaseCacheConfig = field(default_factory=MemoryCacheConfig)

        test_args = ["script.py"]
        with patch.object(sys, "argv", test_args):
            config = parse_cli_args(AppConfig)

        assert config.name == "app"
        assert isinstance(config.cache, MemoryCacheConfig)
        assert config.cache.ttl_seconds == 3600
        assert config.cache.max_size == 1000

    def test_select_variant_via_type_arg(self):
        """Test selecting variant via --cache_type argument."""

        class CacheType(Enum):
            MEMORY = "memory"
            REDIS = "redis"

        @frozen_dataclass
        class BaseCacheConfig(BasePolyConfig):
            ttl_seconds: int = 3600

            @classmethod
            def get_type(cls) -> CacheType:
                raise NotImplementedError()

        @frozen_dataclass
        class MemoryCacheConfig(BaseCacheConfig):
            max_size: int = 1000

            @classmethod
            def get_type(cls) -> CacheType:
                return CacheType.MEMORY

        @frozen_dataclass
        class RedisCacheConfig(BaseCacheConfig):
            host: str = "localhost"
            port: int = 6379

            @classmethod
            def get_type(cls) -> CacheType:
                return CacheType.REDIS

        @frozen_dataclass
        class AppConfig:
            cache: BaseCacheConfig = field(default_factory=MemoryCacheConfig)

        test_args = ["script.py", "--cache.type", "redis"]
        with patch.object(sys, "argv", test_args):
            config = parse_cli_args(AppConfig)

        assert isinstance(config.cache, RedisCacheConfig)
        assert config.cache.host == "localhost"
        assert config.cache.port == 6379

    def test_variant_specific_fields(self):
        """Test setting variant-specific fields."""

        class CacheType(Enum):
            MEMORY = "memory"
            REDIS = "redis"

        @frozen_dataclass
        class BaseCacheConfig(BasePolyConfig):
            @classmethod
            def get_type(cls) -> CacheType:
                raise NotImplementedError()

        @frozen_dataclass
        class MemoryCacheConfig(BaseCacheConfig):
            @classmethod
            def get_type(cls) -> CacheType:
                return CacheType.MEMORY

        @frozen_dataclass
        class RedisCacheConfig(BaseCacheConfig):
            host: str = "localhost"
            port: int = 6379

            @classmethod
            def get_type(cls) -> CacheType:
                return CacheType.REDIS

        @frozen_dataclass
        class AppConfig:
            cache: BaseCacheConfig = field(default_factory=MemoryCacheConfig)

        test_args = [
            "script.py",
            "--cache.type",
            "redis",
            "--cache.host",
            "redis.example.com",
            "--cache.port",
            "6380",
        ]
        with patch.object(sys, "argv", test_args):
            config = parse_cli_args(AppConfig)

        assert isinstance(config.cache, RedisCacheConfig)
        assert config.cache.host == "redis.example.com"
        assert config.cache.port == 6380

    def test_common_fields_across_variants(self):
        """Test that common fields work across all variants."""

        class CacheType(Enum):
            MEMORY = "memory"
            REDIS = "redis"

        @frozen_dataclass
        class BaseCacheConfig(BasePolyConfig):
            ttl_seconds: int = 3600

            @classmethod
            def get_type(cls) -> CacheType:
                raise NotImplementedError()

        @frozen_dataclass
        class MemoryCacheConfig(BaseCacheConfig):
            @classmethod
            def get_type(cls) -> CacheType:
                return CacheType.MEMORY

        @frozen_dataclass
        class RedisCacheConfig(BaseCacheConfig):
            host: str = "localhost"

            @classmethod
            def get_type(cls) -> CacheType:
                return CacheType.REDIS

        @frozen_dataclass
        class AppConfig:
            cache: BaseCacheConfig = field(default_factory=MemoryCacheConfig)

        # Memory variant
        test_args = [
            "script.py",
            "--cache.type",
            "memory",
            "--cache.ttl_seconds",
            "7200",
        ]
        with patch.object(sys, "argv", test_args):
            config = parse_cli_args(AppConfig)

        assert isinstance(config.cache, MemoryCacheConfig)
        assert config.cache.ttl_seconds == 7200

        # Redis variant
        test_args = [
            "script.py",
            "--cache.type",
            "redis",
            "--cache.ttl_seconds",
            "1800",
        ]
        with patch.object(sys, "argv", test_args):
            config = parse_cli_args(AppConfig)

        assert isinstance(config.cache, RedisCacheConfig)
        assert config.cache.ttl_seconds == 1800

    def test_invalid_variant_type(self):
        """Test that invalid variant type raises error."""

        class CacheType(Enum):
            MEMORY = "memory"
            REDIS = "redis"

        @frozen_dataclass
        class BaseCacheConfig(BasePolyConfig):
            @classmethod
            def get_type(cls) -> CacheType:
                raise NotImplementedError()

        @frozen_dataclass
        class MemoryCacheConfig(BaseCacheConfig):
            @classmethod
            def get_type(cls) -> CacheType:
                return CacheType.MEMORY

        @frozen_dataclass
        class RedisCacheConfig(BaseCacheConfig):
            @classmethod
            def get_type(cls) -> CacheType:
                return CacheType.REDIS

        @frozen_dataclass
        class AppConfig:
            cache: BaseCacheConfig = field(default_factory=MemoryCacheConfig)

        test_args = ["script.py", "--cache.type", "invalid"]
        with patch.object(sys, "argv", test_args):
            # Invalid type raises SystemExit from parser's choices validation
            with pytest.raises(SystemExit):
                parse_cli_args(AppConfig)


# =============================================================================
# Tests: Nested Polymorphic CLI Parsing (Poly inside Poly)
# =============================================================================


class TestNestedPolymorphicParsing:
    """Tests for nested polymorphic CLI argument parsing."""

    def test_default_nested_variant(self):
        """Test default nested variant when parent variant is selected."""

        class PoolType(Enum):
            SIMPLE = "simple"
            SENTINEL = "sentinel"

        @frozen_dataclass
        class BasePoolConfig(BasePolyConfig):
            max_connections: int = 10

            @classmethod
            def get_type(cls) -> PoolType:
                raise NotImplementedError()

        @frozen_dataclass
        class SimplePoolConfig(BasePoolConfig):
            @classmethod
            def get_type(cls) -> PoolType:
                return PoolType.SIMPLE

        @frozen_dataclass
        class SentinelPoolConfig(BasePoolConfig):
            sentinels: str = "localhost:26379"

            @classmethod
            def get_type(cls) -> PoolType:
                return PoolType.SENTINEL

        class CacheType(Enum):
            MEMORY = "memory"
            REDIS = "redis"

        @frozen_dataclass
        class BaseCacheConfig(BasePolyConfig):
            ttl_seconds: int = 3600

            @classmethod
            def get_type(cls) -> CacheType:
                raise NotImplementedError()

        @frozen_dataclass
        class MemoryCacheConfig(BaseCacheConfig):
            @classmethod
            def get_type(cls) -> CacheType:
                return CacheType.MEMORY

        @frozen_dataclass
        class RedisCacheConfig(BaseCacheConfig):
            host: str = "localhost"
            pool: BasePoolConfig = field(default_factory=SimplePoolConfig)

            @classmethod
            def get_type(cls) -> CacheType:
                return CacheType.REDIS

        @frozen_dataclass
        class AppConfig:
            cache: BaseCacheConfig = field(default_factory=MemoryCacheConfig)

        test_args = ["script.py", "--cache.type", "redis"]
        with patch.object(sys, "argv", test_args):
            config = parse_cli_args(AppConfig)

        assert isinstance(config.cache, RedisCacheConfig)
        assert isinstance(config.cache.pool, SimplePoolConfig)
        assert config.cache.pool.max_connections == 10

    def test_select_nested_variant(self):
        """Test selecting nested variant via type argument."""

        class PoolType(Enum):
            SIMPLE = "simple"
            SENTINEL = "sentinel"

        @frozen_dataclass
        class BasePoolConfig(BasePolyConfig):
            max_connections: int = 10

            @classmethod
            def get_type(cls) -> PoolType:
                raise NotImplementedError()

        @frozen_dataclass
        class SimplePoolConfig(BasePoolConfig):
            @classmethod
            def get_type(cls) -> PoolType:
                return PoolType.SIMPLE

        @frozen_dataclass
        class SentinelPoolConfig(BasePoolConfig):
            sentinels: str = "localhost:26379"
            master_name: str = "mymaster"

            @classmethod
            def get_type(cls) -> PoolType:
                return PoolType.SENTINEL

        class CacheType(Enum):
            MEMORY = "memory"
            REDIS = "redis"

        @frozen_dataclass
        class BaseCacheConfig(BasePolyConfig):
            @classmethod
            def get_type(cls) -> CacheType:
                raise NotImplementedError()

        @frozen_dataclass
        class MemoryCacheConfig(BaseCacheConfig):
            @classmethod
            def get_type(cls) -> CacheType:
                return CacheType.MEMORY

        @frozen_dataclass
        class RedisCacheConfig(BaseCacheConfig):
            host: str = "localhost"
            pool: BasePoolConfig = field(default_factory=SimplePoolConfig)

            @classmethod
            def get_type(cls) -> CacheType:
                return CacheType.REDIS

        @frozen_dataclass
        class AppConfig:
            cache: BaseCacheConfig = field(default_factory=MemoryCacheConfig)

        test_args = [
            "script.py",
            "--cache.type",
            "redis",
            "--cache.pool.type",
            "sentinel",
        ]
        with patch.object(sys, "argv", test_args):
            config = parse_cli_args(AppConfig)

        assert isinstance(config.cache, RedisCacheConfig)
        assert isinstance(config.cache.pool, SentinelPoolConfig)
        assert config.cache.pool.sentinels == "localhost:26379"
        assert config.cache.pool.master_name == "mymaster"

    def test_nested_variant_specific_fields(self):
        """Test setting nested variant-specific fields."""

        class PoolType(Enum):
            SIMPLE = "simple"
            SENTINEL = "sentinel"

        @frozen_dataclass
        class BasePoolConfig(BasePolyConfig):
            max_connections: int = 10

            @classmethod
            def get_type(cls) -> PoolType:
                raise NotImplementedError()

        @frozen_dataclass
        class SimplePoolConfig(BasePoolConfig):
            @classmethod
            def get_type(cls) -> PoolType:
                return PoolType.SIMPLE

        @frozen_dataclass
        class SentinelPoolConfig(BasePoolConfig):
            sentinels: str = "localhost:26379"
            master_name: str = "mymaster"

            @classmethod
            def get_type(cls) -> PoolType:
                return PoolType.SENTINEL

        class CacheType(Enum):
            MEMORY = "memory"
            REDIS = "redis"

        @frozen_dataclass
        class BaseCacheConfig(BasePolyConfig):
            @classmethod
            def get_type(cls) -> CacheType:
                raise NotImplementedError()

        @frozen_dataclass
        class MemoryCacheConfig(BaseCacheConfig):
            @classmethod
            def get_type(cls) -> CacheType:
                return CacheType.MEMORY

        @frozen_dataclass
        class RedisCacheConfig(BaseCacheConfig):
            pool: BasePoolConfig = field(default_factory=SimplePoolConfig)

            @classmethod
            def get_type(cls) -> CacheType:
                return CacheType.REDIS

        @frozen_dataclass
        class AppConfig:
            cache: BaseCacheConfig = field(default_factory=MemoryCacheConfig)

        test_args = [
            "script.py",
            "--cache.type",
            "redis",
            "--cache.pool.type",
            "sentinel",
            "--cache.pool.sentinels",
            "host1:26379,host2:26379",
            "--cache.pool.master_name",
            "primary",
        ]
        with patch.object(sys, "argv", test_args):
            config = parse_cli_args(AppConfig)

        assert isinstance(config.cache.pool, SentinelPoolConfig)
        assert config.cache.pool.sentinels == "host1:26379,host2:26379"
        assert config.cache.pool.master_name == "primary"

    def test_nested_common_fields(self):
        """Test common fields in nested polymorphic config."""

        class PoolType(Enum):
            SIMPLE = "simple"
            SENTINEL = "sentinel"

        @frozen_dataclass
        class BasePoolConfig(BasePolyConfig):
            max_connections: int = 10

            @classmethod
            def get_type(cls) -> PoolType:
                raise NotImplementedError()

        @frozen_dataclass
        class SimplePoolConfig(BasePoolConfig):
            @classmethod
            def get_type(cls) -> PoolType:
                return PoolType.SIMPLE

        @frozen_dataclass
        class SentinelPoolConfig(BasePoolConfig):
            sentinels: str = "localhost:26379"

            @classmethod
            def get_type(cls) -> PoolType:
                return PoolType.SENTINEL

        class CacheType(Enum):
            MEMORY = "memory"
            REDIS = "redis"

        @frozen_dataclass
        class BaseCacheConfig(BasePolyConfig):
            @classmethod
            def get_type(cls) -> CacheType:
                raise NotImplementedError()

        @frozen_dataclass
        class MemoryCacheConfig(BaseCacheConfig):
            @classmethod
            def get_type(cls) -> CacheType:
                return CacheType.MEMORY

        @frozen_dataclass
        class RedisCacheConfig(BaseCacheConfig):
            pool: BasePoolConfig = field(default_factory=SimplePoolConfig)

            @classmethod
            def get_type(cls) -> CacheType:
                return CacheType.REDIS

        @frozen_dataclass
        class AppConfig:
            cache: BaseCacheConfig = field(default_factory=MemoryCacheConfig)

        test_args = [
            "script.py",
            "--cache.type",
            "redis",
            "--cache.pool.type",
            "sentinel",
            "--cache.pool.max_connections",
            "20",
        ]
        with patch.object(sys, "argv", test_args):
            config = parse_cli_args(AppConfig)

        assert config.cache.pool.max_connections == 20

    def test_parent_and_nested_fields_together(self):
        """Test setting both parent and nested variant fields."""

        class PoolType(Enum):
            SIMPLE = "simple"
            SENTINEL = "sentinel"

        @frozen_dataclass
        class BasePoolConfig(BasePolyConfig):
            @classmethod
            def get_type(cls) -> PoolType:
                raise NotImplementedError()

        @frozen_dataclass
        class SimplePoolConfig(BasePoolConfig):
            @classmethod
            def get_type(cls) -> PoolType:
                return PoolType.SIMPLE

        @frozen_dataclass
        class SentinelPoolConfig(BasePoolConfig):
            sentinels: str = "localhost:26379"

            @classmethod
            def get_type(cls) -> PoolType:
                return PoolType.SENTINEL

        class CacheType(Enum):
            MEMORY = "memory"
            REDIS = "redis"

        @frozen_dataclass
        class BaseCacheConfig(BasePolyConfig):
            @classmethod
            def get_type(cls) -> CacheType:
                raise NotImplementedError()

        @frozen_dataclass
        class MemoryCacheConfig(BaseCacheConfig):
            @classmethod
            def get_type(cls) -> CacheType:
                return CacheType.MEMORY

        @frozen_dataclass
        class RedisCacheConfig(BaseCacheConfig):
            host: str = "localhost"
            port: int = 6379
            pool: BasePoolConfig = field(default_factory=SimplePoolConfig)

            @classmethod
            def get_type(cls) -> CacheType:
                return CacheType.REDIS

        @frozen_dataclass
        class AppConfig:
            cache: BaseCacheConfig = field(default_factory=MemoryCacheConfig)

        test_args = [
            "script.py",
            "--cache.type",
            "redis",
            "--cache.host",
            "redis.example.com",
            "--cache.port",
            "6380",
            "--cache.pool.type",
            "sentinel",
            "--cache.pool.sentinels",
            "sentinel.example.com:26379",
        ]
        with patch.object(sys, "argv", test_args):
            config = parse_cli_args(AppConfig)

        assert config.cache.host == "redis.example.com"
        assert config.cache.port == 6380
        assert isinstance(config.cache.pool, SentinelPoolConfig)
        assert config.cache.pool.sentinels == "sentinel.example.com:26379"

    def test_nested_not_available_for_wrong_parent(self):
        """Test that nested poly args are ignored for wrong parent variant."""

        class PoolType(Enum):
            SIMPLE = "simple"

        @frozen_dataclass
        class BasePoolConfig(BasePolyConfig):
            @classmethod
            def get_type(cls) -> PoolType:
                raise NotImplementedError()

        @frozen_dataclass
        class SimplePoolConfig(BasePoolConfig):
            @classmethod
            def get_type(cls) -> PoolType:
                return PoolType.SIMPLE

        class CacheType(Enum):
            MEMORY = "memory"
            REDIS = "redis"

        @frozen_dataclass
        class BaseCacheConfig(BasePolyConfig):
            @classmethod
            def get_type(cls) -> CacheType:
                raise NotImplementedError()

        @frozen_dataclass
        class MemoryCacheConfig(BaseCacheConfig):
            max_size: int = 1000

            @classmethod
            def get_type(cls) -> CacheType:
                return CacheType.MEMORY

        @frozen_dataclass
        class RedisCacheConfig(BaseCacheConfig):
            pool: BasePoolConfig = field(default_factory=SimplePoolConfig)

            @classmethod
            def get_type(cls) -> CacheType:
                return CacheType.REDIS

        @frozen_dataclass
        class AppConfig:
            cache: BaseCacheConfig = field(default_factory=MemoryCacheConfig)

        # Memory cache doesn't have pool, so pool args should be ignored
        test_args = [
            "script.py",
            "--cache.type",
            "memory",
            "--cache.max_size",
            "2000",
        ]
        with patch.object(sys, "argv", test_args):
            config = parse_cli_args(AppConfig)

        assert isinstance(config.cache, MemoryCacheConfig)
        assert config.cache.max_size == 2000
        assert not hasattr(config.cache, "pool")


# =============================================================================
# Tests: Help Output
# =============================================================================


class TestPolymorphicHelpOutput:
    """Tests for polymorphic CLI help output."""

    def test_help_shows_type_selector(self):
        """Test that help output shows type selector."""

        class CacheType(Enum):
            MEMORY = "memory"
            REDIS = "redis"

        @frozen_dataclass
        class BaseCacheConfig(BasePolyConfig):
            @classmethod
            def get_type(cls) -> CacheType:
                raise NotImplementedError()

        @frozen_dataclass
        class MemoryCacheConfig(BaseCacheConfig):
            @classmethod
            def get_type(cls) -> CacheType:
                return CacheType.MEMORY

        @frozen_dataclass
        class RedisCacheConfig(BaseCacheConfig):
            @classmethod
            def get_type(cls) -> CacheType:
                return CacheType.REDIS

        @frozen_dataclass
        class AppConfig:
            cache: BaseCacheConfig = field(default_factory=MemoryCacheConfig)

        test_args = ["script.py", "--help"]
        with patch.object(sys, "argv", test_args):
            with pytest.raises(SystemExit) as exc_info:
                parse_cli_args(AppConfig)

        assert exc_info.value.code == 0

    def test_help_shows_variant_options(self, capsys):
        """Test that help output shows variant-specific options."""

        class CacheType(Enum):
            MEMORY = "memory"
            REDIS = "redis"

        @frozen_dataclass
        class BaseCacheConfig(BasePolyConfig):
            @classmethod
            def get_type(cls) -> CacheType:
                raise NotImplementedError()

        @frozen_dataclass
        class MemoryCacheConfig(BaseCacheConfig):
            @classmethod
            def get_type(cls) -> CacheType:
                return CacheType.MEMORY

        @frozen_dataclass
        class RedisCacheConfig(BaseCacheConfig):
            host: str = "localhost"

            @classmethod
            def get_type(cls) -> CacheType:
                return CacheType.REDIS

        @frozen_dataclass
        class AppConfig:
            cache: BaseCacheConfig = field(default_factory=MemoryCacheConfig)

        test_args = ["script.py", "--help"]
        with patch.object(sys, "argv", test_args):
            with pytest.raises(SystemExit):
                parse_cli_args(AppConfig)

        captured = capsys.readouterr()
        # Check for variant names in help
        assert "memory" in captured.out.lower() or "redis" in captured.out.lower()

    def test_help_shows_nested_variants(self, capsys):
        """Test that help output shows nested variant options."""

        class PoolType(Enum):
            SIMPLE = "simple"
            SENTINEL = "sentinel"

        @frozen_dataclass
        class BasePoolConfig(BasePolyConfig):
            @classmethod
            def get_type(cls) -> PoolType:
                raise NotImplementedError()

        @frozen_dataclass
        class SimplePoolConfig(BasePoolConfig):
            @classmethod
            def get_type(cls) -> PoolType:
                return PoolType.SIMPLE

        @frozen_dataclass
        class SentinelPoolConfig(BasePoolConfig):
            @classmethod
            def get_type(cls) -> PoolType:
                return PoolType.SENTINEL

        class CacheType(Enum):
            MEMORY = "memory"
            REDIS = "redis"

        @frozen_dataclass
        class BaseCacheConfig(BasePolyConfig):
            @classmethod
            def get_type(cls) -> CacheType:
                raise NotImplementedError()

        @frozen_dataclass
        class MemoryCacheConfig(BaseCacheConfig):
            @classmethod
            def get_type(cls) -> CacheType:
                return CacheType.MEMORY

        @frozen_dataclass
        class RedisCacheConfig(BaseCacheConfig):
            pool: BasePoolConfig = field(default_factory=SimplePoolConfig)

            @classmethod
            def get_type(cls) -> CacheType:
                return CacheType.REDIS

        @frozen_dataclass
        class AppConfig:
            cache: BaseCacheConfig = field(default_factory=MemoryCacheConfig)

        test_args = ["script.py", "--help"]
        with patch.object(sys, "argv", test_args):
            with pytest.raises(SystemExit):
                parse_cli_args(AppConfig)

        captured = capsys.readouterr()
        # Check for nested pool options
        assert "pool" in captured.out.lower()


# =============================================================================
# Tests: Edge Cases
# =============================================================================


class TestPolymorphicEdgeCases:
    """Tests for edge cases in polymorphic CLI parsing."""

    def test_empty_args_uses_defaults(self):
        """Test that empty args use all defaults."""

        class CacheType(Enum):
            MEMORY = "memory"
            REDIS = "redis"

        @frozen_dataclass
        class BaseCacheConfig(BasePolyConfig):
            @classmethod
            def get_type(cls) -> CacheType:
                raise NotImplementedError()

        @frozen_dataclass
        class MemoryCacheConfig(BaseCacheConfig):
            max_size: int = 1000

            @classmethod
            def get_type(cls) -> CacheType:
                return CacheType.MEMORY

        @frozen_dataclass
        class RedisCacheConfig(BaseCacheConfig):
            @classmethod
            def get_type(cls) -> CacheType:
                return CacheType.REDIS

        @frozen_dataclass
        class AppConfig:
            name: str = "app"
            cache: BaseCacheConfig = field(default_factory=MemoryCacheConfig)

        test_args = ["script.py"]
        with patch.object(sys, "argv", test_args):
            config = parse_cli_args(AppConfig)

        assert config.name == "app"
        assert isinstance(config.cache, MemoryCacheConfig)

    def test_only_type_arg(self):
        """Test providing only the type argument."""

        class CacheType(Enum):
            MEMORY = "memory"
            REDIS = "redis"

        @frozen_dataclass
        class BaseCacheConfig(BasePolyConfig):
            ttl_seconds: int = 3600

            @classmethod
            def get_type(cls) -> CacheType:
                raise NotImplementedError()

        @frozen_dataclass
        class MemoryCacheConfig(BaseCacheConfig):
            @classmethod
            def get_type(cls) -> CacheType:
                return CacheType.MEMORY

        @frozen_dataclass
        class RedisCacheConfig(BaseCacheConfig):
            host: str = "localhost"
            port: int = 6379

            @classmethod
            def get_type(cls) -> CacheType:
                return CacheType.REDIS

        @frozen_dataclass
        class AppConfig:
            cache: BaseCacheConfig = field(default_factory=MemoryCacheConfig)

        test_args = ["script.py", "--cache.type", "redis"]
        with patch.object(sys, "argv", test_args):
            config = parse_cli_args(AppConfig)

        assert isinstance(config.cache, RedisCacheConfig)
        # All fields should have defaults
        assert config.cache.ttl_seconds == 3600
        assert config.cache.host == "localhost"
        assert config.cache.port == 6379

    def test_multiple_polymorphic_fields(self):
        """Test config with multiple polymorphic fields."""

        class CacheType(Enum):
            MEMORY = "memory"
            REDIS = "redis"

        @frozen_dataclass
        class BaseCacheConfig(BasePolyConfig):
            @classmethod
            def get_type(cls) -> CacheType:
                raise NotImplementedError()

        @frozen_dataclass
        class MemoryCacheConfig(BaseCacheConfig):
            @classmethod
            def get_type(cls) -> CacheType:
                return CacheType.MEMORY

        @frozen_dataclass
        class RedisCacheConfig(BaseCacheConfig):
            host: str = "localhost"

            @classmethod
            def get_type(cls) -> CacheType:
                return CacheType.REDIS

        class SchedulerType(Enum):
            FIFO = "fifo"
            PRIORITY = "priority"

        @frozen_dataclass
        class BaseSchedulerConfig(BasePolyConfig):
            timeout: int = 30

            @classmethod
            def get_type(cls) -> SchedulerType:
                raise NotImplementedError()

        @frozen_dataclass
        class FifoSchedulerConfig(BaseSchedulerConfig):
            queue_size: int = 100

            @classmethod
            def get_type(cls) -> SchedulerType:
                return SchedulerType.FIFO

        @frozen_dataclass
        class PrioritySchedulerConfig(BaseSchedulerConfig):
            levels: int = 5

            @classmethod
            def get_type(cls) -> SchedulerType:
                return SchedulerType.PRIORITY

        @frozen_dataclass
        class AppConfig:
            cache: BaseCacheConfig = field(default_factory=MemoryCacheConfig)
            scheduler: BaseSchedulerConfig = field(default_factory=FifoSchedulerConfig)

        test_args = [
            "script.py",
            "--cache.type",
            "redis",
            "--scheduler.type",
            "priority",
            "--cache.host",
            "redis.local",
            "--scheduler.levels",
            "10",
        ]
        with patch.object(sys, "argv", test_args):
            config = parse_cli_args(AppConfig)

        assert isinstance(config.cache, RedisCacheConfig)
        assert config.cache.host == "redis.local"
        assert isinstance(config.scheduler, PrioritySchedulerConfig)
        assert config.scheduler.levels == 10


# =============================================================================
# Tests: Regular Config Nested in Polymorphic
# =============================================================================


class TestRegularNestedInPolymorphic:
    """Tests for regular configs nested inside polymorphic configs."""

    def test_regular_nested_in_poly(self):
        """Test regular dataclass nested inside polymorphic config."""

        @frozen_dataclass
        class RetryConfig:
            max_attempts: int = 3
            backoff_ms: int = 100

        class ServiceType(Enum):
            HTTP = "http"
            GRPC = "grpc"

        @frozen_dataclass
        class BaseServiceConfig(BasePolyConfig):
            timeout: int = 30
            retry: RetryConfig = field(default_factory=RetryConfig)

            @classmethod
            def get_type(cls) -> ServiceType:
                raise NotImplementedError()

        @frozen_dataclass
        class HttpServiceConfig(BaseServiceConfig):
            url: str = "http://localhost"

            @classmethod
            def get_type(cls) -> ServiceType:
                return ServiceType.HTTP

        @frozen_dataclass
        class GrpcServiceConfig(BaseServiceConfig):
            address: str = "localhost:50051"

            @classmethod
            def get_type(cls) -> ServiceType:
                return ServiceType.GRPC

        @frozen_dataclass
        class AppConfig:
            service: BaseServiceConfig = field(default_factory=HttpServiceConfig)

        test_args = [
            "script.py",
            "--service.type",
            "grpc",
            "--service.address",
            "grpc.example.com:50051",
            "--service.retry.max_attempts",
            "5",
            "--service.retry.backoff_ms",
            "200",
        ]
        with patch.object(sys, "argv", test_args):
            config = parse_cli_args(AppConfig)

        assert isinstance(config.service, GrpcServiceConfig)
        assert config.service.address == "grpc.example.com:50051"
        assert config.service.retry.max_attempts == 5
        assert config.service.retry.backoff_ms == 200


# =============================================================================
# Tests: Type Coercion
# =============================================================================


class TestPolymorphicTypeCoercion:
    """Tests for type coercion in polymorphic configs."""

    def test_int_coercion(self):
        """Test integer type coercion."""

        class CacheType(Enum):
            MEMORY = "memory"
            REDIS = "redis"

        @frozen_dataclass
        class BaseCacheConfig(BasePolyConfig):
            @classmethod
            def get_type(cls) -> CacheType:
                raise NotImplementedError()

        @frozen_dataclass
        class MemoryCacheConfig(BaseCacheConfig):
            @classmethod
            def get_type(cls) -> CacheType:
                return CacheType.MEMORY

        @frozen_dataclass
        class RedisCacheConfig(BaseCacheConfig):
            port: int = 6379

            @classmethod
            def get_type(cls) -> CacheType:
                return CacheType.REDIS

        @frozen_dataclass
        class AppConfig:
            cache: BaseCacheConfig = field(default_factory=MemoryCacheConfig)

        test_args = ["script.py", "--cache.type", "redis", "--cache.port", "6380"]
        with patch.object(sys, "argv", test_args):
            config = parse_cli_args(AppConfig)

        assert config.cache.port == 6380
        assert isinstance(config.cache.port, int)

    def test_bool_coercion(self):
        """Test boolean type coercion."""

        class CacheType(Enum):
            MEMORY = "memory"

        @frozen_dataclass
        class BaseCacheConfig(BasePolyConfig):
            @classmethod
            def get_type(cls) -> CacheType:
                raise NotImplementedError()

        @frozen_dataclass
        class MemoryCacheConfig(BaseCacheConfig):
            enabled: bool = True

            @classmethod
            def get_type(cls) -> CacheType:
                return CacheType.MEMORY

        @frozen_dataclass
        class AppConfig:
            cache: BaseCacheConfig = field(default_factory=MemoryCacheConfig)

        # Test explicit false value syntax
        test_args = ["script.py", "--cache.enabled", "false"]
        with patch.object(sys, "argv", test_args):
            config = parse_cli_args(AppConfig)

        assert config.cache.enabled is False

    def test_float_coercion(self):
        """Test float type coercion."""

        class CacheType(Enum):
            MEMORY = "memory"

        @frozen_dataclass
        class BaseCacheConfig(BasePolyConfig):
            @classmethod
            def get_type(cls) -> CacheType:
                raise NotImplementedError()

        @frozen_dataclass
        class MemoryCacheConfig(BaseCacheConfig):
            rate: float = 1.0

            @classmethod
            def get_type(cls) -> CacheType:
                return CacheType.MEMORY

        @frozen_dataclass
        class AppConfig:
            cache: BaseCacheConfig = field(default_factory=MemoryCacheConfig)

        test_args = ["script.py", "--cache.rate", "0.5"]
        with patch.object(sys, "argv", test_args):
            config = parse_cli_args(AppConfig)

        assert config.cache.rate == 0.5
        assert isinstance(config.cache.rate, float)


# =============================================================================
# Tests: Triple Nested Polymorphic (3 levels deep)
# =============================================================================


class TestTripleNestedPolymorphic:
    """Tests for three levels of nested polymorphic configs."""

    def test_three_level_nesting(self):
        """Test cache -> pool -> strategy nesting."""

        class StrategyType(Enum):
            RANDOM = "random"
            ROUND_ROBIN = "round_robin"

        @frozen_dataclass
        class BaseStrategyConfig(BasePolyConfig):
            @classmethod
            def get_type(cls) -> StrategyType:
                raise NotImplementedError()

        @frozen_dataclass
        class RandomStrategyConfig(BaseStrategyConfig):
            weight: float = 1.0

            @classmethod
            def get_type(cls) -> StrategyType:
                return StrategyType.RANDOM

        @frozen_dataclass
        class RoundRobinStrategyConfig(BaseStrategyConfig):
            @classmethod
            def get_type(cls) -> StrategyType:
                return StrategyType.ROUND_ROBIN

        class PoolType(Enum):
            SIMPLE = "simple"
            ADVANCED = "advanced"

        @frozen_dataclass
        class BasePoolConfig(BasePolyConfig):
            max_connections: int = 10

            @classmethod
            def get_type(cls) -> PoolType:
                raise NotImplementedError()

        @frozen_dataclass
        class SimplePoolConfig(BasePoolConfig):
            @classmethod
            def get_type(cls) -> PoolType:
                return PoolType.SIMPLE

        @frozen_dataclass
        class AdvancedPoolConfig(BasePoolConfig):
            strategy: BaseStrategyConfig = field(
                default_factory=RoundRobinStrategyConfig
            )

            @classmethod
            def get_type(cls) -> PoolType:
                return PoolType.ADVANCED

        class CacheType(Enum):
            MEMORY = "memory"
            REDIS = "redis"

        @frozen_dataclass
        class BaseCacheConfig(BasePolyConfig):
            @classmethod
            def get_type(cls) -> CacheType:
                raise NotImplementedError()

        @frozen_dataclass
        class MemoryCacheConfig(BaseCacheConfig):
            @classmethod
            def get_type(cls) -> CacheType:
                return CacheType.MEMORY

        @frozen_dataclass
        class RedisCacheConfig(BaseCacheConfig):
            host: str = "localhost"
            pool: BasePoolConfig = field(default_factory=SimplePoolConfig)

            @classmethod
            def get_type(cls) -> CacheType:
                return CacheType.REDIS

        @frozen_dataclass
        class AppConfig:
            cache: BaseCacheConfig = field(default_factory=MemoryCacheConfig)

        # Test selecting all three levels
        test_args = [
            "script.py",
            "--cache.type",
            "redis",
            "--cache.host",
            "redis.example.com",
            "--cache.pool.type",
            "advanced",
            "--cache.pool.max_connections",
            "50",
            "--cache.pool.strategy.type",
            "random",
            "--cache.pool.strategy.weight",
            "0.5",
        ]
        with patch.object(sys, "argv", test_args):
            config = parse_cli_args(AppConfig)

        assert isinstance(config.cache, RedisCacheConfig)
        assert config.cache.host == "redis.example.com"
        assert isinstance(config.cache.pool, AdvancedPoolConfig)
        assert config.cache.pool.max_connections == 50
        assert isinstance(config.cache.pool.strategy, RandomStrategyConfig)
        assert config.cache.pool.strategy.weight == 0.5

    def test_three_level_defaults(self):
        """Test that defaults work at all three levels."""

        class StrategyType(Enum):
            RANDOM = "random"
            ROUND_ROBIN = "round_robin"

        @frozen_dataclass
        class BaseStrategyConfig(BasePolyConfig):
            @classmethod
            def get_type(cls) -> StrategyType:
                raise NotImplementedError()

        @frozen_dataclass
        class RandomStrategyConfig(BaseStrategyConfig):
            weight: float = 1.0

            @classmethod
            def get_type(cls) -> StrategyType:
                return StrategyType.RANDOM

        @frozen_dataclass
        class RoundRobinStrategyConfig(BaseStrategyConfig):
            @classmethod
            def get_type(cls) -> StrategyType:
                return StrategyType.ROUND_ROBIN

        class PoolType(Enum):
            SIMPLE = "simple"
            ADVANCED = "advanced"

        @frozen_dataclass
        class BasePoolConfig(BasePolyConfig):
            max_connections: int = 10

            @classmethod
            def get_type(cls) -> PoolType:
                raise NotImplementedError()

        @frozen_dataclass
        class SimplePoolConfig(BasePoolConfig):
            @classmethod
            def get_type(cls) -> PoolType:
                return PoolType.SIMPLE

        @frozen_dataclass
        class AdvancedPoolConfig(BasePoolConfig):
            strategy: BaseStrategyConfig = field(
                default_factory=RoundRobinStrategyConfig
            )

            @classmethod
            def get_type(cls) -> PoolType:
                return PoolType.ADVANCED

        class CacheType(Enum):
            MEMORY = "memory"
            REDIS = "redis"

        @frozen_dataclass
        class BaseCacheConfig(BasePolyConfig):
            @classmethod
            def get_type(cls) -> CacheType:
                raise NotImplementedError()

        @frozen_dataclass
        class MemoryCacheConfig(BaseCacheConfig):
            @classmethod
            def get_type(cls) -> CacheType:
                return CacheType.MEMORY

        @frozen_dataclass
        class RedisCacheConfig(BaseCacheConfig):
            pool: BasePoolConfig = field(default_factory=SimplePoolConfig)

            @classmethod
            def get_type(cls) -> CacheType:
                return CacheType.REDIS

        @frozen_dataclass
        class AppConfig:
            cache: BaseCacheConfig = field(default_factory=MemoryCacheConfig)

        # Only select cache and pool types, let strategy use default
        test_args = [
            "script.py",
            "--cache.type",
            "redis",
            "--cache.pool.type",
            "advanced",
        ]
        with patch.object(sys, "argv", test_args):
            config = parse_cli_args(AppConfig)

        assert isinstance(config.cache, RedisCacheConfig)
        assert isinstance(config.cache.pool, AdvancedPoolConfig)
        # Default strategy is RoundRobin
        assert isinstance(config.cache.pool.strategy, RoundRobinStrategyConfig)
