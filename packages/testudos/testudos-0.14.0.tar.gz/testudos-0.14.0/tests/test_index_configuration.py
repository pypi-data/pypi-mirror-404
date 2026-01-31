"""Tests for custom PyPI index URL configuration.

This module tests the index configuration features including:
- URL validation in executor.py
- Config loading from pyproject.toml
- Command building with index options
- CLI option parsing
"""

from pathlib import Path

import pytest

from testudos.config import (
    ConfigValidationError,
    TestudosConfig,
    _is_valid_index_url,
    validate_config,
)
from testudos.executor import (
    CommandValidationError,
    _build_test_command,
    validate_find_links,
    validate_index_strategy,
    validate_index_url,
)
from testudos.runner import RunOptions, RunPlan


class TestIndexUrlValidation:
    """Tests for index URL validation functions."""

    def test_validate_index_url_valid_https(self):
        """Test that valid HTTPS URLs pass validation."""
        url = "https://pypi.example.com/simple"
        assert validate_index_url(url) == url

    def test_validate_index_url_valid_http(self):
        """Test that valid HTTP URLs pass validation."""
        url = "http://internal.company.com/pypi/simple"
        assert validate_index_url(url) == url

    def test_validate_index_url_invalid_scheme(self):
        """Test that URLs without http/https are rejected."""
        with pytest.raises(CommandValidationError) as exc_info:
            validate_index_url("ftp://example.com/packages")
        assert "must start with http:// or https://" in str(exc_info.value)

    def test_validate_index_url_no_scheme(self):
        """Test that URLs without a scheme are rejected."""
        with pytest.raises(CommandValidationError) as exc_info:
            validate_index_url("example.com/packages")
        assert "must start with http:// or https://" in str(exc_info.value)

    def test_validate_index_url_dangerous_characters(self):
        """Test that URLs with dangerous characters are rejected."""
        with pytest.raises(CommandValidationError) as exc_info:
            validate_index_url("https://example.com/$(whoami)")
        assert "dangerous characters" in str(exc_info.value)

    def test_validate_find_links_valid_path(self):
        """Test that valid paths pass validation."""
        path = "/var/packages/local"
        assert validate_find_links(path) == path

    def test_validate_find_links_valid_url(self):
        """Test that valid URLs pass validation for find-links."""
        url = "https://example.com/packages"
        assert validate_find_links(url) == url

    def test_validate_find_links_dangerous_characters(self):
        """Test that paths with dangerous characters are rejected."""
        with pytest.raises(CommandValidationError) as exc_info:
            validate_find_links("/path/$(rm -rf /)")
        assert "dangerous characters" in str(exc_info.value)

    def test_validate_index_strategy_valid(self):
        """Test that valid strategies pass validation."""
        assert validate_index_strategy("first-index") == "first-index"
        assert validate_index_strategy("unsafe-first-match") == "unsafe-first-match"
        assert validate_index_strategy("unsafe-best-match") == "unsafe-best-match"

    def test_validate_index_strategy_invalid(self):
        """Test that invalid strategies are rejected."""
        with pytest.raises(CommandValidationError) as exc_info:
            validate_index_strategy("invalid-strategy")
        assert "Invalid index-strategy" in str(exc_info.value)


