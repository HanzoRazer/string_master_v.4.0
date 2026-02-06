# `zt-gravity` CLI Tool Documentation

**Command-line interface for the Zone-Tritone System.**

---

## 🎯 Overview

`zt-gravity` is a musician-facing CLI tool that provides:

1. **Gravity chains** — Generate dominant cycles descending in fourths
2. **Chord analysis** — Analyze harmonic progressions using the Zone-Tritone framework
3. **Markov models** — Build transition probability matrices from chord sequences

---

## 🎵 MIDI Generation Invariants (Do Not Break)

All generated MIDI must satisfy:
- Standard MIDI File (SMF) Type 1 preferred (multi-track) unless intentionally Type 0.
- Valid tempo map (BPM) and time signature events at time 0.
- No stuck notes: every note_on must have a corresponding note_off.
- Deterministic outputs when seed/inputs are identical (unless explicitly randomized with a documented seed).
- Track names should be stable when possible (e.g., Comp, Bass, Drums, Meta).
- Output must import cleanly in a DAW without manual repair.

**Quick smoke test:**
- Generate → import into DAW → press play → sound + no hanging notes.

---

## 📦 Installation

After installing the `zone-tritone` package:

```bash
pip install -e .
```

The `zt-gravity` command becomes available in your terminal.

### Alternative Usage

If the command isn't in your PATH, use:

```bash
python -m zone_tritone.cli [command] [options]
```

---

## 🛠 Commands

### `gravity` — Generate Gravity Chains

Print a dominant cycle (circle of fourths) starting from any root.

#### Syntax

```bash
zt-gravity gravity --root <NOTE> [--steps <N>]
```

#### Options

