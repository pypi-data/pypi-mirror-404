Installation
============

Requirements
------------

- Python 3.12+
- PyYAML (for YAML config loading)


Install from PyPI
-----------------

.. code-block:: bash

    pip install vidhi


Install from Source
-------------------

.. code-block:: bash

    git clone https://github.com/project-vajra/vidhi.git
    cd vidhi
    pip install -e .


Development Installation
------------------------

For development with testing and linting tools:

.. code-block:: bash

    pip install -e ".[dev]"


Verify Installation
-------------------

.. code-block:: python

    from vidhi import frozen_dataclass, parse_cli_args

    @frozen_dataclass
    class Config:
        name: str = "test"

    print("Vidhi installed successfully!")
