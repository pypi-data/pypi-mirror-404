"""
Using the Analyze Command
==========================

This example demonstrates how to use the ``mixref analyze`` command to analyze
audio files and compare them against platform and genre targets.

The analyze command provides loudness measurements (LUFS, true peak, LRA) and
compares your track against streaming platform targets or genre-specific targets.
"""

import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf

from mixref.audio import load_audio
from mixref.meters import calculate_lufs, compare_to_target, get_target, Genre, Platform

# %%
# Create Example Audio Files
# ---------------------------
#
# First, let's create three different audio files to demonstrate the analyze
# command with different loudness levels.

sample_rate = 44100
duration = 3.0
samples = int(sample_rate * duration)

# Set random seed for reproducibility
np.random.seed(42)

# Create temporary directory for files
temp_dir = Path(tempfile.mkdtemp())

# 1. Quiet track (good for streaming)
quiet_audio = np.random.randn(samples, 2) * 0.01
quiet_file = temp_dir / "streaming_master.wav"
sf.write(quiet_file, quiet_audio, sample_rate)

# 2. Club-ready track (louder)
club_audio = np.random.randn(samples, 2) * 0.3
club_file = temp_dir / "club_master.wav"
sf.write(club_file, club_audio, sample_rate)

# 3. Over-loud track (potential clipping)
loud_audio = np.random.randn(samples, 2) * 0.8
loud_file = temp_dir / "too_loud.wav"
sf.write(loud_file, loud_audio, sample_rate)

print(f"Created test files in: {temp_dir}")

# %%
# Analyze Basic: Get Loudness Metrics
# ------------------------------------
#
# The simplest use case is analyzing a file without specifying targets.
# This shows the raw loudness measurements.
#
# Command line equivalent:
#
# .. code-block:: bash
#
#     mixref analyze streaming_master.wav

audio, sr = load_audio(quiet_file)
result = calculate_lufs(audio.T if audio.ndim == 2 else audio, sr)

print(f"\n=== Analysis: {quiet_file.name} ===")
print(f"Integrated LUFS:  {result.integrated_lufs:>6.1f} LUFS")
print(f"True Peak:        {result.true_peak_db:>6.1f} dBTP")
print(f"Loudness Range:   {result.loudness_range_lu:>6.1f} LU")
print(f"Short-term Max:   {result.short_term_max_lufs:>6.1f} LUFS")
print(f"Short-term Min:   {result.short_term_min_lufs:>6.1f} LUFS")

# %%
# Compare Against Streaming Platforms
# ------------------------------------
#
# Compare your track against platform targets like Spotify, YouTube, or Apple Music.
#
# Command line equivalent:
#
# .. code-block:: bash
#
#     mixref analyze streaming_master.wav --platform spotify
#     mixref analyze streaming_master.wav --platform youtube
#     mixref analyze streaming_master.wav -p tidal  # short form

platforms = [Platform.SPOTIFY, Platform.YOUTUBE, Platform.APPLE_MUSIC]

print(f"\n=== Platform Comparison: {quiet_file.name} ===")
for platform in platforms:
    target = get_target(platform=platform)
    is_ok, diff, message = compare_to_target(result.integrated_lufs, target)
    
    status = "✅" if is_ok else "⚠️"
    print(f"\n{platform.value.upper():12} {status}")
    print(f"  Target: {target.target_lufs} LUFS")
    print(f"  Diff:   {diff:+.1f} dB")
    print(f"  {message}")

# %%
# Compare Against Genre Targets
# ------------------------------
#
# Compare against genre-specific targets for club/DJ playback.
#
# Command line equivalent:
#
# .. code-block:: bash
#
#     mixref analyze club_master.wav --genre dnb
#     mixref analyze club_master.wav --genre techno
#     mixref analyze club_master.wav -g house  # short form

# Analyze the club-ready track
audio_club, sr = load_audio(club_file)
result_club = calculate_lufs(audio_club.T if audio_club.ndim == 2 else audio_club, sr)

genres = [Genre.DNB, Genre.TECHNO, Genre.HOUSE]

print(f"\n=== Genre Comparison: {club_file.name} ===")
print(f"Measured LUFS: {result_club.integrated_lufs:.1f}")

for genre in genres:
    target = get_target(genre=genre)
    is_ok, diff, message = compare_to_target(result_club.integrated_lufs, target)
    
    status = "✅" if is_ok else "⚠️"
    print(f"\n{genre.value.upper():8} {status}")
    print(f"  Target: {target.target_lufs} LUFS")
    print(f"  Diff:   {diff:+.1f} dB")

# %%
# Detect Potential Issues
# -----------------------
#
# The analyze command warns you about potential problems like clipping
# or excessive loudness.

