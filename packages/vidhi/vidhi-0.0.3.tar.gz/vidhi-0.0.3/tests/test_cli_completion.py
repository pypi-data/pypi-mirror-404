"""Tests for CLI completion script generation."""

from dataclasses import field
from enum import Enum

import pytest

from vidhi.base_poly_config import BasePolyConfig
from vidhi.cli_completion import (
    generate_bash_completion,
    generate_completion_script,
    generate_fish_completion,
    generate_zsh_completion,
    get_cli_arguments,
)
from vidhi.flat_dataclass import create_flat_dataclass
from vidhi.frozen_dataclass import frozen_dataclass


class TestGetCLIArguments:
    """Tests for CLI argument extraction."""

    def test_basic_argument_extraction(self):
        """Test extracting basic CLI arguments."""

        @frozen_dataclass
        class SimpleConfig:
            name: str = "default"
            count: int = 10
            enabled: bool = True

        FlatConfig = create_flat_dataclass(SimpleConfig)
        args = get_cli_arguments(FlatConfig)

        arg_names = {arg["name"] for arg in args}
        assert "name" in arg_names
        assert "count" in arg_names
        assert "enabled" in arg_names

    def test_nested_argument_extraction(self):
        """Test extracting arguments from nested configs."""

        @frozen_dataclass
        class DatabaseConfig:
            host: str = "localhost"
            port: int = 5432

        @frozen_dataclass
        class AppConfig:
            database: DatabaseConfig = field(default_factory=DatabaseConfig)

        FlatConfig = create_flat_dataclass(AppConfig)
        args = get_cli_arguments(FlatConfig)

        arg_names = {arg["name"] for arg in args}
        assert "database.host" in arg_names
        assert "database.port" in arg_names

    def test_boolean_flag_detection(self):
        """Test that boolean fields are detected."""

        @frozen_dataclass
        class ConfigWithBool:
            debug: bool = False
            verbose: bool = True

        FlatConfig = create_flat_dataclass(ConfigWithBool)
        args = get_cli_arguments(FlatConfig)

        debug_arg = next(a for a in args if a["name"] == "debug")
        assert debug_arg["is_bool"] is True

    def test_polymorphic_choices_extraction(self):
        """Test extracting choices from polymorphic type selectors."""

        class ModeType(Enum):
            FAST = "fast"
            SLOW = "slow"

        @frozen_dataclass
        class BaseMode(BasePolyConfig):
            @classmethod
            def get_type(cls) -> ModeType:
                raise NotImplementedError()

        @frozen_dataclass
        class FastMode(BaseMode):
            speed: int = 10

            @classmethod
            def get_type(cls) -> ModeType:
                return ModeType.FAST

        @frozen_dataclass
        class SlowMode(BaseMode):
            delay: int = 100

            @classmethod
            def get_type(cls) -> ModeType:
                return ModeType.SLOW

        @frozen_dataclass
        class AppConfig:
            mode: BaseMode = field(default_factory=FastMode)

        FlatConfig = create_flat_dataclass(AppConfig)
        args = get_cli_arguments(FlatConfig)

        type_arg = next(a for a in args if a["name"] == "mode.type")
        assert "fast" in type_arg["choices"]
        assert "slow" in type_arg["choices"]


class TestBashCompletion:
    """Tests for bash completion script generation."""

    def test_bash_script_structure(self):
        """Test bash completion script has correct structure."""

        @frozen_dataclass
        class SimpleConfig:
            name: str = "default"

        FlatConfig = create_flat_dataclass(SimpleConfig)
        script = generate_bash_completion(FlatConfig, "myapp")

        assert "_myapp_completions()" in script
        assert "complete -F _myapp_completions myapp" in script
        assert "--name" in script

    def test_bash_script_with_choices(self):
        """Test bash completion includes choices."""

        class Level(Enum):
            LOW = "low"
            HIGH = "high"

        @frozen_dataclass
        class ConfigWithChoices:
            level: Level = Level.LOW

        FlatConfig = create_flat_dataclass(ConfigWithChoices)
        script = generate_bash_completion(FlatConfig, "myapp")

        assert "--level" in script

    def test_bash_script_with_bool_values(self):
        """Test bash completion includes true/false values for booleans."""

        @frozen_dataclass
        class ConfigWithBool:
            debug: bool = False

        FlatConfig = create_flat_dataclass(ConfigWithBool)
        script = generate_bash_completion(FlatConfig, "myapp")

        assert "--debug" in script
        # Boolean args should offer true/false as choices
        assert "true false" in script


class TestZshCompletion:
    """Tests for zsh completion script generation."""

    def test_zsh_script_structure(self):
        """Test zsh completion script has correct structure."""

        @frozen_dataclass
        class SimpleConfig:
            name: str = "default"

        FlatConfig = create_flat_dataclass(SimpleConfig)
        script = generate_zsh_completion(FlatConfig, "myapp")

        assert "#compdef myapp" in script
        assert "_myapp()" in script
        assert "--name" in script

    def test_zsh_script_with_description(self):
        """Test zsh completion includes help text."""
        from vidhi.constants import METADATA_KEY_HELP

        @frozen_dataclass
        class ConfigWithHelp:
            name: str = field(
                default="default",
                metadata={METADATA_KEY_HELP: "The application name"},
            )

        FlatConfig = create_flat_dataclass(ConfigWithHelp)
        script = generate_zsh_completion(FlatConfig, "myapp")

        assert "The application name" in script