- `--root` (required) — Starting note name (C, F#, Bb, etc.)
- `--steps` (optional) — Number of steps to generate (default: 7)

#### Examples

**Basic gravity chain from G:**

```bash
zt-gravity gravity --root G --steps 7
```

Output:

```
# Gravity chain starting from G (steps=7)
# (cycle of fourths, Zone–Tritone gravity view)

 0: G    (pc= 7, Zone 2)
 1: C    (pc= 0, Zone 1)
 2: F    (pc= 5, Zone 2)
 3: Bb   (pc=10, Zone 1)
 4: Eb   (pc= 3, Zone 2)
 5: Ab   (pc= 8, Zone 1)
 6: C#   (pc= 1, Zone 2)
 7: F#   (pc= 6, Zone 1)
```

**Complete cycle (12 steps):**

```bash
zt-gravity gravity --root C --steps 12
```

**Short chain for analysis:**

```bash
zt-gravity gravity --root D --steps 3
```

---

### `analyze` — Analyze Chord Sequences

Analyze harmonic progressions using the Zone-Tritone gravity model.

#### Syntax

```bash
zt-gravity analyze [--chords "..."] [--file PATH] [OPTIONS]
```

#### Options

- `--chords <STRING>` — Inline chord sequence (space-separated)
- `--file <PATH>` — Path to text file with chord symbols
- `--smoothing <FLOAT>` — Laplace smoothing value (default: 0.1)
- `--show-matrix` — Display full 12×12 transition probability matrix

**Note:** Either `--chords` or `--file` must be provided.

#### Examples

**Analyze a ii-V-I progression:**

```bash
zt-gravity analyze --chords "Dm7 G7 Cmaj7"
```

Output:

```
# Zone–Tritone Gravity Analysis
# Chord sequence:
  Dm7 G7 Cmaj7

# Root sequence (pc / name):
   2:D  7:G  0:C

# Transition statistics:
  Total transitions      : 2
  Descending 4th motion  : 0 (0.0% if any)
  Same-root transitions  : 0
```

**Analyze a longer sequence:**

```bash
zt-gravity analyze --chords "Dm7 G7 Cmaj7 A7 Dm7 G7 Cmaj7"
```

**Analyze from a file:**

```bash
zt-gravity analyze --file my_tune.txt
```

**Show full probability matrix:**

```bash
zt-gravity analyze --chords "Dm7 G7 Cmaj7 Fmaj7" --show-matrix
```

Output includes 12×12 matrix:

```
# Transition probability matrix (rows = from, cols = to)
        0    1    2    3    4    5    6    7    8    9   10   11
 0: 0.03 0.03 0.03 0.03 0.03 0.66 0.03 0.03 0.03 0.03 0.03 0.03
 2: 0.03 0.03 0.03 0.03 0.03 0.03 0.03 0.66 0.03 0.03 0.03 0.03
 ...
```

---

## 📄 Chord File Format

Chord files should contain space-separated chord symbols, one or more per line.

### Example: `my_tune.txt`

```
Dm7 G7 Cmaj7
Fmaj7 Bbmaj7 Ebmaj7
Am7 D7 Gmaj7
Cm7 F7 Bbmaj7
```

Lines can be organized by section:

```
# Intro
Cmaj7 Fmaj7

# A Section
Dm7 G7 Cmaj7
Em7 A7 Dmaj7

# Bridge
Fm7 Bb7 Ebmaj7
Gm7 C7 Fmaj7
```

**Note:** Lines starting with `#` are treated as chord symbols. Use blank lines for visual separation.

---

## 🎼 Usage Patterns

### Exploring Harmonic Relationships

**Generate all tritone substitutes for a dominant:**

```bash
# Original: G7
zt-gravity gravity --root G --steps 1

# Substitute: Db7
zt-gravity gravity --root Db --steps 1
```

### Analyzing Jazz Standards

**Step 1:** Create a chord file with the changes

```bash
echo "Dm7 G7 Cmaj7 Cmaj7" > rhythm_changes_a.txt
echo "Dm7 G7 Cmaj7 Cmaj7" >> rhythm_changes_a.txt
echo "Em7 A7 Dm7 G7" >> rhythm_changes_a.txt
echo "Dm7 G7 Cmaj7 Cmaj7" >> rhythm_changes_a.txt
```

**Step 2:** Analyze

```bash
zt-gravity analyze --file rhythm_changes_a.txt --show-matrix
```

### Comparing Different Progressions

**Modal progression (zone-stable):**

```bash
zt-gravity analyze --chords "Cmaj7 Dm7 Em7 Fmaj7"
```

**Functional progression (zone-crossing):**

```bash
zt-gravity analyze --chords "Dm7 G7 Cmaj7 A7"
```

---

## 🧪 Integration with Python

The CLI can be called from Python scripts:

```python
import subprocess

result = subprocess.run(
    ["zt-gravity", "gravity", "--root", "C", "--steps", "5"],
    capture_output=True,
    text=True,
)

print(result.stdout)
```

Or use the library directly:

```python
from zone_tritone.cli import main

# Run with custom arguments
exit_code = main(["gravity", "--root", "G", "--steps", "7"])
```

---

## 📊 Output Interpretation

### Gravity Chain Output

- **Index** — Step number in the chain (0 = starting root)
- **Note** — Pitch class name (C, C#, D, etc.)
- **pc** — Pitch class integer (0-11)
- **Zone** — Whole-tone zone (Zone 1 = even, Zone 2 = odd)

### Analysis Output

- **Root sequence** — Pitch classes extracted from chord symbols
- **Total transitions** — Number of chord changes
- **Descending 4th motion** — Count of strong functional resolutions (V→I pattern)
- **Same-root transitions** — Chord quality changes without root movement

### Transition Matrix

- **Rows** — Source pitch class (where you're coming from)
- **Columns** — Target pitch class (where you're going to)
- **Values** — Probability of transition (0.0 to 1.0)
- **High values (>0.5)** — Strong gravitational pull

---

## 🎯 Common Use Cases

### 1. Learning Dominant Cycles

```bash
zt-gravity gravity --root G --steps 11
```

Memorize the sequence for jazz comping.

### 2. Analyzing Your Compositions

```bash
# Save your progression
echo "Cmaj7 Am7 Dm7 G7 Cmaj7" > my_song.txt

# Analyze it
zt-gravity analyze --file my_song.txt
```

### 3. Comparing Genres

**Jazz standard:**
```bash
zt-gravity analyze --chords "Dm7 G7 Cmaj7 Am7 Dm7 G7 Cmaj7"
```

**Pop progression:**
```bash
zt-gravity analyze --chords "C G Am F C G Am F"
```

Compare transition statistics to see harmonic differences.

### 4. Ear Training

Generate a chain, then practice singing/playing each root:

```bash
zt-gravity gravity --root F --steps 5
```

### 5. Teaching

Show students the relationship between tritones and dominants:

```bash
# Show G7 resolves to C
zt-gravity gravity --root G --steps 1

# Show Db7 also resolves to C (tritone sub)
zt-gravity gravity --root Db --steps 1
```

---

## 🚀 Advanced Features

### Custom Smoothing

Control how the Markov model handles unseen transitions:

```bash
# More smoothing (uniform distribution bias)
zt-gravity analyze --chords "Dm7 G7 Cmaj7" --smoothing 1.0

# Less smoothing (data-driven)
zt-gravity analyze --chords "Dm7 G7 Cmaj7" --smoothing 0.01
```

### Piping and Scripting

Pipe chord sequences:

```bash
echo "Dm7 G7 Cmaj7" | xargs zt-gravity analyze --chords
```

Process multiple files:

```bash
for file in *.txt; do
    echo "=== $file ==="
    zt-gravity analyze --file "$file"
done
```

---

## ❓ Troubleshooting

### Command not found

**Solution 1:** Use module syntax:

```bash
python -m zone_tritone.cli gravity --root C
```

**Solution 2:** Check if `.venv/Scripts` is in PATH (Windows) or `.venv/bin` (Unix).

### Invalid note name

```
error: Unrecognized pitch name: 'X'
```

Use standard note names: C, C#, Db, D, D#, Eb, E, F, F#, Gb, G, G#, Ab, A, A#, Bb, B

### File not found

```
error: file not found: chords.txt
```

Use absolute path or ensure file is in current directory:

```bash
zt-gravity analyze --file /full/path/to/chords.txt
```

---

## 📚 Related Documentation

- [PYTHON_PACKAGE.md](PYTHON_PACKAGE.md) — Python API reference
- [demo.py](demo.py) — Interactive library demo
- [README.md](README.md) — Project overview
- [CANON.md](CANON.md) — Theoretical foundations

---

## 🔬 Testing

CLI smoke tests are included:

```bash
pytest tests/test_cli_smoke.py -v
```

---

## 🎓 Educational Use

The CLI is designed for:

- **Music theory students** — Visualize dominant cycles
- **Jazz musicians** — Analyze standards and progressions
- **Composers** — Validate harmonic choices
- **Educators** — Demonstrate Zone-Tritone concepts
- **Researchers** — Extract transition statistics from corpora

---

## Raspberry Pi + Ardour Quick-Start (Proof-of-Sound)

This guide verifies that zt-band MIDI output produces audible sound on a
Raspberry Pi using Ardour.

### Supported Platform
- Raspberry Pi 5
- Raspberry Pi OS (64-bit) or Debian 12
- I2S or USB audio interface
- Ardour (Linux build)

---

### 1. Install Ardour
```bash
sudo apt update
sudo apt install ardour
```

(Optional but recommended for MIDI sound)
```bash
sudo apt install fluidsynth fluid-soundfont-gm
```

### 2. Audio System Settings (First Launch)

When Ardour starts:

- **Audio System**: ALSA (or JACK if already configured)
- **Sample Rate**: 48000
- **Buffer Size**: 128 (256 if underruns occur)
- **Input/Output device**: select your I2S codec or USB interface

### 3. Import zt-band MIDI

Generate MIDI using zt-band:
```bash
zt-band play <program>.ztprog
```

Export for DAW use:
```bash
zt-band daw-export --midi output.mid
```

Open Ardour:
- Drag the exported `.mid` file into the timeline
- Accept tempo and time-signature prompts

### 4. Assign Sound (If Silent)

If no sound is heard:
- Add a MIDI track instrument
- Load FluidSynth
- Select a GM sound (piano, bass, etc.)

This is expected behavior on fresh systems.

### 5. Proof-of-Sound Checklist

- ▶ Press Play → sound is heard
- ⏱ Tempo matches program
- 🎼 No stuck or hanging notes
- 📁 MIDI imports without errors

**At this point, Project 1A is complete.**

---

## Headless Raspberry Pi Operation

zt-band does not require a graphical environment.

Supported headless workflow:
- SSH into Pi
- Generate MIDI via CLI
- Export DAW-ready bundles
- Transfer files via SCP or USB

Example:
```bash
zt-band play cycle_5ths.ztprog
zt-band daw-export --midi output.mid
scp exports/daw/*/*.mid user@desktop:/music/
```

The DAW may run on another machine if desired.

**This keeps your Smart Guitar usable without a screen.**

---

**Built with canonical precision. Ready for musicians.**
