"""Tests for verifying that dependencies are correctly installed for subject projects.

These tests verify that when testudos runs tests on a subject project,
the project's dependencies are properly installed in the isolated environment.
"""

import subprocess
import sys

import pytest


@pytest.fixture
def package_with_dependencies(tmp_path):
    """Create a sample Python package with real dependencies.

    This package has actual dependencies that must be installed
    for its tests to pass.
    """
    pkg_dir = tmp_path / "pkg_with_deps"
    pkg_dir.mkdir()

    # Create pyproject.toml with real dependencies
    pyproject = pkg_dir / "pyproject.toml"
    pyproject.write_text(
        """[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "package-with-deps"
version = "0.1.0"
requires-python = ">=3.10"
# This package has httpx as a dependency - tests must be able to import it
dependencies = ["httpx>=0.20.0"]

[tool.hatch.build.targets.wheel]
packages = ["src/pkg_with_deps"]

[tool.testudos]
test-command = "pytest"
test-args = ["-v"]
"""
    )

    # Create source directory
    src_dir = pkg_dir / "src" / "pkg_with_deps"
    src_dir.mkdir(parents=True)

    # Create __init__.py
    init_file = src_dir / "__init__.py"
    init_file.write_text('"""Package that uses httpx."""\n\n__version__ = "0.1.0"\n')

    # Create a module that uses the dependency
    module_file = src_dir / "client.py"
    module_file.write_text(
        '''"""HTTP client module using httpx."""

import httpx


def get_client() -> httpx.Client:
    """Return a configured httpx client."""
    return httpx.Client(timeout=10.0)


def get_async_client() -> httpx.AsyncClient:
    """Return a configured async httpx client."""
    return httpx.AsyncClient(timeout=10.0)


def check_httpx_version() -> str:
    """Return the httpx version."""
    return httpx.__version__
'''
    )

    # Create tests directory
    tests_dir = pkg_dir / "tests"
    tests_dir.mkdir()

    # Create test file that imports and uses the dependency
    test_file = tests_dir / "test_dependency_import.py"
    test_file.write_text(
        '''"""Tests that verify dependencies can be imported and used.

These tests will FAIL if dependencies are not properly installed.
"""


def test_httpx_can_be_imported():
    """Test that httpx can be imported.

    This test will fail with ImportError if httpx is not installed.
    """
    import httpx
    assert httpx is not None


def test_httpx_client_can_be_created():
    """Test that httpx Client can be instantiated.

    This verifies the dependency is not just importable but functional.
    """
    import httpx
    client = httpx.Client(timeout=5.0)
    assert client is not None
    client.close()


def test_httpx_version_accessible():
    """Test that httpx version is accessible."""
    import httpx
    version = httpx.__version__
    assert version is not None
    assert isinstance(version, str)
    assert len(version) > 0


def test_package_module_uses_dependency():
    """Test that our package module can use the dependency.

    This imports from our own package which itself imports httpx.
    """
    from pkg_with_deps.client import check_httpx_version, get_client

    # Test that we can get the version through our module
    version = check_httpx_version()
    assert version is not None

    # Test that we can create a client through our module
    client = get_client()
    assert client is not None
    client.close()
'''
    )

    return pkg_dir


@pytest.fixture
def package_with_multiple_dependencies(tmp_path):
    """Create a package with multiple dependencies to verify all are installed."""
    pkg_dir = tmp_path / "multi_deps_pkg"
    pkg_dir.mkdir()

    # Create pyproject.toml with multiple dependencies
    pyproject = pkg_dir / "pyproject.toml"
    pyproject.write_text(
        """[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "multi-deps-package"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "httpx>=0.20.0",
    "packaging>=21.0",
]

[tool.hatch.build.targets.wheel]
packages = ["src/multi_deps"]

[tool.testudos]
test-command = "pytest"
test-args = ["-v"]
"""
    )

    # Create source directory
    src_dir = pkg_dir / "src" / "multi_deps"
    src_dir.mkdir(parents=True)
    (src_dir / "__init__.py").write_text('"""Multi-dependency package."""\n')

    # Create tests directory
    tests_dir = pkg_dir / "tests"
    tests_dir.mkdir()

    # Create test that uses multiple dependencies
    test_file = tests_dir / "test_multi_deps.py"
    test_file.write_text(
        '''"""Tests for multiple dependencies."""


def test_httpx_available():
    """Verify httpx is installed."""
    import httpx
    assert httpx.__version__


def test_packaging_available():
    """Verify packaging is installed."""
    from packaging.version import Version
    v = Version("1.2.3")
    assert v.major == 1
    assert v.minor == 2
    assert v.micro == 3


def test_both_dependencies_work_together():
    """Test that both dependencies can be used together."""
    import httpx
    from packaging.version import Version

    # Parse the httpx version using packaging
    httpx_version = Version(httpx.__version__)
    assert httpx_version.major >= 0
'''
    )

    return pkg_dir


