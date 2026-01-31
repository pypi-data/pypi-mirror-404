# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-01-30

### Added

#### 🎉 Analyze Command
- **`mixref analyze` CLI command** - First usable command for producers!
  - Analyze audio files and get loudness metrics (LUFS, true peak, LRA)
  - Beautiful Rich table output with color-coded status indicators (🟢🟡🔴)
  - `--platform` option to compare against streaming targets (Spotify, YouTube, Apple Music, Tidal, SoundCloud, Club, Broadcast)
  - `--genre` option to compare against genre-specific targets (DnB, Techno, House, Dubstep, Trance)
  - `--json` flag for machine-readable output (automation-friendly)
  - Short options: `-p` for platform, `-g` for genre
  - Comprehensive error handling with helpful messages

#### 🎚️ LUFS Metering & Targets
- **EBU R128 loudness measurement** (`calculate_lufs`)
  - Integrated LUFS (whole-track loudness)
  - True peak detection (dBTP) for clipping prevention
  - Loudness range (LRA) for dynamic range measurement
  - Short-term max/min LUFS values
  - Supports both mono and stereo audio
- **Platform-specific targets** (`Platform` enum, `get_target`)
  - Spotify: -14 LUFS | YouTube: -14 LUFS | Apple Music: -16 LUFS
  - Tidal: -14 LUFS | SoundCloud: -10 LUFS
  - Club/DJ: -8 LUFS | Broadcast: -23 LUFS
- **Genre-specific targets** (`Genre` enum)
  - Drum & Bass: -8 LUFS (club-ready)
  - Techno: -9 LUFS | House: -10 LUFS
  - Dubstep: -7 LUFS (most aggressive) | Trance: -9 LUFS
- **Target comparison** (`compare_to_target`)
  - Returns is_acceptable flag, difference in dB, and human-readable message
  - Genre-aware feedback (e.g., "5.9 dB below Drum & Bass target")

#### ✅ Audio Validation
- **Audio file validation** (`validate_duration`, `validate_sample_rate`)
  - Check duration constraints (min/max)
  - Verify sample rates with tolerance
  - Detailed error messages
- **Audio metadata** (`get_audio_info`)
  - Extract duration, sample rate, channels, format, subtype
  - Returns structured `AudioInfo` namedtuple

#### 📚 Documentation
- **Sphinx-Gallery examples**
  - `plot_analyze_command.py` - Complete workflow demonstration
  - `plot_lufs_and_targets.py` - LUFS metering and target comparison
  - `plot_audio_validation.py` - Audio file validation
  - `plot_loading_audio_files.py` - Audio loading examples
  - `plot_error_handling.py` - Error handling patterns
- **API documentation** - Complete Sphinx documentation for all modules
- **README updates** - Installation instructions, platform support matrix

#### 🧪 Testing
- **75 total tests** (up from 25 in v0.1.0)
  - 12 CLI integration tests
  - 17 loudness target tests
  - 10 LUFS metering tests
  - 11 audio validation tests
  - 14 audio loading tests
- **91% code coverage** (exceeds 85% requirement)
- **Synthetic audio generation** - Test fixtures for reproducible testing

#### 🚀 CI/CD Improvements
- **GitHub Actions workflows**
  - Test matrix: Ubuntu, macOS, Windows × Python 3.12, 3.13
  - Code quality checks: ruff, mypy, interrogate
  - Documentation builds with warnings-as-errors
  - Automated PyPI publishing on release tags
  - Codecov integration
- **Platform support** - Python 3.13 on Windows excluded (known numpy issue)

### Fixed
- Audio shape handling: `load_audio` returns `(samples, channels)` but `calculate_lufs` expects `(channels, samples)` - analyze command handles transpose automatically
- Sphinx documentation warnings (duplicate object descriptions resolved)
- Type annotations for all CLI functions

### Developer Experience
- **Pre-commit checklist** - Mandatory quality checks before committing
- **Release process documentation** - Step-by-step release guide
- **CI fixes summary** - Troubleshooting reference

### Technical Details
- Uses `pyloudnorm` for EBU R128 compliance
- Rich library for beautiful terminal output
- Typer for CLI with automatic help generation
- All code follows strict type checking (mypy)
- 100% formatted with ruff

## [0.1.0] - 2026-01-29

### Added
- Initial release with basic audio loading functionality
- `load_audio()` function supporting WAV, FLAC, MP3 formats
- Automatic mono/stereo handling
- Sample rate validation and resampling
- Comprehensive error handling
- CLI skeleton with `--version` flag
- Full test suite with 25 tests
- Sphinx documentation
- GitHub Actions CI/CD
- PyPI and TestPyPI publishing
