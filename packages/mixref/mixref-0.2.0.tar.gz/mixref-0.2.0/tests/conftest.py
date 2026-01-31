"""Test fixtures and configuration for mixref tests."""

import pytest


@pytest.fixture
def sample_rate() -> int:
    """Standard sample rate for tests."""
    return 44100


@pytest.fixture
def duration() -> float:
    """Standard duration for test audio (seconds)."""
    return 1.0
