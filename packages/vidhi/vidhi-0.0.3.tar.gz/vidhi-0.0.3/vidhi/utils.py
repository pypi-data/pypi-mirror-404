from __future__ import annotations

import json
import logging
import os
from copy import deepcopy
from dataclasses import fields, is_dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Type, Union, get_args, get_origin

import yaml

from vidhi.constants import (
    DICT_KEY_NAME,
    DICT_KEY_TYPE,
    MSG_INVALID_TYPE_VALUE,
    MSG_UNKNOWN_ARGUMENTS,
)
from vidhi.types import ConfigDict

# Primitive types that don't require special handling
PRIMITIVE_TYPES = {int, str, float, bool, type(None)}

logger = logging.getLogger(__name__)


def get_all_subclasses(cls):
    subclasses = cls.__subclasses__()
    return subclasses + [g for s in subclasses for g in get_all_subclasses(s)]


def is_primitive_type(field_type: type) -> bool:
    """Check if the given type is a primitive type.

    Args:
        field_type: The type to check

    Returns:
        True if the type is a primitive (int, str, float, bool, or None)
    """
    return field_type in PRIMITIVE_TYPES


def is_generic_composed_of_primitives(field_type: type) -> bool:
    origin = get_origin(field_type)
    if origin in {list, dict, tuple, Union}:
        # Check all arguments of the generic type
        args = get_args(field_type)
        return all(is_composed_of_primitives(arg) for arg in args)
    return False


def is_composed_of_primitives(field_type: type) -> bool:
    # Check if the type is a primitive type
    if is_primitive_type(field_type):
        return True

    # Check if the type is a generic type composed of primitives
    if is_generic_composed_of_primitives(field_type):
        return True

    return False


def to_snake_case(name: str) -> str:
    return "".join(["_" + i.lower() if i.isupper() else i for i in name]).lstrip("_")


def is_optional(field_type: Any) -> bool:
    return get_origin(field_type) is Union and type(None) in get_args(field_type)


def is_list(field_type: Any) -> bool:
    # Check if the field type is a List
    return get_origin(field_type) is list


def is_dict(field_type: Any) -> bool:
    # Check if the field type is a Dict
    return get_origin(field_type) is dict


def is_bool(field_type: Any) -> bool:
    return field_type is bool


def get_inner_type(field_type: type) -> type:
    return next(t for t in get_args(field_type) if t is not type(None))


def is_subclass(cls, parent: type) -> bool:
    return hasattr(cls, "__bases__") and parent in cls.__bases__


