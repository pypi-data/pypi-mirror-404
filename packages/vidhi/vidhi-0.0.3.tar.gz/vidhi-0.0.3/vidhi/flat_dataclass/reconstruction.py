"""Dataclass reconstruction logic.

This module handles reconstructing the original nested dataclass structure
from a flattened representation. It includes:
- Topological sorting of dependencies
- Instance instantiation in correct order
- Polymorphic type resolution
- Iterable field initialization
"""

from __future__ import annotations

import logging
from collections import defaultdict, deque
from dataclasses import MISSING, fields
from typing import Any, Dict, List

from vidhi.base_poly_config import BasePolyConfig
from vidhi.constants import DICT_KEY_TYPE, FIELD_NAME_SEPARATOR, FIELD_SUFFIX_TYPE
from vidhi.flat_dataclass.state import _get_type_key
from vidhi.utils import get_all_subclasses, is_subclass

logger = logging.getLogger(__name__)


def topological_sort(dataclass_dependencies: Dict[str, List[str]]) -> List[str]:
    """Perform topological sort on dataclass dependencies using Kahn's algorithm.

    Nested dataclasses have dependencies on their children. This function sorts
    them so that child dataclasses are instantiated before their parents during
    reconstruction.

    Args:
        dataclass_dependencies: Mapping from dataclass names to lists of their
            dependency names. For example: {"app_config": ["database", "cache"]}
            means app_config depends on database and cache being instantiated first.

    Returns:
        List of dataclass names in topological order (dependencies before dependents).
        Example: ["database", "cache", "app_config"]

    Raises:
        ValueError: If circular dependencies are detected in the dataclass graph.

    Example:
        >>> deps = {
        >>>     "app": ["database", "cache"],
        >>>     "database": [],
        >>>     "cache": []
        >>> }
        >>> topological_sort(deps)
        ['database', 'cache', 'app']
    """
    in_degree = defaultdict(int)
    for dataclass_name, dependencies in dataclass_dependencies.items():
        for dependency in dependencies:
            in_degree[dependency] += 1

    zero_in_degree_classes = deque(
        [
            dataclass_name
            for dataclass_name in dataclass_dependencies
            if in_degree[dataclass_name] == 0
        ]
    )
    sorted_classes = []

    while zero_in_degree_classes:
        current_class = zero_in_degree_classes.popleft()
        sorted_classes.append(current_class)
        for dependency in dataclass_dependencies[current_class]:
            in_degree[dependency] -= 1
            if in_degree[dependency] == 0:
                zero_in_degree_classes.append(dependency)

    # Detect circular dependencies
    if len(sorted_classes) != len(dataclass_dependencies):
        cyclic_classes = set(dataclass_dependencies.keys()) - set(sorted_classes)
        # Find the actual cycle for a helpful error message
        cycle_description = _find_cycle_path(dataclass_dependencies, cyclic_classes)
        raise ValueError(
            f"Circular dependency detected in dataclass configuration. "
            f"The following classes form a cycle: {cycle_description}. "
            f"Please restructure your dataclasses to remove circular references."
        )

    return sorted_classes


def _find_cycle_path(
    dataclass_dependencies: Dict[str, List[str]], cyclic_classes: set
) -> str:
    """Find and describe a cycle path for error reporting.

    Args:
        dataclass_dependencies: The dependency graph
        cyclic_classes: Set of classes involved in cycles

    Returns:
        A string describing the cycle, e.g., "A -> B -> C -> A"
    """
    if not cyclic_classes:
        return "unknown cycle"

    # Start from any cyclic class and follow dependencies to find a cycle
    start = next(iter(cyclic_classes))
    visited = set()
    path = []
    current = start

    while current not in visited:
        visited.add(current)
        path.append(current)
        # Find next node in cycle
        for dep in dataclass_dependencies.get(current, []):
            if dep in cyclic_classes:
                current = dep
                break
        else:
            break

    # Complete the cycle
    if current in path:
        cycle_start_idx = path.index(current)
        cycle = path[cycle_start_idx:] + [current]
        return " -> ".join(cycle)

    return " -> ".join(path) if path else "unknown cycle"


