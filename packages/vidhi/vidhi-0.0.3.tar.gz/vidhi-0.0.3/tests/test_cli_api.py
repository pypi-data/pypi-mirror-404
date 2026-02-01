"""Tests for the public CLI API (field, parse_cli_args, with_cli_overrides)."""

import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from vidhi import field, frozen_dataclass, parse_cli_args, with_cli_overrides


class TestFieldHelper:
    def test_field_with_help(self):
        """Test field() with help text."""

        @frozen_dataclass
        class Config:
            learning_rate: float = field(0.001, help="Learning rate")

        # Verify metadata is set correctly
        from dataclasses import fields

        lr_field = fields(Config)[0]
        assert lr_field.metadata["help"] == "Learning rate"
        assert lr_field.default == 0.001

    def test_field_with_custom_name(self):
        """Test field() with custom CLI name."""

        @frozen_dataclass
        class Config:
            learning_rate: float = field(0.001, name="lr")

        from dataclasses import fields

        lr_field = fields(Config)[0]
        assert lr_field.metadata["argname"] == "lr"

    def test_field_with_all_options(self):
        """Test field() with all CLI options."""

        @frozen_dataclass
        class Config:
            learning_rate: float = field(
                0.001, help="Learning rate for optimizer", name="lr"
            )

        from dataclasses import fields

        lr_field = fields(Config)[0]
        assert lr_field.metadata["help"] == "Learning rate for optimizer"
        assert lr_field.metadata["argname"] == "lr"
        assert lr_field.default == 0.001

    def test_field_preserves_existing_metadata(self):
        """Test that field() preserves user-provided metadata."""

        @frozen_dataclass
        class Config:
            value: int = field(10, help="Help text", metadata={"custom": "data"})

        from dataclasses import fields

        val_field = fields(Config)[0]
        assert val_field.metadata["help"] == "Help text"
        assert val_field.metadata["custom"] == "data"

    def test_field_without_cli_options(self):
        """Test field() works as drop-in for dataclasses.field."""

        @frozen_dataclass
        class Config:
            value: int = field(default=42)

        config = Config()
        assert config.value == 42

    def test_field_with_default_factory(self):
        """Test field() with default_factory."""

        @frozen_dataclass
        class Config:
            items: list = field(default_factory=list, help="List of items")

        config = Config()
        assert config.items == []


class TestParseCLIArgs:
    def test_basic_parsing(self):
        """Test basic CLI argument parsing."""

        @frozen_dataclass
        class Config:
            name: str = field("default", help="Name")
            count: int = field(10, help="Count")

        test_args = ["script.py", "--name", "test", "--count", "42"]
        with patch.object(sys, "argv", test_args):
            config = parse_cli_args(Config)

        assert config.name == "test"
        assert config.count == 42

    def test_custom_arg_name(self):
        """Test parsing with custom argument name."""

        @frozen_dataclass
        class Config:
            learning_rate: float = field(0.001, name="lr")

        test_args = ["script.py", "--lr", "0.01"]
        with patch.object(sys, "argv", test_args):
            config = parse_cli_args(Config)

        assert config.learning_rate == 0.01

    def test_nested_config(self):
        """Test parsing nested config structures."""

        @frozen_dataclass
        class DatabaseConfig:
            host: str = "localhost"
            port: int = 5432

        @frozen_dataclass
        class AppConfig:
            name: str = "app"
            database: DatabaseConfig = None

        test_args = [
            "script.py",
            "--database.host",
            "db.example.com",
            "--database.port",
            "3306",
        ]
        with patch.object(sys, "argv", test_args):
            config = parse_cli_args(AppConfig)

        assert config.database.host == "db.example.com"
        assert config.database.port == 3306


