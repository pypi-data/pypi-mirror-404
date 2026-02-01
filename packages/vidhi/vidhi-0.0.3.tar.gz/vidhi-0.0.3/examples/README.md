# Vidhi Examples

Runnable examples demonstrating Vidhi's configuration management features.

## Examples

### 01_basic_usage.py
Basic frozen dataclasses and CLI argument parsing.

```bash
python 01_basic_usage.py --help
python 01_basic_usage.py --lr 0.01 --epochs 20
```

### 02_polymorphic_cli.py
Polymorphic configurations with variant-specific CLI arguments.

```bash
python 02_polymorphic_cli.py --help
python 02_polymorphic_cli.py --scheduler_type priority --scheduler.levels 10
python 02_polymorphic_cli.py --scheduler_type round_robin --scheduler.quantum_ms 50
```

### 03_yaml_config.py
Loading configurations from YAML files with nested and polymorphic types.

```bash
python 03_yaml_config.py
python 03_yaml_config.py config.yaml
```

## Running Examples

From the repository root:

```bash
cd examples
python 01_basic_usage.py --help
```

Or directly:

```bash
python examples/02_polymorphic_cli.py --scheduler_type priority
```
