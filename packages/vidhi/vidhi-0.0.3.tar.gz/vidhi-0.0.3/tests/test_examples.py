"""
Tests to validate that documentation examples work correctly.

These tests ensure that the examples in examples/ remain functional
and serve as regression tests for user-facing API stability.
"""

import subprocess
import sys
from pathlib import Path

import pytest


def get_example_path(example_name: str) -> Path:
    """Get the path to an example file."""
    return Path(__file__).parent.parent / "examples" / example_name


def run_example(example_name: str) -> subprocess.CompletedProcess:
    """Run an example file and return the result."""
    example_path = get_example_path(example_name)
    if not example_path.exists():
        pytest.skip(f"Example file not found: {example_path}")

    result = subprocess.run(
        [sys.executable, str(example_path)],
        capture_output=True,
        text=True,
        timeout=10,
    )
    return result


class TestBasicUsageExample:
    """Tests for examples/01_basic_usage.py"""

    def test_runs_successfully(self):
        """Test that the example runs without errors."""
        result = run_example("01_basic_usage.py")
        assert result.returncode == 0, f"Example failed with stderr: {result.stderr}"

    def test_demonstrates_config(self):
        """Test that configuration output is shown."""
        result = run_example("01_basic_usage.py")
        assert "Training Configuration" in result.stdout
        assert "Model:" in result.stdout
        assert "Learning Rate:" in result.stdout

    def test_demonstrates_immutability(self):
        """Test that immutability is demonstrated."""
        result = run_example("01_basic_usage.py")
        assert "immutable" in result.stdout.lower()


class TestPolymorphicCLIExample:
    """Tests for examples/02_polymorphic_cli.py"""

    def test_runs_successfully(self):
        """Test that the example runs without errors."""
        result = run_example("02_polymorphic_cli.py")
        assert result.returncode == 0, f"Example failed with stderr: {result.stderr}"

    def test_shows_scheduler(self):
        """Test that scheduler configuration is shown."""
        result = run_example("02_polymorphic_cli.py")
        assert "Scheduler:" in result.stdout
        assert "FifoScheduler" in result.stdout or "fifo" in result.stdout.lower()

    def test_shows_cache(self):
        """Test that nested cache config is shown."""
        result = run_example("02_polymorphic_cli.py")
        assert "Cache:" in result.stdout
        assert "TTL:" in result.stdout


class TestYAMLConfigExample:
    """Tests for examples/03_yaml_config.py"""

    def test_runs_successfully(self):
        """Test that the example runs without errors."""
        result = run_example("03_yaml_config.py")
        assert result.returncode == 0, f"Example failed with stderr: {result.stderr}"

    def test_shows_yaml_loading(self):
        """Test that YAML loading is demonstrated."""
        result = run_example("03_yaml_config.py")
        assert "Loading configuration" in result.stdout

    def test_shows_parsed_config(self):
        """Test that parsed configuration is shown."""
        result = run_example("03_yaml_config.py")
        assert "Parsed Configuration" in result.stdout
        assert "App:" in result.stdout

    def test_shows_polymorphic_storage(self):
        """Test that polymorphic storage is demonstrated."""
        result = run_example("03_yaml_config.py")
        assert "Storage:" in result.stdout
        assert "S3StorageConfig" in result.stdout or "s3" in result.stdout.lower()


class TestCLIYAMLComboExample:
    """Tests for examples/04_cli_yaml_combo.py"""

    def test_runs_successfully(self):
        """Test that the example runs without errors."""
        result = run_example("04_cli_yaml_combo.py")
        assert result.returncode == 0, f"Example failed with stderr: {result.stderr}"

    def test_shows_usage_examples(self):
        """Test that usage examples are shown."""
        result = run_example("04_cli_yaml_combo.py")
        assert "Usage Examples" in result.stdout

    def test_demonstrates_cli_overrides(self):
        """Test that CLI overrides are demonstrated."""
        result = run_example("04_cli_yaml_combo.py")
        assert "with_cli_overrides" in result.stdout or "CLI" in result.stdout