class TestConfigValidation:
    """Tests for config validation of index options."""

    def test_is_valid_index_url_https(self):
        """Test _is_valid_index_url with HTTPS URL."""
        assert _is_valid_index_url("https://example.com/simple") is True

    def test_is_valid_index_url_http(self):
        """Test _is_valid_index_url with HTTP URL."""
        assert _is_valid_index_url("http://example.com/simple") is True

    def test_is_valid_index_url_invalid(self):
        """Test _is_valid_index_url with invalid URL."""
        assert _is_valid_index_url("ftp://example.com") is False
        assert _is_valid_index_url("example.com") is False
        assert _is_valid_index_url("/local/path") is False

    def test_validate_config_default_index_valid(self):
        """Test validation of valid default-index."""
        config = {"default-index": "https://pypi.example.com/simple"}
        warnings = validate_config(config)
        assert warnings == []

    def test_validate_config_default_index_invalid(self):
        """Test validation of invalid default-index."""
        config = {"default-index": "not-a-url"}
        with pytest.raises(ConfigValidationError) as exc_info:
            validate_config(config)
        assert "default-index" in str(exc_info.value)
        assert "http://" in str(exc_info.value)

    def test_validate_config_index_list_valid(self):
        """Test validation of valid index list."""
        config = {
            "index": [
                "https://pypi1.example.com/simple",
                "https://pypi2.example.com/simple",
            ]
        }
        warnings = validate_config(config)
        assert warnings == []

    def test_validate_config_index_list_invalid_url(self):
        """Test validation of index list with invalid URL."""
        config = {"index": ["https://valid.com/simple", "invalid-url"]}
        with pytest.raises(ConfigValidationError) as exc_info:
            validate_config(config)
        assert "invalid-url" in str(exc_info.value)

    def test_validate_config_index_list_not_strings(self):
        """Test validation of index list with non-strings."""
        config = {"index": [123, "https://example.com"]}
        with pytest.raises(ConfigValidationError) as exc_info:
            validate_config(config)
        assert "list of strings" in str(exc_info.value)

    def test_validate_config_find_links_valid(self):
        """Test validation of valid find-links."""
        config = {"find-links": ["/local/packages", "https://example.com/packages"]}
        warnings = validate_config(config)
        assert warnings == []

    def test_validate_config_find_links_not_strings(self):
        """Test validation of find-links with non-strings."""
        config = {"find-links": [123]}
        with pytest.raises(ConfigValidationError) as exc_info:
            validate_config(config)
        assert "list of strings" in str(exc_info.value)

    def test_validate_config_index_strategy_valid(self):
        """Test validation of valid index-strategy."""
        for strategy in ["first-index", "unsafe-first-match", "unsafe-best-match"]:
            config = {"index-strategy": strategy}
            warnings = validate_config(config)
            assert warnings == []

    def test_validate_config_index_strategy_invalid(self):
        """Test validation of invalid index-strategy."""
        config = {"index-strategy": "invalid"}
        with pytest.raises(ConfigValidationError) as exc_info:
            validate_config(config)
        assert "Invalid index-strategy" in str(exc_info.value)


class TestConfigLoading:
    """Tests for loading index config from TestudosConfig."""

    def test_config_defaults(self):
        """Test that index config has correct defaults."""
        config = TestudosConfig()
        assert config.default_index is None
        assert config.index == []
        assert config.find_links == []
        assert config.no_index is False
        assert config.index_strategy is None

    def test_config_from_pyproject(self, tmp_path):
        """Test loading index config from pyproject.toml."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[tool.testudos]
default-index = "https://pypi.internal.com/simple"
index = ["https://extra1.com/simple", "https://extra2.com/simple"]
find-links = ["/local/packages"]
no-index = false
index-strategy = "first-index"
""")

        config = TestudosConfig.from_pyproject(pyproject)
        assert config.default_index == "https://pypi.internal.com/simple"
        assert config.index == ["https://extra1.com/simple", "https://extra2.com/simple"]
        assert config.find_links == ["/local/packages"]
        assert config.no_index is False
        assert config.index_strategy == "first-index"

    def test_config_no_index_true(self, tmp_path):
        """Test loading no-index=true from pyproject.toml."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[tool.testudos]
no-index = true
find-links = ["/offline/packages"]
""")

        config = TestudosConfig.from_pyproject(pyproject)
        assert config.no_index is True
        assert config.find_links == ["/offline/packages"]


