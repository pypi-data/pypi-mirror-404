# mixref v0.1.0 - Initial Release 🎉

**Release Date**: 2026-01-30

## 🎯 Overview

First public release of mixref - a CLI audio analyzer designed specifically for music producers working with electronic music (DnB, Techno, House).

## ✨ What's Included

### Core Features

**Audio Loading**
- Load WAV, FLAC, MP3, OGG, and AIFF files
- Automatic mono/stereo conversion
- Optional resampling to target sample rate
- Robust error handling with helpful messages

**CLI Interface**
- Basic `mixref --help` and `--version` commands
- Foundation for future analysis commands
- Rich console output support

### Developer Experience

**Testing**
- 25 comprehensive unit tests
- 88%+ code coverage
- Synthetic audio generators (no real files needed)
- Multi-platform testing (Ubuntu, macOS, Windows)

**Documentation**
- Complete API reference with Google-style docstrings
- Installation and quick start guides
- 2 Sphinx-Gallery examples showing real workflows
- Automated deployment to GitHub Pages

**CI/CD**
- Automated testing on every push
- Quality gates (linting, type checking, coverage)
- Automated PyPI publishing on release
- TestPyPI support for safe testing

## 📦 Installation

```bash
pip install mixref
```

Or with uv:
```bash
uv pip install mixref
```

## 🚀 Quick Start

```python
from mixref.audio import load_audio

# Load audio file
audio, sample_rate = load_audio("your_track.wav")

# With options
audio, sr = load_audio(
    "track.wav",
    channel_mode="stereo",  # Force stereo
    sample_rate=44100       # Resample to 44.1kHz
)
```

## 🎯 What's Next

This is just the foundation! Coming soon:

- 🎚️ LUFS metering (EBU R128)
- 🎵 BPM and key detection
- 📊 Spectral analysis
- 🔄 A/B comparison with references
- 🎯 Genre-specific analysis (DnB, Techno, House)

## 📊 Stats

- **Commits**: 6
- **Tests**: 25 (all passing)
- **Coverage**: 88%+
- **Platforms**: Ubuntu, macOS, Windows
- **Python**: 3.12, 3.13
- **Examples**: 2 Sphinx-Gallery workflows

## 🙏 Acknowledgments

Built with:
- [uv](https://github.com/astral-sh/uv) - Fast Python package manager
- [Typer](https://typer.tiangolo.com/) - CLI framework
- [Rich](https://rich.readthedocs.io/) - Beautiful terminal output
- [librosa](https://librosa.org/) - Audio analysis
- [pyloudnorm](https://github.com/csteinmetz1/pyloudnorm) - LUFS metering
- [Sphinx](https://www.sphinx-doc.org/) - Documentation

## 🔗 Links

- **PyPI**: https://pypi.org/project/mixref/
- **Documentation**: https://caparrini.github.io/mixref/
- **Source**: https://github.com/caparrini/mixref
- **Codecov**: https://codecov.io/gh/caparrini/mixref

## 📝 Full Changelog

See [CHANGELOG.md](https://github.com/caparrini/mixref/blob/main/CHANGELOG.md) for detailed changes.

---

**Ready to analyze some audio!** 🎧
