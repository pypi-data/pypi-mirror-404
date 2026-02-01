API Reference
=============

Core Functions
--------------

``frozen_dataclass``
    Decorator for immutable config classes.

``field(default, *, help=None, name=None, ...)``
    Enhanced field with CLI metadata.

    - ``help``: Help text for ``--help`` output
    - ``name``: Custom CLI argument name

``parse_cli_args(config_class)``
    Parse CLI into a config instance.

``parse_cli_sweep(config_class)``
    Parse CLI into multiple config instances.

``with_cli_overrides(config)``
    Override programmatic config from CLI.


Data Loading
------------

``load_yaml_config(path)``
    Load YAML file to dict.

``create_class_from_dict(cls, config_dict)``
    Create config from dict.

``dataclass_to_dict(obj)``
    Serialize config to dict.


Polymorphism
------------

``BasePolyConfig``
    Base class for polymorphic configs.

``BasePolyConfig.create_from_type(type_enum)``
    Factory method for creating variant instances.

``BasePolyConfig.get_type()``
    Abstract method returning the config type (must be implemented).


Schema & Completion
-------------------

``ConfigSchema(config_class)``
    Introspect and export config schemas.

    - ``export_json_schema(path)``: Generate JSON Schema
    - ``export_yaml(path)``: Generate YAML docs
    - ``export_markdown(path)``: Generate Markdown docs

``FlatConfig.install_completion(name, shell=None)``
    Install shell completion.

``FlatConfig.get_completion_script(name, shell)``
    Get completion script as string.
