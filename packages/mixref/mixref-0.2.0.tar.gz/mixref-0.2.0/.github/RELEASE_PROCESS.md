# Release Process for mixref

This document outlines the complete release process for publishing a new version of mixref to PyPI.

## ⚠️ Pre-Release Requirements

**CRITICAL: All checks MUST pass locally before creating a release!**

### 1. Run Complete Test Suite

```bash
# All tests must pass
uv run pytest -v

# Must show 46/46 tests passing (or current total)
```

### 2. Verify Coverage

```bash
# Must be 85%+ (currently at 90.5%+)
uv run pytest --cov=src/mixref --cov-report=term --cov-fail-under=85

# Should show "Required test coverage of 85% reached"
```

### 3. Code Quality Checks

```bash
# Format code
uv run ruff format src/ tests/

# Linting must pass
uv run ruff check src/ tests/

# Type checking must pass
uv run mypy src/

# All three should show "All checks passed" or "Success: no issues found"
```

### 4. Documentation Build

```bash
# CRITICAL: Must build without errors
cd docs
uv run make clean
uv run make html
cd ..

# Should show "build succeeded" (warnings OK if < 30)
# Check that docs/build/html/index.html exists
```

### 5. Test Installation Locally

```bash
# Build the package
uv build

# Install in a fresh environment
pip install dist/mixref-X.Y.Z-py3-none-any.whl

# Test the CLI
mixref --version
mixref --help

# Test Python import
python -c "from mixref.audio import load_audio; from mixref.meters import calculate_lufs; print('OK')"
```

---

## 📋 Release Checklist

Use this checklist for every release:

- [ ] All local tests pass (`uv run pytest -v`)
- [ ] Coverage ≥ 85% (`pytest --cov`)
- [ ] Ruff formatting clean (`ruff format --check`)
- [ ] Ruff linting clean (`ruff check`)
- [ ] Mypy type checking clean (`mypy src/`)
- [ ] Documentation builds successfully (`make html`)
- [ ] Local wheel builds and installs (`uv build`)
- [ ] CHANGELOG.md updated with new version
- [ ] Version bumped in `pyproject.toml`
- [ ] Version bumped in `src/mixref/__init__.py`
- [ ] All changes committed and pushed to main
- [ ] GitHub CI workflows all green ✅

---

## 🚀 Release Steps

### Step 1: Update Version Numbers

**File 1: `pyproject.toml`**
```toml
[project]
name = "mixref"
version = "0.2.0"  # ← Update this
```

**File 2: `src/mixref/__init__.py`**
```python
__version__ = "0.2.0"  # ← Update this
```

**File 3: `docs/source/conf.py`** (if needed)
```python
release = "0.2.0"  # ← Update this
```

### Step 2: Update CHANGELOG.md

Add new section at top:

```markdown
## [0.2.0] - 2026-01-30

### Added
- Audio validation utilities (get_audio_info, validate_duration, validate_sample_rate)
- LUFS metering with EBU R128 standard
- Loudness calculation (integrated LUFS, true peak, LRA)
- Sphinx-Gallery examples for validation and metering

### Fixed
- Mypy type errors in validation module
- Documentation duplicate object warnings
- Python 3.13 Windows compatibility (excluded from test matrix)

### Documentation
- Added pre-commit checklist for developers
- Added CI fixes summary
- Added platform compatibility documentation
```

### Step 3: Commit Version Bump

```bash
git add pyproject.toml src/mixref/__init__.py CHANGELOG.md
git commit -m "chore: bump version to 0.2.0"
git push origin main
```

### Step 4: Verify CI Passes

**WAIT for GitHub Actions to complete!**

Go to: https://github.com/caparrini/mixref/actions

Check that ALL workflows pass:
- ✅ Tests (all platforms)
- ✅ Code Quality
- ✅ Documentation Build

**Do NOT proceed if any workflow fails!**

### Step 5: Create Git Tag

```bash
# Create annotated tag
git tag -a v0.2.0 -m "Release version 0.2.0 - Audio validation and LUFS metering"

# Push tag to GitHub
git push origin v0.2.0
```

### Step 6: Create GitHub Release

1. Go to: https://github.com/caparrini/mixref/releases
2. Click "Draft a new release"
3. **Choose a tag:** Select `v0.2.0` from dropdown
4. **Release title:** `v0.2.0 - Audio Validation & LUFS Metering`
5. **Description:** Copy from CHANGELOG.md or use "Generate release notes"
6. **Set as latest release:** ✅ Check this box
7. Click **"Publish release"**

