# mixref Developer Companion

**Project**: mixref – CLI Audio Analyzer for Music Producers  
**Focus**: Electronic Music, Drum & Bass, Techno  
**Status**: Active Development  
**Last Updated**: 2026-01-30

---

## 🎯 PROJECT VISION
A sharp, opinionated audio tool that speaks the language of producers. Not another generic analyzer—something that understands that a DnB track should hit differently than a deep house tune.

---

## 🛠️ BUILD SPECS

### Core Stack
```
Python 3.12+
uv for dependency wrangling
Typer + Rich = beautiful CLI
Audio: librosa, pyloudnorm, soundfile
```

### Directory Blueprint
```
mixref/
├── src/mixref/
│   ├── cli/           # Command definitions
│   ├── audio/         # Raw audio handling
│   ├── meters/        # LUFS, peaks, LRA
│   ├── detective/     # BPM, key, spectral
│   └── compare/       # A/B comparison engine
├── tests/
│   └── synthetic_audio.py  # Fake tracks for testing
└── pyproject.toml
```

---

## 🔊 AUDIO PHILOSOPHY

### Loudness Rules
- **Streaming**: -14 LUFS (play nice with platforms)
- **Club/DnB**: -8 to -6 LUFS (when you need to slap)
- **True Peak**: Never clip above -1.0 dBTP
- **LRA**: < 8LU for compressed genres, > 12LU for dynamic

### BPM Detection
Electronic music cheat codes:
- If BPM < 100 → probably half-time detection → double it
- DnB range: 160-180 BPM
- Techno range: 120-140 BPM
- House range: 118-128 BPM

### Key Notation
- **Prefer flats**: Eb minor, not D# minor
- **Camelot codes**: 8A, 5B, etc. (DJs love this)
- **Confidence score**: Show how sure we are

---

## ⌨️ CLI PERSONALITY

### Commands Structure
```
mixref analyze <file> [--genre dnb|techno|house]
mixref compare <my_track> <reference> [--focus bass|highs|mids]
mixref shootout <folder>  # Batch compare multiple tracks
```

### Output Vibe
- Clean Rich tables with subtle colors
- Warning messages in yellow with specific suggestions
- Progress bars for anything taking > 2 seconds
- JSON output available but not the default

### Exit Codes
```
0 = Everything's perfect
1 = Something broke (file error, etc.)
2 = Warning (clipping detected, but analysis complete)
3 = You used it wrong (invalid args)
```

---

## 🧠 COPILOT CONVERSATION GUIDE

### When Starting New Feature
```
"Create a function that loads WAV files and handles mono/stereo conversion.
Use soundfile for reading, return numpy array and sample rate.
Include error handling for corrupt files."
```

### For Audio Processing Logic
```
"Implement EBU R128 loudness measurement using pyloudnorm.
Meter should be K-weighted, include integrated LUFS and true peak.
Add option for genre-specific targets."
```

### For CLI Polish
```
"Make a Rich table showing frequency band comparison.
Left column: my track, right column: reference.
Highlight differences > 3dB in yellow."
```

---

## 🎛️ GENRE PRESETS (THE SECRET SAUCE)

### DnB Mode (`--genre dnb`)
- Focus: Sub-bass clarity (40-80Hz)
- Expect: Heavy sidechain, sharp transients
- Warning if: Kick and bass fighting in same frequency

### Techno Mode (`--genre techno`)
- Focus: Kick weight (60-100Hz), hi-hat presence (8-12kHz)
- Expect: 4/4 kick, minimal dynamics
- Warning if: Too much mid-range mud (250-500Hz)

### House Mode (`--genre house`)
- Focus: Vocal clarity (2-5kHz), bass warmth (100-200Hz)
- Expect: Groove, swing, dynamics
- Warning if: Vocals buried or bass too thin

---

## 🧪 TESTING WITH FAKE AUDIO

Never commit real tracks. Generate synthetic test signals:

```python
# Test fixtures should create:
- Sine wave at 440Hz (A4 reference)
- Pink noise (full spectrum)
- Kick drum impulse (synthesized)
- Silent buffer (edge case)
- Clipped signal (for warning tests)
```

---

## 🚀 DEVELOPMENT MILESTONES

### Week 1: Foundation
- [ ] Project skeleton with uv
- [ ] Basic CLI with `--help`
- [ ] WAV file loader with channel handling
- [ ] LUFS meter implementation

### Week 2: Analysis Suite
- [ ] BPM detection (with genre awareness)
- [ ] Key detection (Camelot output)
- [ ] Frequency band analyzer
- [ ] `mixref analyze` command complete

### Week 3: Comparison Engine
- [ ] Track vs Reference comparison
- [ ] Smart suggestions engine
- [ ] Genre-specific feedback
- [ ] `mixref compare` command

### Week 4: Polish & Ship
- [ ] JSON output option
- [ ] All tests passing
- [ ] README with producer examples
- [ ] PyPI package ready

