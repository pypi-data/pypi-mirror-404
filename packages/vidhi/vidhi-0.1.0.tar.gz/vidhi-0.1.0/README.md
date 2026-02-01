# Vidhi

**Vidhi** (विधि, "method" in Sanskrit) is a Python configuration library for building type-safe, immutable configs with CLI and YAML support.

## Features

- **Immutable configs** - Frozen dataclasses prevent accidental modifications
- **CLI generation** - Auto-generate `--help` and argument parsing from config classes
- **Polymorphic configs** - Runtime variant selection with type-safe inheritance
- **Nested configs** - Compose complex configurations from smaller pieces
- **YAML loading** - Load configs from files with `--config config.yaml`
- **IDE autocomplete** - Export JSON Schema for YAML file completion
- **Shell completion** - Tab completion for bash, zsh, and fish

## Installation

```bash
pip install vidhi
```

## Quick Start

### Basic Config

```python
from vidhi import frozen_dataclass, field, parse_cli_args

@frozen_dataclass
class TrainingConfig:
    learning_rate: float = field(0.001, help="Learning rate", name="lr")
    batch_size: int = field(32, help="Batch size")
    epochs: int = field(10, help="Number of epochs")

config = parse_cli_args(TrainingConfig)
```

```bash
python train.py --help
python train.py --lr 0.01 --batch_size 64
python train.py --config config.yaml
```

### Nested Configs

```python
@frozen_dataclass
class DatabaseConfig:
    host: str = "localhost"
    port: int = 5432

@frozen_dataclass
class AppConfig:
    name: str = "app"
    database: DatabaseConfig = field(default_factory=DatabaseConfig)

config = parse_cli_args(AppConfig)
```

```bash
python app.py --database.host db.example.com --database.port 3306
```

### Polymorphic Configs

```python
from enum import Enum
from vidhi import BasePolyConfig, frozen_dataclass, field

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
```

```bash
python app.py --cache_type redis --cache.host redis.example.com
python app.py --cache_type memory --cache.max_size 5000
```

### YAML Loading

```yaml
# config.yaml
cache_type: redis
cache:
  host: redis.example.com
  port: 6379
  ttl: 7200
```

```bash
python app.py --config config.yaml
python app.py --config config.yaml --cache.ttl 3600  # CLI overrides YAML
```

## CLI Features

Every Vidhi config automatically supports:

| Flag | Description |
|------|-------------|
| `--help` | Show help with all options organized by variant |
| `--config FILE` | Load configuration from YAML file |
| `--export-json-schema [FILE]` | Export JSON Schema for IDE autocomplete |
| `--install-shell-completions [SHELL]` | Install tab completion (bash/zsh/fish) |

## API Summary

| Function | Description |
|----------|-------------|
| `@frozen_dataclass` | Decorator for immutable config classes |
| `field(default, help=, name=)` | Field with CLI metadata |
| `parse_cli_args(cls)` | Parse CLI into config |
| `with_cli_overrides(config)` | Override existing config from CLI |
| `load_yaml_config(path)` | Load YAML to dict |
| `create_class_from_dict(cls, dict)` | Create config from dict |
| `dataclass_to_dict(config)` | Serialize config to dict |
| `BasePolyConfig` | Base class for polymorphic configs |

## Documentation

Full documentation: https://project-vajra.github.io/vidhi

See [`examples/`](examples/) for runnable code samples.

## License

Apache License 2.0
