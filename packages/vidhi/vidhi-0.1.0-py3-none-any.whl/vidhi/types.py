"""Type aliases for the Vidhi configuration library.

This module defines type aliases for complex types used throughout the codebase
to improve readability and maintainability.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Set, Tuple, Type, Union

# =============================================================================
# Configuration Types
# =============================================================================

# A dictionary representing a configuration (key-value pairs)
ConfigDict = Dict[str, Any]

# A list of configuration dictionaries
ConfigDictList = List[ConfigDict]


# =============================================================================
# Metadata Types
# =============================================================================

# Metadata for a single field (help text, argname, etc.)
FieldMetadata = Dict[str, Any]

# Mapping from field names to their metadata
MetadataMapping = Dict[str, FieldMetadata]

# Mapping from dataclass names to their classes
ClassMapping = Dict[str, Type[Any]]


# =============================================================================
# CLI Types
# =============================================================================

# Mapping from argument names to field names
ArgNameMapping = Dict[str, str]

# Dictionary of default values for fields
DefaultValues = Dict[str, Any]


# =============================================================================
# Flattening State Types
# =============================================================================

# A field definition: (field_name, field_type) or (field_name, field_type, default_value)
FieldDef = Union[Tuple[str, Type[Any]], Tuple[str, Type[Any], Any]]

# List of field definitions
FieldDefList = List[FieldDef]

# Mapping from dataclass names to their dependencies
DependencyMapping = Dict[str, List[str]]

# Mapping from dataclass names to their field definitions
DataclassArgsMapping = Dict[str, List[Tuple[str, str, Type[Any]]]]

# Mapping from polymorphic field names to their children
PolyChildrenMapping = Dict[str, Dict[str, Type[Any]]]

# Mapping from polymorphic field names to type -> child name
PolyChildrenTypeMapping = Dict[str, Dict[str, str]]


# =============================================================================
# Utility Types
# =============================================================================

# A set of field names
FieldNameSet = Set[str]

# A factory function that creates default values
DefaultFactory = Callable[[], Any]
