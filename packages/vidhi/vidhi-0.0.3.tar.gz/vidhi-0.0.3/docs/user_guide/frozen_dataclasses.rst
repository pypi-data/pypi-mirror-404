Frozen Dataclasses
==================

The ``@frozen_dataclass`` decorator creates immutable configuration classes.

Basic Usage
-----------

::

    from vidhi import frozen_dataclass

    @frozen_dataclass
    class Config:
        name: str
        value: int = 10

    config = Config(name="test")
    config.value = 20  # Raises AttributeError

Post-Initialization
-------------------

Modify attributes during ``__post_init__`` using ``object.__setattr__()``::

    @frozen_dataclass
    class Config:
        value: int = 10
        doubled: int = None

        def __post_init__(self):
            object.__setattr__(self, "doubled", self.value * 2)


Field Helper
------------

The ``field()`` function adds CLI metadata to fields::

    from vidhi import frozen_dataclass, field

    @frozen_dataclass
    class Config:
        learning_rate: float = field(
            0.001,
            help="Learning rate for optimizer",
            name="lr"  # CLI alias: --lr instead of --learning_rate
        )

Parameters:

- ``default``: Default value
- ``help``: Help text for ``--help`` output
- ``name``: Custom CLI argument name