class TestAllExamples:
    """Tests that validate all examples together."""

    def test_all_examples_exist(self):
        """Test that all expected example files exist."""
        examples_dir = Path(__file__).parent.parent / "examples"

        expected_examples = [
            "01_basic_usage.py",
            "02_polymorphic_cli.py",
            "03_yaml_config.py",
            "04_cli_yaml_combo.py",
        ]

        for example in expected_examples:
            example_path = examples_dir / example
            assert example_path.exists(), f"Missing example file: {example}"

    def test_all_examples_are_executable(self):
        """Test that all examples can be executed."""
        examples_dir = Path(__file__).parent.parent / "examples"

        for example_file in examples_dir.glob("*.py"):
            result = subprocess.run(
                [sys.executable, str(example_file)],
                capture_output=True,
                text=True,
                timeout=10,
            )

            assert (
                result.returncode == 0
            ), f"{example_file.name} failed with stderr: {result.stderr}"

    def test_all_examples_import_vidhi(self):
        """Test that all examples properly import from vidhi."""
        examples_dir = Path(__file__).parent.parent / "examples"

        for example_file in examples_dir.glob("*.py"):
            content = example_file.read_text()

            assert (
                "from vidhi" in content or "import vidhi" in content
            ), f"{example_file.name} doesn't import from vidhi"

    def test_examples_have_docstrings(self):
        """Test that all examples have docstrings."""
        examples_dir = Path(__file__).parent.parent / "examples"

        for example_file in examples_dir.glob("*.py"):
            content = example_file.read_text()
            assert '"""' in content, f"{example_file.name} missing docstring"

    def test_examples_have_main_guard(self):
        """Test that all examples use if __name__ == '__main__'."""
        examples_dir = Path(__file__).parent.parent / "examples"

        for example_file in examples_dir.glob("*.py"):
            content = example_file.read_text()

            assert (
                'if __name__ == "__main__"' in content
            ), f"{example_file.name} missing main guard"


class TestExampleAPIUsage:
    """Tests that validate examples use the correct public API."""

    def test_basic_example_uses_frozen_dataclass(self):
        """Test that basic example uses frozen_dataclass."""
        content = get_example_path("01_basic_usage.py").read_text()
        assert "frozen_dataclass" in content

    def test_polymorphic_example_uses_base_poly_config(self):
        """Test that polymorphic example uses BasePolyConfig."""
        content = get_example_path("02_polymorphic_cli.py").read_text()
        assert "BasePolyConfig" in content

    def test_yaml_example_uses_create_class_from_dict(self):
        """Test that YAML example uses create_class_from_dict."""
        content = get_example_path("03_yaml_config.py").read_text()
        assert "create_class_from_dict" in content

    def test_yaml_example_uses_load_yaml_config(self):
        """Test that YAML example uses load_yaml_config."""
        content = get_example_path("03_yaml_config.py").read_text()
        assert "load_yaml_config" in content


class TestExampleQuality:
    """Tests for example code quality."""

    def test_examples_produce_output(self):
        """Test that examples produce helpful output."""
        examples_dir = Path(__file__).parent.parent / "examples"

        for example_file in examples_dir.glob("*.py"):
            result = subprocess.run(
                [sys.executable, str(example_file)],
                capture_output=True,
                text=True,
                timeout=10,
            )

            assert result.stdout.strip(), f"{example_file.name} produces no output"
            assert (
                len(result.stdout.strip()) > 50
            ), f"{example_file.name} output is too brief"


class TestREADMEExamples:
    """Tests to validate README exists and has examples."""

    def test_readme_exists(self):
        """Test that README exists."""
        readme_path = Path(__file__).parent.parent / "README.md"
        assert readme_path.exists(), "README.md not found"


class TestDocsExist:
    """Tests to validate documentation structure."""

    def test_docs_index_exists(self):
        """Test that docs index exists."""
        index_path = Path(__file__).parent.parent / "docs" / "index.rst"
        assert index_path.exists(), "docs/index.rst not found"

    def test_quickstart_exists(self):
        """Test that quickstart guide exists."""
        quickstart_path = Path(__file__).parent.parent / "docs" / "quickstart.rst"
        assert quickstart_path.exists(), "docs/quickstart.rst not found"

    def test_user_guide_exists(self):
        """Test that user guide exists."""
        guide_path = Path(__file__).parent.parent / "docs" / "user_guide" / "index.rst"
        assert guide_path.exists(), "docs/user_guide/index.rst not found"
