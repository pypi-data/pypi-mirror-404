"""
LUFS Metering and Platform Targets
===================================

This example demonstrates how to measure loudness using EBU R128 standards
and compare against platform-specific and genre-specific targets.

Essential for:
- Mastering for streaming platforms (Spotify, Apple Music, YouTube)
- Club/DJ masters
- Genre-specific loudness practices (DnB, Techno, House)
"""

# %%
# Setup
# -----
import tempfile
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import soundfile as sf

from mixref.audio import load_audio
from mixref.meters import (
    Genre,
    Platform,
    calculate_lufs,
    compare_to_target,
    get_target,
)


# Helper function to create test audio
def generate_sine_wave(frequency=440, duration=1.0, sample_rate=44100, amplitude=0.5):
    """Generate a simple sine wave."""
    t = np.linspace(0, duration, int(sample_rate * duration))
    return np.sin(2 * np.pi * frequency * t).astype(np.float32) * amplitude, sample_rate


# %%
# Measure Track Loudness
# -----------------------
# Calculate integrated LUFS, true peak, and loudness range.

# Create a test file at moderate loudness
audio, sr = generate_sine_wave(frequency=440, duration=5.0, amplitude=0.15)
test_file = Path(tempfile.gettempdir()) / "lufs_demo.wav"
sf.write(test_file, audio, sr)

# Load and analyze
audio_data, sample_rate = load_audio(test_file)  # Uses native sample rate
# load_audio returns (samples, 2) for stereo, but calculate_lufs expects (2, samples)
if audio_data.ndim == 2:
    audio_data = audio_data.T  # Transpose to (2, samples)
result = calculate_lufs(audio_data, sample_rate)

print("📊 LUFS Analysis Results:")
print(f"  Integrated LUFS:  {result.integrated_lufs:.1f} LUFS")
print(f"  True Peak:        {result.true_peak_db:.1f} dBTP")
print(f"  Loudness Range:   {result.loudness_range_lu:.1f} LU")
print(f"  Short-term Max:   {result.short_term_max_lufs:.1f} LUFS")
print(f"  Short-term Min:   {result.short_term_min_lufs:.1f} LUFS")

# %%
# Compare to Platform Targets
# ----------------------------
# Check how the track matches streaming platform requirements.

platforms_to_check = [
    Platform.SPOTIFY,
    Platform.YOUTUBE,
    Platform.APPLE_MUSIC,
    Platform.CLUB,
]

print("\n🎯 Platform Target Comparison:\n")
platform_results = []

for platform in platforms_to_check:
    target = get_target(platform=platform)
    is_ok, diff, message = compare_to_target(result.integrated_lufs, target)
    
    platform_results.append({
        "platform": target.name,
        "target": target.target_lufs,
        "diff": diff,
        "ok": is_ok,
    })
    
    status = "✅" if is_ok else "⚠️"
    print(f"{status} {target.name}:")
    print(f"   {message}\n")

# %%
# Compare to Genre Targets
# -------------------------
# Check against genre-specific mastering practices.

genres_to_check = [Genre.DNB, Genre.TECHNO, Genre.HOUSE]

print("🎸 Genre Target Comparison:\n")
genre_results = []

for genre in genres_to_check:
    target = get_target(genre=genre)
    is_ok, diff, message = compare_to_target(result.integrated_lufs, target)
    
    genre_results.append({
        "genre": target.name,
        "target": target.target_lufs,
        "diff": diff,
        "ok": is_ok,
    })
    
    status = "✅" if is_ok else "⚠️"
    print(f"{status} {target.name}:")
    print(f"   {message}\n")

# %%
# Visualize Target Comparison
# ----------------------------
# Create a visual comparison of measured loudness vs targets.

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

# Platform targets
platform_names = [r["platform"] for r in platform_results]
platform_targets = [r["target"] for r in platform_results]
platform_diffs = [r["diff"] for r in platform_results]
platform_colors = ["green" if r["ok"] else "red" for r in platform_results]

ax1.barh(platform_names, platform_diffs, color=platform_colors, alpha=0.7)
ax1.axvline(x=0, color="black", linestyle="--", linewidth=1)
ax1.set_xlabel("Difference from Target (dB)")
ax1.set_title("Platform Target Comparison")
ax1.grid(axis="x", alpha=0.3)

# Add measured LUFS annotation
for i, (name, target, diff) in enumerate(zip(platform_names, platform_targets, platform_diffs)):
    measured = target + diff
    ax1.text(diff, i, f"  {measured:.1f} LUFS", va="center", fontsize=9)

# Genre targets
genre_names = [r["genre"] for r in genre_results]
genre_targets = [r["target"] for r in genre_results]
genre_diffs = [r["diff"] for r in genre_results]
genre_colors = ["green" if r["ok"] else "red" for r in genre_results]

ax2.barh(genre_names, genre_diffs, color=genre_colors, alpha=0.7)
ax2.axvline(x=0, color="black", linestyle="--", linewidth=1)
ax2.set_xlabel("Difference from Target (dB)")
ax2.set_title("Genre Target Comparison")
ax2.grid(axis="x", alpha=0.3)

