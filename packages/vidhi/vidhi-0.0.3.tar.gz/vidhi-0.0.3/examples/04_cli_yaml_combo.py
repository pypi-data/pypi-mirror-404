#!/usr/bin/env python
"""Combining CLI arguments with YAML config files.

This example demonstrates:
- Using with_cli_overrides() to override programmatic defaults
- Loading base config from YAML and overriding with CLI args
- Priority order: CLI args > YAML file > code defaults

Run with:
    python 04_cli_yaml_combo.py --help
    python 04_cli_yaml_combo.py
    python 04_cli_yaml_combo.py --batch_size 128
    python 04_cli_yaml_combo.py --config config.yaml
    python 04_cli_yaml_combo.py --config config.yaml --batch_size 256

This is useful when you have:
1. Sensible defaults in code
2. Environment-specific settings in YAML files
3. Quick overrides via CLI for experimentation

Example config.yaml:

    model_name: "efficientnet"
    batch_size: 64
    learning_rate: 0.0001

Example --help output:

    usage: 04_cli_yaml_combo.py [options]

    Built-in Options:
      -h, --help            show this help message and exit
      --config <path>       load configuration from YAML file

    Options:
      --model_name <str> [resnet50]
          Model architecture
      --batch_size <int> [32]
          Training batch size
      --learning_rate, --lr <float> [0.001]
          Learning rate
      --epochs <int> [10]
          Number of training epochs
      --device <str> [cuda]
          Device to train on
"""

from dataclasses import field
from pathlib import Path

from vidhi import frozen_dataclass, with_cli_overrides


@frozen_dataclass
class TrainingConfig:
    """Training configuration with sensible defaults."""

    model_name: str = field(default="resnet50", metadata={"help": "Model architecture"})
    batch_size: int = field(default=32, metadata={"help": "Training batch size"})
    learning_rate: float = field(
        default=0.001,
        metadata={"help": "Learning rate", "aliases": ["lr"]},
    )
    epochs: int = field(default=10, metadata={"help": "Number of training epochs"})
    device: str = field(default="cuda", metadata={"help": "Device to train on"})


def create_default_config() -> TrainingConfig:
    """Create config with programmatic defaults.

    This function can contain logic to set defaults based on
    environment, hardware detection, etc.
    """
    return TrainingConfig(
        model_name="resnet50",
        batch_size=32,
        learning_rate=0.001,
        epochs=10,
        device="cuda",
    )


# Sample YAML for demonstration
SAMPLE_YAML = """\
# Environment-specific overrides
model_name: "efficientnet"
batch_size: 64
learning_rate: 0.0001
"""


def main():
    # Create a sample config file for demonstration
    sample_config_path = Path("/tmp/vidhi_training_config.yaml")
    sample_config_path.write_text(SAMPLE_YAML)
    print(f"Sample config file created: {sample_config_path}")
    print(f"Contents:\n{SAMPLE_YAML}")

    # Method 1: Start with programmatic defaults, allow CLI overrides
    # Priority: CLI args > code defaults
    print("=" * 60)
    print("Method 1: Programmatic defaults + CLI overrides")
    print("=" * 60)

    base_config = create_default_config()
    config = with_cli_overrides(base_config)

    print(f"\nFinal config:")
    print(f"  Model:         {config.model_name}")
    print(f"  Batch Size:    {config.batch_size}")
    print(f"  Learning Rate: {config.learning_rate}")
    print(f"  Epochs:        {config.epochs}")
    print(f"  Device:        {config.device}")

    # Usage tips
    print("\n" + "=" * 60)
    print("Usage Examples")
    print("=" * 60)
    print("""
# Use defaults from code:
python 04_cli_yaml_combo.py

# Override specific values via CLI:
python 04_cli_yaml_combo.py --batch_size 128 --lr 0.01

# Load from YAML file:
python 04_cli_yaml_combo.py --config /tmp/vidhi_training_config.yaml

# YAML + CLI overrides (CLI wins):
python 04_cli_yaml_combo.py --config /tmp/vidhi_training_config.yaml --batch_size 256
""")


if __name__ == "__main__":
    main()
