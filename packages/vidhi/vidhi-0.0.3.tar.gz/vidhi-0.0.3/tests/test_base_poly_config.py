from enum import Enum

import pytest

from vidhi.base_poly_config import BasePolyConfig


class ChildType(Enum):
    CHILDA = "childA"
    CHILDB = "childB"


class ParentConfig(BasePolyConfig):
    common: str = "hi"


class ChildAConfig(ParentConfig):
    @classmethod
    def get_type(cls):
        return ChildType.CHILDA


class ChildBConfig(ParentConfig):
    @classmethod
    def get_type(cls):
        return ChildType.CHILDB


class TestBasePolyConfig:
    def test_create_from_type(self):
        instance = ParentConfig.create_from_type(ChildType.CHILDA)
        assert isinstance(instance, ChildAConfig)

        instance = ParentConfig.create_from_type(ChildType.CHILDB)
        assert isinstance(instance, ChildBConfig)

    def test_create_from_invalid_type(self):
        with pytest.raises(ValueError, match="Invalid type: type_invalid"):
            ParentConfig.create_from_type("type_invalid")

    def test_get_type_not_implemented(self):
        with pytest.raises(NotImplementedError):
            BasePolyConfig.get_type()