for i, (name, target, diff) in enumerate(zip(genre_names, genre_targets, genre_diffs)):
    measured = target + diff
    ax2.text(diff, i, f"  {measured:.1f} LUFS", va="center", fontsize=9)

plt.tight_layout()
plt.show()

# %%
# Target Ranges Visualization
# ----------------------------
# Show acceptable loudness ranges for different platforms and genres.

fig, ax = plt.subplots(figsize=(12, 6))

# Collect all targets
all_targets = []
for platform in [Platform.SPOTIFY, Platform.YOUTUBE, Platform.APPLE_MUSIC, Platform.CLUB]:
    target = get_target(platform=platform)
    all_targets.append(("Platform", target))

for genre in [Genre.DNB, Genre.TECHNO, Genre.HOUSE, Genre.DUBSTEP]:
    target = get_target(genre=genre)
    all_targets.append(("Genre", target))

# Plot ranges
y_pos = np.arange(len(all_targets))
for i, (category, target) in enumerate(all_targets):
    # Target point
    ax.plot(target.target_lufs, i, "o", color="blue", markersize=10, zorder=3)
    
    # Acceptable range (if defined)
    if target.min_lufs is not None and target.max_lufs is not None:
        ax.plot([target.min_lufs, target.max_lufs], [i, i], "-", 
                color="green", linewidth=4, alpha=0.5, zorder=2)
    
    # Color code by category
    color = "steelblue" if category == "Platform" else "coral"
    ax.text(-25, i, target.name, va="center", fontsize=9, color=color, weight="bold")

# Add measured loudness
ax.axvline(result.integrated_lufs, color="red", linestyle="--", 
           linewidth=2, label=f"Your Track: {result.integrated_lufs:.1f} LUFS")

ax.set_yticks([])
ax.set_xlabel("Integrated Loudness (LUFS)", fontsize=12)
ax.set_title("Loudness Targets: Platforms vs Genres", fontsize=14, weight="bold")
ax.grid(axis="x", alpha=0.3)
ax.legend(loc="lower right")
ax.set_xlim(-26, -4)

plt.tight_layout()
plt.show()

# %%
# Mastering Workflow Example
# ---------------------------
# Demonstrate a typical mastering workflow with target checking.


def check_master(audio_file, target_platform=None, target_genre=None):
    """Check if a master meets target requirements.
    
    Args:
        audio_file: Path to audio file
        target_platform: Target platform (e.g., Platform.SPOTIFY)
        target_genre: Target genre (e.g., Genre.DNB)
    
    Returns:
        Dictionary with results and recommendations
    """
    # Load and analyze
    audio, sr = load_audio(audio_file)  # Uses native sample rate
    # load_audio returns (samples, 2) for stereo, transpose to (2, samples)
    if audio.ndim == 2:
        audio = audio.T
    result = calculate_lufs(audio, sr)
    
    # Get target
    if target_platform:
        target = get_target(platform=target_platform)
    elif target_genre:
        target = get_target(genre=target_genre)
    else:
        raise ValueError("Must specify target_platform or target_genre")
    
    # Compare
    is_ok, diff, message = compare_to_target(result.integrated_lufs, target)
    
    # Check true peak
    peak_ok = result.true_peak_db <= target.max_true_peak_db
    
    # Generate recommendations
    recommendations = []
    if not is_ok:
        if diff > 0:
            recommendations.append(f"Reduce gain by {abs(diff):.1f} dB")
        else:
            recommendations.append(f"Increase gain by {abs(diff):.1f} dB")
    
    if not peak_ok:
        peak_diff = result.true_peak_db - target.max_true_peak_db
        recommendations.append(f"True peak too hot by {peak_diff:.1f} dB - use limiting")
    
    if not recommendations:
        recommendations.append("Perfect! Ready for release.")
    
    return {
        "integrated_lufs": result.integrated_lufs,
        "true_peak_db": result.true_peak_db,
        "target_name": target.name,
        "target_lufs": target.target_lufs,
        "difference_db": diff,
        "lufs_ok": is_ok,
        "peak_ok": peak_ok,
        "ready_for_release": is_ok and peak_ok,
        "recommendations": recommendations,
    }


# Test the workflow
print("🎛️ Mastering Workflow Check:\n")

# Check for Spotify
spotify_check = check_master(test_file, target_platform=Platform.SPOTIFY)
print(f"Target: {spotify_check['target_name']}")
print(f"Measured: {spotify_check['integrated_lufs']:.1f} LUFS "
      f"(target: {spotify_check['target_lufs']:.1f} LUFS)")
print(f"Difference: {spotify_check['difference_db']:+.1f} dB")
print(f"Status: {'✅ Ready' if spotify_check['ready_for_release'] else '⚠️ Needs adjustment'}")
print(f"Recommendations:")
for rec in spotify_check['recommendations']:
    print(f"  - {rec}")

# %%
# Clean up
test_file.unlink(missing_ok=True)

print("\n✨ LUFS metering and target comparison complete!")