def dataclass_to_dict(obj: Any) -> Any:
    """Recursively convert a dataclass to a JSON-serializable dictionary.

    This function converts dataclass instances (and any nested structures) into
    dictionaries composed only of primitives, lists, and dicts. This is useful
    for:
    - Saving configurations to YAML/JSON files
    - Serializing for APIs
    - Round-trip testing (dataclass → dict → dataclass)

    Special handling:
    - Dataclasses: Converted to dictionaries recursively
    - Lists/tuples: Elements converted recursively
    - Enums: Converted to their value (or name if value isn't JSON-serializable)
    - Polymorphic configs: Adds a "type" key with the enum name
    - Primitives: Returned as-is

    Args:
        obj: The object to convert. Can be a dataclass, list, dict, enum, or primitive.

    Returns:
        A JSON-serializable structure (dict, list, or primitive). Dataclasses
        become dicts with field names as keys.

    Example:
        >>> @frozen_dataclass
        >>> class DatabaseConfig:
        >>>     host: str
        >>>     port: int = 5432
        >>>
        >>> db = DatabaseConfig(host="localhost")
        >>> dataclass_to_dict(db)
        {'host': 'localhost', 'port': 5432}
        >>>
        >>> # Polymorphic example:
        >>> storage = S3Storage(bucket="my-bucket")
        >>> dataclass_to_dict(storage)
        {'bucket': 'my-bucket', 'type': 'S3'}  # 'type' added automatically
    """
    # lists and tuples
    if isinstance(obj, list):
        return [dataclass_to_dict(item) for item in obj]

    # dicts
    if isinstance(obj, dict):
        return {k: dataclass_to_dict(v) for k, v in obj.items()}

    # enums
    if isinstance(obj, Enum):
        return (
            obj.value
            if isinstance(obj.value, (str, int, float, bool, type(None)))
            else obj.name
        )

    # dataclasses
    if is_dataclass(obj):
        data = {}
        for field in fields(obj):
            value = getattr(obj, field.name)
            data[field.name] = dataclass_to_dict(value)

        for key, value in obj.__dict__.items():
            # Exclude private/internal attributes and already-processed fields
            if key not in data and not key.startswith("_"):
                data[key] = dataclass_to_dict(value)

        if hasattr(obj, "get_type") and callable(getattr(obj, "get_type", None)):
            type_val = obj.get_type()  # type: ignore[attr-defined]
            # Store enum value for polymorphic types (e.g., "lru" not "LRU")
            # This matches typical YAML/JSON config conventions
            if hasattr(type_val, "value") and isinstance(type_val.value, str):
                data[DICT_KEY_TYPE] = type_val.value
            elif hasattr(type_val, "name"):
                data[DICT_KEY_TYPE] = type_val.name.lower()
            else:
                data[DICT_KEY_TYPE] = str(type_val)
        elif hasattr(obj, "get_name") and callable(getattr(obj, "get_name", None)):
            data[DICT_KEY_NAME] = obj.get_name()  # type: ignore[attr-defined]
        return data

    # all other values (primitives and non-serializable types like torch.dtype)
    return obj


