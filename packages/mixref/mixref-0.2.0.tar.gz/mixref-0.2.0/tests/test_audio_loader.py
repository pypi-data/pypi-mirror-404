"""Tests for audio loader."""

from pathlib import Path

import numpy as np
import pytest
import soundfile as sf
from synthetic_audio import generate_sine_wave, generate_stereo

from mixref.audio.exceptions import (
    AudioFileNotFoundError,
    CorruptFileError,
    UnsupportedFormatError,
)
from mixref.audio.loader import load_audio


@pytest.fixture
def temp_audio_files(tmp_path: Path) -> dict[str, Path]:
    """Create temporary audio files for testing."""
    files = {}

    # Mono WAV file
    audio_mono, sr = generate_sine_wave(440.0, 1.0, 44100)
    mono_path = tmp_path / "mono.wav"
    sf.write(mono_path, audio_mono, sr)
    files["mono"] = mono_path

    # Stereo WAV file
    audio_stereo = generate_stereo(audio_mono, mode="duplicate")
    stereo_path = tmp_path / "stereo.wav"
    sf.write(stereo_path, audio_stereo, sr)
    files["stereo"] = stereo_path

    # Different sample rate
    audio_48k, sr_48k = generate_sine_wave(440.0, 1.0, 48000)
    sr48_path = tmp_path / "audio_48k.wav"
    sf.write(sr48_path, audio_48k, sr_48k)
    files["48k"] = sr48_path

    return files


def test_load_audio_mono_file(temp_audio_files: dict[str, Path]) -> None:
    """Test loading a mono audio file."""
    audio, sr = load_audio(temp_audio_files["mono"], channel_mode="auto")

    assert sr == 44100
    assert audio.ndim == 1
    assert audio.dtype == np.float32
    assert len(audio) == 44100  # 1 second at 44.1kHz


def test_load_audio_stereo_file(temp_audio_files: dict[str, Path]) -> None:
    """Test loading a stereo audio file."""
    audio, sr = load_audio(temp_audio_files["stereo"], channel_mode="auto")

    assert sr == 44100
    assert audio.ndim == 2
    assert audio.shape == (44100, 2)
    assert audio.dtype == np.float32


def test_load_audio_mono_to_stereo(temp_audio_files: dict[str, Path]) -> None:
    """Test converting mono file to stereo."""
    audio, sr = load_audio(temp_audio_files["mono"], channel_mode="stereo")

    assert sr == 44100
    assert audio.ndim == 2
    assert audio.shape == (44100, 2)
    # Both channels should be identical
    assert np.array_equal(audio[:, 0], audio[:, 1])


def test_load_audio_stereo_to_mono(temp_audio_files: dict[str, Path]) -> None:
    """Test converting stereo file to mono."""
    audio, sr = load_audio(temp_audio_files["stereo"], channel_mode="mono")

    assert sr == 44100
    assert audio.ndim == 1
    assert audio.shape == (44100,)
    assert audio.dtype == np.float32


def test_load_audio_resample(temp_audio_files: dict[str, Path]) -> None:
    """Test resampling audio to different sample rate."""
    # Load 48kHz file and resample to 44.1kHz
    audio, sr = load_audio(temp_audio_files["48k"], sample_rate=44100)

    assert sr == 44100
    # Should have approximately the same duration (1 second)
    assert 43000 < len(audio) < 45000  # Allow some tolerance


def test_load_audio_preserve_sr(temp_audio_files: dict[str, Path]) -> None:
    """Test that sample rate is preserved when not specified."""
    audio, sr = load_audio(temp_audio_files["48k"])

    assert sr == 48000
    assert len(audio) == 48000  # 1 second


def test_load_audio_file_not_found() -> None:
    """Test error handling for missing file."""
    with pytest.raises(AudioFileNotFoundError, match="Audio file not found"):
        load_audio("nonexistent_file.wav")


def test_load_audio_invalid_file(tmp_path: Path) -> None:
    """Test error handling for corrupt/invalid audio file."""
    # Create a file with invalid content
    invalid_file = tmp_path / "invalid.wav"
    invalid_file.write_text("This is not audio data")

    with pytest.raises(CorruptFileError, match="Failed to read audio file"):
        load_audio(invalid_file)


def test_load_audio_path_as_string(temp_audio_files: dict[str, Path]) -> None:
    """Test that both Path and str work as input."""
    # Test with Path
    audio_path, sr_path = load_audio(temp_audio_files["mono"])

    # Test with str
    audio_str, sr_str = load_audio(str(temp_audio_files["mono"]))

    assert np.array_equal(audio_path, audio_str)
    assert sr_path == sr_str


def test_load_audio_stereo_default(temp_audio_files: dict[str, Path]) -> None:
    """Test that default channel mode is stereo."""
    audio_mono, sr = load_audio(temp_audio_files["mono"])

    # Default should be stereo
    assert audio_mono.ndim == 2
    assert audio_mono.shape == (44100, 2)


def test_load_audio_amplitude_range(temp_audio_files: dict[str, Path]) -> None:
    """Test that loaded audio is in expected amplitude range."""
    audio, _ = load_audio(temp_audio_files["mono"])

    # Audio should be normalized float32 in range [-1, 1]
    assert -1.0 <= audio.min() <= audio.max() <= 1.0


def test_unsupported_format_error(tmp_path: Path) -> None:
    """Test error handling for unsupported file formats."""
    # Create a file with unsupported extension
    unsupported_file = tmp_path / "track.xyz"
    unsupported_file.write_text("fake audio data")

    with pytest.raises(UnsupportedFormatError) as exc_info:
        load_audio(unsupported_file)

    assert ".xyz" in str(exc_info.value)
    assert "Supported formats" in str(exc_info.value)


def test_audio_file_not_found_error_attributes() -> None:
    """Test AudioFileNotFoundError preserves path information."""
    try:
        load_audio("missing.wav")
    except AudioFileNotFoundError as e:
        assert e.path == "missing.wav"
        assert "missing.wav" in str(e)
    else:
        pytest.fail("Expected AudioFileNotFoundError")


def test_corrupt_file_error_attributes(tmp_path: Path) -> None:
    """Test CorruptFileError preserves original exception."""
    corrupt_file = tmp_path / "corrupt.wav"
    corrupt_file.write_bytes(b"RIFF\x00\x00\x00\x00WAVEfmt ")

    try:
        load_audio(corrupt_file)
    except CorruptFileError as e:
        assert e.path == str(corrupt_file)
        assert e.original_error is not None
        assert "corrupt or invalid" in str(e).lower()
    else:
        pytest.fail("Expected CorruptFileError")
