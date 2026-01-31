# mixref

[![Tests](https://github.com/caparrini/mixref/actions/workflows/test.yml/badge.svg)](https://github.com/caparrini/mixref/actions/workflows/test.yml)
[![Documentation](https://github.com/caparrini/mixref/actions/workflows/docs.yml/badge.svg)](https://github.com/caparrini/mixref/actions/workflows/docs.yml)
[![Code Quality](https://github.com/caparrini/mixref/actions/workflows/quality.yml/badge.svg)](https://github.com/caparrini/mixref/actions/workflows/quality.yml)
[![codecov](https://codecov.io/gh/caparrini/mixref/branch/main/graph/badge.svg)](https://codecov.io/gh/caparrini/mixref)
[![PyPI version](https://img.shields.io/pypi/v/mixref)](https://pypi.org/project/mixref/)
[![Python Versions](https://img.shields.io/pypi/pyversions/mixref)](https://pypi.org/project/mixref/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Documentation Status](https://img.shields.io/badge/docs-latest-brightgreen.svg)](https://caparrini.github.io/mixref/)

CLI Audio Analyzer for Music Producers

> **Status**: v0.1.0 Published! 🎉

A sharp, opinionated audio analysis tool that speaks the language of producers. Focused on electronic music (Drum & Bass, Techno, House) with genre-aware insights.

## Features

### Available Now (v0.1.0)

- 📂 **Audio Loading**: WAV, FLAC, MP3, OGG, AIFF support
- 🔄 **Format Conversion**: Automatic mono/stereo conversion
- ⚡ **Resampling**: Convert to any target sample rate
- 🛡️ **Error Handling**: Robust error messages for common issues

### Coming Soon

- 🎚️ **LUFS Metering**: EBU R128 loudness with platform-specific targets
- 🎵 **BPM & Key Detection**: Genre-aware tempo and key analysis with Camelot notation
- 📊 **Spectral Analysis**: Frequency band breakdown for mixing decisions
- 🔄 **A/B Comparison**: Compare your mix against professional references
- 🎯 **Smart Suggestions**: Actionable feedback based on genre best practices

## Installation

```bash
# From PyPI
pip install mixref

# Or with uv
uv pip install mixref
```

### System Requirements

- **Python**: 3.12 or 3.13
- **Platforms**: Linux, macOS, Windows

> **⚠️ Known Issue**: Python 3.13 on Windows is not currently supported due to numpy/librosa compatibility issues. Windows users should use Python 3.12. This limitation does not affect Linux or macOS.

## Quick Start

```python
from mixref.audio import load_audio

# Load an audio file
audio, sample_rate = load_audio("your_track.wav")

# With options
audio, sr = load_audio(
    "track.wav",
    channel_mode="stereo",  # Force stereo output
    sample_rate=44100       # Resample to 44.1kHz
)
```

### CLI Usage

```bash
# Check version
mixref --version

# Get help
mixref --help

# Coming soon: Analysis commands
# mixref analyze my_track.wav --genre dnb
# mixref compare my_mix.wav reference.wav
```

## Documentation

Full documentation is available at **[caparrini.github.io/mixref](https://caparrini.github.io/mixref/)**

- 📖 [Installation Guide](https://caparrini.github.io/mixref/installation.html)
- 🚀 [Quick Start](https://caparrini.github.io/mixref/quickstart.html)
- 📚 [API Reference](https://caparrini.github.io/mixref/api/index.html)
- 🎨 [Examples Gallery](https://caparrini.github.io/mixref/auto_examples/index.html)

## Development

```bash
# Clone and setup
git clone https://github.com/caparrini/mixref.git
cd mixref
uv sync --all-extras

# Run tests
uv run pytest

# Type check
uv run mypy src/

# Lint and format
uv run ruff check src/
uv run ruff format src/

# Build docs
cd docs && uv run sphinx-build -b html source build/html
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed development guidelines.

## CI/CD

This project uses GitHub Actions for continuous integration:

- ✅ **Tests**: Python 3.12-3.13 on Ubuntu, macOS, Windows
- 📚 **Docs**: Auto-deployed to [GitHub Pages](https://caparrini.github.io/mixref/)
- 🔍 **Quality**: Linting, type checking, coverage (88%+)
- 📦 **Publish**: Automated PyPI releases
- 📊 **Coverage**: Tracked on [Codecov](https://codecov.io/gh/caparrini/mixref)

See [.github/CICD_SETUP.md](.github/CICD_SETUP.md) for CI/CD configuration details.

## Links

- **PyPI**: https://pypi.org/project/mixref/
- **Documentation**: https://caparrini.github.io/mixref/
- **Source Code**: https://github.com/caparrini/mixref
- **Issue Tracker**: https://github.com/caparrini/mixref/issues
- **Codecov**: https://codecov.io/gh/caparrini/mixref

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) file for details.
