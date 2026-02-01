from abc import ABC
from typing import Any

from vidhi.frozen_dataclass import frozen_dataclass
from vidhi.utils import get_all_subclasses


@frozen_dataclass
class BasePolyConfig(ABC):
    @classmethod
    def create_from_type(cls, type_: Any) -> Any:
        """Create an instance of a subclass based on the type discriminator.

        Supports lenient matching:
        - Exact enum match
        - Case-insensitive string matching by enum name
        - Case-insensitive string matching by enum value
        """
        for subclass in get_all_subclasses(cls):
            subtype = subclass.get_type()
            # Exact match
            if subtype == type_:
                return subclass()
            # String matching for enums
            if isinstance(type_, str):
                # Match by enum name (e.g., "LRU" or "lru")
                if hasattr(subtype, "name") and subtype.name.lower() == type_.lower():
                    return subclass()
                # Match by enum value (e.g., "lru" for AllocatorType.LRU)
                if (
                    hasattr(subtype, "value")
                    and isinstance(subtype.value, str)
                    and subtype.value.lower() == type_.lower()
                ):
                    return subclass()
                # Match by string type directly
                if isinstance(subtype, str) and subtype.lower() == type_.lower():
                    return subclass()
        raise ValueError(f"Invalid type: {type_}")

    @classmethod
    def get_type(cls) -> Any:
        raise NotImplementedError(
            f"[{cls.__name__}] get_type() method is not implemented"
        )
