"""Core API for flat dataclass creation.

This module provides the main public API for creating flattened dataclasses
from nested configuration dataclasses.
"""

from __future__ import annotations

from typing import Any, Optional, Type

from vidhi.flat_dataclass.cli import create_from_cli_args
from vidhi.flat_dataclass.reconstruction import reconstruct_original_dataclass
from vidhi.flat_dataclass.state import (
    _create_flat_class_type,
    _initialize_dataclass_state,
    _process_single_dataclass,
)
from vidhi.utils import to_snake_case


def create_flat_dataclass(input_dataclass: Type[Any]) -> Type[Any]:
    """Create a flattened dataclass from a nested configuration dataclass.

    This function recursively processes a dataclass and its nested dataclasses,
    creating a single flat dataclass where nested fields are prefixed with their
    parent's name. This transformation enables:
    - Easy CLI argument generation (no nested structures in argparse)
    - Simple YAML/JSON file loading and saving
    - Support for polymorphic configurations
    - Configuration validation and type checking

    The returned flat dataclass includes:
    - All fields from nested structures with prefixed names (e.g., `database_host`)
    - Metadata for reconstruction (`dataclass_args`, `base_poly_children`, etc.)
    - Helper methods: `create_from_cli_args()` and `reconstruct_original_dataclass()`

    Args:
        input_dataclass: The root dataclass to flatten. Must be a dataclass type
            decorated with @dataclass or @frozen_dataclass.

    Returns:
        A new dataclass type with all nested fields flattened. The returned class
        has additional attributes and methods for CLI parsing and reconstruction.

    Raises:
        ValueError: If polymorphic fields lack required defaults

    Example:
        >>> @frozen_dataclass
        >>> class DatabaseConfig:
        >>>     host: str = "localhost"
        >>>     port: int = 5432
        >>>
        >>> @frozen_dataclass
        >>> class AppConfig:
        >>>     name: str
        >>>     database: DatabaseConfig
        >>>
        >>> FlatConfig = create_flat_dataclass(AppConfig)
        >>> # FlatConfig has fields: name, database_host, database_port
        >>>
        >>> # Use from CLI:
        >>> configs = FlatConfig.create_from_cli_args()
        >>> app = configs[0].reconstruct_original_dataclass()
        >>>
        >>> # Or create directly:
        >>> flat = FlatConfig(name="MyApp", database_host="db.local", database_port=5432)
        >>> app = flat.reconstruct_original_dataclass()
    """
    flattening_state = _initialize_dataclass_state()
    _process_single_dataclass(flattening_state, input_dataclass)

    flat_dataclass = _create_flat_class_type(flattening_state)
    flat_dataclass.root_dataclass_name = to_snake_case(input_dataclass.__name__)
    flat_dataclass._original_dataclass = input_dataclass

    # attach helper methods
    flat_dataclass.reconstruct_original_dataclass = reconstruct_original_dataclass
    flat_dataclass.create_from_cli_args = classmethod(create_from_cli_args)

    # Add schema export methods
    def get_schema(cls):
        """Get ConfigSchema for the original dataclass."""
        from vidhi.schema import ConfigSchema

        return ConfigSchema(cls._original_dataclass)

    def export_json_schema(cls, path: str, indent: int = 2):
        """Export JSON Schema for IDE autocomplete."""
        cls.get_schema().export_json_schema(path, indent)

    def export_yaml_schema(cls, path: str):
        """Export YAML documentation."""
        cls.get_schema().export_yaml(path)

    def export_markdown_docs(cls, path: str):
        """Export Markdown documentation."""
        cls.get_schema().export_markdown(path)

    flat_dataclass.get_schema = classmethod(get_schema)
    flat_dataclass.export_json_schema = classmethod(export_json_schema)
    flat_dataclass.export_yaml_schema = classmethod(export_yaml_schema)
    flat_dataclass.export_markdown_docs = classmethod(export_markdown_docs)

    # Add CLI completion methods
    def get_completion_script(cls, command_name: str, shell: str) -> str:
        """Generate shell completion script.

        Args:
            command_name: Name of the CLI command
            shell: Shell type - "bash", "zsh", or "fish"

        Returns:
            Completion script as a string
        """
        from vidhi.cli_completion import generate_completion_script

        return generate_completion_script(cls, command_name, shell)

    def print_completion(cls, command_name: str, shell: str):
        """Print shell completion script to stdout."""
        print(cls.get_completion_script(command_name, shell))

    flat_dataclass.get_completion_script = classmethod(get_completion_script)
    flat_dataclass.print_completion = classmethod(print_completion)

    # Add completion installation method
    def install_completion(cls, command_name: str, shell: Optional[str] = None) -> str:
        """Install shell completion for this CLI.

        Writes the completion script to the appropriate location for the shell.

        Args:
            command_name: Name of the CLI command
            shell: Shell type (bash, zsh, fish). Auto-detected if not provided.

        Returns:
            Path where completion was installed

        Example:
            >>> FlatConfig.install_completion("myapp")
            'Completion installed to ~/.local/share/bash-completion/completions/myapp'
        """
        from vidhi.cli_completion import install_completion as _install

        return _install(cls, command_name, shell)

    flat_dataclass.install_completion = classmethod(install_completion)

    return flat_dataclass
