#!/usr/bin/env python
"""Polymorphic configuration with CLI support.

This example demonstrates:
- Defining polymorphic configs with BasePolyConfig
- Using enum-based type discriminators
- CLI arguments that adapt to the selected variant
- Nested polymorphic configurations (pool config inside redis cache)
- Nested regular configs inside polymorphic configs (retry inside scheduler)

Run with:
    python 02_polymorphic_cli.py --help
    python 02_polymorphic_cli.py
    python 02_polymorphic_cli.py --scheduler.type priority --scheduler.levels 10
    python 02_polymorphic_cli.py --scheduler.type round_robin --scheduler.quantum_ms 50
    python 02_polymorphic_cli.py --cache.type redis --cache.host redis.example.com
    python 02_polymorphic_cli.py --cache.type redis --cache.pool.type sentinel \\
        --cache.pool.sentinels "host1:26379,host2:26379"
    python 02_polymorphic_cli.py --debug true --workers 8

Example --help output (abbreviated):

    usage: 02_polymorphic_cli.py [options]

    Options:
      --app_name <str> [MyApp]
      --debug {true,false} [False]
      --workers <int> [4]
      --cache.type {memory,redis,memcached} [memory]
      --scheduler.type {fifo,priority,round_robin} [fifo]

    Cache Options:
      Select variant with --cache.type {memory,redis,memcached}

      Cache -> memory
        --cache.ttl_seconds <int> [3600]
        --cache.eviction_policy <str> [lru]

      Cache -> redis
        --cache.host <str> [localhost]
        --cache.port <int> [6379]

        Pool Options:
          Select with --cache.pool.type {simple,sentinel,cluster}

          Pool -> sentinel
            --cache.pool.sentinels <str> [localhost:26379]
            --cache.pool.master_name <str> [mymaster]

    Scheduler Options:
      Select variant with --scheduler.type {fifo,priority,round_robin}

      Scheduler -> priority
        --scheduler.levels <int> [5]
        --scheduler.preemption {true,false} [True]
        --scheduler.retry.max_attempts <int> [3]
"""

from dataclasses import field
from enum import Enum

from vidhi import BasePolyConfig, frozen_dataclass, parse_cli_args


# =============================================================================
# Connection Pool Configuration (Polymorphic - nested inside Redis cache)
# =============================================================================


class PoolType(Enum):
    """Available connection pool implementations."""

    SIMPLE = "simple"
    SENTINEL = "sentinel"
    CLUSTER = "cluster"


@frozen_dataclass
class BasePoolConfig(BasePolyConfig):
    """Base class for connection pool configurations."""

    max_connections: int = field(default=10, metadata={"help": "Maximum pool connections"})
    timeout_ms: int = field(default=5000, metadata={"help": "Connection timeout in ms"})

    @classmethod
    def get_type(cls) -> PoolType:
        raise NotImplementedError()


@frozen_dataclass
class SimplePoolConfig(BasePoolConfig):
    """Simple single-node connection pool."""

    @classmethod
    def get_type(cls) -> PoolType:
        return PoolType.SIMPLE


@frozen_dataclass
class SentinelPoolConfig(BasePoolConfig):
    """Redis Sentinel connection pool for high availability."""

    sentinels: str = field(
        default="localhost:26379",
        metadata={"help": "Sentinel addresses (comma-separated host:port)"},
    )
    master_name: str = field(default="mymaster", metadata={"help": "Sentinel master name"})

    @classmethod
    def get_type(cls) -> PoolType:
        return PoolType.SENTINEL


@frozen_dataclass
class ClusterPoolConfig(BasePoolConfig):
    """Redis Cluster connection pool for horizontal scaling."""

    cluster_nodes: str = field(
        default="localhost:7000",
        metadata={"help": "Cluster node addresses (comma-separated host:port)"},
    )
    read_from_replicas: bool = field(
        default=False, metadata={"help": "Allow reads from replica nodes"}
    )

    @classmethod
    def get_type(cls) -> PoolType:
        return PoolType.CLUSTER


# =============================================================================
# Cache Configuration (Polymorphic)
# =============================================================================


class CacheType(Enum):
    """Available cache implementations."""

    MEMORY = "memory"
    REDIS = "redis"
    MEMCACHED = "memcached"


@frozen_dataclass
class BaseCacheConfig(BasePolyConfig):
    """Base class for all cache configurations."""

    ttl_seconds: int = field(default=3600, metadata={"help": "Default TTL in seconds"})
    max_entries: int = field(default=10000, metadata={"help": "Maximum cache entries"})

    @classmethod
    def get_type(cls) -> CacheType:
        raise NotImplementedError()


@frozen_dataclass
class MemoryCacheConfig(BaseCacheConfig):
    """In-memory cache using dict."""

    eviction_policy: str = field(
        default="lru", metadata={"help": "Eviction policy: lru, lfu, fifo"}
    )

    @classmethod
    def get_type(cls) -> CacheType:
        return CacheType.MEMORY


@frozen_dataclass
class RedisCacheConfig(BaseCacheConfig):
    """Redis-backed cache."""

    host: str = field(default="localhost", metadata={"help": "Redis host"})
    port: int = field(default=6379, metadata={"help": "Redis port"})
    db: int = field(default=0, metadata={"help": "Redis database number"})
    password: str = field(default="", metadata={"help": "Redis password"})
    # Nested polymorphic config: connection pool inside Redis cache
    pool: BasePoolConfig = field(default_factory=SimplePoolConfig)

    @classmethod
    def get_type(cls) -> CacheType:
        return CacheType.REDIS


