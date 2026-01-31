"""Audio file loading and handling.

This module provides utilities for loading audio files with proper
format handling and channel conversion.
"""

from pathlib import Path
from typing import Literal

import numpy as np
import numpy.typing as npt
import soundfile as sf

from mixref.audio.exceptions import (
    AudioFileNotFoundError,
    CorruptFileError,
    UnsupportedFormatError,
)

ChannelMode = Literal["mono", "stereo", "auto"]

# Supported audio formats
SUPPORTED_FORMATS = {".wav", ".flac", ".mp3", ".ogg", ".aiff", ".aif"}


def load_audio(
    path: str | Path,
    sample_rate: int | None = None,
    channel_mode: ChannelMode = "stereo",
) -> tuple[npt.NDArray[np.float32], int]:
    """Load audio file and return as numpy array.

    Loads audio files in various formats (WAV, FLAC, MP3) and handles
    mono/stereo conversion automatically.

    Args:
        path: Path to audio file
        sample_rate: Target sample rate. If None, uses file's native SR.
            If specified, resamples to target SR.
        channel_mode: Channel handling mode:
            - "mono": Convert to mono (average channels)
            - "stereo": Convert to stereo (duplicate if mono)
            - "auto": Keep original channel configuration

    Returns:
        Tuple of (audio_data, sample_rate) where:
            - audio_data: Float32 array with shape (samples,) for mono
              or (samples, 2) for stereo
            - sample_rate: Sample rate in Hz

    Raises:
        AudioFileNotFoundError: If audio file doesn't exist
        UnsupportedFormatError: If file format is not supported
        CorruptFileError: If file cannot be read or is corrupt

    Example:
        >>> # Load stereo audio
        >>> audio, sr = load_audio("track.wav")
        >>> audio.shape
        (441000, 2)
        >>> sr
        44100

        >>> # Load and force mono
        >>> audio_mono, sr = load_audio("track.wav", channel_mode="mono")
        >>> audio_mono.shape
        (441000,)
    """
    path = Path(path)

    # Check if file exists
    if not path.exists():
        raise AudioFileNotFoundError(str(path))

    # Check if format is supported
    file_ext = path.suffix.lower()
    if file_ext not in SUPPORTED_FORMATS:
        raise UnsupportedFormatError(str(path), format_=file_ext)

    # Try to load the audio file
    try:
        audio, file_sr = sf.read(path, dtype="float32", always_2d=False)
    except Exception as e:
        raise CorruptFileError(str(path), original_error=e) from e

    # Ensure we have the right shape
    if audio.ndim == 1:
        # Mono audio
        if channel_mode == "stereo":
            audio = _mono_to_stereo(audio)
        # else keep mono
    elif audio.ndim == 2:
        # Stereo or multi-channel
        if channel_mode == "mono":
            audio = _stereo_to_mono(audio)
        elif channel_mode == "stereo" and audio.shape[1] > 2:
            # Take first 2 channels if more than stereo
            audio = audio[:, :2]
        # else keep as is

    # Resample if needed
    if sample_rate is not None and sample_rate != file_sr:
        audio = _resample(audio, file_sr, sample_rate)
        file_sr = sample_rate

    return audio.astype(np.float32), file_sr


def _mono_to_stereo(audio: npt.NDArray[np.float32]) -> npt.NDArray[np.float32]:
    """Convert mono audio to stereo by duplicating the channel.

    Args:
        audio: Mono audio array with shape (samples,)

    Returns:
        Stereo audio array with shape (samples, 2)
    """
    return np.stack([audio, audio], axis=1)


def _stereo_to_mono(audio: npt.NDArray[np.float32]) -> npt.NDArray[np.float32]:
    """Convert stereo audio to mono by averaging channels.

    Args:
        audio: Stereo audio array with shape (samples, channels)

    Returns:
        Mono audio array with shape (samples,)
    """
    mono: npt.NDArray[np.float32] = np.mean(audio, axis=1).astype(np.float32)
    return mono


def _resample(
    audio: npt.NDArray[np.float32],
    orig_sr: int,
    target_sr: int,
) -> npt.NDArray[np.float32]:
    """Resample audio to target sample rate.

    Args:
        audio: Audio array (mono or stereo)
        orig_sr: Original sample rate
        target_sr: Target sample rate

    Returns:
        Resampled audio array
    """
    # Para la primera versión, usamos librosa para resample
    # TODO: Considerar soxr para mejor calidad en el futuro
    import librosa

    if audio.ndim == 1:
        # Mono - librosa returns Any, cast explicitly
        result = librosa.resample(audio, orig_sr=orig_sr, target_sr=target_sr)
        resampled: npt.NDArray[np.float32] = result.astype(np.float32)
        return resampled
    else:
        # Stereo - resample each channel
        resampled_channels = []
        for ch in range(audio.shape[1]):
            resampled_ch = librosa.resample(
                audio[:, ch],
                orig_sr=orig_sr,
                target_sr=target_sr,
            )
            resampled_channels.append(resampled_ch)
        stereo: npt.NDArray[np.float32] = np.stack(resampled_channels, axis=1).astype(np.float32)
        return stereo
