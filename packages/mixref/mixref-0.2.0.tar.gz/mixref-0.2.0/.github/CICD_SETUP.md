# CI/CD Setup Guide

This document explains the automated CI/CD pipeline for mixref.

## GitHub Actions Workflows

### 1. Tests (`test.yml`)

**Triggers:** Push and PRs to `main` or `develop`

**Jobs:**
- **Test Matrix:** Tests on Python 3.12 & 3.13 across Ubuntu, macOS, Windows
- **Lint:** Ruff formatting and linting checks
- **Type Check:** mypy strict type checking
- **Coverage:** Ensures 85%+ code coverage
- **Codecov:** Uploads coverage reports (requires `CODECOV_TOKEN` secret)

**Status:** ✅ Required to pass before merge

### 2. Documentation (`docs.yml`)

**Triggers:** 
- Push to `main` (builds and deploys)
- PRs to `main` (builds only)

**Jobs:**
- **Build Docs:** Sphinx documentation with strict warnings
- **Deploy to GitHub Pages:** Automatic deployment on main branch

**Setup Required:**
1. Go to Settings → Pages
2. Set Source to "GitHub Actions"
3. Documentation will be available at `https://<username>.github.io/mixref/`

### 3. Code Quality (`quality.yml`)

**Triggers:** Push and PRs to `main` or `develop`

**Jobs:**
- **Formatting:** Ruff format check
- **Linting:** Ruff linting
- **Type Safety:** mypy checks
- **Security:** Dependency vulnerability scanning
- **Docstrings:** 80%+ docstring coverage
- **Docs Build:** Validates Sphinx builds without warnings

### 4. Publish to PyPI (`publish.yml`)

**Triggers:**
- **Release:** Automatically on GitHub release creation
- **Manual:** Workflow dispatch with TestPyPI option

**Jobs:**
- **Build:** Runs tests, builds docs, creates wheel/sdist
- **Publish to PyPI:** On release (requires trusted publishing)
- **Publish to TestPyPI:** Manual workflow with test flag
- **GitHub Release:** Updates release notes from CHANGELOG.md

## Setting Up PyPI Publishing

### Option 1: Trusted Publisher (Recommended)

1. Go to https://pypi.org/manage/account/publishing/
2. Add a new trusted publisher:
   - **PyPI Project Name:** `mixref`
   - **Owner:** `<your-github-username>`
   - **Repository:** `mixref`
   - **Workflow:** `publish.yml`
   - **Environment:** `pypi`

3. For TestPyPI (optional): https://test.pypi.org/manage/account/publishing/
   - Same settings, environment: `testpypi`

4. Create GitHub environments:
   - Settings → Environments → New environment: `pypi`
   - Settings → Environments → New environment: `testpypi`

### Option 2: API Token (Legacy)

1. Generate API token on PyPI
2. Add to GitHub secrets: `PYPI_API_TOKEN`
3. Update `publish.yml` to use token authentication

## Making a Release

### 1. Update Version

Edit `pyproject.toml`:
```toml
version = "0.2.0"
```

Also update `src/mixref/__init__.py`:
```python
__version__ = "0.2.0"
```

### 2. Update CHANGELOG.md (Optional)

```markdown
## [0.2.0] - 2026-01-30

### Added
- LUFS metering functionality
- BPM detection
- Genre-specific analysis

### Fixed
- Audio loading edge cases
```

### 3. Create Git Tag

```bash
git tag -a v0.2.0 -m "Release version 0.2.0"
git push origin v0.2.0
```

### 4. Create GitHub Release

1. Go to Releases → Draft a new release
2. Choose tag: `v0.2.0`
3. Title: `v0.2.0`
4. Auto-generate release notes or paste from CHANGELOG
5. Publish release

**The workflow will automatically:**
- ✅ Run all tests
- ✅ Build documentation
- ✅ Create wheel and sdist
- ✅ Upload to PyPI
- ✅ Attach distributions to GitHub release

## Testing Before Release

### Test on TestPyPI

1. Go to Actions → Publish to PyPI
2. Click "Run workflow"
3. Check "Publish to TestPyPI"
4. Run workflow

Install from TestPyPI:
```bash
pip install --index-url https://test.pypi.org/simple/ mixref
```

### Local Testing

```bash
# Build locally
uv build

# Check the distribution
ls dist/

# Install locally
pip install dist/mixref-0.1.0-py3-none-any.whl

# Test it works
mixref --version
```

## Monitoring CI/CD

### Branch Protection Rules (Recommended)

Settings → Branches → Add rule for `main`:

- ✅ Require status checks to pass:
  - Tests / Test Matrix
  - Tests / Lint
  - Tests / Coverage
  - Code Quality / Quality Checks
  - Documentation / Build Docs
- ✅ Require branches to be up to date
- ✅ Require linear history
- ✅ Include administrators

### Codecov Setup (Optional)

1. Go to https://codecov.io
2. Sign in with GitHub
3. Enable mixref repository
4. Add `CODECOV_TOKEN` to GitHub secrets
5. Coverage reports will appear on PRs

## Troubleshooting

### Tests Fail on Windows

Check for path issues - use `pathlib.Path` instead of string paths.

### Documentation Build Fails

Run locally:
```bash
cd docs
uv run sphinx-build -W -b html source build/html
```

Fix any warnings/errors.

### PyPI Upload Fails

1. Check package name isn't taken
2. Verify trusted publisher settings
3. Check GitHub environment matches workflow
4. Ensure version number is incremented

## Workflow Status Badges

Add to README.md:

```markdown
[![Tests](https://github.com/caparrini/mixref/actions/workflows/test.yml/badge.svg)](https://github.com/caparrini/mixref/actions/workflows/test.yml)
[![Docs](https://github.com/caparrini/mixref/actions/workflows/docs.yml/badge.svg)](https://github.com/caparrini/mixref/actions/workflows/docs.yml)
[![PyPI](https://img.shields.io/pypi/v/mixref)](https://pypi.org/project/mixref/)
[![codecov](https://codecov.io/gh/caparrini/mixref/branch/main/graph/badge.svg)](https://codecov.io/gh/caparrini/mixref)
```