def reconstruct_original_dataclass(self) -> Any:
    """Reconstruct the original nested dataclass from a flattened representation.

    This method takes a flat dataclass instance (created by create_flat_dataclass)
    and reconstructs the original nested structure by:
    1. Identifying which nested dataclasses were actually provided by the user
    2. Skipping optional nested dataclasses that weren't specified
    3. Building instances in dependency order (children before parents)
    4. Handling polymorphic fields by selecting the correct subclass

    The reconstruction respects:
    - Fields with default None that weren't provided are skipped
    - Polymorphic type selection via `<field>_type` arguments
    - Nested dataclass dependencies

    Returns:
        An instance of the original (nested) dataclass type

    Example:
        >>> @frozen_dataclass
        >>> class DatabaseConfig:
        >>>     host: str = "localhost"
        >>>
        >>> @frozen_dataclass
        >>> class AppConfig:
        >>>     name: str
        >>>     database: DatabaseConfig
        >>>
        >>> FlatConfig = create_flat_dataclass(AppConfig)
        >>> flat = FlatConfig(name="MyApp", database_host="db.example.com")
        >>> original = flat.reconstruct_original_dataclass()
        >>> # Returns: AppConfig(name="MyApp", database=DatabaseConfig(host="db.example.com"))
    """
    # skip all classes with default None and that have not been provided by the user
    classes_to_skip = set()
    for dataclass_name, dependencies in self.dataclass_dependencies.items():
        # did the user provide anything that belongs to this dataclass?
        sub_arg_provided = any(
            k.startswith(f"{dataclass_name}{FIELD_NAME_SEPARATOR}")
            for k in self.provided_args
        )
        # fallback for base poly configs: to specify a poly class, one provides the type
        dataclass_type_arg = dataclass_name + FIELD_SUFFIX_TYPE

        # skip if the field defaults to None and the user did not provide it
        #   – For polymorphic configs: no <dataclass_name><FIELD_SUFFIX_TYPE>
        #   – For regular dataclasses: no sub-field with the <dataclass_name><FIELD_NAME_SEPARATOR> prefix
        if (
            dataclass_name in self.args_with_default_none
            and dataclass_type_arg not in self.provided_args
            and not sub_arg_provided
        ):
            classes_to_skip.add(dataclass_name)
            for dependency in dependencies:
                classes_to_skip.add(dependency)

    filtered_dependencies = {}
    for dataclass_name, dependencies in self.dataclass_dependencies.items():
        if dataclass_name not in classes_to_skip:
            filtered_dependencies[dataclass_name] = [
                dependency
                for dependency in dependencies
                if dependency not in classes_to_skip
            ]

    # list of classes, from the most dependent to the least dependent
    sorted_classes = topological_sort(filtered_dependencies)

    instances = {}

    # iter over classes from least dependent to most
    for current_dataclass_name in reversed(sorted_classes):
        constructor_args = {}
        # instantiate current class fields
        for prefixed_field_name, original_field_name, field_type in self.dataclass_args[
            current_dataclass_name
        ]:
            if is_subclass(field_type, BasePolyConfig):
                # pick the instantiated child that matches the selected type
                config_type = getattr(self, f"{prefixed_field_name}{FIELD_SUFFIX_TYPE}")
                if config_type == "None":
                    constructor_args[original_field_name] = None
                else:
                    type_key = config_type.lower()
                    try:
                        child_node_name = self.base_poly_children_types[
                            prefixed_field_name
                        ][type_key]
                    except KeyError:
                        valid = list(
                            self.base_poly_children_types.get(
                                prefixed_field_name, {}
                            ).keys()
                        )
                        raise ValueError(
                            f"Invalid type '{config_type}' (key: {type_key}) for '{prefixed_field_name}{FIELD_SUFFIX_TYPE}'. Valid types: {valid}"
                        ) from None
                    constructor_args[original_field_name] = instances[child_node_name]
            # child dataclass has already been instantiated, so just assign it
            elif hasattr(field_type, "__dataclass_fields__"):
                # The prefixed_field_name directly maps to the dependency name
                # (e.g., "service_a" field has dependency "service_a")
                dependency_name = prefixed_field_name

                if dependency_name in instances:
                    constructor_args[original_field_name] = instances[dependency_name]
                elif dependency_name in self.dataclass_dependencies.get(
                    current_dataclass_name, []
                ):
                    # Dependency exists but hasn't been instantiated yet - shouldn't happen
                    # with proper topological sort, but handle gracefully
                    if prefixed_field_name in self.args_with_default_none:
                        constructor_args[original_field_name] = None
                    else:
                        raise ValueError(
                            f"Dependency '{dependency_name}' for field '{original_field_name}' "
                            f"in '{current_dataclass_name}' was not instantiated"
                        )
                else:
                    # Not a tracked dependency - check if it's optional
                    if prefixed_field_name in self.args_with_default_none:
                        constructor_args[original_field_name] = None
                    else:
                        raise ValueError(
                            f"Class {current_dataclass_name} has no dependency "
                            f"'{dependency_name}' and field is not optional"
                        )
            # primitive type
            else:
                value = getattr(self, prefixed_field_name)
                if value is not MISSING and callable(value):
                    # to handle default factory values
                    value = value()
                constructor_args[original_field_name] = value

        # Determine which class to instantiate
        # For polymorphic configs, we need to use the selected subclass
        if current_dataclass_name in self.base_poly_children:
            # This is a polymorphic config - get the type selector and instantiate correct subclass
            type_selector_field = f"{current_dataclass_name}{FIELD_SUFFIX_TYPE}"
            selected_type = getattr(self, type_selector_field, None)
            if selected_type and selected_type != "None":
                # Handle enum types (including pybind11 C++ enums with integer values)
                type_key = _get_type_key(selected_type)
                target_class = self.base_poly_children[current_dataclass_name].get(
                    type_key
                )
                if target_class is None:
                    valid = list(self.base_poly_children[current_dataclass_name].keys())
                    raise ValueError(
                        f"Invalid type '{selected_type}' for '{type_selector_field}'. Valid types: {valid}"
                    )

                # Apply variant-specific defaults for fields not explicitly provided
                # This ensures that when switching variants, we use the new variant's defaults
                if (
                    hasattr(self, "poly_variant_defaults")
                    and current_dataclass_name in self.poly_variant_defaults
                ):
                    variant_defaults = self.poly_variant_defaults[
                        current_dataclass_name
                    ]
                    default_type = getattr(self, "poly_default_types", {}).get(
                        current_dataclass_name
                    )

                    # Only apply variant defaults if we switched to a different type
                    if default_type and type_key != default_type:
                        for prefixed_field, variant_vals in variant_defaults.items():
                            # Get original field name from prefixed name
                            orig_name = prefixed_field.split(FIELD_NAME_SEPARATOR)[-1]

                            # Skip nested dataclasses - they are handled by the dependency system
                            # Nested dataclasses have their own entries in dataclass_dependencies
                            if prefixed_field in self.dataclass_dependencies:
                                continue

                            # Only override if field wasn't explicitly provided by user
                            if (
                                prefixed_field not in self.provided_args
                                and type_key in variant_vals
                            ):
                                variant_default = variant_vals[type_key]
                                if variant_default is not MISSING:
                                    if callable(variant_default) and not isinstance(
                                        variant_default, type
                                    ):
                                        constructor_args[orig_name] = variant_default()
                                    else:
                                        constructor_args[orig_name] = variant_default

                # Filter constructor_args to only include fields valid for target_class
                valid_fields = (
                    {f.name for f in fields(target_class)}
                    if hasattr(target_class, "__dataclass_fields__")
                    else set()
                )
                constructor_args = {
                    k: v for k, v in constructor_args.items() if k in valid_fields
                }
            else:
                # Use the base class if no type selected (shouldn't happen normally)
                target_class = self.dataclass_names_to_classes[current_dataclass_name]
        else:
            target_class = self.dataclass_names_to_classes[current_dataclass_name]

        instances[current_dataclass_name] = target_class(**constructor_args)

    return instances[sorted_classes[0]]


