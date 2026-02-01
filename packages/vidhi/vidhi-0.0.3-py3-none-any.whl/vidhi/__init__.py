"""Vidhi - Configuration management library for Python.

Public API:
    - frozen_dataclass: Decorator for creating immutable config classes
    - field: Enhanced dataclass field with CLI options
    - parse_cli_args: Parse CLI arguments into a single config
    - parse_cli_sweep: Parse CLI arguments into multiple configs (sweeps)
    - with_cli_overrides: Override a programmatic config from CLI
    - BasePolyConfig: Base class for polymorphic configurations
    - load_yaml_config: Load configuration from YAML files
    - create_class_from_dict: Instantiate config from dictionary
"""

from vidhi.base_poly_config import BasePolyConfig
from vidhi.cli import field, parse_cli_args, parse_cli_sweep, with_cli_overrides

# Keep for backward compatibility, but prefer parse_cli_args
from vidhi.flat_dataclass import create_flat_dataclass as _create_flat_dataclass
from vidhi.frozen_dataclass import FrozenDataclassMixin, frozen_dataclass
from vidhi.utils import (
    create_class_from_dict,
    dataclass_to_dict,
    dataclass_to_json,
    dataclass_to_yaml,
    load_yaml_config,
)

__all__ = [
    # Core API
    "frozen_dataclass",
    "FrozenDataclassMixin",
    "field",
    "parse_cli_args",
    "parse_cli_sweep",
    "with_cli_overrides",
    # Polymorphic configs
    "BasePolyConfig",
    # YAML/dict utilities
    "load_yaml_config",
    "create_class_from_dict",
    "dataclass_to_dict",
    "dataclass_to_json",
    "dataclass_to_yaml",
]
try:
    from vidhi._version import version as __version__
except ImportError:
    __version__ = "0.0.0.dev0"

__author__ = "Vajra Team"
__email__ = "team@project-vajra.org"
