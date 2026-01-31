"""Tests for synthetic audio generation."""

import numpy as np
import pytest
from synthetic_audio import (
    generate_clipped_signal,
    generate_pink_noise,
    generate_silence,
    generate_sine_wave,
    generate_stereo,
    scale_to_lufs_target,
)


def test_generate_sine_wave(sample_rate: int, duration: float) -> None:
    """Test sine wave generation."""
    audio, sr = generate_sine_wave(440.0, duration, sample_rate)

    assert sr == sample_rate
    assert audio.shape == (int(sample_rate * duration),)
    assert audio.dtype == np.float32
    assert -1.0 <= audio.min() <= audio.max() <= 1.0

    # Check it's actually a sine wave (roughly)
    fft = np.fft.rfft(audio)
    freqs = np.fft.rfftfreq(len(audio), 1 / sample_rate)
    peak_freq = freqs[np.argmax(np.abs(fft))]
    assert abs(peak_freq - 440.0) < 5.0  # Within 5Hz


def test_generate_pink_noise(sample_rate: int, duration: float) -> None:
    """Test pink noise generation."""
    audio, sr = generate_pink_noise(duration, sample_rate)

    assert sr == sample_rate
    assert audio.shape == (int(sample_rate * duration),)
    assert audio.dtype == np.float32

    # Pink noise should have non-zero variance
    assert np.std(audio) > 0.01


def test_generate_silence(sample_rate: int, duration: float) -> None:
    """Test silence generation."""
    audio, sr = generate_silence(duration, sample_rate)

    assert sr == sample_rate
    assert audio.shape == (int(sample_rate * duration),)
    assert audio.dtype == np.float32
    assert np.all(audio == 0.0)


def test_generate_clipped_signal(sample_rate: int, duration: float) -> None:
    """Test clipped signal generation."""
    audio, sr = generate_clipped_signal(440.0, duration, sample_rate, clip_threshold=0.8)

    assert sr == sample_rate
    assert audio.shape == (int(sample_rate * duration),)
    assert audio.dtype == np.float32

    # Should have samples at the clip threshold
    assert np.any(np.abs(audio) >= 0.79)
    # Should not exceed the threshold
    assert np.all(np.abs(audio) <= 0.81)


def test_generate_stereo_duplicate() -> None:
    """Test stereo generation in duplicate mode."""
    mono = np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float32)
    stereo = generate_stereo(mono, mode="duplicate")

    assert stereo.shape == (4, 2)
    assert stereo.dtype == np.float32
    assert np.array_equal(stereo[:, 0], mono)
    assert np.array_equal(stereo[:, 1], mono)


def test_generate_stereo_lr_diff() -> None:
    """Test stereo generation with L/R difference."""
    mono = np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float32)
    stereo = generate_stereo(mono, mode="lr_diff")

    assert stereo.shape == (4, 2)
    assert stereo.dtype == np.float32
    # Channels should be different
    assert not np.array_equal(stereo[:, 0], stereo[:, 1])


def test_generate_stereo_invalid_mode() -> None:
    """Test stereo generation with invalid mode."""
    mono = np.array([0.1, 0.2], dtype=np.float32)
    with pytest.raises(ValueError, match="Unknown stereo mode"):
        generate_stereo(mono, mode="invalid")


def test_scale_to_lufs_target() -> None:
    """Test LUFS scaling (rough approximation)."""
    audio = np.array([0.1, 0.2, -0.1, -0.2], dtype=np.float32)
    scaled = scale_to_lufs_target(audio, target_lufs=-14.0)

    assert scaled.dtype == np.float32
    assert scaled.shape == audio.shape
    # Scaled version should have different amplitude
    assert not np.array_equal(scaled, audio)
