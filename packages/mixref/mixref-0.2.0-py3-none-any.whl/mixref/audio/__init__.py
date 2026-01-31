"""Audio file loading and handling.

This module provides utilities for loading, processing, and validating audio files.
"""

from mixref.audio.exceptions import (
    AudioError,
    AudioFileNotFoundError,
    CorruptFileError,
    InvalidAudioDataError,
    UnsupportedFormatError,
)
from mixref.audio.loader import load_audio
from mixref.audio.validation import (
    AudioInfo,
    get_audio_info,
    validate_duration,
    validate_sample_rate,
)

__all__ = [
    "load_audio",
    "AudioError",
    "AudioFileNotFoundError",
    "CorruptFileError",
    "InvalidAudioDataError",
    "UnsupportedFormatError",
    "AudioInfo",
    "get_audio_info",
    "validate_duration",
    "validate_sample_rate",
]
