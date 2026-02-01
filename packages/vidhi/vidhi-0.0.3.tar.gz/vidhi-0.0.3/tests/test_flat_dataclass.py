import sys
from dataclasses import field
from enum import Enum
from unittest.mock import patch

from vidhi.base_poly_config import BasePolyConfig
from vidhi.flat_dataclass import create_flat_dataclass
from vidhi.frozen_dataclass import frozen_dataclass


class ChildType(Enum):
    CHILDA = "childA"
    CHILDB = "childB"


class ParentConfig(BasePolyConfig):
    common: str = "hi"


class ChildAConfig(ParentConfig):
    numA: int = 10

    @classmethod
    def get_type(cls):
        return ChildType.CHILDA


class ChildBConfig(ParentConfig):
    numB: int = 20

    @classmethod
    def get_type(cls):
        return ChildType.CHILDB


@frozen_dataclass
class NestedConfig:
    nestedval_int: int = 2
    nestedval_str: str = "nested"


@frozen_dataclass
class SampleConfig:
    val_int: int = field(
        default=1,
        metadata={"help": "Test int value."},
    )
    val_str: str = field(
        default="test",
        metadata={"help": "Test str value."},
    )
    val_nested: NestedConfig = field(default_factory=NestedConfig)
    poly: ParentConfig = field(
        default_factory=ChildAConfig, metadata={"help": "This is ParentConfig"}
    )

    @classmethod
    def create_from_cli_args(cls):
        flat_configs = create_flat_dataclass(cls).create_from_cli_args()
        instances = []
        for flat_config in flat_configs:
            instance = flat_config.reconstruct_original_dataclass()
            object.__setattr__(instance, "__flat_config__", flat_config)
            instances.append(instance)
        return instances


class TestFlatDataClass:
    def test_create_flat_dataclass_basic(self):
        flat_class = create_flat_dataclass(SampleConfig)

        assert hasattr(flat_class, "val_int")
        assert hasattr(flat_class, "val_str")
        assert hasattr(flat_class, "val_nested__nestedval_int")
        assert hasattr(flat_class, "val_nested__nestedval_str")

        assert hasattr(flat_class, "dataclass_args")
        assert hasattr(flat_class, "dataclass_dependencies")
        assert hasattr(flat_class, "root_dataclass_name")

    def test_create_from_cli_args_basic(self):
        test_args = ["test_script.py", "--val_int", "2", "--val_str", "test2"]
        with patch.object(sys, "argv", test_args):
            config = SampleConfig.create_from_cli_args()
            assert isinstance(config[0], SampleConfig)

        instance = config[0]
        assert instance.val_int == 2
        assert instance.val_str == "test2"
        assert instance.val_nested.nestedval_int == 2
        assert instance.val_nested.nestedval_str == "nested"

    def test_create_from_cli_args_nested_values(self):
        test_args = [
            "test_script.py",
            "--val_nested.nestedval_int",
            "3",
            "--val_nested.nestedval_str",
            "nested2",
        ]

        with patch.object(sys, "argv", test_args):
            config = SampleConfig.create_from_cli_args()
            assert isinstance(config[0], SampleConfig)

        instance = config[0]
        assert instance.val_int == 1
        assert instance.val_str == "test"
        assert instance.val_nested.nestedval_int == 3
        assert instance.val_nested.nestedval_str == "nested2"

    def test_create_from_cli_args_polymorphic(self):
        test_args = [
            "test_script.py",
            "--val_int",
            "2",
            "--val_str",
            "test2",
            "--poly.type",
            "childa",
        ]
        with patch.object(sys, "argv", test_args):
            config = SampleConfig.create_from_cli_args()
            assert isinstance(config[0], SampleConfig)

        instance = config[0]
        assert instance.poly.common == "hi"
        assert instance.poly.numA == 10