# Analyze the over-loud track
audio_loud, sr = load_audio(loud_file)
result_loud = calculate_lufs(audio_loud.T if audio_loud.ndim == 2 else audio_loud, sr)

print(f"\n=== Problem Detection: {loud_file.name} ===")
print(f"Integrated LUFS: {result_loud.integrated_lufs:.1f}")
print(f"True Peak:       {result_loud.true_peak_db:.1f} dBTP")

# Check for clipping danger
if result_loud.true_peak_db > -1.0:
    print("\n⚠️ WARNING: True peak above -1.0 dBTP!")
    print("   Risk of clipping when converted to lossy formats.")
    print("   Recommendation: Reduce gain by at least "
          f"{abs(-1.0 - result_loud.true_peak_db):.1f} dB")

# Check against streaming targets
spotify_target = get_target(platform=Platform.SPOTIFY)
is_ok, diff, message = compare_to_target(result_loud.integrated_lufs, spotify_target)

print(f"\n{message}")

# %%
# JSON Output for Automation
# ---------------------------
#
# Get machine-readable output for scripts and automation.
#
# Command line equivalent:
#
# .. code-block:: bash
#
#     mixref analyze my_track.wav --platform spotify --json | jq .

import json

# Build JSON output structure (matches CLI --json output)
output = {
    "file": str(quiet_file),
    "loudness": {
        "integrated_lufs": round(result.integrated_lufs, 2),
        "true_peak_db": round(result.true_peak_db, 2),
        "loudness_range_lu": round(result.loudness_range_lu, 2),
        "short_term_max_lufs": round(result.short_term_max_lufs, 2),
        "short_term_min_lufs": round(result.short_term_min_lufs, 2),
    },
}

# Add platform comparison
spotify_target = get_target(platform=Platform.SPOTIFY)
is_ok, diff, message = compare_to_target(result.integrated_lufs, spotify_target)
output["platform"] = {
    "name": "spotify",
    "target_lufs": spotify_target.target_lufs,
    "difference": round(diff, 2),
    "is_acceptable": is_ok,
    "message": message,
}

print("\n=== JSON Output ===")
print(json.dumps(output, indent=2))

# %%
# Workflow Example: Pre-Release Check
# ------------------------------------
#
# Typical producer workflow: check if track meets targets before release.

def check_release_ready(file_path: Path) -> dict:
    """Check if track is ready for release.
    
    Args:
        file_path: Path to audio file
        
    Returns:
        Dictionary with pass/fail status and recommendations
    """
    audio, sr = load_audio(file_path)
    result = calculate_lufs(audio.T if audio.ndim == 2 else audio, sr)
    
    checks = {
        "file": file_path.name,
        "lufs": result.integrated_lufs,
        "peak": result.true_peak_db,
        "issues": [],
        "ready": True,
    }
    
    # Check 1: No clipping
    if result.true_peak_db > -1.0:
        checks["issues"].append(f"⚠️ True peak too high ({result.true_peak_db:.1f} dBTP)")
        checks["ready"] = False
    
    # Check 2: Spotify target
    spotify = get_target(platform=Platform.SPOTIFY)
    is_ok, diff, msg = compare_to_target(result.integrated_lufs, spotify)
    if abs(diff) > 2.0:
        checks["issues"].append(f"⚠️ {diff:+.1f} dB from Spotify target")
    
    # Check 3: Dynamic range
    if result.loudness_range_lu < 3.0:
        checks["issues"].append("⚠️ Very low dynamic range (over-compressed)")
    
    return checks

# Check all three files
print("\n=== Pre-Release Checks ===")
for file_path in [quiet_file, club_file, loud_file]:
    status = check_release_ready(file_path)
    
    print(f"\n{status['file']}")
    print(f"  LUFS: {status['lufs']:.1f}")
    print(f"  Peak: {status['peak']:.1f} dBTP")
    print(f"  Ready: {'✅ YES' if status['ready'] else '❌ NO'}")
    
    if status['issues']:
        print("  Issues:")
        for issue in status['issues']:
            print(f"    {issue}")

# %%
# Key Takeaways
# -------------
#
# 1. **Basic analysis**: ``mixref analyze file.wav`` shows loudness metrics
# 2. **Platform targets**: Add ``--platform spotify`` to compare against streaming
# 3. **Genre targets**: Add ``--genre dnb`` for club/DJ playback
# 4. **JSON output**: Add ``--json`` for machine-readable results
# 5. **Automation**: Combine with scripts for batch processing
#
# The analyze command integrates audio loading, LUFS calculation, and target
# comparison into a single, producer-friendly tool.

# Clean up temporary files
import shutil
shutil.rmtree(temp_dir)
print("\n✅ Example complete!")
