YAML Configuration
==================

Load configurations from YAML files with full validation.

Loading via CLI
---------------

Use the ``--config`` flag to load from YAML::

    python train.py --config config.yaml

YAML file (config.yaml)::

    model: "efficientnet"
    learning_rate: 0.01
    batch_size: 64

CLI arguments can override YAML values::

    python train.py --config config.yaml --batch_size 128


Nested Configs
--------------

::

    # config.yaml
    name: "MyApp"
    database:
      host: "db.example.com"
      port: 5432


Polymorphic Configs
-------------------

Use the ``type`` field to select variants::

    # scheduler.yaml
    type: "priority"
    timeout: 60
    levels: 10


Programmatic Loading
--------------------

For direct YAML loading without CLI::

    from vidhi import load_yaml_config, create_class_from_dict

    config_dict = load_yaml_config("config.yaml")
    config = create_class_from_dict(Config, config_dict)


Serialization
-------------

Convert configs to dictionaries for YAML/JSON output::

    from vidhi import dataclass_to_dict

    config = AppConfig(name="test")
    config_dict = dataclass_to_dict(config)
    # {'name': 'test', 'port': 8080, 'debug': False}

Polymorphic configs include the ``type`` field automatically.
