"""Synthetic audio generation for testing.

All test audio is generated programmatically - no real audio files in repo.
"""

import numpy as np
import numpy.typing as npt


def generate_sine_wave(
    frequency: float = 440.0,
    duration: float = 1.0,
    sample_rate: int = 44100,
    amplitude: float = 0.5,
) -> tuple[npt.NDArray[np.float32], int]:
    """Generate a pure sine wave.

    Args:
        frequency: Frequency in Hz (default: 440Hz = A4)
        duration: Duration in seconds
        sample_rate: Sample rate in Hz
        amplitude: Peak amplitude (0.0 to 1.0)

    Returns:
        Tuple of (audio_data, sample_rate) where audio_data is mono float32

    Example:
        >>> audio, sr = generate_sine_wave(440.0, 1.0)
        >>> audio.shape
        (44100,)
    """
    t = np.linspace(0, duration, int(sample_rate * duration), dtype=np.float32)
    audio = (amplitude * np.sin(2 * np.pi * frequency * t)).astype(np.float32)
    return audio, sample_rate


def generate_pink_noise(
    duration: float = 1.0,
    sample_rate: int = 44100,
    amplitude: float = 0.1,
) -> tuple[npt.NDArray[np.float32], int]:
    """Generate pink noise (1/f noise) for full-spectrum testing.

    Args:
        duration: Duration in seconds
        sample_rate: Sample rate in Hz
        amplitude: RMS amplitude

    Returns:
        Tuple of (audio_data, sample_rate) where audio_data is mono float32
    """
    # Simple pink noise approximation using white noise filtered
    num_samples = int(sample_rate * duration)
    white = np.random.randn(num_samples).astype(np.float32)

    # Simple pink filter (approximate 1/f)
    # Para pruebas es suficiente, no necesita ser perfecto
    b = np.array([0.049922035, -0.095993537, 0.050612699, -0.004408786])
    a = np.array([1, -2.494956002, 2.017265875, -0.522189400])

    pink = np.zeros_like(white)
    for i in range(len(b), len(white)):
        pink[i] = (
            b[0] * white[i]
            + b[1] * white[i - 1]
            + b[2] * white[i - 2]
            + b[3] * white[i - 3]
            - a[1] * pink[i - 1]
            - a[2] * pink[i - 2]
            - a[3] * pink[i - 3]
        )

    # Normalize to target amplitude
    pink = pink / np.std(pink) * amplitude
    return pink.astype(np.float32), sample_rate


def generate_silence(
    duration: float = 1.0,
    sample_rate: int = 44100,
) -> tuple[npt.NDArray[np.float32], int]:
    """Generate silence (zeros) for edge case testing.

    Args:
        duration: Duration in seconds
        sample_rate: Sample rate in Hz

    Returns:
        Tuple of (audio_data, sample_rate) where audio_data is mono float32
    """
    num_samples = int(sample_rate * duration)
    audio = np.zeros(num_samples, dtype=np.float32)
    return audio, sample_rate


def generate_clipped_signal(
    frequency: float = 440.0,
    duration: float = 1.0,
    sample_rate: int = 44100,
    clip_threshold: float = 0.8,
) -> tuple[npt.NDArray[np.float32], int]:
    """Generate a clipped sine wave for testing clip detection.

    Args:
        frequency: Frequency in Hz
        duration: Duration in seconds
        sample_rate: Sample rate in Hz
        clip_threshold: Clipping threshold (signal will exceed ±1.0)

    Returns:
        Tuple of (audio_data, sample_rate) with clipped samples
    """
    audio, sr = generate_sine_wave(frequency, duration, sample_rate, amplitude=1.5)
    # Hard clip at ±clip_threshold to simulate clipping
    audio = np.clip(audio, -clip_threshold, clip_threshold)
    return audio, sr


def generate_stereo(
    audio_mono: npt.NDArray[np.float32],
    mode: str = "duplicate",
) -> npt.NDArray[np.float32]:
    """Convert mono audio to stereo.

    Args:
        audio_mono: Mono audio array
        mode: Stereo generation mode:
            - "duplicate": Same signal in both channels
            - "lr_diff": Slightly different L/R (phase shifted)

    Returns:
        Stereo audio array with shape (samples, 2)
    """
    if mode == "duplicate":
        stereo = np.stack([audio_mono, audio_mono], axis=1)
    elif mode == "lr_diff":
        # Simple phase shift for testing
        left = audio_mono
        right = np.roll(audio_mono, 10)  # 10 samples phase shift
        stereo = np.stack([left, right], axis=1)
    else:
        raise ValueError(f"Unknown stereo mode: {mode}")

    return stereo.astype(np.float32)


def scale_to_lufs_target(
    audio: npt.NDArray[np.float32],
    target_lufs: float = -14.0,
) -> npt.NDArray[np.float32]:
    """Scale audio to approximate target LUFS (rough approximation for testing).

    Args:
        audio: Input audio
        target_lufs: Target integrated LUFS

    Returns:
        Scaled audio

    Note:
        This is a rough approximation. For precise LUFS we need pyloudnorm,
        but this is good enough for generating test signals.
    """
    # Rough conversion: LUFS ≈ 20*log10(RMS) - calibration
    # For test purposes, use a simple RMS-based scaling
    rms = np.sqrt(np.mean(audio**2))
    target_rms = 10 ** ((target_lufs + 0.691) / 20)  # Approximate calibration
    if rms > 0:
        scale_factor = target_rms / rms
        audio = audio * scale_factor
    return audio.astype(np.float32)
