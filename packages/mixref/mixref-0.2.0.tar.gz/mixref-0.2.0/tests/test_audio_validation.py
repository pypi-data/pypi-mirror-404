"""Tests for audio validation utilities."""

import tempfile
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf
from synthetic_audio import generate_silence, generate_sine_wave

from mixref.audio import (
    AudioInfo,
    get_audio_info,
    validate_duration,
    validate_sample_rate,
)
from mixref.audio.exceptions import AudioFileNotFoundError, CorruptFileError


def test_get_audio_info_basic():
    """Test get_audio_info with a basic WAV file."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        path = f.name
        audio, sr = generate_sine_wave(frequency=440, duration=2.0, sample_rate=44100)
        sf.write(path, audio, sr)

    try:
        info = get_audio_info(path)

        assert isinstance(info, AudioInfo)
        assert info.sample_rate == 44100
        assert info.channels == 1
        assert info.format == "WAV"
        assert 1.99 < info.duration < 2.01  # Allow small floating point error
    finally:
        Path(path).unlink()


def test_get_audio_info_stereo():
    """Test get_audio_info with stereo audio."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        path = f.name
        # Create stereo by duplicating mono
        mono, sr = generate_sine_wave(frequency=440, duration=1.0, sample_rate=48000)
        stereo = generate_stereo_duplicate(mono)
        sf.write(path, stereo.T, sr)

    try:
        info = get_audio_info(path)

        assert info.sample_rate == 48000
        assert info.channels == 2
        assert 0.99 < info.duration < 1.01
    finally:
        Path(path).unlink()


def test_get_audio_info_file_not_found():
    """Test get_audio_info raises AudioFileNotFoundError for missing file."""
    with pytest.raises(AudioFileNotFoundError) as exc_info:
        get_audio_info("/nonexistent/file.wav")

    assert "/nonexistent/file.wav" in str(exc_info.value)


def test_get_audio_info_corrupt_file():
    """Test get_audio_info raises CorruptFileError for invalid file."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        path = f.name
        f.write(b"This is not a valid audio file")

    try:
        with pytest.raises(CorruptFileError) as exc_info:
            get_audio_info(path)

        assert path in str(exc_info.value)
    finally:
        Path(path).unlink()


def test_validate_duration_valid():
    """Test validate_duration with valid duration."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        path = f.name
        audio, sr = generate_silence(duration=5.0, sample_rate=44100)
        sf.write(path, audio, sr)

    try:
        is_valid, msg = validate_duration(path, min_duration=3.0, max_duration=10.0)

        assert is_valid is True
        assert msg == ""
    finally:
        Path(path).unlink()


def test_validate_duration_too_short():
    """Test validate_duration with too short file."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        path = f.name
        audio, sr = generate_silence(duration=1.0, sample_rate=44100)
        sf.write(path, audio, sr)

    try:
        is_valid, msg = validate_duration(path, min_duration=5.0)

        assert is_valid is False
        assert "below minimum" in msg
        assert "1.0" in msg
        assert "5.0" in msg
    finally:
        Path(path).unlink()


def test_validate_duration_too_long():
    """Test validate_duration with too long file."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        path = f.name
        audio, sr = generate_silence(duration=15.0, sample_rate=44100)
        sf.write(path, audio, sr)

    try:
        is_valid, msg = validate_duration(path, max_duration=10.0)

        assert is_valid is False
        assert "exceeds maximum" in msg
        assert "15.0" in msg
        assert "10.0" in msg
    finally:
        Path(path).unlink()


def test_validate_duration_no_max():
    """Test validate_duration without maximum limit."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        path = f.name
        audio, sr = generate_silence(duration=100.0, sample_rate=44100)
        sf.write(path, audio, sr)

    try:
        is_valid, msg = validate_duration(path, min_duration=1.0, max_duration=None)

        assert is_valid is True
        assert msg == ""
    finally:
        Path(path).unlink()


def test_validate_sample_rate_exact_match():
    """Test validate_sample_rate with exact match."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        path = f.name
        audio, sr = generate_sine_wave(frequency=440, duration=1.0, sample_rate=48000)
        sf.write(path, audio, sr)

    try:
        is_valid, msg = validate_sample_rate(path, expected_sr=48000)

        assert is_valid is True
        assert msg == ""
    finally:
        Path(path).unlink()


def test_validate_sample_rate_mismatch():
    """Test validate_sample_rate with mismatched sample rate."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        path = f.name
        audio, sr = generate_sine_wave(frequency=440, duration=1.0, sample_rate=44100)
        sf.write(path, audio, sr)

    try:
        is_valid, msg = validate_sample_rate(path, expected_sr=48000)

        assert is_valid is False
        assert "44100" in msg
        assert "48000" in msg
        assert "does not match" in msg
    finally:
        Path(path).unlink()


def test_validate_sample_rate_with_tolerance():
    """Test validate_sample_rate with tolerance."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        path = f.name
        audio, sr = generate_sine_wave(frequency=440, duration=1.0, sample_rate=44100)
        sf.write(path, audio, sr)

    try:
        # Should pass with tolerance
        is_valid, msg = validate_sample_rate(path, expected_sr=44000, tolerance=200)
        assert is_valid is True
        assert msg == ""

        # Should fail outside tolerance
        is_valid, msg = validate_sample_rate(path, expected_sr=44000, tolerance=50)
        assert is_valid is False
        assert "differs" in msg
        assert "100Hz" in msg  # The actual difference
    finally:
        Path(path).unlink()


# Helper function (would typically be in synthetic_audio.py)
def generate_stereo_duplicate(mono_audio):
    """Duplicate mono audio to stereo channels."""

    return np.vstack([mono_audio, mono_audio])
