"""Flat dataclass creation for easy CLI and file-based configuration.

This package provides tools for flattening nested dataclass structures to enable:
- Easy command-line argument parsing
- Configuration file loading (YAML/JSON)
- Polymorphic configuration support
- Automatic reconstruction of original nested structures

Main exports:
- create_flat_dataclass: Main API for creating flattened dataclasses
- explode_dict: Utility for expanding configuration dictionaries
"""

from vidhi.flat_dataclass.core import create_flat_dataclass
from vidhi.flat_dataclass.explosion import explode_dict
from vidhi.flat_dataclass.reconstruction import get_config_class_by_type_name

__all__ = [
    "create_flat_dataclass",
    "explode_dict",
    "get_config_class_by_type_name",
]