def instantiate_from_args(flat_dataclass_type, args_list, provided_args_list):
    """Instantiate a dataclass from a list of args and provided args.

    Args:
        flat_dataclass_type: The flat dataclass type
        args_list: List of argument instances (argparse.Namespace objects)
        provided_args_list: List of sets containing the names of provided arguments

    Returns:
        List of dataclass instances with provided_args set
    """
    dataclass_instances = []
    for index, arg_instance in enumerate(args_list):
        instance = flat_dataclass_type(**vars(arg_instance))
        instance.provided_args = provided_args_list[index]
        dataclass_instances.append(instance)
    return dataclass_instances


def init_iterable_args(loaded_configs, cli_provided_args, list_fields):
    """Initialize iterable args by converting raw values to typed instances.

    This function processes list fields that contain polymorphic configs or
    dataclass instances, converting raw dictionaries to properly typed objects.

    Args:
        loaded_configs: Dictionary mapping file field names to lists of configs
        cli_provided_args: Dictionary of CLI-provided argument names and values
        list_fields: Dictionary mapping field names to their target types

    Returns:
        Tuple of (processed_loaded_configs, processed_cli_args)
    """

    def _init_iterable_args(arg_map, list_fields):
        """Convert raw iterable values to typed instances."""
        return_map = {}
        for arg_name, arg_value in arg_map.items():
            # at this point, an iterable field contains raw values. Can be maps, lists, primitives...
            # we check what value they need to be converted to, i.e. poly configs, dataclasses, primitives, etc
            if arg_name in list_fields:
                return_iterable = []
                target_type = list_fields[arg_name]
                # we assume each raw value is a dict with config values
                if isinstance(target_type, type) and issubclass(
                    target_type, BasePolyConfig
                ):
                    # get all subclasses of the target type
                    subclasses = get_all_subclasses(target_type)
                    for raw_value in arg_value:
                        assert (
                            DICT_KEY_TYPE in raw_value
                        ), f"Each raw value in an iterable of BasePolyConfigs must contain a '{DICT_KEY_TYPE}' key. Obtained '{raw_value}'"
                        is_match = False
                        # linear matching... do we assume there is a registry?
                        for subclass in subclasses:
                            if (
                                subclass.get_type().name.upper()
                                == raw_value[DICT_KEY_TYPE].upper()
                            ):
                                subclass_kwargs = {
                                    k: v
                                    for k, v in raw_value.items()
                                    if k != DICT_KEY_TYPE
                                }
                                return_iterable.append(subclass(**subclass_kwargs))
                                is_match = True
                                break
                        assert (
                            is_match
                        ), f"No class found for type '{raw_value['type']}' in children of {target_type}"
                elif hasattr(target_type, "__dataclass_fields__"):
                    for raw_value in arg_value:
                        return_iterable.append(target_type(**raw_value))
                elif isinstance(target_type, type):
                    for raw_value in arg_value:
                        return_iterable.append(target_type(raw_value))
                else:
                    raise ValueError(f"Unsupported target type: {target_type}")
                return_map[arg_name] = return_iterable
            else:
                return_map[arg_name] = arg_value
        return return_map

    # loaded_configs is a dict of file_field_name -> list of configs
    final_loaded_configs = {}
    for file_field_name, configs in loaded_configs.items():
        tmp_configs = []
        for config in configs:
            tmp_config = _init_iterable_args(config, list_fields)
            tmp_configs.append(tmp_config)
        final_loaded_configs[file_field_name] = tmp_configs

    # cli_provided_args is a dict of arg_name -> value
    final_cli_args = _init_iterable_args(cli_provided_args, list_fields)

    return final_loaded_configs, final_cli_args


def get_config_class_by_type_name(config_class: Any, type_name: str) -> Any:
    """Find a subclass of config_class that matches the given type name.

    Args:
        config_class: The base polymorphic config class
        type_name: The type name to match (case-insensitive)

    Returns:
        The matching subclass

    Raises:
        ValueError: If no matching subclass is found
    """
    for subclass in get_all_subclasses(config_class):
        if subclass.get_type().name.upper() == type_name.upper():
            return subclass

    raise ValueError(f"Config class with name {type_name} not found.")
