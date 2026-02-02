# Wizzlethorpe Python Client

Python client library and CLI for Wizzlethorpe Labs APIs (Quickbrush image generation and Cocktails database).

## Environment Setup

**This project uses `uv` for dependency management.**

To set up the development environment:

```bash
# Install dependencies and create virtual environment
uv sync

# Run commands with uv
uv run wzl --help
```

If you need to install uv first:

```bash
# Windows PowerShell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or via pip
pip install uv
```

## Project Structure

- `wizzlethorpe/` - Main package source code
  - `cli.py` - CLI entry point (accessible as `wizzlethorpe` or `wzl`)
  - `cocktails/` - Cocktails API client
  - `quickbrush/` - Quickbrush image generation client
- `pyproject.toml` - Package configuration and dependencies
- `publish.py` - Build and publish automation script
- `README.md` - User-facing documentation
- `PUBLISHING.md` - Publishing workflow documentation

## Code Style

- **Line length**: 100 characters max
- **Target Python**: 3.10+
- **Linting**: Use `ruff` for code quality checks
- **Imports**: Follow ruff's import sorting (E, F, I, UP rules enabled)
- **Dependencies**: Keep minimal - currently using httpx, pydantic, and click

## CLI Commands

The package provides two CLI entry points (both do the same thing):
- `wizzlethorpe` - Full name
- `wzl` - Short alias

## Building and Publishing

**uv has built-in commands for building and publishing:**

```bash
# Build the package
uv build

# Publish to TestPyPI first (recommended)
uv publish --index-url https://test.pypi.org/legacy/

# If TestPyPI works, publish to production PyPI
uv publish
```

**Authentication:**
- uv uses your `~/.pypirc` configuration
- Or set environment variables: `UV_PUBLISH_TOKEN` or `UV_PUBLISH_USERNAME`/`UV_PUBLISH_PASSWORD`

**Important**: Always test on TestPyPI before publishing to PyPI production. You cannot delete or overwrite versions on PyPI once published.

## Version Management

Update version in `pyproject.toml` before publishing:

```toml
[project]
version = "0.1.1"  # Follow semver: MAJOR.MINOR.PATCH
```

## Repository Workflow

- Main branch: `main`
- After publishing to PyPI, tag releases:
  ```bash
  git tag v0.1.0
  git push origin v0.1.0
  ```

## Project-Specific Notes

- The package name "wizzlethorpe" should always be lowercase
- Both CLI entry points (`wizzlethorpe` and `wzl`) must be kept in sync in pyproject.toml
- TestPyPI and PyPI require separate account credentials configured in `~/.pypirc`

## Development Workflow

Run CLI commands during development:

```bash
# Run the CLI
uv run wzl --help
uv run wizzlethorpe --help

# Test imports
uv run python -c "from wizzlethorpe import WizzlethorpeClient; print('OK')"
```

## Testing Installation

After publishing, verify the package works:

```bash
# Install from PyPI
pip install wizzlethorpe

# Or with uv
uv pip install wizzlethorpe

# Test it works
wzl --help
wizzlethorpe --help
python -c "from wizzlethorpe import WizzlethorpeClient; print('OK')"
```
