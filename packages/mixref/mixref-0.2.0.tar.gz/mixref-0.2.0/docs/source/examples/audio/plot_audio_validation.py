"""
Audio Validation Workflows
===========================

This example demonstrates how to validate audio files before processing.

Validation helps you catch issues like:
- Missing or corrupt files
- Incorrect sample rates
- Too short/long durations
- Unexpected formats

This is essential for production workflows where you process batches of audio.
"""

# %%
# Setup
# -----
import tempfile
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import soundfile as sf

from mixref.audio import get_audio_info, validate_duration, validate_sample_rate


# Helper function to create test audio
def generate_sine_wave(frequency=440, duration=1.0, sample_rate=44100):
    """Generate a simple sine wave for testing."""
    t = np.linspace(0, duration, int(sample_rate * duration))
    return np.sin(2 * np.pi * frequency * t).astype(np.float32), sample_rate

# %%
# Get Audio File Information
# ---------------------------
# The `get_audio_info()` function extracts metadata without loading the full audio.

# Create a test file
audio, sr = generate_sine_wave(frequency=440, duration=3.5, sample_rate=48000)
test_file = Path(tempfile.gettempdir()) / "validation_demo.wav"
sf.write(test_file, audio, sr)

# Get info
info = get_audio_info(test_file)

print(f"📊 Audio File Information:")
print(f"  Duration:     {info.duration:.2f} seconds")
print(f"  Sample Rate:  {info.sample_rate} Hz")
print(f"  Channels:     {info.channels} ({'mono' if info.channels == 1 else 'stereo'})")
print(f"  Format:       {info.format}")
print(f"  Subtype:      {info.subtype}")

# %%
# Validate Duration
# -----------------
# Check if audio files meet minimum/maximum duration requirements.

# Valid duration
is_valid, msg = validate_duration(test_file, min_duration=2.0, max_duration=5.0)
print(f"\n✅ Duration Check (2.0s - 5.0s):")
print(f"  Valid: {is_valid}")
if not is_valid:
    print(f"  Issue: {msg}")

# Too short
is_valid, msg = validate_duration(test_file, min_duration=10.0)
print(f"\n❌ Duration Check (min 10.0s):")
print(f"  Valid: {is_valid}")
if not is_valid:
    print(f"  Issue: {msg}")

# %%
# Validate Sample Rate
# --------------------
# Verify audio has the expected sample rate.

# Exact match
is_valid, msg = validate_sample_rate(test_file, expected_sr=48000)
print(f"\n✅ Sample Rate Check (48000 Hz):")
print(f"  Valid: {is_valid}")

# Mismatch
is_valid, msg = validate_sample_rate(test_file, expected_sr=44100)
print(f"\n❌ Sample Rate Check (44100 Hz):")
print(f"  Valid: {is_valid}")
if not is_valid:
    print(f"  Issue: {msg}")

# With tolerance
is_valid, msg = validate_sample_rate(test_file, expected_sr=47900, tolerance=200)
print(f"\n✅ Sample Rate Check (47900 Hz ± 200 Hz):")
print(f"  Valid: {is_valid}")

# %%
# Production Workflow Example
# ---------------------------
# Validate a batch of files before processing.


def validate_audio_batch(file_paths, min_duration=1.0, expected_sr=48000):
    """Validate a batch of audio files.

    Args:
        file_paths: List of audio file paths
        min_duration: Minimum duration in seconds
        expected_sr: Expected sample rate in Hz

    Returns:
        Dictionary of validation results
    """
    results = {"valid": [], "invalid": []}

    for path in file_paths:
        try:
            # Get info
            info = get_audio_info(path)

            # Validate duration
            dur_valid, dur_msg = validate_duration(path, min_duration=min_duration)

            # Validate sample rate
            sr_valid, sr_msg = validate_sample_rate(path, expected_sr=expected_sr)

            if dur_valid and sr_valid:
                results["valid"].append(str(path))
            else:
                reasons = []
                if not dur_valid:
                    reasons.append(dur_msg)
                if not sr_valid:
                    reasons.append(sr_msg)
                results["invalid"].append((str(path), reasons))

        except Exception as e:
            results["invalid"].append((str(path), [f"Error: {str(e)}"]))

    return results


# Create test files with different characteristics
test_files = []

# Valid file
audio1, sr1 = generate_sine_wave(frequency=440, duration=5.0, sample_rate=48000)
file1 = Path(tempfile.gettempdir()) / "valid_track.wav"
sf.write(file1, audio1, sr1)
test_files.append(file1)

# Too short
audio2, sr2 = generate_sine_wave(frequency=440, duration=0.5, sample_rate=48000)
file2 = Path(tempfile.gettempdir()) / "too_short.wav"
sf.write(file2, audio2, sr2)
test_files.append(file2)

# Wrong sample rate
audio3, sr3 = generate_sine_wave(frequency=440, duration=5.0, sample_rate=44100)
file3 = Path(tempfile.gettempdir()) / "wrong_sr.wav"
sf.write(file3, audio3, sr3)
test_files.append(file3)

# Validate batch
results = validate_audio_batch(test_files, min_duration=2.0, expected_sr=48000)

print(f"\n🔍 Batch Validation Results:")
print(f"  Valid files:   {len(results['valid'])}")
print(f"  Invalid files: {len(results['invalid'])}")

if results["invalid"]:
    print(f"\n❌ Invalid Files:")
    for path, reasons in results["invalid"]:
        print(f"  {Path(path).name}:")
        for reason in reasons:
            print(f"    - {reason}")

# %%
# Visualize Validation Statistics
# --------------------------------
# Create a summary plot of validation results.

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))

# Validation status
statuses = ["Valid", "Invalid"]
counts = [len(results["valid"]), len(results["invalid"])]
colors = ["#2ecc71", "#e74c3c"]

ax1.bar(statuses, counts, color=colors, alpha=0.7, edgecolor="black")
ax1.set_ylabel("Number of Files")
ax1.set_title("Validation Status")
ax1.grid(axis="y", alpha=0.3)

# File characteristics
file_info = [get_audio_info(f) for f in test_files]
durations = [info.duration for info in file_info]
sample_rates = [info.sample_rate for info in file_info]

# Color code each point (green for valid, red for invalid)
file_colors = []
for f in test_files:
    if str(f) in results["valid"]:
        file_colors.append(1.0)  # Green
    else:
        file_colors.append(0.0)  # Red

ax2.scatter(sample_rates, durations, c=file_colors, cmap="RdYlGn", s=200, alpha=0.7, edgecolors="black")
ax2.axhline(y=2.0, color="red", linestyle="--", alpha=0.5, label="Min Duration")
ax2.axvline(x=48000, color="blue", linestyle="--", alpha=0.5, label="Target SR")
ax2.set_xlabel("Sample Rate (Hz)")
ax2.set_ylabel("Duration (seconds)")
ax2.set_title("File Characteristics")
ax2.legend()
ax2.grid(alpha=0.3)

plt.tight_layout()
plt.show()

# %%
# Clean up test files
for f in test_files + [test_file]:
    f.unlink(missing_ok=True)

print("\n✨ Validation workflow complete!")
