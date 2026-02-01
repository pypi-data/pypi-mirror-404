CLI Integration
===============

Vidhi provides automatic CLI argument parsing for your configuration classes.


Basic Usage
-----------

Use ``parse_cli_args()`` to parse command-line arguments into a typed config:

.. code-block:: python

    from vidhi import frozen_dataclass, field, parse_cli_args

    @frozen_dataclass
    class Config:
        host: str = field("localhost", help="Server host")
        port: int = field(8080, help="Server port")
        workers: int = field(4, help="Number of workers")

    config = parse_cli_args(Config)

Running ``python app.py --help``:

.. code-block:: text

    usage: app.py [options]

    Built-in Options:
      -h, --help            show this help message and exit
      --config <path>       load configuration from YAML file
      --install-shell-completions [shell]
                            install shell completions and exit
      --export-json-schema [path]
                            export JSON schema for IDE autocomplete

    Options:
      --host <str> [localhost]
          Server host
      --port <int> [8080]
          Server port
      --workers <int> [4]
          Number of workers


Field Metadata
--------------

Use the ``field()`` helper to add CLI metadata:

.. code-block:: python

    from vidhi import frozen_dataclass, field

    @frozen_dataclass
    class Config:
        # Basic field with help text
        host: str = field("localhost", help="Server hostname")

        # Field with custom CLI name (alias)
        learning_rate: float = field(0.001, help="Learning rate", name="lr")

        # Field with multiple aliases
        output_dir: str = field(
            "./output",
            help="Output directory",
            aliases=["out", "o"]
        )

This generates:

.. code-block:: text

    --host <str> [localhost]
        Server hostname
    --lr <float> [0.001]
        Learning rate
    --output_dir, --out, --o <str> [./output]
        Output directory


Nested Configurations
---------------------

Nested configs use dot notation in CLI arguments:

.. code-block:: python

    from dataclasses import field
    from vidhi import frozen_dataclass

    @frozen_dataclass
    class DatabaseConfig:
        host: str = "localhost"
        port: int = 5432

    @frozen_dataclass
    class AppConfig:
        name: str = "MyApp"
        database: DatabaseConfig = field(default_factory=DatabaseConfig)

CLI usage:

.. code-block:: bash

    python app.py --database.host db.example.com --database.port 5433


Boolean Arguments
-----------------

Boolean fields require explicit ``true`` or ``false`` values:

.. code-block:: python

    @frozen_dataclass
    class Config:
        debug: bool = False
        use_cache: bool = True

CLI usage:

.. code-block:: bash

    python app.py --debug true
    python app.py --use_cache false

Accepted values: ``true``/``false``, ``yes``/``no``, ``1``/``0``

The ``--help`` output shows boolean fields with ``{true,false}`` choices:

.. code-block:: text

    --debug {true,false} [False]
        Enable debug mode
    --use_cache {true,false} [True]
        Enable caching


List Arguments
--------------

List fields accept multiple values:

.. code-block:: python

    from typing import List

    @frozen_dataclass
    class Config:
        hosts: List[str] = field(default_factory=list)
        ports: List[int] = field(default_factory=lambda: [8080, 8081])

CLI usage:

.. code-block:: bash

    python app.py --hosts server1 server2 server3
    python app.py --ports 9000 9001 9002


Polymorphic Type Selection
--------------------------

For polymorphic configs, use ``--<field>.type`` to select the variant:

.. code-block:: python

    @frozen_dataclass
    class AppConfig:
        cache: BaseCacheConfig = field(default_factory=MemoryCacheConfig)
        scheduler: BaseSchedulerConfig = field(default_factory=FifoScheduler)

CLI usage:

.. code-block:: bash

    # Select cache type
    python app.py --cache.type redis --cache.host redis.example.com

    # Select scheduler type
    python app.py --scheduler.type priority --scheduler.levels 10

    # Nested polymorphic (pool inside redis cache)
    python app.py --cache.type redis --cache.pool.type sentinel \
        --cache.pool.sentinels "host1:26379,host2:26379"

The ``--help`` output groups options by variant:

.. code-block:: text

    Cache Options:
      Select variant with --cache.type {memory,redis,memcached}

      Cache -> memory
        --cache.ttl_seconds <int> [3600]
        --cache.max_entries <int> [10000]
        --cache.eviction_policy <str> [lru]

      Cache -> redis
        --cache.ttl_seconds <int> [3600]
        --cache.host <str> [localhost]
        --cache.port <int> [6379]


YAML File Loading
-----------------

Use ``--config`` to load configuration from a YAML file:

.. code-block:: bash

    python app.py --config config.yaml

    # CLI arguments override YAML values
    python app.py --config config.yaml --port 9000


Overriding Programmatic Defaults
--------------------------------

Use ``with_cli_overrides()`` when you define defaults in code:

.. code-block:: python

    from vidhi import with_cli_overrides

    def create_config():
        return AppConfig(
            model="resnet50",
            batch_size=32,
        )

    # Allows CLI to override the programmatic defaults
    config = with_cli_overrides(create_config())

Priority order: **CLI args > YAML file > code defaults**
