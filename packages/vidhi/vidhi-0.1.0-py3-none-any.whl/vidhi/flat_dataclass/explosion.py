"""Configuration explosion and expansion logic.

This module handles the explosion of configuration dictionaries containing lists
into all possible combinations (cartesian product). It supports:
- Nested dictionaries and lists
- Polymorphic configurations with type resolution
- Prefix application for namespacing
- Combinatorial explosion protection
"""

from __future__ import annotations

from itertools import product
from typing import Any, Dict, List, Type

from vidhi.constants import (
    DEFAULT_MAX_COMBINATIONS,
    DICT_KEY_TYPE,
    FIELD_NAME_SEPARATOR,
    FIELD_SUFFIX_TYPE,
    MSG_COMBINATORIAL_EXPLOSION,
)
from vidhi.types import ConfigDict, ConfigDictList
from vidhi.utils import is_list


def explode_dict(
    flat_dataclass_type: Type[Any],
    config_dict: ConfigDict,
    prefix: str = "",
    *,
    max_combinations: int = DEFAULT_MAX_COMBINATIONS,
) -> ConfigDictList:
    """
    Recursively explode a dictionary containing lists of values into a list of dictionaries
    representing all combinations (cartesian product), with optional prefix applied to keys.

    Args:
        flat_dataclass_type: The flat dataclass type (for resolving polymorphic types)
        config_dict: Dictionary potentially containing lists to explode
        prefix: Prefix to apply to all top-level keys
        max_combinations: Maximum number of combinations allowed before raising ValueError

    Returns:
        List of configuration dictionaries representing all combinations

    Raises:
        ValueError: If the number of combinations exceeds max_combinations

    Example:
        Input: {'a': [1, 2], 'b': [3, 4]}, prefix='test_'
        Output: [{'test_a': 1, 'test_b': 3}, {'test_a': 1, 'test_b': 4},
                 {'test_a': 2, 'test_b': 3}, {'test_a': 2, 'test_b': 4}]

    NOTE:
        In deeply–nested configs with many lists, the number of combinations can grow
        exponentially. This method raises a ``ValueError`` if the number of combinations
        exceeds ``max_combinations``. Pass ``float('inf')`` to disable the limit.
    """

    # for guarding against combinatorial explosion
    combination_counter = [0]  # mutable counter in a closure

    def _increment_counter(n: int):
        """Increment the global combination counter and enforce the max limit."""
        if n == 0:
            return
        combination_counter[0] += n
        if combination_counter[0] > max_combinations:
            raise ValueError(
                MSG_COMBINATORIAL_EXPLOSION.format(
                    count=combination_counter[0], max=max_combinations
                )
            )

    def _resolve_prefix_for_data(
        flat_dataclass_type, current_prefix: str, data: ConfigDict, strict: bool = True
    ) -> str:
        """Resolve the effective prefix for a dictionary possibly representing a BasePolyConfig.

        If the dictionary contains a "type" key, resolve the typed child name from
        `base_poly_children_types` using the stripped `current_prefix`. When `strict`
        is True, raise a ValueError if the type is invalid for the given prefix.
        """
        resolved_prefix = current_prefix
        if DICT_KEY_TYPE in data:
            stripped_prefix = (
                current_prefix[: -len(FIELD_NAME_SEPARATOR)]
                if current_prefix and current_prefix.endswith(FIELD_NAME_SEPARATOR)
                else current_prefix
            )
            # remove a trailing "_type"
            if stripped_prefix.endswith(FIELD_SUFFIX_TYPE):
                stripped_prefix = stripped_prefix[: -len(FIELD_SUFFIX_TYPE)]
            type_key = str(data[DICT_KEY_TYPE]).lower()
            if data[DICT_KEY_TYPE] is None or type_key in {"none", "null", ""}:
                return current_prefix
            typed_child_name = flat_dataclass_type.base_poly_children_types.get(
                stripped_prefix, {}
            ).get(type_key)
            if typed_child_name:
                resolved_prefix = f"{typed_child_name}{FIELD_NAME_SEPARATOR}"
            elif strict:
                valid = list(
                    flat_dataclass_type.base_poly_children_types.get(
                        stripped_prefix, {}
                    ).keys()
                )
                raise ValueError(
                    f"Invalid type '{data['type']}' for '{stripped_prefix}{FIELD_SUFFIX_TYPE}'. Valid types: {valid}"
                )
        return resolved_prefix

    def _categorize_dict_items(
        config_dict: Dict[str, Any], current_prefix: str = ""
    ) -> tuple:
        """Categorize dictionary items into lists, dicts, and primitives."""
        list_keys = []
        list_values = []
        non_list_items = {}
        dict_items = {}

        for key, value in config_dict.items():
            prefixed_key = f"{current_prefix}{key}" if current_prefix else key
            expected_type = getattr(flat_dataclass_type, "__annotations__", {}).get(
                prefixed_key, None
            )
            is_literal_list = expected_type and is_list(expected_type)

            if isinstance(value, list) and len(value) > 0:
                # (only) if the dataclass declares the field as a List[...]
                # we treat the whole list as a single literal value and don't
                # explode it
                if is_literal_list:
                    non_list_items[key] = value
                else:
                    # will explode
                    if isinstance(value[0], dict):
                        # list of config dictionaries
                        list_keys.append(key)
                        list_values.append(value)
                    else:
                        # list of primitive values
                        list_keys.append(key)
                        list_values.append(value)
            elif isinstance(value, dict):
                dict_items[key] = value
            else:
                non_list_items[key] = value

        return list_keys, list_values, non_list_items, dict_items

    def _explode_dict_list(
        dict_list: List[Dict[str, Any]], level: int, current_prefix: str = ""
    ) -> List[Dict[str, Any]]:
        """Explode a list of dictionaries recursively."""
        exploded_configs = []
        for config in dict_list:
            # child will resolve its own prefix types if needed
            exploded = _explode_dict_recursive(config, level + 1, current_prefix)
            exploded_configs.extend(exploded)
        return exploded_configs

    def _generate_dict_combinations(
        dict_items: Dict[str, Dict[str, Any]], level: int, current_prefix: str = ""
    ) -> List[Dict[str, Any]]:
        """Generate all combinations from nested dictionaries."""
        dict_combinations = [{}]

        for key, nested_dict in dict_items.items():
            # Build prefix for nested dictionary - add current key to prefix chain
            nested_prefix = (
                f"{current_prefix}{key}{FIELD_NAME_SEPARATOR}"
                if current_prefix or key
                else f"{key}{FIELD_NAME_SEPARATOR}"
            )
            exploded_nested = _explode_dict_recursive(
                nested_dict, level + 1, nested_prefix
            )
            new_combinations = []

            for base_combo in dict_combinations:
                for nested_combo in exploded_nested:
                    new_combo = base_combo.copy()
                    new_combo[key] = nested_combo
                    new_combinations.append(new_combo)

            dict_combinations = new_combinations

        return dict_combinations

    def _combine_non_list_items(
        non_list_items: Dict[str, Any], dict_combinations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Combine non-list items with dictionary combinations."""
        result = []
        for dict_combo in dict_combinations:
            combined = non_list_items.copy()
            combined.update(dict_combo)
            result.append(combined)
        _increment_counter(len(result))
        return result

    def _generate_all_combinations(
        list_keys: List[str],
        list_values: List[List[Any]],
        non_list_items: Dict[str, Any],
        dict_combinations: List[Dict[str, Any]],
        level: int,
        current_prefix: str = "",
    ) -> List[Dict[str, Any]]:
        """Generate all combinations including list values."""
        # handle list of config dictionaries vs primitives
        processed_list_values = []
        for key, values in zip(list_keys, list_values):
            if values and isinstance(values[0], dict):
                # Build prefix including the key for proper type resolution
                list_item_prefix = f"{current_prefix}{key}{FIELD_NAME_SEPARATOR}"
                # explode each config dict in the list
                processed_list_values.append(
                    _explode_dict_list(values, level, list_item_prefix)
                )
            else:
                # keep primitive values as-is
                processed_list_values.append(values)

        result = []
        for combination in product(*processed_list_values):
            for dict_combo in dict_combinations:
                new_config = non_list_items.copy()
                new_config.update(dict_combo)

                for key, value in zip(list_keys, combination):
                    new_config[key] = value

                result.append(new_config)

        _increment_counter(len(result))
        return result

    def _explode_dict_recursive(
        config_dict: Dict[str, Any], level: int = 0, current_prefix: str = ""
    ) -> List[Dict[str, Any]]:
        """Recursively explode a dictionary into all combinations."""

        # resolve effective prefix (might be typed)
        effective_prefix = _resolve_prefix_for_data(
            flat_dataclass_type,
            current_prefix=current_prefix,
            data=config_dict,
            strict=True,
        )

        list_keys, list_values, non_list_items, dict_items = _categorize_dict_items(
            config_dict, effective_prefix
        )

        # generate combinations from nested dictionaries
        dict_combinations = _generate_dict_combinations(
            dict_items, level, effective_prefix
        )

        # if no lists found, just combine non-list items with dict combinations
        if not list_keys:
            return _combine_non_list_items(non_list_items, dict_combinations)

        # generate all combinations including lists
        return _generate_all_combinations(
            list_keys,
            list_values,
            non_list_items,
            dict_combinations,
            level,
            effective_prefix,
        )

    def _add_prefix_to_dict(
        flat_dataclass_type, config_dict: Dict[str, Any], prefix: str
    ) -> Dict[str, Any]:
        """Add prefix to all keys in a dictionary."""

        def _add_prefix_recursive(
            flat_dataclass_type, data: Dict[str, Any], current_prefix: str = ""
        ) -> Dict[str, Any]:
            result = {}

            # resolve effective typed prefix once per node
            effective_prefix = _resolve_prefix_for_data(
                flat_dataclass_type,
                current_prefix=current_prefix,
                data=data,
                strict=True,
            )

            for key, value in data.items():
                # For the 'type' meta-key itself, use _type suffix (not __type)
                if DICT_KEY_TYPE in data and key == DICT_KEY_TYPE:
                    # Strip trailing separator from prefix and add _type suffix
                    stripped = current_prefix.rstrip(FIELD_NAME_SEPARATOR)
                    prefixed_key = f"{stripped}{FIELD_SUFFIX_TYPE}"
                else:
                    prefixed_key = f"{effective_prefix}{key}"

                if isinstance(value, dict):
                    # for nested dicts, recursively process with composed prefix
                    flattened = _add_prefix_recursive(
                        flat_dataclass_type,
                        value,
                        f"{prefixed_key}{FIELD_NAME_SEPARATOR}",
                    )
                    result.update(flattened)
                else:
                    # leaf value - add it with the full prefix
                    result[prefixed_key] = value

            return result

        return _add_prefix_recursive(flat_dataclass_type, config_dict, prefix)

    def _handle_list_config(
        config_with_list: Dict[str, Any], prefix: str
    ) -> List[Dict[str, Any]]:
        """Handle special case where config has a '_list' key."""
        list_data = config_with_list["_list"]
        if not isinstance(list_data, list):
            return []

        all_exploded = []
        for item in list_data:
            if isinstance(item, dict):
                exploded = _explode_dict_recursive(item, current_prefix=prefix)
                all_exploded.extend(exploded)
            else:
                # non-dict items are wrapped
                all_exploded.append({"_value": item})

        prefixed = [
            _add_prefix_to_dict(flat_dataclass_type, cfg, prefix)
            for cfg in all_exploded
        ]
        _increment_counter(len(prefixed))
        return prefixed

    # handle special case where config has a '_list' key (from load_yaml_config)
    if (
        isinstance(config_dict, dict)
        and len(config_dict) == 1
        and "_list" in config_dict
    ):
        return _handle_list_config(config_dict, prefix)

    # standard case: explode the config and add prefixes
    exploded_configs = _explode_dict_recursive(config_dict, current_prefix=prefix)
    _increment_counter(len(exploded_configs))
    return [
        _add_prefix_to_dict(flat_dataclass_type, cfg, prefix)
        for cfg in exploded_configs
    ]


def expand_dict(config_dict: ConfigDict, prefix: str = "") -> ConfigDict:
    """Expand a nested dictionary into a flat dictionary with prefixed keys.

    This is a simpler version of explode_dict that doesn't handle lists or
    generate combinations. It simply flattens nested dictionaries by prefixing keys.

    Args:
        config_dict: The nested dictionary to expand
        prefix: Prefix to apply to all keys

    Returns:
        A flat dictionary with all keys prefixed

    Example:
        >>> expand_dict({'a': {'b': 1, 'c': 2}}, 'test_')
        {'test_a_b': 1, 'test_a_c': 2}
    """
    result = {}
    for key, value in config_dict.items():
        prefixed_key = f"{prefix}{key}" if prefix else key
        if isinstance(value, dict):
            # Recursively expand nested dictionaries
            nested = expand_dict(value, f"{prefixed_key}{FIELD_NAME_SEPARATOR}")
            result.update(nested)
        else:
            result[prefixed_key] = value
    return result