@frozen_dataclass
class MemcachedCacheConfig(BaseCacheConfig):
    """Memcached-backed cache."""

    servers: str = field(
        default="localhost:11211",
        metadata={"help": "Memcached servers (comma-separated)"},
    )

    @classmethod
    def get_type(cls) -> CacheType:
        return CacheType.MEMCACHED


# =============================================================================
# Scheduler Configuration (Polymorphic with nested regular config)
# =============================================================================


class SchedulerType(Enum):
    """Available scheduler implementations."""

    FIFO = "fifo"
    PRIORITY = "priority"
    ROUND_ROBIN = "round_robin"


@frozen_dataclass
class RetryConfig:
    """Retry behavior configuration (nested inside scheduler)."""

    max_attempts: int = field(default=3, metadata={"help": "Maximum retry attempts"})
    backoff_ms: int = field(default=100, metadata={"help": "Initial backoff in ms"})
    exponential: bool = field(
        default=True, metadata={"help": "Use exponential backoff"}
    )


@frozen_dataclass
class BaseSchedulerConfig(BasePolyConfig):
    """Base class for all scheduler configurations."""

    timeout: int = field(default=30, metadata={"help": "Request timeout in seconds"})
    # Nested regular config inside polymorphic config
    retry: RetryConfig = field(default_factory=RetryConfig)

    @classmethod
    def get_type(cls) -> SchedulerType:
        raise NotImplementedError()


@frozen_dataclass
class FifoScheduler(BaseSchedulerConfig):
    """First-in-first-out scheduler."""

    queue_size: int = field(default=1000, metadata={"help": "Maximum queue size"})

    @classmethod
    def get_type(cls) -> SchedulerType:
        return SchedulerType.FIFO


@frozen_dataclass
class PriorityScheduler(BaseSchedulerConfig):
    """Priority-based scheduler with multiple levels."""

    levels: int = field(default=5, metadata={"help": "Number of priority levels"})
    preemption: bool = field(default=True, metadata={"help": "Enable preemption"})

    @classmethod
    def get_type(cls) -> SchedulerType:
        return SchedulerType.PRIORITY


@frozen_dataclass
class RoundRobinScheduler(BaseSchedulerConfig):
    """Round-robin scheduler with time slicing."""

    quantum_ms: int = field(default=100, metadata={"help": "Time quantum in ms"})

    @classmethod
    def get_type(cls) -> SchedulerType:
        return SchedulerType.ROUND_ROBIN


# =============================================================================
# Main Application Configuration
# =============================================================================


@frozen_dataclass
class AppConfig:
    """Main application configuration with nested polymorphic configs."""

    app_name: str = field(default="MyApp", metadata={"help": "Application name"})
    debug: bool = field(default=False, metadata={"help": "Enable debug mode"})
    workers: int = field(default=4, metadata={"help": "Number of workers"})

    # Polymorphic cache config
    cache: BaseCacheConfig = field(default_factory=MemoryCacheConfig)

    # Polymorphic scheduler config (which itself has nested RetryConfig)
    scheduler: BaseSchedulerConfig = field(default_factory=FifoScheduler)


def main():
    config = parse_cli_args(AppConfig)

    print(f"\nApplication: {config.app_name}")
    print(f"Debug: {config.debug}")
    print(f"Workers: {config.workers}")

    print(f"\nCache: {type(config.cache).__name__}")
    print(f"  Type: {config.cache.get_type().value}")
    print(f"  TTL: {config.cache.ttl_seconds}s")
    print(f"  Max Entries: {config.cache.max_entries}")

    if isinstance(config.cache, MemoryCacheConfig):
        print(f"  Eviction Policy: {config.cache.eviction_policy}")
    elif isinstance(config.cache, RedisCacheConfig):
        print(f"  Host: {config.cache.host}:{config.cache.port}")
        print(f"  Database: {config.cache.db}")
        # Show nested polymorphic pool config
        print(f"  Pool: {type(config.cache.pool).__name__}")
        print(f"    Max Connections: {config.cache.pool.max_connections}")
        print(f"    Timeout: {config.cache.pool.timeout_ms}ms")
        if isinstance(config.cache.pool, SentinelPoolConfig):
            print(f"    Sentinels: {config.cache.pool.sentinels}")
            print(f"    Master: {config.cache.pool.master_name}")
        elif isinstance(config.cache.pool, ClusterPoolConfig):
            print(f"    Cluster Nodes: {config.cache.pool.cluster_nodes}")
            print(f"    Read from Replicas: {config.cache.pool.read_from_replicas}")
    elif isinstance(config.cache, MemcachedCacheConfig):
        print(f"  Servers: {config.cache.servers}")

    print(f"\nScheduler: {type(config.scheduler).__name__}")
    print(f"  Type: {config.scheduler.get_type().value}")
    print(f"  Timeout: {config.scheduler.timeout}s")
    print(f"  Retry Config:")
    print(f"    Max Attempts: {config.scheduler.retry.max_attempts}")
    print(f"    Backoff: {config.scheduler.retry.backoff_ms}ms")
    print(f"    Exponential: {config.scheduler.retry.exponential}")

    if isinstance(config.scheduler, FifoScheduler):
        print(f"  Queue Size: {config.scheduler.queue_size}")
    elif isinstance(config.scheduler, PriorityScheduler):
        print(f"  Levels: {config.scheduler.levels}")
        print(f"  Preemption: {config.scheduler.preemption}")
    elif isinstance(config.scheduler, RoundRobinScheduler):
        print(f"  Quantum: {config.scheduler.quantum_ms}ms")


if __name__ == "__main__":
    main()
