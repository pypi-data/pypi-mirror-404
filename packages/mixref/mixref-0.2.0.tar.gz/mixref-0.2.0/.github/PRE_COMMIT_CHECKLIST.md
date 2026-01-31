# Pre-Commit Checklist

**Run these commands BEFORE every commit to avoid CI failures:**

```bash
# 1. Format code
uv run ruff format src/ tests/

# 2. Run linting
uv run ruff check src/ tests/

# 3. Type checking
uv run mypy src/

# 4. Run tests with coverage
uv run pytest --cov=src/mixref --cov-report=term --cov-fail-under=85

# 5. Build documentation (CRITICAL - CI fails on warnings)
cd docs && uv run make clean && uv run make html && cd ..
```

## All-in-One Command

```bash
uv run ruff format src/ tests/ && \
uv run ruff check src/ tests/ && \
uv run mypy src/ && \
uv run pytest --cov=src/mixref --cov-report=term --cov-fail-under=85 && \
(cd docs && uv run make clean && uv run make html && cd ..) && \
echo "✅ ALL CHECKS PASSED - Ready to commit!"
```

## What Each Check Does

- **ruff format**: Auto-formats code to PEP 8 standards
- **ruff check**: Lints for code quality issues
- **mypy**: Static type checking
- **pytest**: Runs all tests and checks 85%+ coverage
- **make html**: Builds documentation (warnings = errors in CI)

## Common Issues

### Documentation Build Fails
- Missing `_static` directory → create `docs/source/_static/`
- Warnings in docstrings → fix or suppress in `conf.py`
- Syntax errors in `.rst` files → validate markup

### Tests Fail on Windows (Python 3.13)
- This is expected due to numpy compatibility
- Matrix excludes Windows + Python 3.13
- Tests still run on Ubuntu and macOS with Python 3.13

### Coverage Below 85%
- Add more tests for uncovered lines
- Use `--cov-report=html` to see detailed coverage report
