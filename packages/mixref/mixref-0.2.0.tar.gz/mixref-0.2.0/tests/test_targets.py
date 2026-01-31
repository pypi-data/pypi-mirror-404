"""Tests for loudness targets."""

import pytest

from mixref.meters import (
    Genre,
    LoudnessTarget,
    Platform,
    compare_to_target,
    get_target,
)


def test_get_target_spotify():
    """Test getting Spotify platform target."""
    target = get_target(platform=Platform.SPOTIFY)

    assert isinstance(target, LoudnessTarget)
    assert target.name == "Spotify"
    assert target.target_lufs == -14.0
    assert target.max_true_peak_db == -1.0
    assert "Spotify" in target.description


def test_get_target_club():
    """Test getting Club platform target."""
    target = get_target(platform=Platform.CLUB)

    assert target.name == "Club/DJ"
    assert target.target_lufs == -8.0
    assert -10.0 <= target.min_lufs <= target.target_lufs  # type: ignore[operator]
    assert target.target_lufs <= target.max_lufs <= -6.0  # type: ignore[operator]


def test_get_target_dnb_genre():
    """Test getting DnB genre target."""
    target = get_target(genre=Genre.DNB)

    assert target.name == "Drum & Bass"
    assert target.target_lufs == -8.0
    assert target.min_lufs == -10.0
    assert target.max_lufs == -6.0
    assert "DnB" in target.description or "Drum" in target.description


def test_get_target_techno_genre():
    """Test getting Techno genre target."""
    target = get_target(genre=Genre.TECHNO)

    assert target.name == "Techno"
    assert target.target_lufs == -9.0
    assert "Techno" in target.description


def test_get_target_house_genre():
    """Test getting House genre target."""
    target = get_target(genre=Genre.HOUSE)

    assert target.name == "House"
    assert target.target_lufs == -10.0
    # House should be less aggressive than DnB
    dnb_target = get_target(genre=Genre.DNB)
    assert target.target_lufs < dnb_target.target_lufs


def test_get_target_no_args():
    """Test that get_target raises error with no arguments."""
    with pytest.raises(ValueError, match="Must specify either platform or genre"):
        get_target()


def test_get_target_both_args():
    """Test that get_target raises error with both platform and genre."""
    with pytest.raises(ValueError, match="Cannot specify both"):
        get_target(platform=Platform.SPOTIFY, genre=Genre.DNB)


def test_compare_to_target_perfect():
    """Test comparison when measured LUFS is perfect."""
    target = get_target(platform=Platform.SPOTIFY)
    measured = -14.0  # Exactly on target

    is_ok, diff, msg = compare_to_target(measured, target)

    assert is_ok is True
    assert abs(diff) < 0.1  # Should be ~0
    assert "Perfect" in msg or "within" in msg.lower()


def test_compare_to_target_slightly_above():
    """Test comparison when slightly too loud but acceptable."""
    target = get_target(platform=Platform.SPOTIFY)
    measured = -13.5  # 0.5 dB above target

    is_ok, diff, msg = compare_to_target(measured, target)

    assert diff > 0  # Positive = too loud
    assert abs(diff - 0.5) < 0.1
    assert "above" in msg.lower()


def test_compare_to_target_too_loud():
    """Test comparison when too loud and unacceptable."""
    target = get_target(platform=Platform.SPOTIFY)
    measured = -8.0  # Way too loud for Spotify

    is_ok, diff, msg = compare_to_target(measured, target)

    assert is_ok is False  # Spotify max_lufs is -14.0
    assert diff > 0
    assert "⚠️" in msg or "warning" in msg.lower() or "turned down" in msg.lower()


def test_compare_to_target_too_quiet():
    """Test comparison when too quiet."""
    target = get_target(platform=Platform.SPOTIFY)
    measured = -20.0  # Quite quiet

    is_ok, diff, msg = compare_to_target(measured, target)

    # Spotify has no min_lufs, so should still be "acceptable"
    assert diff < 0  # Negative = too quiet
    assert "below" in msg.lower()


def test_compare_to_target_club_range():
    """Test Club target with acceptable range."""
    target = get_target(platform=Platform.CLUB)

    # Within range (-10 to -6 LUFS)
    is_ok, diff, msg = compare_to_target(-8.0, target)
    assert is_ok is True

    # Below range (too quiet for club)
    is_ok, diff, msg = compare_to_target(-12.0, target)
    assert is_ok is False
    assert diff < 0
    assert "⚠️" in msg or "below" in msg.lower()

    # Above range (too loud even for club)
    is_ok, diff, msg = compare_to_target(-5.0, target)
    assert is_ok is False
    assert diff > 0


def test_all_platforms_have_targets():
    """Test that all platforms have defined targets."""
    for platform in Platform:
        target = get_target(platform=platform)
        assert target.name
        assert target.target_lufs < 0  # LUFS is always negative
        assert target.max_true_peak_db <= 0  # True peak in dBFS


def test_all_genres_have_targets():
    """Test that all genres have defined targets."""
    for genre in Genre:
        target = get_target(genre=genre)
        assert target.name
        assert target.target_lufs < 0
        assert target.description


def test_genre_loudness_hierarchy():
    """Test that genre targets follow expected loudness hierarchy."""
    dubstep = get_target(genre=Genre.DUBSTEP)
    dnb = get_target(genre=Genre.DNB)
    house = get_target(genre=Genre.HOUSE)

    # Dubstep should be loudest (most aggressive)
    assert dubstep.target_lufs > dnb.target_lufs
    assert dnb.target_lufs > house.target_lufs

    # All club genres should be louder than streaming
    spotify = get_target(platform=Platform.SPOTIFY)
    assert dnb.target_lufs > spotify.target_lufs
    assert house.target_lufs > spotify.target_lufs


def test_platform_targets_consistency():
    """Test that platform targets are consistent."""
    # Most streaming services use -14 LUFS
    spotify = get_target(platform=Platform.SPOTIFY)
    youtube = get_target(platform=Platform.YOUTUBE)
    tidal = get_target(platform=Platform.TIDAL)

    assert spotify.target_lufs == youtube.target_lufs == tidal.target_lufs == -14.0

    # Apple Music is quieter
    apple = get_target(platform=Platform.APPLE_MUSIC)
    assert apple.target_lufs == -16.0
    assert apple.target_lufs < spotify.target_lufs

    # Club is much louder
    club = get_target(platform=Platform.CLUB)
    assert club.target_lufs > spotify.target_lufs


def test_compare_message_formats():
    """Test that comparison messages are helpful."""
    target = get_target(platform=Platform.SPOTIFY)

    # Test various scenarios and check message quality
    scenarios = [
        (-14.0, "Perfect"),  # Perfect
        (-13.5, "above"),  # Slightly loud
        (-14.5, "below"),  # Slightly quiet
        (-8.0, "⚠️"),  # Way too loud
    ]

    for measured, expected_word in scenarios:
        _, _, msg = compare_to_target(measured, target)
        assert expected_word in msg, f"Expected '{expected_word}' in message for {measured} LUFS"
        assert target.name in msg  # Should mention platform name
        assert "LUFS" in msg  # Should include units