class TestBuildTestCommand:
    """Tests for command building with index options."""

    def test_build_command_default_index(self):
        """Test that --default-index is added to command."""
        cmd = _build_test_command(
            version="3.11",
            test_command="pytest",
            test_args=[],
            default_index="https://pypi.internal.com/simple",
        )
        assert "--default-index" in cmd
        assert "https://pypi.internal.com/simple" in cmd

    def test_build_command_multiple_indexes(self):
        """Test that multiple --index flags are added."""
        cmd = _build_test_command(
            version="3.11",
            test_command="pytest",
            test_args=[],
            index=["https://idx1.com/simple", "https://idx2.com/simple"],
        )
        # Count occurrences of --index
        index_count = cmd.count("--index")
        assert index_count == 2
        assert "https://idx1.com/simple" in cmd
        assert "https://idx2.com/simple" in cmd

    def test_build_command_find_links(self):
        """Test that --find-links flags are added."""
        cmd = _build_test_command(
            version="3.11",
            test_command="pytest",
            test_args=[],
            find_links=["/local/packages", "https://remote.com/packages"],
        )
        find_links_count = cmd.count("--find-links")
        assert find_links_count == 2
        assert "/local/packages" in cmd
        assert "https://remote.com/packages" in cmd

    def test_build_command_no_index(self):
        """Test that --no-index flag is added."""
        cmd = _build_test_command(
            version="3.11",
            test_command="pytest",
            test_args=[],
            no_index=True,
        )
        assert "--no-index" in cmd

    def test_build_command_index_strategy(self):
        """Test that --index-strategy is added."""
        cmd = _build_test_command(
            version="3.11",
            test_command="pytest",
            test_args=[],
            index_strategy="first-index",
        )
        assert "--index-strategy" in cmd
        assert "first-index" in cmd

    def test_build_command_all_index_options(self):
        """Test command with all index options."""
        cmd = _build_test_command(
            version="3.11",
            test_command="pytest",
            test_args=["-v"],
            default_index="https://default.com/simple",
            index=["https://extra.com/simple"],
            find_links=["/local"],
            no_index=False,
            index_strategy="unsafe-first-match",
        )
        assert "--default-index" in cmd
        assert "https://default.com/simple" in cmd
        assert "--index" in cmd
        assert "https://extra.com/simple" in cmd
        assert "--find-links" in cmd
        assert "/local" in cmd
        assert "--index-strategy" in cmd
        assert "unsafe-first-match" in cmd
        # Make sure --no-index is NOT present when no_index=False
        assert "--no-index" not in cmd

    def test_build_command_index_options_before_with(self):
        """Test that index options appear before --with flags."""
        cmd = _build_test_command(
            version="3.11",
            test_command="pytest",
            test_args=[],
            default_index="https://pypi.internal.com/simple",
        )
        # Find positions
        default_index_pos = cmd.index("--default-index")
        with_pos = cmd.index("--with")
        assert default_index_pos < with_pos


class TestRunPlanWithIndexOptions:
    """Tests for RunPlan with index options."""

    def test_run_plan_includes_index_in_commands(self):
        """Test that RunPlan._build_command includes index options."""
        plan = RunPlan(
            versions=["3.11"],
            test_command="pytest",
            test_args=[],
            working_dir=Path("/test"),
            parallel=False,
            max_jobs=None,
            default_index="https://pypi.internal.com/simple",
            index=["https://extra.com/simple"],
            find_links=["/local/packages"],
            index_strategy="first-index",
        )
        cmd_str = plan.commands[0]
        assert "--default-index" in cmd_str
        assert "https://pypi.internal.com/simple" in cmd_str
        assert "--index" in cmd_str
        assert "--find-links" in cmd_str
        assert "--index-strategy" in cmd_str

    def test_run_plan_no_index_flag(self):
        """Test that RunPlan includes --no-index when set."""
        plan = RunPlan(
            versions=["3.11"],
            test_command="pytest",
            test_args=[],
            working_dir=Path("/test"),
            parallel=False,
            max_jobs=None,
            no_index=True,
            find_links=["/offline/packages"],
        )
        cmd_str = plan.commands[0]
        assert "--no-index" in cmd_str
        assert "--find-links" in cmd_str


class TestRunOptionsWithIndexOptions:
    """Tests for RunOptions with index options."""

    def test_run_options_defaults(self):
        """Test that RunOptions has correct index defaults."""
        options = RunOptions()
        assert options.default_index is None
        assert options.index is None
        assert options.find_links is None
        assert options.no_index is False
        assert options.index_strategy is None

    def test_run_options_with_index(self):
        """Test RunOptions with index options set."""
        options = RunOptions(
            default_index="https://pypi.internal.com/simple",
            index=["https://extra.com/simple"],
            find_links=["/local"],
            no_index=False,
            index_strategy="first-index",
        )
        assert options.default_index == "https://pypi.internal.com/simple"
        assert options.index == ["https://extra.com/simple"]
        assert options.find_links == ["/local"]
        assert options.no_index is False
        assert options.index_strategy == "first-index"
