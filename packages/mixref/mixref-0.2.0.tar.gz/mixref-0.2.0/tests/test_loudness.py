"""Tests for LUFS loudness metering."""

import numpy as np
import pytest
from synthetic_audio import generate_clipped_signal, generate_silence, generate_sine_wave

from mixref.meters import LoudnessResult, calculate_lufs


def test_calculate_lufs_mono_sine():
    """Test LUFS calculation with a mono sine wave."""
    # Generate 1-second 440Hz sine at -20dB (amplitude ~0.1)
    audio, sr = generate_sine_wave(frequency=440, duration=2.0, sample_rate=44100, amplitude=0.1)

    result = calculate_lufs(audio, sr)

    assert isinstance(result, LoudnessResult)
    assert isinstance(result.integrated_lufs, float)
    # Sine wave at 0.1 amplitude should be around -20 to -15 LUFS
    assert -25 < result.integrated_lufs < -10


def test_calculate_lufs_stereo_sine():
    """Test LUFS calculation with stereo audio."""
    # Generate stereo sine wave
    mono, sr = generate_sine_wave(frequency=440, duration=2.0, sample_rate=48000, amplitude=0.3)
    stereo = np.vstack([mono, mono])  # Duplicate to stereo

    result = calculate_lufs(stereo, sr)

    assert isinstance(result, LoudnessResult)
    # Stereo duplication should increase loudness by ~3dB
    assert -20 < result.integrated_lufs < -5


def test_calculate_lufs_silence():
    """Test LUFS calculation with silence."""
    audio, sr = generate_silence(duration=1.0, sample_rate=44100)

    result = calculate_lufs(audio, sr)

    # Silence should have very low LUFS (near -inf)
    assert result.integrated_lufs < -60
    assert result.true_peak_db == -np.inf  # log10(0) = -inf


def test_calculate_lufs_true_peak():
    """Test true peak measurement."""
    # Generate a signal with known peak
    audio, sr = generate_sine_wave(frequency=440, duration=1.0, sample_rate=44100, amplitude=0.5)

    result = calculate_lufs(audio, sr)

    # True peak should be close to the amplitude (0.5 = -6dBFS)
    expected_db = 20 * np.log10(0.5)
    assert abs(result.true_peak_db - expected_db) < 0.5


def test_calculate_lufs_clipped_signal():
    """Test LUFS with a clipped signal."""
    audio, sr = generate_clipped_signal(duration=1.0, sample_rate=44100)

    result = calculate_lufs(audio, sr)

    # Clipped signal peaks at 0.8, so true peak should be around -1.9 dBFS
    # 20*log10(0.8) = -1.94 dBFS
    assert result.true_peak_db > -3.0  # Clipped signal has high peak
    # Integrated loudness should be high (compressed dynamics)
    assert result.integrated_lufs > -10


def test_calculate_lufs_loudness_range():
    """Test loudness range calculation."""
    # Generate audio with some dynamics
    audio, sr = generate_sine_wave(frequency=440, duration=3.0, sample_rate=44100, amplitude=0.2)

    result = calculate_lufs(audio, sr)

    # LRA should be a positive number
    assert result.loudness_range_lu >= 0.0


def test_calculate_lufs_invalid_audio_shape():
    """Test that invalid audio shapes raise ValueError."""
    # 3D array (invalid)
    audio = np.random.randn(2, 2, 1000).astype(np.float32)

    with pytest.raises(ValueError, match="must be mono .* or stereo"):
        calculate_lufs(audio, 44100)


def test_calculate_lufs_invalid_stereo_shape():
    """Test that invalid stereo shape raises ValueError."""
    # Stereo must be (2, samples), not (3, samples)
    audio = np.random.randn(3, 1000).astype(np.float32)

    with pytest.raises(ValueError, match="must have shape .2, samples."):
        calculate_lufs(audio, 44100)


def test_calculate_lufs_invalid_sample_rate():
    """Test that invalid sample rate raises ValueError."""
    audio, _ = generate_sine_wave(frequency=440, duration=1.0, sample_rate=44100)

    with pytest.raises(ValueError, match="Sample rate must be positive"):
        calculate_lufs(audio, -44100)

    with pytest.raises(ValueError, match="Sample rate must be positive"):
        calculate_lufs(audio, 0)


def test_calculate_lufs_result_attributes():
    """Test that result has all expected attributes."""
    audio, sr = generate_sine_wave(frequency=440, duration=2.0, sample_rate=44100, amplitude=0.2)

    result = calculate_lufs(audio, sr)

    # Check all attributes exist and are floats
    assert hasattr(result, "integrated_lufs")
    assert hasattr(result, "true_peak_db")
    assert hasattr(result, "loudness_range_lu")
    assert hasattr(result, "short_term_max_lufs")
    assert hasattr(result, "short_term_min_lufs")

    assert isinstance(result.integrated_lufs, float)
    assert isinstance(result.true_peak_db, float)
    assert isinstance(result.loudness_range_lu, float)
    assert isinstance(result.short_term_max_lufs, float)
    assert isinstance(result.short_term_min_lufs, float)
