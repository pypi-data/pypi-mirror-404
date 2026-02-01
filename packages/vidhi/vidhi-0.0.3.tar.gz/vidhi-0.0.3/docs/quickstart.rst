Quick Start
===========

Get up and running with Vidhi in 5 minutes.


Installation
------------

.. code-block:: bash

    pip install vidhi


1. Basic Configuration
----------------------

Create an immutable configuration class using ``@frozen_dataclass``:

.. code-block:: python

    from vidhi import frozen_dataclass, field

    @frozen_dataclass
    class ServerConfig:
        host: str = field("localhost", help="Server hostname")
        port: int = field(8080, help="Server port")
        workers: int = field(4, help="Number of worker processes")
        debug: bool = field(False, help="Enable debug mode")

    # Create an instance
    config = ServerConfig(port=9000)
    print(config.port)  # 9000

    # Configs are immutable - prevents accidental modifications
    config.port = 8080  # Raises AttributeError


2. CLI Integration
------------------

Add ``parse_cli_args()`` to get automatic command-line parsing:

.. code-block:: python

    from vidhi import frozen_dataclass, field, parse_cli_args

    @frozen_dataclass
    class TrainingConfig:
        model: str = field("resnet50", help="Model architecture")
        learning_rate: float = field(0.001, help="Learning rate", name="lr")
        batch_size: int = field(32, help="Batch size")
        epochs: int = field(10, help="Number of epochs")
        use_amp: bool = field(True, help="Use automatic mixed precision")

    if __name__ == "__main__":
        config = parse_cli_args(TrainingConfig)
        print(f"Training {config.model} for {config.epochs} epochs")

Running ``python train.py --help`` produces:

.. code-block:: text

    usage: train.py [options]

    Built-in Options:
      -h, --help            show this help message and exit
      --config <path>       load configuration from YAML file

    Options:
      --model <str> [resnet50]
          Model architecture
      --lr <float> [0.001]
          Learning rate
      --batch_size <int> [32]
          Batch size
      --epochs <int> [10]
          Number of epochs
      --use_amp {true,false} [True]
          Use automatic mixed precision

Example usage:

.. code-block:: bash

    python train.py --lr 0.01 --batch_size 64 --epochs 20
    python train.py --model efficientnet --use_amp false


3. Nested Configurations
------------------------

Compose configurations from smaller pieces using ``field(default_factory=...)``:

.. code-block:: python

    from dataclasses import field
    from vidhi import frozen_dataclass

    @frozen_dataclass
    class DatabaseConfig:
        host: str = "localhost"
        port: int = 5432

    @frozen_dataclass
    class CacheConfig:
        host: str = "localhost"
        ttl: int = 3600

    @frozen_dataclass
    class AppConfig:
        name: str = "MyApp"
        database: DatabaseConfig = field(default_factory=DatabaseConfig)
        cache: CacheConfig = field(default_factory=CacheConfig)

CLI arguments use dot notation:

.. code-block:: bash

    python app.py --database.host db.example.com --database.port 5433
    python app.py --cache.host redis.example.com --cache.ttl 7200


4. Polymorphic Configurations
-----------------------------

Define configuration variants that can be selected at runtime:

.. code-block:: python

    from enum import Enum
    from dataclasses import field
    from vidhi import BasePolyConfig, frozen_dataclass, parse_cli_args

    class CacheType(Enum):
        MEMORY = "memory"
        REDIS = "redis"

    @frozen_dataclass
    class BaseCacheConfig(BasePolyConfig):
        ttl: int = 3600

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

    config = parse_cli_args(AppConfig)

The ``--help`` output shows variant-specific options:

.. code-block:: text

    Cache Options:
      Select variant with --cache.type {memory,redis}

      Cache -> memory
        --cache.ttl <int> [3600]
        --cache.max_size <int> [1000]

      Cache -> redis
        --cache.ttl <int> [3600]
        --cache.host <str> [localhost]
        --cache.port <int> [6379]

Usage:

.. code-block:: bash

    python app.py --cache.type memory --cache.max_size 5000
    python app.py --cache.type redis --cache.host redis.example.com


5. YAML Configuration
---------------------

Load configurations from YAML files:

.. code-block:: yaml

    # config.yaml
    name: "ProductionApp"
    database:
      host: "db.example.com"
      port: 5433
    cache:
      type: "redis"        # Selects the Redis variant
      host: "redis.example.com"
      port: 6379

Use ``--config`` to load:

.. code-block:: bash

    python app.py --config config.yaml

    # CLI args override YAML values
    python app.py --config config.yaml --cache.port 6380


6. Override Programmatic Defaults
---------------------------------

Use ``with_cli_overrides()`` when you want to start with code-defined defaults
but allow CLI overrides:

.. code-block:: python

    from vidhi import with_cli_overrides

    def create_config():
        # Logic to determine defaults (e.g., based on environment)
        return TrainingConfig(
            model="resnet50",
            batch_size=32,
            learning_rate=0.001,
        )

    # Start with programmatic defaults, allow CLI overrides
    config = with_cli_overrides(create_config())

Priority order: **CLI args > YAML file > code defaults**


7. IDE Autocomplete for YAML
----------------------------

Generate JSON Schema for YAML autocomplete in VS Code or other editors:

.. code-block:: bash

    python app.py --export-json-schema config.schema.json

Add to ``.vscode/settings.json``:

.. code-block:: json

    {
      "yaml.schemas": {
        "./config.schema.json": "*.yaml"
      }
    }

You'll get autocomplete and validation for your config files.


Next Steps
----------

- See the :doc:`user_guide/index` for detailed documentation
- Check out the ``examples/`` directory for complete runnable examples:
  - ``01_basic_usage.py`` - Basic CLI parsing
  - ``02_polymorphic_cli.py`` - Polymorphic configs with nested variants
  - ``03_yaml_config.py`` - YAML file loading
  - ``04_cli_yaml_combo.py`` - Combining YAML and CLI
