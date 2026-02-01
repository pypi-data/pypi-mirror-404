IDE Autocomplete
================

Generate JSON Schema for YAML autocomplete in your IDE.

Quick Export
------------

Any Vidhi CLI supports ``--export-json-schema``::

    python train.py --export-json-schema config.schema.json

This exports the schema and prints setup instructions.


VS Code Setup
-------------

1. Export the schema::

    python train.py --export-json-schema config.schema.json

2. Add to ``.vscode/settings.json``::

    {
      "yaml.schemas": {
        "./config.schema.json": "*.yaml"
      }
    }

3. Get autocomplete and validation in your YAML config files


Programmatic Export
-------------------

::

    from vidhi.schema import ConfigSchema

    schema = ConfigSchema(AppConfig)
    schema.export_json_schema("config.schema.json")


Other Formats
-------------

::

    schema = ConfigSchema(AppConfig)

    # YAML documentation
    schema.export_yaml("config_docs.yaml")

    # Markdown documentation
    schema.export_markdown("CONFIG.md")
