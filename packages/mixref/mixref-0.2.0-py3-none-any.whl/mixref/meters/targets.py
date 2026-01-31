"""Loudness targets for different platforms and genres.

This module defines target loudness levels for various streaming platforms,
broadcast standards, and genre-specific mastering practices.
"""

from enum import Enum
from typing import NamedTuple


class Platform(str, Enum):
    """Streaming and playback platforms with standard loudness targets."""

    SPOTIFY = "spotify"
    YOUTUBE = "youtube"
    APPLE_MUSIC = "apple_music"
    TIDAL = "tidal"
    SOUNDCLOUD = "soundcloud"
    CLUB = "club"
    BROADCAST = "broadcast"


class Genre(str, Enum):
    """Electronic music genres with specific mastering practices."""

    DNB = "dnb"  # Drum & Bass
    TECHNO = "techno"
    HOUSE = "house"
    DUBSTEP = "dubstep"
    TRANCE = "trance"


class LoudnessTarget(NamedTuple):
    """Loudness target specification.

    Attributes:
        name: Human-readable name (e.g., "Spotify", "DnB Club Master")
        target_lufs: Target integrated loudness in LUFS
        min_lufs: Minimum acceptable LUFS (None = no minimum)
        max_lufs: Maximum acceptable LUFS (None = no maximum)
        max_true_peak_db: Maximum true peak in dBTP (typically -1.0)
        description: Description of the target use case
    """

    name: str
    target_lufs: float
    min_lufs: float | None
    max_lufs: float | None
    max_true_peak_db: float
    description: str


# Platform-specific targets (streaming services)
PLATFORM_TARGETS: dict[Platform, LoudnessTarget] = {
    Platform.SPOTIFY: LoudnessTarget(
        name="Spotify",
        target_lufs=-14.0,
        min_lufs=None,
        max_lufs=-14.0,
        max_true_peak_db=-1.0,
        description="Spotify normalizes to -14 LUFS. Louder tracks are turned down.",
    ),
    Platform.YOUTUBE: LoudnessTarget(
        name="YouTube",
        target_lufs=-14.0,
        min_lufs=None,
        max_lufs=-13.0,
        max_true_peak_db=-1.0,
        description="YouTube normalizes to -14 LUFS with some tolerance.",
    ),
    Platform.APPLE_MUSIC: LoudnessTarget(
        name="Apple Music",
        target_lufs=-16.0,
        min_lufs=None,
        max_lufs=-16.0,
        max_true_peak_db=-1.0,
        description="Apple Music uses -16 LUFS. Sound Check normalization.",
    ),
    Platform.TIDAL: LoudnessTarget(
        name="Tidal",
        target_lufs=-14.0,
        min_lufs=None,
        max_lufs=-14.0,
        max_true_peak_db=-1.0,
        description="Tidal normalizes to -14 LUFS for consistent playback.",
    ),
    Platform.SOUNDCLOUD: LoudnessTarget(
        name="SoundCloud",
        target_lufs=-14.0,
        min_lufs=None,
        max_lufs=-8.0,
        max_true_peak_db=-1.0,
        description="SoundCloud targets -14 LUFS but accepts louder masters.",
    ),
    Platform.CLUB: LoudnessTarget(
        name="Club/DJ",
        target_lufs=-8.0,
        min_lufs=-10.0,
        max_lufs=-6.0,
        max_true_peak_db=-0.3,
        description="Club systems expect hot masters (-8 to -6 LUFS). Compete with DJ mixes.",
    ),
    Platform.BROADCAST: LoudnessTarget(
        name="Broadcast (EBU R128)",
        target_lufs=-23.0,
        min_lufs=-24.0,
        max_lufs=-22.0,
        max_true_peak_db=-1.0,
        description="EBU R128 standard for broadcast (TV, radio).",
    ),
}

