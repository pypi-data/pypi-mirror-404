"""Loudness and metering utilities.

This module provides loudness measurement following EBU R128 standards
for broadcast and streaming audio, plus platform and genre-specific targets.
"""

from mixref.meters.loudness import LoudnessResult, calculate_lufs
from mixref.meters.targets import (
    Genre,
    LoudnessTarget,
    Platform,
    compare_to_target,
    get_target,
)

__all__ = [
    "calculate_lufs",
    "LoudnessResult",
    "Platform",
    "Genre",
    "LoudnessTarget",
    "get_target",
    "compare_to_target",
]
