#!/usr/bin/env python
"""Basic Vidhi usage: frozen dataclasses and CLI parsing.

This example demonstrates:
- Creating immutable configurations with @frozen_dataclass
- Using the field() helper for CLI metadata (help text, aliases)
- Parsing command-line arguments with parse_cli_args()
- Boolean arguments with explicit true/false values

Run with:
    python 01_basic_usage.py --help
    python 01_basic_usage.py
    python 01_basic_usage.py --lr 0.01 --batch_size 64
    python 01_basic_usage.py --pretrained false --epochs 20

Example --help output:

    usage: 01_basic_usage.py [options]

    Configuration for model training.

    Built-in Options:
      -h, --help            show this help message and exit
      --config <path>       load configuration from YAML file

    Options:
      --model_name <str> [resnet50]
          Model architecture name
      --pretrained {true,false} [True]
          Use pretrained weights
      --lr <float> [0.001]
          Learning rate
      --batch_size <int> [32]
          Batch size
      --epochs <int> [10]
          Number of epochs
      --data_dir <str> [./data]
          Path to training data
      --num_workers <int> [4]
          Data loading workers
"""

from vidhi import field, frozen_dataclass, parse_cli_args


@frozen_dataclass
class TrainingConfig:
    """Configuration for model training."""

    # Model settings
    model_name: str = field("resnet50", help="Model architecture name")
    pretrained: bool = field(True, help="Use pretrained weights")

    # Training hyperparameters - note the 'name' parameter creates a short alias
    learning_rate: float = field(0.001, help="Learning rate", name="lr")
    batch_size: int = field(32, help="Batch size")
    epochs: int = field(10, help="Number of epochs")

    # Data settings
    data_dir: str = field("./data", help="Path to training data")
    num_workers: int = field(4, help="Data loading workers")


def main():
    # Parse CLI arguments into a typed config object
    config = parse_cli_args(TrainingConfig)

    print("Training Configuration")
    print("=" * 40)
    print(f"Model:         {config.model_name}")
    print(f"Pretrained:    {config.pretrained}")
    print(f"Learning Rate: {config.learning_rate}")
    print(f"Batch Size:    {config.batch_size}")
    print(f"Epochs:        {config.epochs}")
    print(f"Data Dir:      {config.data_dir}")
    print(f"Workers:       {config.num_workers}")

    # Configs are immutable - this prevents accidental modifications
    try:
        config.epochs = 20
    except AttributeError:
        print("\nConfig is immutable (as expected)")


if __name__ == "__main__":
    main()