# Genre-specific mastering targets
GENRE_TARGETS: dict[Genre, LoudnessTarget] = {
    Genre.DNB: LoudnessTarget(
        name="Drum & Bass",
        target_lufs=-8.0,
        min_lufs=-10.0,
        max_lufs=-6.0,
        max_true_peak_db=-0.3,
        description="DnB masters are typically hot (-8 to -6 LUFS) for club play and DJ sets.",
    ),
    Genre.TECHNO: LoudnessTarget(
        name="Techno",
        target_lufs=-9.0,
        min_lufs=-11.0,
        max_lufs=-7.0,
        max_true_peak_db=-0.5,
        description="Techno balances club loudness with dynamics. Hypnotic, driving.",
    ),
    Genre.HOUSE: LoudnessTarget(
        name="House",
        target_lufs=-10.0,
        min_lufs=-12.0,
        max_lufs=-8.0,
        max_true_peak_db=-1.0,
        description="House music retains groove and dynamics. Less aggressive than DnB/Techno.",
    ),
    Genre.DUBSTEP: LoudnessTarget(
        name="Dubstep",
        target_lufs=-7.0,
        min_lufs=-9.0,
        max_lufs=-5.0,
        max_true_peak_db=-0.3,
        description="Dubstep masters are very loud (-7 to -5 LUFS) for maximum impact.",
    ),
    Genre.TRANCE: LoudnessTarget(
        name="Trance",
        target_lufs=-9.0,
        min_lufs=-11.0,
        max_lufs=-7.0,
        max_true_peak_db=-1.0,
        description="Trance balances energy with melodic clarity.",
    ),
}


def get_target(platform: Platform | None = None, genre: Genre | None = None) -> LoudnessTarget:
    """Get loudness target for a platform or genre.

    Args:
        platform: Target platform (Spotify, YouTube, Club, etc.)
        genre: Music genre (DnB, Techno, House, etc.)

    Returns:
        LoudnessTarget with target LUFS, ranges, and description

    Raises:
        ValueError: If neither platform nor genre specified, or both specified

    Example:
        >>> target = get_target(platform=Platform.SPOTIFY)
        >>> print(f"Target: {target.target_lufs} LUFS")
        Target: -14.0 LUFS

        >>> target = get_target(genre=Genre.DNB)
        >>> print(f"DnB target: {target.target_lufs} LUFS")
        DnB target: -8.0 LUFS
    """
    if platform is None and genre is None:
        raise ValueError("Must specify either platform or genre")

    if platform is not None and genre is not None:
        raise ValueError("Cannot specify both platform and genre (choose one)")

    if platform is not None:
        return PLATFORM_TARGETS[platform]

    if genre is not None:
        return GENRE_TARGETS[genre]

    # Should never reach here due to checks above
    raise ValueError("Invalid arguments")


def compare_to_target(
    measured_lufs: float,
    target: LoudnessTarget,
) -> tuple[bool, float, str]:
    """Compare measured loudness against target.

    Args:
        measured_lufs: Measured integrated LUFS
        target: Target loudness specification

    Returns:
        Tuple of (is_acceptable, difference_db, message):
            - is_acceptable: True if within acceptable range
            - difference_db: Difference from target (+ve = too loud, -ve = too quiet)
            - message: Human-readable feedback

    Example:
        >>> from mixref.meters import calculate_lufs
        >>> result = calculate_lufs(audio, 44100)
        >>> target = get_target(platform=Platform.SPOTIFY)
        >>> ok, diff, msg = compare_to_target(result.integrated_lufs, target)
        >>> print(msg)
        2.3 dB above Spotify target (-14.0 LUFS). Will be turned down.
    """
    difference = measured_lufs - target.target_lufs

    # Check if within acceptable range
    is_acceptable = True
    if target.min_lufs is not None and measured_lufs < target.min_lufs:
        is_acceptable = False
    if target.max_lufs is not None and measured_lufs > target.max_lufs:
        is_acceptable = False

    # Generate feedback message
    if abs(difference) < 0.5:
        message = f"Perfect! Within 0.5 dB of {target.name} target ({target.target_lufs} LUFS)."
    elif difference > 0:
        # Too loud
        if is_acceptable:
            message = (
                f"{abs(difference):.1f} dB above {target.name} target "
                f"({target.target_lufs} LUFS). Still acceptable."
            )
        else:
            message = (
                f"⚠️ {abs(difference):.1f} dB above {target.name} target "
                f"({target.target_lufs} LUFS). May be turned down or distorted."
            )
    else:
        # Too quiet
        if is_acceptable:
            message = (
                f"{abs(difference):.1f} dB below {target.name} target "
                f"({target.target_lufs} LUFS). Still acceptable."
            )
        else:
            message = (
                f"⚠️ {abs(difference):.1f} dB below {target.name} target "
                f"({target.target_lufs} LUFS). Consider increasing loudness."
            )

    return is_acceptable, difference, message
