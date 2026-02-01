import dataclasses
import typing
from enum import Enum
from typing import Any, Dict, Union, get_args, get_origin

from vidhi.utils import dataclass_to_dict, dataclass_to_json, dataclass_to_yaml


class FrozenDataclassMixin:
    """Mixin providing serialization methods for frozen dataclasses.

    Inherit from this class to make serialization methods visible to type checkers.
    The @frozen_dataclass decorator adds these methods dynamically, but type checkers
    cannot see dynamically added methods. Explicit inheritance solves this.

    Example:
        @frozen_dataclass
        class MyConfig(FrozenDataclassMixin):
            name: str = "default"

        config = MyConfig()
        config.to_yaml()  # Type checker now sees this method
    """

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary (preserves Python types)."""
        return dataclass_to_dict(self)

    def to_json(self, indent: int = 2) -> str:
        """Convert to a JSON string (serializes all types)."""
        return dataclass_to_json(self)

    def to_yaml(self) -> str:
        """Convert to a YAML string (serializes all types)."""
        return dataclass_to_yaml(self)


def _convert_enum_fields(instance, datacls):
    """Convert string values to enum types for enum-typed fields.

    This enables passing enum values as strings (e.g., from CLI or config files)
    and having them automatically converted to the proper enum type.
    """
    type_hints = typing.get_type_hints(datacls)

    for field in dataclasses.fields(datacls):
        field_type = type_hints.get(field.name, field.type)
        current_value = getattr(instance, field.name)

        # Handle Optional[EnumType] - extract the inner type
        origin = get_origin(field_type)
        if origin is Union:
            args = get_args(field_type)
            # Check if it's Optional (Union with None)
            non_none_args = [a for a in args if a is not type(None)]
            if len(non_none_args) == 1:
                field_type = non_none_args[0]

        # Check if field type is an Enum and current value is a string
        if (
            isinstance(field_type, type)
            and issubclass(field_type, Enum)
            and isinstance(current_value, str)
        ):
            # Try to convert string to enum
            try:
                # First try by value (case-insensitive)
                for member in field_type:
                    if (
                        isinstance(member.value, str)
                        and member.value.lower() == current_value.lower()
                    ):
                        object.__setattr__(instance, field.name, member)
                        break
                else:
                    # Try by name (case-insensitive)
                    for member in field_type:
                        if member.name.lower() == current_value.lower():
                            object.__setattr__(instance, field.name, member)
                            break
            except (ValueError, KeyError):
                # If conversion fails, leave as-is (will likely fail validation later)
                pass


@typing.dataclass_transform()
def frozen_dataclass(_cls=None, **kwargs):
    """
    A decorator that creates a frozen dataclass, allowing attribute modifications
    only during the __post_init__ method.

    Features:
    - Automatic enum conversion: String values are converted to enum types

    Args:
        _cls: The class to decorate (for decorator syntax handling).
        **kwargs: Additional keyword arguments to pass to dataclasses.dataclass.
    """

    def wrap(cls):
        # Store the original __post_init__ if it exists
        original_post_init = getattr(cls, "__post_init__", None)

        # We need to add __post_init__ to the class BEFORE applying dataclass decorator
        # so that dataclass knows to call it. We'll replace it after with our wrapper.
        # Create a placeholder if there isn't one already
        if not hasattr(cls, "__post_init__"):
            cls.__post_init__ = lambda self: None

        # Apply dataclass with frozen=True
        datacls = dataclasses.dataclass(cls, frozen=True, **kwargs)  # type: ignore

        # Add serialization methods directly to the class
        # Note: For type checker visibility, classes should inherit from FrozenDataclassMixin
        datacls.to_dict = lambda self: dataclass_to_dict(self)
        datacls.to_json = lambda self: dataclass_to_json(self)
        datacls.to_yaml = lambda self: dataclass_to_yaml(self)

        # Now define our wrapper __post_init__ method that includes enum conversion
        def __post_init__(self):
            # Set the flag to allow attribute modifications
            object.__setattr__(self, "_in_post_init", True)
            try:
                # Auto-convert string values to enums
                _convert_enum_fields(self, datacls)

                if original_post_init:
                    original_post_init(self)
            finally:
                # Reset the flag after __post_init__ completes
                object.__setattr__(self, "_in_post_init", False)

        datacls.__post_init__ = __post_init__

        # Store the original __setattr__ method
        original_setattr = datacls.__setattr__

        # Define a new __setattr__ method
        def __setattr__(self, name, value):
            # Check if we are in __post_init__
            if getattr(self, "_in_post_init", False):
                object.__setattr__(self, name, value)
            else:
                original_setattr(self, name, value)

        datacls.__setattr__ = __setattr__

        return datacls

    # Support both @frozen_dataclass and @frozen_dataclass() syntax
    if _cls is None:
        return wrap
    return wrap(_cls)
