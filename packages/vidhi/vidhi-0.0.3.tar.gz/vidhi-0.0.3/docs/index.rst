Vidhi Documentation
====================

**Vidhi** is a configuration management library for Python applications that provides
type-safe, immutable configurations with CLI and YAML support.

.. note::

   Vidhi (विधि) means "method" or "procedure" in Sanskrit.


Key Features
------------

**Type-safe configurations**
    Build on Python dataclasses with full type checking support.

**Immutability**
    Configurations are frozen after creation, preventing accidental modifications.

**Polymorphic configs**
    Define configuration variants with automatic type-based selection.

**CLI integration**
    Auto-generate CLI arguments from your config classes with ``--help`` support.

**YAML/JSON loading**
    Load configurations from files with nested structure support.


Quick Example
-------------

Define a configuration::

    from vidhi import frozen_dataclass, field, parse_cli_args

    @frozen_dataclass
    class TrainingConfig:
        learning_rate: float = field(0.001, help="Learning rate", name="lr")
        batch_size: int = field(32, help="Batch size")
        epochs: int = field(10, help="Number of epochs")

    config = parse_cli_args(TrainingConfig)

Run from command line::

    python train.py --lr 0.01 --batch_size 64 --epochs 20


Documentation
-------------

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   installation
   quickstart

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   user_guide/index
