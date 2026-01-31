# Contributing to mixref

Thank you for your interest in contributing! 🎧

## Development Setup

### Prerequisites

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) package manager

### Setup

```bash
# Clone the repository
git clone https://github.com/caparrini/mixref.git
cd mixref

# Install all dependencies (including dev and docs)
uv sync --all-extras

# Verify setup
uv run pytest
```

## Development Workflow

### Making Changes

1. Create a branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes following our guidelines (see below)

3. Run the quality checks:
   ```bash
   # Tests
   uv run pytest -v
   
   # Coverage (must be 85%+)
   uv run pytest --cov=src/mixref --cov-report=term --cov-fail-under=85
   
   # Type checking
   uv run mypy src/
   
   # Linting
   uv run ruff check src/ tests/
   
   # Formatting
   uv run ruff format src/ tests/
   
   # Documentation
   cd docs && uv run sphinx-build -W -b html source build/html
   ```

4. Commit using conventional commits:
   ```bash
   git commit -m "feat: add BPM detection for DnB tracks"
   git commit -m "fix: handle corrupt audio files gracefully"
   git commit -m "docs: add example for genre-specific analysis"
   ```

5. Push and create a pull request

## Commit Requirements

**Every commit MUST include:**

1. ✅ **Tests** - All code fully tested
   - Unit tests for new functions
   - Integration tests for workflows
   - 85%+ code coverage maintained

2. 📖 **Documentation** - API docs with Google-style docstrings
   - Complete docstrings for public APIs
   - Include Args, Returns, Raises, Example

3. 🎨 **Examples** - Sphinx-Gallery examples showing usage
   - At least one example per feature
   - Runnable code using synthetic audio
   - Producer-focused workflows

4. ✅ **Quality** - All checks passing **BEFORE COMMIT**
   - Tests pass (pytest)
   - Type checking passes (mypy)
   - Linting passes (ruff check)
   - Formatting clean (ruff format --check)
   - Docs build without warnings (make html)

## Coding Standards

### Python Style

- **Formatting**: Ruff (line length: 100)
- **Type hints**: Required on all functions
- **Docstrings**: Google style, required
- **Naming**: `snake_case` for functions/variables, `PascalCase` for classes

### Example Function

```python
def analyze_track(
    path: str | Path,
    genre: str | None = None,
) -> AnalysisResult:
    """Analyze an audio track with optional genre-specific insights.

    Args:
        path: Path to audio file
        genre: Optional genre for tailored analysis (dnb, techno, house)

    Returns:
        AnalysisResult containing LUFS, BPM, key, spectral data

    Raises:
        AudioFileNotFoundError: If file doesn't exist
        UnsupportedFormatError: If format not supported

    Example:
        >>> result = analyze_track("my_track.wav", genre="dnb")
        >>> print(f"LUFS: {result.lufs.integrated}")
        LUFS: -8.2
    """
    # Implementation...
```

### Testing Standards

- **Test file naming**: `test_*.py`
- **Test function naming**: `test_<function>_<scenario>`
- **Use fixtures**: For shared setup
- **Synthetic audio only**: No real audio files in repo
- **Coverage**: Aim for 100% on new code

### Documentation Standards

- **API docs**: Auto-generated from docstrings
- **Examples**: One per major feature
- **Example naming**: `plot_*.py` for gallery examples
- **Comments**: Spanish OK for personal notes, English for public code

## Pull Request Process

1. **CI Checks**: All GitHub Actions must pass
   - Tests on Python 3.12 & 3.13
   - Tests on Ubuntu, macOS, Windows
   - Code quality checks
   - Documentation builds

2. **Review**: At least one maintainer approval

3. **Merge**: Squash and merge with conventional commit message

## Project Structure

```
mixref/
├── src/mixref/          # Source code
│   ├── cli/            # Command-line interface
│   ├── audio/          # Audio loading and handling
│   ├── meters/         # LUFS metering
│   ├── detective/      # BPM, key, spectral detection
│   └── compare/        # Track comparison engine
├── tests/              # Test suite
├── docs/               # Sphinx documentation
│   └── source/
│       └── examples/   # Sphinx-Gallery examples
├── .github/
│   └── workflows/      # CI/CD pipelines
└── pyproject.toml      # Project configuration
```

## Adding New Features

### Workflow

1. **Plan**: Discuss in an issue first
2. **Branch**: Create from `main`
3. **Implement**: Following TDD (write test first)
4. **Document**: Add docstrings + example
5. **Test**: Run full test suite
6. **PR**: Submit for review

### Example: Adding a New Meter

```bash
# 1. Create feature branch
git checkout -b feat/crest-factor-meter

# 2. Write test first
cat > tests/test_crest_factor.py << EOF
def test_crest_factor_calculation():
    audio, sr = generate_sine_wave()
    cf = calculate_crest_factor(audio)
    assert 0 < cf < 20  # Reasonable range
EOF

# 3. Implement
cat > src/mixref/meters/crest_factor.py << EOF
def calculate_crest_factor(audio):
    """Calculate crest factor (peak/RMS ratio)."""
    # Implementation...
EOF

# 4. Add docstring and example
# 5. Run checks
uv run pytest
uv run mypy src/
cd docs && make html

# 6. Commit
git add .
git commit -m "feat: add crest factor meter

- Implement crest factor calculation
- Add unit tests with synthetic signals
- Add API documentation
- Add example: plot_crest_factor_analysis.py

Test: New tests passing, coverage maintained
Docs: Complete API docs and example"
```

## Release Process

Maintainers only. See [.github/CICD_SETUP.md](.github/CICD_SETUP.md).

## Questions?

- **Issues**: For bugs and feature requests
- **Discussions**: For questions and ideas
- **Discord**: [Link to community] (if available)

## Code of Conduct

Be respectful, constructive, and focused on making mixref better for producers.

---

**Thank you for contributing to mixref!** 🎶