### Step 7: Automatic PyPI Upload

The `publish.yml` workflow will automatically:
1. ✅ Run all tests
2. ✅ Build documentation
3. ✅ Create wheel and source distribution
4. ✅ Upload to PyPI (using trusted publishing)
5. ✅ Attach distributions to GitHub release

**Monitor:** https://github.com/caparrini/mixref/actions/workflows/publish.yml

**Verify:** https://pypi.org/project/mixref/

---

## 🧪 Testing on TestPyPI (Optional)

Before official release, you can test on TestPyPI:

### Option A: Manual Workflow Dispatch

1. Go to Actions → "Publish to PyPI"
2. Click "Run workflow"
3. Select branch: `main`
4. ✅ Check "Publish to TestPyPI instead"
5. Click "Run workflow"

### Option B: Command Line

```bash
# Build locally
uv build

# Upload to TestPyPI (requires twine and token)
twine upload --repository testpypi dist/*

# Test installation
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ mixref==0.2.0
```

---

## 🔧 Troubleshooting

### Release Failed - What to Do?

**If PyPI upload fails:**
1. Delete the GitHub release (it's reversible)
2. Delete the git tag: `git tag -d v0.2.0 && git push origin :refs/tags/v0.2.0`
3. Fix the issue
4. Start over from Step 1

**Common Issues:**

| Issue | Solution |
|-------|----------|
| Version already exists on PyPI | Bump to next version (can't reuse versions) |
| Tests fail in CI | Fix tests, commit, push, wait for green ✅ |
| Docs build fails | Run `make html` locally first, fix warnings |
| Import errors after install | Check dependencies in `pyproject.toml` |
| Type errors in CI | Run `mypy src/` locally, must pass first |

---

## 📊 Post-Release Verification

After release is published:

1. ✅ Check PyPI page: https://pypi.org/project/mixref/0.2.0/
2. ✅ Test installation: `pip install --upgrade mixref`
3. ✅ Verify version: `mixref --version` (should show 0.2.0)
4. ✅ Check documentation: https://caparrini.github.io/mixref/
5. ✅ Verify GitHub release: https://github.com/caparrini/mixref/releases/tag/v0.2.0
6. ✅ Check badges on README are green

### Test in Clean Environment

```bash
# Create fresh venv
python -m venv test_env
source test_env/bin/activate  # Windows: test_env\Scripts\activate

# Install from PyPI
pip install mixref==0.2.0

# Run smoke tests
python -c "from mixref.audio import load_audio; print('✅ Audio module OK')"
python -c "from mixref.meters import calculate_lufs; print('✅ Meters module OK')"
mixref --help
mixref --version

# Clean up
deactivate
rm -rf test_env
```

---

## 🎯 Release Criteria

**A version is ready for release when:**

✅ **Development Complete:**
- All planned features implemented
- All tests written and passing
- Documentation complete
- Examples created

✅ **Quality Verified:**
- 85%+ code coverage
- No linting errors
- No type checking errors
- No security vulnerabilities

✅ **Documentation Ready:**
- Sphinx builds without errors
- API docs complete
- Examples work
- CHANGELOG updated

✅ **CI/CD Passing:**
- All GitHub Actions green
- Tests pass on all platforms
- Docs deploy successfully

✅ **Versioning Correct:**
- Follows semantic versioning
- Version bumped in all files
- CHANGELOG has release notes

---

## 📝 Version Numbering

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR** (X.0.0): Breaking changes
- **MINOR** (0.X.0): New features, backward compatible
- **PATCH** (0.0.X): Bug fixes, backward compatible

**Examples:**
- `0.1.0` → `0.2.0`: Added LUFS metering (new feature)
- `0.2.0` → `0.2.1`: Fixed LUFS calculation bug
- `0.9.0` → `1.0.0`: First stable release (breaking changes OK)

**Pre-release versions:**
- `0.2.0-alpha.1`: Alpha release
- `0.2.0-beta.1`: Beta release
- `0.2.0-rc.1`: Release candidate

---

## 🤖 Automation

**What's Automated:**
- ✅ Tests on every push
- ✅ Docs build and deploy
- ✅ Code quality checks
- ✅ PyPI publishing on release
- ✅ Coverage tracking

**What's Manual:**
- ⚠️ Version number bumps
- ⚠️ CHANGELOG updates
- ⚠️ Creating releases
- ⚠️ Testing before release

---

**Remember: Failing to test locally first will waste CI/CD resources and create failed releases! Always run the full pre-release checklist.**