---

## 💬 CODE VOICE & STYLE

- **Type hints**: Every function, no exceptions
- **Docstrings**: Google style, include example usage
- **Spanish comments**: OK for personal notes
- **Function size**: If it doesn't fit on screen, split it
- **Naming**: `calculate_lufs()` not `calcLufs()`
- **Errors**: Custom exception classes, helpful messages

---

## 🔧 QUICK START FOR DEVELOPER

```bash
# Inside the Copilot container:
uv init mixref --package
cd mixref

# Create the audio soul:
mkdir -p src/mixref/{audio,meters,detective,compare}

# First command to build:
echo 'Build the analyze command with loudness and BPM detection'
```

---

## 🎧 PRODUCER-FRIENDLY OUTPUT EXAMPLE

What the user should see:

```
╭─ mixref analyze ──────────────────────────╮
│                                           │
│  Track:     neurofunk_banger.wav         │
│  Duration:  4:22 | 160.5 BPM | 8A        │
│                                           │
│  LOUDNESS                                │
│  • LUFS:    -6.2  (DnB target: -8 to -6) │
│  • Peak:    -0.8 dBTP  ⚠️ Near clipping! │
│  • LRA:     5.2 LU (very compressed)     │
│                                           │
│  SPECTRAL BALANCE                        │
│  • Sub:     ■■■■■■■□□□ (strong)          │
│  • Bass:    ■■■■■■■■■■ (dominant)        │
│  • Mids:    ■■■■■□□□□□ (could open up)   │
│  • Highs:   ■■■■■■■■■□ (crisp)           │
│                                           │
╰───────────────────────────────────────────╯

⚠️  Suggestion: Your sub-bass is 4dB hotter than
    typical DnB references. Check 40Hz region.
```

---

## 📦 SHIP CRITERIA

Ready when:
- [ ] Analyzes any WAV/FLAC/MP3 you throw at it
- [ ] Gives useful feedback to producers
- [ ] Runs fast enough for batch processing
- [ ] Doesn't crash on weird edge cases
- [ ] Makes a DnB producer nod and say "useful"

Example output:

```bash
# Análisis rápido con output bonito
$ mixref analyze my_track.wav

╭─────────────────── Track Analysis ───────────────────╮
│ File: my_track.wav                                   │
│ Duration: 5:32 | Sample Rate: 44.1kHz | Stereo       │
├──────────────────────────────────────────────────────┤
│ 🎚️  LOUDNESS                                         │
│   Integrated LUFS:  -8.2                             │
│   True Peak:        -0.3 dBTP  ⚠️  (clip risk)       │
│   LRA:              6.2 LU                           │
│   Short-term range: -12.1 to -6.8 LUFS              │
├──────────────────────────────────────────────────────┤
│ 🎵  RHYTHM & TONALITY                                │
│   BPM:              174 (confidence: 0.92)           │
│   Key:              F minor (confidence: 0.78)       │
├──────────────────────────────────────────────────────┤
│ 📊  PLATFORM TARGETS                                 │
│   Spotify (-14):    🔴 +5.8 dB too loud              │
│   YouTube (-14):    🔴 +5.8 dB too loud              │
│   Apple Music (-16):🔴 +7.8 dB too loud              │
│   Club/DJ:          🟢 OK                            │
╰──────────────────────────────────────────────────────╯

# 🔥 LA FUNCIÓN KILLER: Comparación con referencia
$ mixref compare my_mix.wav noisia_track.wav

╭─────────────── Reference Comparison ─────────────────╮
│ YOUR MIX vs REFERENCE                                │
├──────────────────────────────────────────────────────┤
│ LOUDNESS                    YOU      REF     DIFF    │
│   Integrated LUFS:         -8.2    -6.1    -2.1 🔻   │
│   True Peak:               -0.3    -0.8    +0.5 ⚠️   │
│   Dynamic Range (LRA):      6.2     4.8    +1.4      │
├──────────────────────────────────────────────────────┤
│ SPECTRAL BALANCE           YOU      REF     DIFF    │
│   Sub (20-60Hz):          -18.2   -15.1    -3.1 🔻   │
│   Low (60-250Hz):         -12.4   -11.8    -0.6      │
│   Mid (250-2kHz):          -8.1    -7.2    -0.9      │
│   High (2k-8kHz):         -14.2   -12.1    -2.1 🔻   │
│   Air (8k-20kHz):         -22.1   -18.4    -3.7 🔻   │
├──────────────────────────────────────────────────────┤
│ 💡 SUGGESTIONS                                       │
│   • Tu sub está 3dB por debajo - revisa el sidechain│
│   • Los highs podrían tener más presencia           │
│   • Referencia más comprimida (considera limiter)   │
╰──────────────────────────────────────────────────────╯

# Batch analysis
$ mixref batch ./renders/ --format csv > analysis.csv

# JSON para scripts
$ mixref analyze track.wav --json | jq '.lufs.integrated'
```