def _serialize_for_output(obj: Any) -> Any:
    """Convert a value to a JSON/YAML serializable form.

    This is used by to_json() and to_yaml() to handle non-serializable types.
    """
    if isinstance(obj, dict):
        return {k: _serialize_for_output(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_serialize_for_output(item) for item in obj]
    if isinstance(obj, Enum):
        return (
            obj.value
            if isinstance(obj.value, (str, int, float, bool, type(None)))
            else obj.name
        )
    if isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    # Non-serializable types (torch.dtype, numpy types, etc.) -> string
    return str(obj)


def dataclass_to_json(obj: Any) -> str:
    """Convert a dataclass to a JSON string.

    Handles non-serializable types by converting them to strings.
    """
    import json

    d = dataclass_to_dict(obj)
    return json.dumps(_serialize_for_output(d), indent=2)


def dataclass_to_yaml(obj: Any) -> str:
    """Convert a dataclass to a YAML string.

    Handles non-serializable types by converting them to strings.
    """
    import yaml

    d = dataclass_to_dict(obj)
    return yaml.dump(_serialize_for_output(d), default_flow_style=False)


def expand_dict(d: Dict) -> List[Dict]:
    """
    Recursively expand a configuration dictionary that may contain lists into
    a list of dictionaries representing every combination in the Cartesian
    product of the list elements. Lists may appear at any depth of the
    configuration tree. Nested dictionaries are handled recursively.
    """
    variants: List[Dict] = [dict()]

    for key, value in d.items():
        # Figure out all the possible values for this key
        if isinstance(value, list):
            # Each element in the list may be a dictionary that itself needs
            # expansion. Scalars are taken as-is.
            possible_values = []
            for item in value:
                if isinstance(item, dict):
                    possible_values.extend(expand_dict(item))
                else:
                    possible_values.append(item)
        elif isinstance(value, dict):
            possible_values = expand_dict(value)
        else:
            possible_values = [value]

        # Compose current variants with the new possibilities (cartesian product)
        new_variants: list[dict] = []
        for base in variants:
            for option in possible_values:
                v_copy = deepcopy(base)
                v_copy[key] = option
                new_variants.append(v_copy)
        variants = new_variants

    return variants


def _strip_optional(t: Any) -> Any:
    """Return the inner type if *t* is Optional[T], otherwise return *t* unchanged."""
    if get_origin(t) is Union:
        non_none = [a for a in get_args(t) if a is not type(None)]  # noqa: E721
        if len(non_none) == 1:
            return non_none[0]
    return t


def _issubclass_safe(cls: Any, parent: type) -> bool:
    """Safe variant of issubclass that returns False for non-class *cls*."""
    try:
        return isinstance(cls, type) and issubclass(cls, parent)
    except TypeError:
        return False


def _process_list_field(
    field_type: type, raw_value: list, BasePolyConfig: type
) -> list:
    """Process a list field, recursively handling dataclass items.

    Args:
        field_type: The type of the list (e.g., List[SomeDataclass])
        raw_value: The raw list value from config
        BasePolyConfig: The BasePolyConfig class for type checking

    Returns:
        Processed list with dataclass items instantiated
    """
    inner_type = _strip_optional(get_args(field_type)[0])
    if is_dataclass(inner_type) or _issubclass_safe(inner_type, BasePolyConfig):
        assert isinstance(inner_type, type), f"Expected type, got {type(inner_type)}"
        return [
            create_class_from_dict(inner_type, item) if isinstance(item, dict) else item
            for item in raw_value
        ]
    return raw_value


def _process_dict_field(
    field_type: type, raw_value: dict, BasePolyConfig: type
) -> dict:
    """Process a dict field, recursively handling dataclass values.

    Args:
        field_type: The type of the dict (e.g., Dict[str, SomeDataclass])
        raw_value: The raw dict value from config
        BasePolyConfig: The BasePolyConfig class for type checking

    Returns:
        Processed dict with dataclass values instantiated
    """
    key_type, val_type = get_args(field_type)
    if is_dataclass(val_type) or _issubclass_safe(val_type, BasePolyConfig):
        assert isinstance(val_type, type), f"Expected type, got {type(val_type)}"
        return {
            k: create_class_from_dict(val_type, v) if isinstance(v, dict) else v
            for k, v in raw_value.items()
        }
    return raw_value


def _process_polymorphic_field(field_type: type, raw_value: Any) -> Any:
    """Process a polymorphic config field.

    Args:
        field_type: The base polymorphic type
        raw_value: The raw value (dict with 'type' key, or type discriminator)

    Returns:
        Instantiated subclass based on the type discriminator
    """
    if isinstance(raw_value, dict):
        type_val = raw_value.get(DICT_KEY_TYPE)
        if type_val is not None:
            subclass = _match_subclass_by_type(field_type, type_val)
            sub_dict = {k: v for k, v in raw_value.items() if k != DICT_KEY_TYPE}
        else:
            subclass = field_type
            sub_dict = raw_value
        return create_class_from_dict(subclass, sub_dict)
    else:
        # raw_value directly specifies the type discriminator
        subclass = _match_subclass_by_type(field_type, raw_value)
        return subclass()


def _match_subclass_by_type(parent: type, type_val: Any) -> type:
    """Return the subclass of *parent* whose ``get_type()`` equals *type_val*.

    The comparison is performed with a bit of leniency: we allow Enum values,
    strings matching Enum names (case-insensitive) or the string or repr of the
    Enum value itself.

    Args:
        parent: The parent class to search subclasses of
        type_val: The type value to match

    Returns:
        The matching subclass

    Raises:
        ValueError: If no subclass matches the type value
    """
    subclasses = get_all_subclasses(parent)
    valid_types = []

    for subclass in subclasses:
        subtype = subclass.get_type()
        type_name = subtype.name if hasattr(subtype, "name") else str(subtype)
        valid_types.append(type_name.lower())

        if subtype == type_val:
            return subclass
        # Handle Enum → str comparisons in either direction
        if hasattr(subtype, "name") and isinstance(type_val, str):
            # Match by enum name (e.g., "COST_AWARE_EXP_DECAY")
            if subtype.name.lower() == type_val.lower():
                return subclass
            # Match by enum value (e.g., "cost_aware_exp_decay")
            if hasattr(subtype, "value") and isinstance(subtype.value, str):
                if subtype.value.lower() == type_val.lower():
                    return subclass
        if isinstance(subtype, str) and isinstance(type_val, str):
            if subtype.lower() == type_val.lower():
                return subclass

    raise ValueError(
        MSG_INVALID_TYPE_VALUE.format(
            parent=parent.__name__,
            type_val=type_val,
            valid_types=", ".join(sorted(valid_types)) or "none",
        )
    )


def create_class_from_dict(cls: Type[Any], config_dict: Optional[ConfigDict]) -> Any:
    """Recursively instantiate a dataclass from a dictionary.

    This function converts a dictionary (typically loaded from YAML/JSON) into
    a dataclass instance, handling:
    - Primitive types (int, str, float, bool) - used directly
    - Nested dataclasses - instantiated recursively
    - Lists and dicts containing dataclasses - processed recursively
    - Polymorphic configs - subclass selected via "type" key
    - Optional fields - can be missing from the dictionary

    Args:
        cls: The dataclass type to instantiate
        config_dict: Dictionary containing configuration values. Can be None,
            in which case None is returned.

    Returns:
        An instance of cls populated with values from config_dict.
        Returns config_dict directly if cls is not a dataclass.

    Raises:
        TypeError: If config_dict contains keys that don't correspond to
            dataclass fields (except for BasePolyConfig subclasses)
        ValueError: If a polymorphic "type" value doesn't match any subclass

    Example:
        >>> @frozen_dataclass
        >>> class DatabaseConfig:
        >>>     host: str
        >>>     port: int = 5432
        >>>
        >>> config_dict = {"host": "localhost", "port": 3306}
        >>> db = create_class_from_dict(DatabaseConfig, config_dict)
        >>> # Returns: DatabaseConfig(host="localhost", port=3306)
        >>>
        >>> # Polymorphic example:
        >>> config_dict = {"type": "s3", "bucket": "my-bucket"}
        >>> storage = create_class_from_dict(BaseStorage, config_dict)
        >>> # Returns: S3Storage(bucket="my-bucket")
    """
    from vidhi.base_poly_config import BasePolyConfig

    # Fast path: if cls is not a dataclass return config_dict as is
    if (
        not is_dataclass(cls)
        or config_dict is None
        or not isinstance(config_dict, dict)
    ):
        logger.debug(
            "create_class_from_dict fast path for %s with value %s", cls, config_dict
        )
        # Caller will assign directly.
        return config_dict

    # Handle polymorphic dispatch at top level if cls is a BasePolyConfig
    # and config_dict has a "type" key
    if _issubclass_safe(cls, BasePolyConfig) and DICT_KEY_TYPE in config_dict:
        type_val = config_dict[DICT_KEY_TYPE]
        subclass = _match_subclass_by_type(cls, type_val)
        sub_dict = {k: v for k, v in config_dict.items() if k != DICT_KEY_TYPE}
        return create_class_from_dict(subclass, sub_dict)

    # Warn about any unexpected keys in the config dictionary
    # Skip this check for BasePolyConfig subclasses since they may have a 'type' key
    # and subclass-specific fields that don't exist on the base class
    if not _issubclass_safe(cls, BasePolyConfig):
        known_fields = {f.name for f in fields(cls)}
        extra_keys = set(config_dict) - known_fields
        if extra_keys:
            logger.error(
                "create_class_from_dict: unknown arguments for %s: %s",
                cls.__name__,
                sorted(extra_keys),
            )
            raise TypeError(
                MSG_UNKNOWN_ARGUMENTS.format(
                    class_name=cls.__name__, extra_keys=sorted(extra_keys)
                )
            )

    kwargs: dict[str, Any] = {}

    for field in fields(cls):
        if field.name not in config_dict:
            logger.debug(
                "Field '%s' not supplied for %s; using default.",
                field.name,
                cls.__name__,
            )
            continue

        raw_value = config_dict[field.name]
        field_type = _strip_optional(field.type)
        origin = get_origin(field_type)

        # Handle list containers with potential dataclass items
        if origin is list and isinstance(raw_value, list):
            kwargs[field.name] = _process_list_field(
                field_type, raw_value, BasePolyConfig
            )
            continue

        # Handle dict containers with potential dataclass values
        if origin is dict and isinstance(raw_value, dict):
            kwargs[field.name] = _process_dict_field(
                field_type, raw_value, BasePolyConfig
            )
            continue

        # Handle polymorphic config fields
        if _issubclass_safe(field_type, BasePolyConfig):
            kwargs[field.name] = _process_polymorphic_field(field_type, raw_value)
            continue

        # Handle nested dataclass (non-polymorphic)
        if is_dataclass(field_type):
            assert isinstance(
                field_type, type
            ), f"Expected type, got {type(field_type)}"
            kwargs[field.name] = (
                create_class_from_dict(field_type, raw_value)
                if isinstance(raw_value, dict)
                else raw_value
            )
            continue

        # Primitive or unknown – assign directly
        kwargs[field.name] = raw_value

    try:
        return cls(**kwargs)
    except TypeError as e:
        logger.error(
            "Failed to instantiate %s with kwargs %s. Error: %s",
            cls.__name__,
            kwargs,
            e,
        )
        raise


def load_yaml_config(file_path: str):
    """Load a YAML configuration file and return its contents.

    The function performs a series of robustness checks and provides
    informative log messages for each failure mode.

    1. Verifies the file exists and is readable.
    2. Attempts to parse using ``yaml.safe_load``.
    3. On YAML parse errors, falls back to ``json.loads`` (helpful when the
       file is actually JSON or a subset thereof).
    4. Returns the parsed content, which can be either a dictionary (mapping)
       or a list. Lists are automatically wrapped in a dictionary with a
       special key to maintain compatibility with the configuration machinery.

    Parameters
    ----------
    file_path : str
        Path to the YAML/JSON configuration file.

    Returns
    -------
    dict
        Parsed configuration. If the top-level is a list, it's wrapped
        as {'_list': <the_list>}.

    Raises
    ------
    FileNotFoundError
        If *file_path* does not exist.
    PermissionError
        If the file cannot be read.
    yaml.YAMLError | json.JSONDecodeError
        If the file cannot be parsed as YAML or JSON.
    ValueError
        If the top-level parsed object is neither a mapping nor a list.
    """
    # check file
    if not os.path.exists(file_path):
        logger.error("Configuration file '%s' does not exist.", file_path)
        raise FileNotFoundError(f"Configuration file '{file_path}' not found.")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            raw_content = f.read()
    except Exception as exc:
        logger.error("Failed to read configuration file '%s': %s", file_path, exc)
        raise

    # try yaml first
    try:
        data = yaml.safe_load(raw_content)
    except yaml.YAMLError as yaml_err:
        logger.warning(
            "YAML parsing error in '%s': %s – attempting JSON fallback.",
            file_path,
            yaml_err,
        )
        # json fallback
        try:
            data = json.loads(raw_content)
            logger.info("File '%s' parsed successfully as JSON.", file_path)
        except json.JSONDecodeError as json_err:
            logger.error(
                "Failed to parse '%s' as either YAML or JSON: %s", file_path, json_err
            )
            # original YAML error for clarity
            raise yaml_err from None

    # handle empty file (safe_load returns None)
    if data is None:
        logger.warning(
            "Configuration file '%s' is empty. Treating as an empty mapping.",
            file_path,
        )
        data = {}

    # handle list at top level by wrapping it
    if isinstance(data, list):
        logger.info(
            "Configuration file '%s' contains a list at the top level. "
            "Wrapping it with '_list' key.",
            file_path,
        )
        return {"_list": data}

    # ensure the loaded data is a mapping
    if not isinstance(data, dict):
        logger.error(
            "Configuration file '%s' must contain either a mapping or a list "
            "at the top level (got %s).",
            file_path,
            type(data).__name__,
        )
        raise ValueError(
            f"Configuration file {file_path} must contain either a mapping "
            f"or a list at the top level, got {type(data).__name__}."
        )
    return data
