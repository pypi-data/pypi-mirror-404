Polymorphic Configurations
==========================

Polymorphic configs allow runtime selection of implementation variants.


Defining Variants
-----------------

1. Create an enum for type discrimination
2. Create a base class extending ``BasePolyConfig``
3. Create variant classes with ``get_type()`` methods

.. code-block:: python

    from enum import Enum
    from dataclasses import field
    from vidhi import BasePolyConfig, frozen_dataclass

    class SchedulerType(Enum):
        FIFO = "fifo"
        PRIORITY = "priority"

    @frozen_dataclass
    class BaseScheduler(BasePolyConfig):
        """Base scheduler with common fields."""
        timeout: int = 30

        @classmethod
        def get_type(cls) -> SchedulerType:
            raise NotImplementedError()

    @frozen_dataclass
    class FifoScheduler(BaseScheduler):
        """First-in-first-out scheduler."""
        queue_size: int = 1000

        @classmethod
        def get_type(cls) -> SchedulerType:
            return SchedulerType.FIFO

    @frozen_dataclass
    class PriorityScheduler(BaseScheduler):
        """Priority-based scheduler."""
        levels: int = 5
        preemption: bool = True

        @classmethod
        def get_type(cls) -> SchedulerType:
            return SchedulerType.PRIORITY


Creating Instances
------------------

**Factory method** - create from type enum:

.. code-block:: python

    scheduler = BaseScheduler.create_from_type(SchedulerType.PRIORITY)
    # Returns PriorityScheduler with defaults

**Direct instantiation**:

.. code-block:: python

    scheduler = PriorityScheduler(levels=10, preemption=False)

**From dictionary** - useful for YAML/JSON:

.. code-block:: python

    from vidhi import create_class_from_dict

    config_dict = {"type": "priority", "levels": 10}
    scheduler = create_class_from_dict(BaseScheduler, config_dict)


CLI with Polymorphic Configs
----------------------------

When used in a parent config, the CLI generates a ``--<field>.type`` argument:

.. code-block:: python

    @frozen_dataclass
    class AppConfig:
        scheduler: BaseScheduler = field(default_factory=FifoScheduler)

CLI arguments:

.. code-block:: bash

    # Select variant with --scheduler.type
    python app.py --scheduler.type priority

    # Set variant-specific fields
    python app.py --scheduler.type priority --scheduler.levels 10

    # Common fields work for all variants
    python app.py --scheduler.type fifo --scheduler.timeout 60

The ``--help`` output organizes options by variant:

.. code-block:: text

    Scheduler Options:
      Select variant with --scheduler.type {fifo,priority}

      Scheduler -> fifo
        First-in-first-out scheduler.
        --scheduler.timeout <int> [30]
            Request timeout in seconds
        --scheduler.queue_size <int> [1000]
            Maximum queue size

      Scheduler -> priority
        Priority-based scheduler.
        --scheduler.timeout <int> [30]
            Request timeout in seconds
        --scheduler.levels <int> [5]
            Number of priority levels
        --scheduler.preemption {true,false} [True]
            Enable preemption


Nested Polymorphic Configs
--------------------------

Polymorphic configs can be nested inside each other:

.. code-block:: python

    # Pool config (nested inside Redis cache)
    class PoolType(Enum):
        SIMPLE = "simple"
        SENTINEL = "sentinel"
        CLUSTER = "cluster"

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

    # Redis cache with nested polymorphic pool config
    @frozen_dataclass
    class RedisCacheConfig(BaseCacheConfig):
        host: str = "localhost"
        port: int = 6379
        pool: BasePoolConfig = field(default_factory=SimplePoolConfig)

        @classmethod
        def get_type(cls) -> CacheType:
            return CacheType.REDIS

CLI usage with nested polymorphic configs:

.. code-block:: bash

    # Select cache type and nested pool type
    python app.py --cache.type redis --cache.pool.type sentinel

    # Set nested variant-specific fields
    python app.py --cache.type redis --cache.pool.type sentinel \
        --cache.pool.sentinels "host1:26379,host2:26379" \
        --cache.pool.master_name "mymaster"

The ``--help`` output shows nested variants:

.. code-block:: text

    Cache Options:
      Select variant with --cache.type {memory,redis,memcached}

      Cache -> redis
        --cache.host <str> [localhost]
        --cache.port <int> [6379]

        Pool Options:
          Select with --cache.pool.type {simple,sentinel,cluster}

          Pool -> sentinel
            --cache.pool.max_connections <int> [10]
            --cache.pool.sentinels <str> [localhost:26379]
            --cache.pool.master_name <str> [mymaster]


YAML with Polymorphic Configs
-----------------------------

In YAML, use the ``type`` field to select the variant:

.. code-block:: yaml

    # Simple polymorphic config
    scheduler:
      type: "priority"
      levels: 10
      preemption: true

    # Nested polymorphic config
    cache:
      type: "redis"
      host: "redis.example.com"
      port: 6379
      pool:
        type: "sentinel"
        sentinels: "host1:26379,host2:26379"
        master_name: "mymaster"


Regular Configs Inside Polymorphic
----------------------------------

You can nest regular (non-polymorphic) configs inside polymorphic ones:

.. code-block:: python

    @frozen_dataclass
    class RetryConfig:
        """Retry behavior configuration."""
        max_attempts: int = 3
        backoff_ms: int = 100

    @frozen_dataclass
    class BaseScheduler(BasePolyConfig):
        timeout: int = 30
        retry: RetryConfig = field(default_factory=RetryConfig)

        @classmethod
        def get_type(cls) -> SchedulerType:
            raise NotImplementedError()

CLI usage:

.. code-block:: bash

    python app.py --scheduler.type fifo --scheduler.retry.max_attempts 5
