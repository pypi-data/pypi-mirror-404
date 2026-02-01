import dataclasses

import pytest

from vidhi.frozen_dataclass import frozen_dataclass


@frozen_dataclass
class SampleClass:
    name: str
    value: int = 42

    def __post_init__(self):
        self.computed = self.value * 2


class TestFrozenDataclass:
    def test_basic_functionality(self):
        obj = SampleClass("test", 10)
        assert obj.name == "test"
        assert obj.value == 10
        assert obj.computed == 20

    def test_immutability_after_init(self):
        obj = SampleClass("test", 10)
        with pytest.raises(dataclasses.FrozenInstanceError):
            obj.value = 20
