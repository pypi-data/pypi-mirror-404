"""
Loading Audio Files
===================

This example demonstrates how to load audio files with mixref.

mixref provides a simple audio loader that handles format conversion,
mono/stereo conversion, and resampling automatically.
"""

# %%
# Basic Audio Loading
# -------------------
#
# The core function for loading audio is :func:`mixref.audio.loader.load_audio`.
# It returns audio as a numpy array and the sample rate.

import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf

from mixref.audio.loader import load_audio

# First, let's create some test audio files
# In real usage, you'd have actual WAV/FLAC/MP3 files
temp_dir = Path(tempfile.mkdtemp())

# Create a simple sine wave
duration = 1.0
sample_rate = 44100
t = np.linspace(0, duration, int(sample_rate * duration), dtype=np.float32)
sine_wave = 0.5 * np.sin(2 * np.pi * 440 * t)

# Save as mono WAV
mono_file = temp_dir / "mono_track.wav"
sf.write(mono_file, sine_wave, sample_rate)

# Save as stereo WAV
stereo_audio = np.stack([sine_wave, sine_wave], axis=1)
stereo_file = temp_dir / "stereo_track.wav"
sf.write(stereo_file, stereo_audio, sample_rate)

print(f"Created test files in {temp_dir}")

# %%
# Loading Mono Audio
# ------------------
#
# Load a mono file and keep it mono:

audio_mono, sr = load_audio(mono_file, channel_mode="auto")
print(f"Mono audio shape: {audio_mono.shape}")
print(f"Sample rate: {sr} Hz")
print(f"Duration: {len(audio_mono) / sr:.2f} seconds")

# %%
# Loading Stereo Audio
# --------------------
#
# Load a stereo file:

audio_stereo, sr = load_audio(stereo_file, channel_mode="auto")
print(f"Stereo audio shape: {audio_stereo.shape}")
print(f"Channels: {audio_stereo.shape[1]}")
print(f"Duration: {len(audio_stereo) / sr:.2f} seconds")

# %%
# Channel Conversion
# ------------------
#
# mixref can automatically convert between mono and stereo.

# Convert mono to stereo (duplicates the channel)
audio_mono_as_stereo, sr = load_audio(mono_file, channel_mode="stereo")
print(f"Mono → Stereo: {audio_mono_as_stereo.shape}")

# Convert stereo to mono (averages channels)
audio_stereo_as_mono, sr = load_audio(stereo_file, channel_mode="mono")
print(f"Stereo → Mono: {audio_stereo_as_mono.shape}")

# %%
# Default Behavior
# ----------------
#
# By default, mixref loads audio as stereo. This is because most
# production workflows work with stereo audio, even if the source is mono.

audio_default, sr = load_audio(mono_file)  # No channel_mode specified
print(f"Default loading (mono file): {audio_default.shape}")

audio_default2, sr = load_audio(stereo_file)  # No channel_mode specified
print(f"Default loading (stereo file): {audio_default2.shape}")

# %%
# Resampling
# ----------
#
# Load audio and resample to a target sample rate:

# Create a 48kHz file
audio_48k = 0.3 * np.sin(2 * np.pi * 440 * np.linspace(0, 1, 48000, dtype=np.float32))
file_48k = temp_dir / "audio_48khz.wav"
sf.write(file_48k, audio_48k, 48000)

# Load and resample to 44.1kHz
audio_resampled, sr_new = load_audio(file_48k, sample_rate=44100)
print(f"\nOriginal: 48000 Hz, {len(audio_48k)} samples")
print(f"Resampled: {sr_new} Hz, {len(audio_resampled)} samples")

# %%
# Producer Workflow Example
# --------------------------
#
# Here's a typical workflow for a producer analyzing multiple tracks:

print("\n" + "=" * 50)
print("Analyzing Multiple Tracks")
print("=" * 50)

tracks = [mono_file, stereo_file, file_48k]

for track_path in tracks:
    # Load as stereo, normalize to 44.1kHz
    audio, sr = load_audio(track_path, sample_rate=44100, channel_mode="stereo")

    # Get some basic info
    duration = len(audio) / sr
    peak = np.abs(audio).max()
    rms = np.sqrt(np.mean(audio**2))

    print(f"\n📁 {track_path.name}")
    print(f"   Duration: {duration:.2f}s | Peak: {peak:.3f} | RMS: {rms:.3f}")

# %%
# Error Handling
# --------------
#
# The loader provides clear errors for common issues:

try:
    load_audio("nonexistent_file.wav")
except FileNotFoundError as e:
    print(f"\n❌ File not found: {e}")

# %%
# Cleanup
import shutil

shutil.rmtree(temp_dir)
print("\n✅ Audio loading examples complete!")
