# CLAUDE.md - Testudos Project Guide

## Project Overview

**Testudos** is a Python testing harness that runs test suites across multiple Python versions using `uv`'s isolated environments. It provides a lightweight alternative to Tox with automatic Python version detection.

**Key Features:**
- Automatically detects compatible Python versions (intersection of supported versions from endoflife.date API and `requires-python` from pyproject.toml)
- Sequential and parallel test execution
- Coverage collection and aggregation across versions
- Rich terminal UI with progress displays

**Repository:** https://github.com/martinristovski/testudos

## Tech Stack

- **Python 3.10+** (src-layout in `src/testudos/`)
- **typer** - CLI framework
- **rich** - Terminal formatting and progress displays
- **httpx** - HTTP client for API requests
- **pytest** + **pytest-asyncio** - Testing
- **mypy** (strict mode) - Static type checking
- **ruff** - Linting and formatting
- **uv** - Package management and isolated environments (required at runtime)

## Development Commands

Use `just` for all development tasks:

```bash
just ci              # Full CI: lint, type-check, test, dogfood, check-version
just lint            # ruff check + format check
just type-check      # mypy src/
just test            # pytest with coverage
just dogfood         # Run testudos on itself (--parallel)
just fix             # Auto-fix linting issues
just install         # uv sync --extra dev
```

Direct commands:
```bash
uv run pytest                     # Run tests
uv run ruff check src tests       # Lint
uv run mypy src                   # Type check
uv run testudos run               # Run testudos
```

## Project Structure

```
src/testudos/
├── cli.py            # Typer CLI entry point
├── runner.py         # High-level TestRunner orchestration
├── executor.py       # Test execution engine (sequential/parallel)
├── versions.py       # Version resolution with API caching
├── config.py         # Configuration loading from pyproject.toml
├── coverage.py       # Coverage collection and aggregation
├── ui.py             # Rich-based UI components
├── python_version.py # Validated PythonVersion type
├── multi_runner.py   # Multi-package orchestration
└── workspace.py      # Workspace/monorepo data structures

tests/                # 11 test files, comprehensive coverage
docs/                 # ARCHITECTURE.md, DESIGN_DECISIONS.md, etc.
```

## Code Style & Patterns

### Formatting
- **Line length:** 100 characters
- **Ruff rules:** E, F, I (isort), N (naming), W, UP (upgrades)
- **MyPy:** Strict mode with all optional checks enabled

### Key Patterns

1. **Version Resolution:**
   ```
   supported_versions (endoflife.date API) ∩ requires_python (pyproject.toml) = test_versions
   ```

2. **Type Safety:** All code uses type hints; dataclasses for data structures; enums for states

3. **Error Handling:** Custom exception hierarchy (`ExecutorError`, `VersionResolutionError`, `ConfigValidationError`)

4. **Security:** Subprocess calls use list-based arguments (no `shell=True`); command validation rejects shell metacharacters

5. **Caching:** File-based JSON cache at `~/.cache/testudos/` with 24-hour TTL

6. **Async Execution:** Parallel test execution uses `asyncio` with `run_tests_parallel_async()`

## Testing Conventions

- Test files mirror source structure: `test_executor.py` tests `executor.py`
- Use `strip_ansi()` helper when testing Rich output
- Use `CliRunner` from typer.testing for CLI tests
- Async tests work automatically (asyncio_mode="auto")
- Mock external dependencies (httpx, subprocess) in tests

## CLI Commands

```bash
testudos run [PATH]           # Run tests across versions
testudos versions [PATH]      # Show which versions would be tested
testudos coverage combine     # Combine coverage data
testudos coverage report      # Generate coverage reports
testudos coverage clean       # Clean coverage files
```

Common flags: `--parallel`, `--jobs`, `--timeout`, `--coverage`, `--dry-run`, `--verbose`, `--color/--no-color`

## Configuration

Testudos reads from `[tool.testudos]` in pyproject.toml:

```toml
[tool.testudos]
python-versions = ["3.10", "3.11", "3.12"]  # Override auto-detection
test-command = "pytest"
test-args = ["-v", "--tb=short"]
parallel = true
max-jobs = 4
coverage = true
timeout = 300
```

## CI/CD

- **Version Check:** PRs must bump version in pyproject.toml and update CHANGELOG.md
- **Test Matrix:** Python 3.10-3.13
- **Dogfood:** Main branch runs testudos on itself
- **Publishing:** Automated PyPI release on version tags

## Important Notes

- Always validate version strings with `PythonVersion.parse()` (enforces "X.Y" format)
- Coverage data stored in `.testudos/coverage/` directory
- Fallback versions `["3.11", "3.12", "3.13", "3.14"]` used when API/cache unavailable
- Respects `NO_COLOR` and `FORCE_COLOR` environment variables
