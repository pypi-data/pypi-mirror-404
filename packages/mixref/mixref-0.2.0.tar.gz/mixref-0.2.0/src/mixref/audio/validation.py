"""Audio file validation and inspection utilities.

This module provides functions to validate audio files and extract
metadata like duration, sample rate, channel count, and format.
"""

from pathlib import Path
from typing import NamedTuple

import soundfile as sf

from mixref.audio.exceptions import AudioFileNotFoundError, CorruptFileError


class AudioInfo(NamedTuple):
    """Audio file information.

    Attributes:
        duration: Duration in seconds
        sample_rate: Sample rate in Hz
        channels: Number of channels (1=mono, 2=stereo)
        format: File format (e.g., 'WAV', 'FLAC', 'MP3')
        subtype: Format subtype (e.g., 'PCM_16', 'FLOAT')
    """

    duration: float
    sample_rate: int
    channels: int
    format: str
    subtype: str


def get_audio_info(path: str | Path) -> AudioInfo:
    """Get detailed information about an audio file.

    Args:
        path: Path to audio file

    Returns:
        AudioInfo object with duration, sample rate, channels, format, and subtype

    Raises:
        AudioFileNotFoundError: If the file doesn't exist
        CorruptFileError: If the file cannot be read or is corrupted

    Example:
        >>> info = get_audio_info("my_track.wav")
        >>> print(f"Duration: {info.duration:.2f}s at {info.sample_rate}Hz")
        Duration: 180.50s at 44100Hz
    """
    path_obj = Path(path)

    if not path_obj.exists():
        raise AudioFileNotFoundError(str(path))

    try:
        info = sf.info(str(path_obj))
    except Exception as e:
        raise CorruptFileError(str(path), original_error=e) from e

    return AudioInfo(
        duration=info.duration,
        sample_rate=info.samplerate,
        channels=info.channels,
        format=info.format,
        subtype=info.subtype,
    )


def validate_duration(
    path: str | Path, min_duration: float = 0.0, max_duration: float | None = None
) -> tuple[bool, str]:
    """Validate audio file duration is within acceptable range.

    Args:
        path: Path to audio file
        min_duration: Minimum acceptable duration in seconds (default: 0.0)
        max_duration: Maximum acceptable duration in seconds (None = no limit)

    Returns:
        Tuple of (is_valid, message). If valid, message is empty string.

    Raises:
        AudioFileNotFoundError: If the file doesn't exist
        CorruptFileError: If the file cannot be read

    Example:
        >>> is_valid, msg = validate_duration("track.wav", min_duration=30.0)
        >>> if not is_valid:
        ...     print(f"Warning: {msg}")
    """
    info = get_audio_info(path)

    # Check for zero-duration (corrupt file indicator)
    if info.duration == 0.0:
        return False, "Audio file has zero duration (possibly corrupt)"

    # Check minimum duration
    if info.duration < min_duration:
        return (
            False,
            f"Duration {info.duration:.2f}s is below minimum {min_duration:.2f}s",
        )

    # Check maximum duration if specified
    if max_duration is not None and info.duration > max_duration:
        return (
            False,
            f"Duration {info.duration:.2f}s exceeds maximum {max_duration:.2f}s",
        )

    return True, ""


def validate_sample_rate(
    path: str | Path, expected_sr: int, tolerance: int = 0
) -> tuple[bool, str]:
    """Validate audio file sample rate matches expected value.

    Args:
        path: Path to audio file
        expected_sr: Expected sample rate in Hz
        tolerance: Allowed deviation in Hz (default: 0 = exact match)

    Returns:
        Tuple of (is_valid, message). If valid, message is empty string.

    Raises:
        AudioFileNotFoundError: If the file doesn't exist
        CorruptFileError: If the file cannot be read

    Example:
        >>> is_valid, msg = validate_sample_rate("track.wav", 44100)
        >>> if not is_valid:
        ...     print(f"Sample rate mismatch: {msg}")
    """
    info = get_audio_info(path)

    if tolerance == 0:
        if info.sample_rate != expected_sr:
            return (
                False,
                f"Sample rate {info.sample_rate}Hz does not match expected {expected_sr}Hz",
            )
    else:
        diff = abs(info.sample_rate - expected_sr)
        if diff > tolerance:
            return (
                False,
                f"Sample rate {info.sample_rate}Hz differs from expected {expected_sr}Hz "
                f"by {diff}Hz (tolerance: {tolerance}Hz)",
            )

    return True, ""
