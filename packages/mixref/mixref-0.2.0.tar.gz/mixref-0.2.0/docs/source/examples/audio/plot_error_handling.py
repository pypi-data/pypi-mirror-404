"""
Error Handling in Audio Loading
================================

This example demonstrates how mixref handles various error conditions
when loading audio files.

mixref provides specific exception types for different error scenarios,
making it easy to handle problems gracefully in your scripts.
"""

# %%
# Custom Exception Types
# ----------------------
#
# mixref defines several exception types for audio loading errors:

from mixref.audio import (
    AudioFileNotFoundError,
    CorruptFileError,
    UnsupportedFormatError,
)

print("Available exception types:")
print("  - AudioFileNotFoundError: File doesn't exist")
print("  - UnsupportedFormatError: File format not supported")
print("  - CorruptFileError: File exists but can't be read")

# %%
# Handling Missing Files
# ----------------------
#
# When a file doesn't exist, you get a clear error:

from mixref.audio import load_audio

try:
    audio, sr = load_audio("this_file_does_not_exist.wav")
except AudioFileNotFoundError as e:
    print(f"❌ File not found: {e.path}")
    print(f"   Error message: {e}")

# %%
# Handling Unsupported Formats
# ----------------------------
#
# mixref supports WAV, FLAC, MP3, and a few other common formats.
# If you try to load an unsupported format:

import tempfile
from pathlib import Path

temp_dir = Path(tempfile.mkdtemp())
unsupported_file = temp_dir / "track.xyz"
unsupported_file.write_text("fake audio data")

try:
    audio, sr = load_audio(unsupported_file)
except UnsupportedFormatError as e:
    print(f"\n❌ Unsupported format: {e.format_}")
    print(f"   File: {e.path}")
    print(f"   Hint: {str(e).split('Supported')[1][:30]}...")

# %%
# Handling Corrupt Files
# ----------------------
#
# When a file exists but can't be read (corrupt, invalid, etc.):

corrupt_file = temp_dir / "corrupt.wav"
corrupt_file.write_bytes(b"RIFF\x00\x00\x00\x00WAVEfmt incomplete...")

try:
    audio, sr = load_audio(corrupt_file)
except CorruptFileError as e:
    print(f"\n❌ Corrupt file: {e.path}")
    print(f"   Original error type: {type(e.original_error).__name__}")

# %%
# Producer Workflow: Batch Processing with Error Handling
# -------------------------------------------------------
#
# Here's a real-world example: analyzing multiple tracks with graceful errors

import numpy as np
import soundfile as sf

# Create a mix of valid and invalid files
valid_file = temp_dir / "valid_track.wav"
sine_wave = 0.5 * np.sin(2 * np.pi * 440 * np.linspace(0, 1.0, 44100, dtype=np.float32))
sf.write(valid_file, sine_wave, 44100)

missing_file = temp_dir / "missing.wav"  # Doesn't exist
bad_format = temp_dir / "track.m4a"  # Unsupported (for this example)
bad_format.write_text("fake data")

files_to_analyze = [
    valid_file,
    missing_file,
    corrupt_file,
    bad_format,
]

print("\n" + "=" * 60)
print("Batch Analysis with Error Handling")
print("=" * 60)

results = {"success": 0, "skipped": 0, "errors": []}

for file_path in files_to_analyze:
    try:
        audio, sr = load_audio(file_path)
        duration = len(audio) / sr
        peak = np.abs(audio).max()

        print(f"\n✅ {file_path.name}")
        print(f"   Duration: {duration:.2f}s | Peak: {peak:.3f}")
        results["success"] += 1

    except AudioFileNotFoundError:
        print(f"\n⚠️  {file_path.name} - File not found (skipping)")
        results["skipped"] += 1

    except UnsupportedFormatError as e:
        print(f"\n⚠️  {file_path.name} - Unsupported format: {e.format_}")
        results["skipped"] += 1

    except CorruptFileError:
        print(f"\n❌ {file_path.name} - File is corrupt or invalid")
        results["errors"].append(file_path.name)

# Summary
print("\n" + "=" * 60)
print(f"Summary: {results['success']} analyzed, {results['skipped']} skipped, "
      f"{len(results['errors'])} errors")

# %%
# Best Practices for Error Handling
# ---------------------------------
#
# **For scripts and automation:**

def analyze_track_safely(file_path: str) -> dict[str, any] | None:
    """Analyze a track with comprehensive error handling.

    Returns:
        Analysis results dict, or None if file couldn't be loaded
    """
    try:
        audio, sr = load_audio(file_path)

        return {
            "duration": len(audio) / sr,
            "peak": float(np.abs(audio).max()),
            "rms": float(np.sqrt(np.mean(audio**2))),
        }

    except AudioFileNotFoundError:
        print(f"Skipping missing file: {file_path}")
        return None

    except (UnsupportedFormatError, CorruptFileError) as e:
        print(f"Cannot process {file_path}: {type(e).__name__}")
        return None


# Test it
result = analyze_track_safely(valid_file)
if result:
    print(f"\n📊 Analysis successful: {result}")

# %%
# Cleanup
import shutil

shutil.rmtree(temp_dir)
print("\n✅ Error handling examples complete!")