class TestEntrypointIsolation:
    """Test that different entrypoints only see their own config args."""

    def test_separate_configs_independent(self):
        """Test that two different config classes work independently."""

        @frozen_dataclass
        class TrainingConfig:
            learning_rate: float = field(0.001, help="LR")
            epochs: int = field(10, help="Epochs")

        @frozen_dataclass
        class InferenceConfig:
            model_path: str = field("model.pt", help="Model path")
            batch_size: int = field(32, help="Batch size")

        # Training entrypoint
        train_args = ["train.py", "--learning_rate", "0.01", "--epochs", "20"]
        with patch.object(sys, "argv", train_args):
            train_config = parse_cli_args(TrainingConfig)

        assert train_config.learning_rate == 0.01
        assert train_config.epochs == 20

        # Inference entrypoint (completely separate)
        infer_args = ["infer.py", "--model_path", "best.pt", "--batch_size", "64"]
        with patch.object(sys, "argv", infer_args):
            infer_config = parse_cli_args(InferenceConfig)

        assert infer_config.model_path == "best.pt"
        assert infer_config.batch_size == 64

    def test_config_doesnt_see_other_args(self):
        """Test that a config doesn't accidentally parse args from another config."""

        @frozen_dataclass
        class ConfigA:
            value_a: int = 1

        @frozen_dataclass
        class ConfigB:
            value_b: int = 2

        # ConfigA should not recognize --value_b
        args_with_b = ["script.py", "--value_a", "10", "--value_b", "20"]
        with patch.object(sys, "argv", args_with_b):
            with pytest.raises(SystemExit):  # argparse exits on unrecognized args
                parse_cli_args(ConfigA)

    def test_shared_nested_config(self):
        """Test that a shared nested config works in different parents."""

        @frozen_dataclass
        class DatabaseConfig:
            host: str = "localhost"

        @frozen_dataclass
        class AppA:
            name: str = "app_a"
            db: DatabaseConfig = None

        @frozen_dataclass
        class AppB:
            name: str = "app_b"
            db: DatabaseConfig = None

        # AppA entrypoint
        args_a = ["app_a.py", "--db.host", "db-a.example.com"]
        with patch.object(sys, "argv", args_a):
            config_a = parse_cli_args(AppA)
        assert config_a.db.host == "db-a.example.com"

        # AppB entrypoint (separate invocation)
        args_b = ["app_b.py", "--db.host", "db-b.example.com"]
        with patch.object(sys, "argv", args_b):
            config_b = parse_cli_args(AppB)
        assert config_b.db.host == "db-b.example.com"


class TestWithCLIOverrides:
    """Tests for with_cli_overrides() function."""

    def test_no_overrides_returns_original(self):
        """Test that no CLI args returns the original config."""

        @frozen_dataclass
        class Config:
            name: str = "default"
            value: int = 10

        base_config = Config(name="custom", value=42)

        test_args = ["script.py"]  # No overrides
        with patch.object(sys, "argv", test_args):
            result = with_cli_overrides(base_config)

        assert result.name == "custom"
        assert result.value == 42

    def test_partial_override(self):
        """Test overriding only some fields."""

        @frozen_dataclass
        class Config:
            name: str = "default"
            value: int = 10
            enabled: bool = False

        base_config = Config(name="custom", value=42, enabled=True)

        test_args = ["script.py", "--value", "100"]
        with patch.object(sys, "argv", test_args):
            result = with_cli_overrides(base_config)

        assert result.name == "custom"  # Unchanged
        assert result.value == 100  # Overridden
        assert result.enabled is True  # Unchanged

    def test_nested_override(self):
        """Test overriding nested config fields."""

        @frozen_dataclass
        class DatabaseConfig:
            host: str = "localhost"
            port: int = 5432

        @frozen_dataclass
        class AppConfig:
            name: str = "app"
            database: DatabaseConfig = None

            def __post_init__(self):
                if self.database is None:
                    object.__setattr__(self, "database", DatabaseConfig())

        base_config = AppConfig(
            name="myapp", database=DatabaseConfig(host="db.local", port=3306)
        )

        test_args = ["script.py", "--database.port", "5433"]
        with patch.object(sys, "argv", test_args):
            result = with_cli_overrides(base_config)

        assert result.name == "myapp"  # Unchanged
        assert result.database.host == "db.local"  # Unchanged
        assert result.database.port == 5433  # Overridden

    def test_override_multiple_fields(self):
        """Test overriding multiple fields at once."""

        @frozen_dataclass
        class Config:
            learning_rate: float = 0.001
            batch_size: int = 32
            epochs: int = 10

        base_config = Config(learning_rate=0.01, batch_size=64, epochs=20)

        test_args = ["script.py", "--learning_rate", "0.1", "--epochs", "50"]
        with patch.object(sys, "argv", test_args):
            result = with_cli_overrides(base_config)

        assert result.learning_rate == 0.1  # Overridden
        assert result.batch_size == 64  # Unchanged
        assert result.epochs == 50  # Overridden

    def test_yaml_file_with_cli_overrides(self):
        """Test loading YAML file via CLI with additional CLI overrides.

        Priority should be: CLI args > YAML file > code defaults
        """

        @frozen_dataclass
        class TrainingConfig:
            model: str = "resnet50"
            learning_rate: float = 0.001
            batch_size: int = 32
            epochs: int = 10

        # Code defaults
        base_config = TrainingConfig(
            model="vgg16",
            learning_rate=0.01,
            batch_size=64,
            epochs=20,
        )

        # YAML overrides some values
        yaml_content = """
model: "efficientnet"
learning_rate: 0.005
batch_size: 128
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            # CLI overrides learning_rate (highest priority)
            test_args = [
                "script.py",
                "--config",
                yaml_path,
                "--learning_rate",
                "0.1",
            ]
            with patch.object(sys, "argv", test_args):
                result = with_cli_overrides(base_config)

            # CLI wins for learning_rate
            assert result.learning_rate == 0.1
            # YAML wins for model and batch_size
            assert result.model == "efficientnet"
            assert result.batch_size == 128
            # Code default wins for epochs (not in YAML or CLI)
            assert result.epochs == 20

        finally:
            Path(yaml_path).unlink()