class TestDependencyInstallation:
    """Tests verifying that uv properly installs dependencies for subject projects."""

    @pytest.mark.skipif(
        subprocess.run(["which", "uv"], capture_output=True).returncode != 0,
        reason="uv not available",
    )
    def test_single_dependency_installed(self, package_with_dependencies):
        """Test that a single dependency (httpx) is properly installed.

        This is the core test - if this fails, dependency installation is broken.
        """
        from testudos.executor import run_single_test

        result = run_single_test(
            version=f"3.{sys.version_info.minor}",  # Use current Python version
            test_command="pytest",
            test_args=["-v"],
            working_dir=package_with_dependencies,
            capture_output=True,
        )

        # Print output for debugging if test fails
        if not result.success:
            print(f"STDOUT:\n{result.output}")
            print(f"STDERR:\n{result.error}")

        assert result.success is True, (
            f"Tests failed - dependencies may not be installed correctly.\n"
            f"Return code: {result.return_code}\n"
            f"Error: {result.error}"
        )

    @pytest.mark.skipif(
        subprocess.run(["which", "uv"], capture_output=True).returncode != 0,
        reason="uv not available",
    )
    def test_multiple_dependencies_installed(self, package_with_multiple_dependencies):
        """Test that multiple dependencies are properly installed."""
        from testudos.executor import run_single_test

        result = run_single_test(
            version=f"3.{sys.version_info.minor}",
            test_command="pytest",
            test_args=["-v"],
            working_dir=package_with_multiple_dependencies,
            capture_output=True,
        )

        if not result.success:
            print(f"STDOUT:\n{result.output}")
            print(f"STDERR:\n{result.error}")

        assert result.success is True, (
            f"Tests failed - multiple dependencies may not be installed correctly.\n"
            f"Error: {result.error}"
        )

    @pytest.mark.skipif(
        subprocess.run(["which", "uv"], capture_output=True).returncode != 0,
        reason="uv not available",
    )
    def test_package_itself_is_importable(self, package_with_dependencies):
        """Test that the package itself is installed and importable.

        The subject package should be installed so tests can import from it.
        """
        from testudos.executor import run_single_test

        result = run_single_test(
            version=f"3.{sys.version_info.minor}",
            test_command="pytest",
            test_args=["-v", "-k", "test_package_module_uses_dependency"],
            working_dir=package_with_dependencies,
            capture_output=True,
        )

        if not result.success:
            print(f"STDOUT:\n{result.output}")
            print(f"STDERR:\n{result.error}")

        assert result.success is True, (
            f"Package import test failed - package may not be installed.\nError: {result.error}"
        )

    @pytest.mark.skipif(
        subprocess.run(["which", "uv"], capture_output=True).returncode != 0,
        reason="uv not available",
    )
    def test_runner_handles_dependencies(self, package_with_dependencies):
        """Test that the full TestRunner properly handles dependencies."""
        from testudos.runner import RunOptions, TestRunner

        runner = TestRunner(
            project_path=package_with_dependencies,
            explicit_versions=[f"3.{sys.version_info.minor}"],
        )

        results = runner.run(RunOptions(verbose=True))

        assert len(results) == 1
        for version, result in results.items():
            assert result.success is True, (
                f"TestRunner failed for Python {version}.\nError: {result.error}"
            )


class TestDependencyInstallationEdgeCases:
    """Tests for edge cases in dependency installation."""

    @pytest.fixture
    def package_with_transitive_dependencies(self, tmp_path):
        """Create a package where we need transitive dependencies."""
        pkg_dir = tmp_path / "transitive_pkg"
        pkg_dir.mkdir()

        pyproject = pkg_dir / "pyproject.toml"
        pyproject.write_text(
            """[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "transitive-pkg"
version = "0.1.0"
requires-python = ">=3.10"
# httpx depends on httpcore, certifi, etc. - these should be installed too
dependencies = ["httpx>=0.20.0"]

[tool.hatch.build.targets.wheel]
packages = ["src/transitive_pkg"]
"""
        )

        src_dir = pkg_dir / "src" / "transitive_pkg"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("")

        tests_dir = pkg_dir / "tests"
        tests_dir.mkdir()

        test_file = tests_dir / "test_transitive.py"
        test_file.write_text(
            '''"""Test transitive dependencies are available."""


def test_httpcore_available():
    """httpcore is a transitive dependency of httpx."""
    import httpcore
    assert httpcore is not None


def test_certifi_available():
    """certifi is a transitive dependency of httpx."""
    import certifi
    assert certifi.where() is not None
'''
        )

        return pkg_dir

    @pytest.mark.skipif(
        subprocess.run(["which", "uv"], capture_output=True).returncode != 0,
        reason="uv not available",
    )
    def test_transitive_dependencies_installed(self, package_with_transitive_dependencies):
        """Test that transitive dependencies (dependencies of dependencies) are installed."""
        from testudos.executor import run_single_test

        result = run_single_test(
            version=f"3.{sys.version_info.minor}",
            test_command="pytest",
            test_args=["-v"],
            working_dir=package_with_transitive_dependencies,
            capture_output=True,
        )

        if not result.success:
            print(f"STDOUT:\n{result.output}")
            print(f"STDERR:\n{result.error}")

        assert result.success is True, f"Transitive dependency test failed.\nError: {result.error}"