class TestFishCompletion:
    """Tests for fish completion script generation."""

    def test_fish_script_structure(self):
        """Test fish completion script has correct structure."""

        @frozen_dataclass
        class SimpleConfig:
            name: str = "default"

        FlatConfig = create_flat_dataclass(SimpleConfig)
        script = generate_fish_completion(FlatConfig, "myapp")

        assert "complete -c myapp" in script
        assert "-l name" in script

    def test_fish_script_with_choices(self):
        """Test fish completion includes choices with -xa."""

        class Mode(Enum):
            DEV = "dev"
            PROD = "prod"

        @frozen_dataclass
        class ConfigWithChoices:
            mode: Mode = Mode.DEV

        FlatConfig = create_flat_dataclass(ConfigWithChoices)
        script = generate_fish_completion(FlatConfig, "myapp")

        assert "-xa" in script  # Fish uses -xa for exclusive arguments


class TestGenerateCompletionScript:
    """Tests for the unified completion script generator."""

    def test_generate_bash(self):
        """Test generating bash completion via unified function."""

        @frozen_dataclass
        class SimpleConfig:
            name: str = "default"

        FlatConfig = create_flat_dataclass(SimpleConfig)
        script = generate_completion_script(FlatConfig, "myapp", "bash")

        assert "_myapp_completions" in script

    def test_generate_zsh(self):
        """Test generating zsh completion via unified function."""

        @frozen_dataclass
        class SimpleConfig:
            name: str = "default"

        FlatConfig = create_flat_dataclass(SimpleConfig)
        script = generate_completion_script(FlatConfig, "myapp", "zsh")

        assert "#compdef myapp" in script

    def test_generate_fish(self):
        """Test generating fish completion via unified function."""

        @frozen_dataclass
        class SimpleConfig:
            name: str = "default"

        FlatConfig = create_flat_dataclass(SimpleConfig)
        script = generate_completion_script(FlatConfig, "myapp", "fish")

        assert "complete -c myapp" in script

    def test_unsupported_shell_error(self):
        """Test that unsupported shells raise ValueError."""

        @frozen_dataclass
        class SimpleConfig:
            name: str = "default"

        FlatConfig = create_flat_dataclass(SimpleConfig)

        with pytest.raises(ValueError, match="Unsupported shell"):
            generate_completion_script(FlatConfig, "myapp", "powershell")


class TestFlatDataclassCompletionIntegration:
    """Tests for completion integration with flat dataclass."""

    def test_get_completion_script_method(self):
        """Test that flat dataclass has get_completion_script method."""

        @frozen_dataclass
        class SimpleConfig:
            name: str = "test"

        FlatConfig = create_flat_dataclass(SimpleConfig)

        # Should have the method
        assert hasattr(FlatConfig, "get_completion_script")

        script = FlatConfig.get_completion_script("myapp", "bash")
        assert "_myapp_completions" in script

    def test_print_completion_method(self, capsys):
        """Test print_completion method outputs to stdout."""

        @frozen_dataclass
        class SimpleConfig:
            name: str = "test"

        FlatConfig = create_flat_dataclass(SimpleConfig)
        FlatConfig.print_completion("myapp", "bash")

        captured = capsys.readouterr()
        assert "_myapp_completions" in captured.out


class TestCompletionInstallation:
    """Tests for completion installation."""

    def test_detect_shell(self):
        """Test shell detection."""
        import os

        from vidhi.cli_completion import detect_shell

        # Save original
        original_shell = os.environ.get("SHELL")

        try:
            os.environ["SHELL"] = "/bin/bash"
            assert detect_shell() == "bash"

            os.environ["SHELL"] = "/usr/bin/zsh"
            assert detect_shell() == "zsh"

            os.environ["SHELL"] = "/usr/bin/fish"
            assert detect_shell() == "fish"
        finally:
            if original_shell:
                os.environ["SHELL"] = original_shell

    def test_get_completion_install_path(self):
        """Test completion install path generation."""
        import os

        from vidhi.cli_completion import get_completion_install_path

        home = os.path.expanduser("~")

        bash_path = get_completion_install_path("myapp", "bash")
        assert "myapp" in bash_path
        assert home in bash_path

        zsh_path = get_completion_install_path("myapp", "zsh")
        assert "_myapp" in zsh_path
        assert home in zsh_path

        fish_path = get_completion_install_path("myapp", "fish")
        assert "myapp.fish" in fish_path
        assert home in fish_path

    def test_install_completion_method_exists(self):
        """Test that flat dataclass has install_completion method."""

        @frozen_dataclass
        class SimpleConfig:
            name: str = "test"

        FlatConfig = create_flat_dataclass(SimpleConfig)
        assert hasattr(FlatConfig, "install_completion")
