"""Tests for the analyze CLI command."""

import json
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf
from typer.testing import CliRunner

from mixref.cli.main import app

runner = CliRunner()


@pytest.fixture
def temp_audio_file(tmp_path: Path) -> Path:
    """Create a temporary audio file for testing.

    Args:
        tmp_path: Pytest temporary directory

    Returns:
        Path to temporary WAV file
    """
    file_path = tmp_path / "test_track.wav"
    sample_rate = 44100
    duration = 3.0
    samples = int(sample_rate * duration)

    # Generate test audio (pink noise at moderate level)
    np.random.seed(42)
    audio = np.random.randn(samples, 2) * 0.1

    sf.write(file_path, audio, sample_rate)
    return file_path


def test_analyze_basic(temp_audio_file: Path) -> None:
    """Test basic analyze command without targets.

    Args:
        temp_audio_file: Temporary audio file fixture
    """
    result = runner.invoke(app, ["analyze", str(temp_audio_file)])

    assert result.exit_code == 0
    assert "Analysis:" in result.stdout
    assert "Integrated Loudness" in result.stdout
    assert "True Peak" in result.stdout
    assert "Loudness Range" in result.stdout
    assert "LUFS" in result.stdout
    assert "dBTP" in result.stdout


def test_analyze_with_platform_target(temp_audio_file: Path) -> None:
    """Test analyze command with platform target.

    Args:
        temp_audio_file: Temporary audio file fixture
    """
    result = runner.invoke(app, ["analyze", str(temp_audio_file), "--platform", "spotify"])

    assert result.exit_code == 0
    assert "Platform Target: SPOTIFY" in result.stdout
    # Check that we got some comparison feedback
    assert (
        "above" in result.stdout.lower()
        or "below" in result.stdout.lower()
        or "perfect" in result.stdout.lower()
    )


def test_analyze_with_genre_target(temp_audio_file: Path) -> None:
    """Test analyze command with genre target.

    Args:
        temp_audio_file: Temporary audio file fixture
    """
    result = runner.invoke(app, ["analyze", str(temp_audio_file), "--genre", "dnb"])

    assert result.exit_code == 0
    assert "Genre Target: DNB" in result.stdout
    # Check that we got some comparison feedback
    assert (
        "above" in result.stdout.lower()
        or "below" in result.stdout.lower()
        or "perfect" in result.stdout.lower()
    )


def test_analyze_with_both_targets(temp_audio_file: Path) -> None:
    """Test analyze command with both platform and genre targets.

    Args:
        temp_audio_file: Temporary audio file fixture
    """
    result = runner.invoke(
        app,
        ["analyze", str(temp_audio_file), "--platform", "youtube", "--genre", "techno"],
    )

    assert result.exit_code == 0
    assert "Platform Target: YOUTUBE" in result.stdout
    assert "Genre Target: TECHNO" in result.stdout


def test_analyze_json_output(temp_audio_file: Path) -> None:
    """Test JSON output format.

    Args:
        temp_audio_file: Temporary audio file fixture
    """
    result = runner.invoke(app, ["analyze", str(temp_audio_file), "--json"])

    assert result.exit_code == 0

    # Parse JSON output
    output = json.loads(result.stdout)

    # Verify structure
    assert "file" in output
    assert "loudness" in output
    assert "integrated_lufs" in output["loudness"]
    assert "true_peak_db" in output["loudness"]
    assert "loudness_range_lu" in output["loudness"]
    assert "short_term_max_lufs" in output["loudness"]
    assert "short_term_min_lufs" in output["loudness"]

    # Verify values are numbers
    assert isinstance(output["loudness"]["integrated_lufs"], (int, float))
    assert isinstance(output["loudness"]["true_peak_db"], (int, float))
    assert isinstance(output["loudness"]["loudness_range_lu"], (int, float))


def test_analyze_json_with_platform(temp_audio_file: Path) -> None:
    """Test JSON output with platform target.

    Args:
        temp_audio_file: Temporary audio file fixture
    """
    result = runner.invoke(
        app,
        ["analyze", str(temp_audio_file), "--platform", "club", "--json"],
    )

    assert result.exit_code == 0

    output = json.loads(result.stdout)
    assert "platform" in output
    assert output["platform"]["name"] == "club"
    assert "target_lufs" in output["platform"]
    assert "difference" in output["platform"]
    assert "is_acceptable" in output["platform"]
    assert "message" in output["platform"]


def test_analyze_json_with_genre(temp_audio_file: Path) -> None:
    """Test JSON output with genre target.

    Args:
        temp_audio_file: Temporary audio file fixture
    """
    result = runner.invoke(
        app,
        ["analyze", str(temp_audio_file), "--genre", "house", "--json"],
    )

    assert result.exit_code == 0

    output = json.loads(result.stdout)
    assert "genre" in output
    assert output["genre"]["name"] == "house"
    assert "target_lufs" in output["genre"]
    assert "difference" in output["genre"]
    assert "is_acceptable" in output["genre"]
    assert "message" in output["genre"]


def test_analyze_file_not_found() -> None:
    """Test error handling when file doesn't exist."""
    result = runner.invoke(app, ["analyze", "nonexistent_file.wav"])

    assert result.exit_code == 1
    assert "Error" in result.stdout
    assert "not found" in result.stdout.lower()


def test_analyze_invalid_platform(temp_audio_file: Path) -> None:
    """Test error handling for invalid platform.

    Args:
        temp_audio_file: Temporary audio file fixture
    """
    result = runner.invoke(
        app,
        ["analyze", str(temp_audio_file), "--platform", "invalid_platform"],
    )

    # Typer should raise error for invalid enum
    assert result.exit_code != 0


def test_analyze_invalid_genre(temp_audio_file: Path) -> None:
    """Test error handling for invalid genre.

    Args:
        temp_audio_file: Temporary audio file fixture
    """
    result = runner.invoke(
        app,
        ["analyze", str(temp_audio_file), "--genre", "invalid_genre"],
    )

    # Typer should raise error for invalid enum
    assert result.exit_code != 0


def test_analyze_short_option_platform(temp_audio_file: Path) -> None:
    """Test short option flag for platform.

    Args:
        temp_audio_file: Temporary audio file fixture
    """
    result = runner.invoke(app, ["analyze", str(temp_audio_file), "-p", "spotify"])

    assert result.exit_code == 0
    assert "Platform Target: SPOTIFY" in result.stdout


def test_analyze_short_option_genre(temp_audio_file: Path) -> None:
    """Test short option flag for genre.

    Args:
        temp_audio_file: Temporary audio file fixture
    """
    result = runner.invoke(app, ["analyze", str(temp_audio_file), "-g", "dnb"])

    assert result.exit_code == 0
    assert "Genre Target: DNB" in result.stdout
