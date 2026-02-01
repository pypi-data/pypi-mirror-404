#!/usr/bin/env python
"""Loading configuration from YAML files.

This example demonstrates:
- Loading configurations from YAML files
- Converting dictionaries to dataclass instances
- Handling nested and polymorphic configs in YAML
- Serializing configs back to dictionaries
- Using field(default_factory=...) for nested configs

Run with:
    python 03_yaml_config.py
    python 03_yaml_config.py config.yaml

Sample YAML file format:

    app_name: "ProductionApp"
    version: "2.0.0"
    debug: false

    database:
      host: "db.example.com"
      port: 5433
      name: "production"

    # Polymorphic config - 'type' field selects the variant
    storage:
      type: "s3"
      bucket: "prod-data"
      region: "us-west-2"
"""

import sys
from dataclasses import field
from enum import Enum
from pathlib import Path

from vidhi import (
    BasePolyConfig,
    create_class_from_dict,
    dataclass_to_dict,
    frozen_dataclass,
    load_yaml_config,
)


# =============================================================================
# Configuration Classes
# =============================================================================


class StorageType(Enum):
    LOCAL = "local"
    S3 = "s3"


@frozen_dataclass
class BaseStorageConfig(BasePolyConfig):
    """Base storage configuration."""

    @classmethod
    def get_type(cls) -> StorageType:
        raise NotImplementedError()


@frozen_dataclass
class LocalStorageConfig(BaseStorageConfig):
    """Local filesystem storage."""

    path: str = "/var/data"

    @classmethod
    def get_type(cls) -> StorageType:
        return StorageType.LOCAL


@frozen_dataclass
class S3StorageConfig(BaseStorageConfig):
    """AWS S3 storage."""

    bucket: str = "my-bucket"
    region: str = "us-east-1"

    @classmethod
    def get_type(cls) -> StorageType:
        return StorageType.S3


@frozen_dataclass
class DatabaseConfig:
    """Database connection configuration."""

    host: str = "localhost"
    port: int = 5432
    name: str = "mydb"


@frozen_dataclass
class AppConfig:
    """Application configuration with nested configs."""

    app_name: str = "MyApp"
    version: str = "1.0.0"
    debug: bool = False
    # Use field(default_factory=...) for nested configs
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    storage: BaseStorageConfig = field(default_factory=LocalStorageConfig)


# =============================================================================
# Sample YAML Content
# =============================================================================

SAMPLE_YAML = """\
# Sample Vidhi configuration file
app_name: "ProductionApp"
version: "2.0.0"
debug: false

database:
  host: "db.example.com"
  port: 5433
  name: "production"

# Polymorphic storage config - 'type' field selects the variant
storage:
  type: "s3"
  bucket: "prod-data"
  region: "us-west-2"
"""


def main():
    # Use provided config file or create a temp one
    if len(sys.argv) > 1:
        config_path = Path(sys.argv[1])
        if not config_path.exists():
            print(f"Error: Config file not found: {config_path}")
            sys.exit(1)
    else:
        # Create a temporary config file
        config_path = Path("/tmp/vidhi_example_config.yaml")
        config_path.write_text(SAMPLE_YAML)
        print(f"Created sample config: {config_path}\n")

    # Load and parse the config
    print("Loading configuration...")
    config_dict = load_yaml_config(str(config_path))

    print("\nRaw YAML content:")
    print("-" * 40)
    for key, value in config_dict.items():
        print(f"  {key}: {value}")

    # Convert to typed dataclass
    print("\n" + "=" * 40)
    print("Parsed Configuration")
    print("=" * 40)

    config = create_class_from_dict(AppConfig, config_dict)

    print(f"\nApp: {config.app_name} v{config.version}")
    print(f"Debug: {config.debug}")

    print(f"\nDatabase:")
    print(f"  Host: {config.database.host}")
    print(f"  Port: {config.database.port}")
    print(f"  Name: {config.database.name}")

    print(f"\nStorage: {type(config.storage).__name__}")
    print(f"  Type: {config.storage.get_type().value}")
    if isinstance(config.storage, S3StorageConfig):
        print(f"  Bucket: {config.storage.bucket}")
        print(f"  Region: {config.storage.region}")
    elif isinstance(config.storage, LocalStorageConfig):
        print(f"  Path: {config.storage.path}")

    # Convert back to dict (for serialization)
    print("\n" + "=" * 40)
    print("Serialized back to dict:")
    print("=" * 40)
    output_dict = dataclass_to_dict(config)
    import json

    print(json.dumps(output_dict, indent=2))


if __name__ == "__main__":
    main()
