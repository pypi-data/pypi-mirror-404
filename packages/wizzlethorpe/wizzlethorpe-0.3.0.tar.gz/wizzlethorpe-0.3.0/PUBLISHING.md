# Publishing to PyPI

This document describes how to publish the `wizzlethorpe` package to PyPI using `uv`.

## Quick Start

```bash
# 1. Update version in pyproject.toml

# 2. Build the package
uv build

# 3. Test on TestPyPI (recommended)
uv publish --index-url https://test.pypi.org/legacy/

# 4. Publish to production PyPI
uv publish
```

## Prerequisites

1. **Install uv** (if not already installed):
   ```bash
   # Windows PowerShell
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

2. **Create accounts**:
   - [PyPI account](https://pypi.org/account/register/)
   - [TestPyPI account](https://test.pypi.org/account/register/) (for testing)

3. **Configure PyPI credentials**:
   - Create a PyPI API token at https://pypi.org/manage/account/token/
   - Create a TestPyPI token at https://test.pypi.org/manage/account/token/
   - Save them in `~/.pypirc`:
     ```ini
     [pypi]
     username = __token__
     password = pypi-...your-token-here...

     [testpypi]
     username = __token__
     password = pypi-...your-token-here...
     ```
   - Or set environment variables: `UV_PUBLISH_TOKEN` or `UV_PUBLISH_USERNAME`/`UV_PUBLISH_PASSWORD`

## Publishing Steps

### 1. Update Version

Edit the version number in `pyproject.toml`:

```toml
[project]
version = "0.2.0"  # Increment appropriately
```

### 2. Build the Package

```bash
uv build
```

This creates in the `dist/` directory:
- `wizzlethorpe-0.2.0.tar.gz` (source distribution)
- `wizzlethorpe-0.2.0-py3-none-any.whl` (wheel)

### 3. Test on TestPyPI (Recommended)

```bash
# Upload to TestPyPI
uv publish --index-url https://test.pypi.org/legacy/

# Test installation (in a separate environment)
pip install --index-url https://test.pypi.org/simple/ wizzlethorpe

# Test it works
wzl --help
```

### 4. Publish to PyPI

```bash
# Upload to production PyPI
uv publish
```

### 5. Verify Installation

```bash
# Install from PyPI
pip install wizzlethorpe

# Or with uv
uv pip install wizzlethorpe

# Test it works (both commands should work)
wizzlethorpe --help
wzl --help
python -c "from wizzlethorpe import WizzlethorpeClient; print('OK')"
```

### 6. Tag the Release

```bash
git tag v0.2.0
git push origin main
git push origin v0.2.0
```

## Automated Publishing with GitHub Actions

You can automate publishing using GitHub Actions with uv. Create `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v5

      - name: Build package
        run: uv build

      - name: Publish to PyPI
        run: uv publish
        env:
          UV_PUBLISH_TOKEN: ${{ secrets.PYPI_API_TOKEN }}
```

Then set `PYPI_API_TOKEN` as a GitHub secret in your repository settings.

## Versioning Guidelines

Follow [Semantic Versioning](https://semver.org/):

- **MAJOR** (1.0.0): Breaking changes
- **MINOR** (0.1.0): New features, backwards compatible
- **PATCH** (0.0.1): Bug fixes, backwards compatible

## Checklist Before Publishing

- [ ] Update version in `pyproject.toml`
- [ ] Update CHANGELOG or README with changes
- [ ] Run tests if available (`uv run pytest`)
- [ ] Build package locally (`uv build`)
- [ ] Test on TestPyPI (`uv publish --index-url https://test.pypi.org/legacy/`)
- [ ] Verify TestPyPI installation works
- [ ] Publish to PyPI (`uv publish`)
- [ ] Tag release in git (`git tag v0.2.0 && git push origin v0.2.0`)
- [ ] Verify installation from PyPI
