# System Flow — Smart Guitar Audio Architecture

This document describes the **end-to-end flow of data** in the Smart Guitar
ecosystem.

The design intentionally separates:
- musical intelligence
- user interaction
- sound production

---

## High-Level Flow

```
       ┌──────────────┐
       │   Touch UI   │
       │  (Pi Screen) │
       └──────┬───────┘
              │ select / control
              ▼
       ┌──────────────┐
       │   zt-band    │
       │ (Music Gen)  │
       └──────┬───────┘
              │ MIDI
              ▼
       ┌──────────────┐
       │     DAW      │
       │  (Ardour)    │
       └──────┬───────┘
              │ Audio
              ▼
       ┌──────────────┐
       │  Speakers /  │
       │  Headphones  │
       └──────────────┘
```

---

## Responsibilities by Layer

### Touch UI (Raspberry Pi)
- Program selection (.ztprog)
- Playlist control (.ztplay)
- Tempo / key / style changes
- Start / stop
- Export trigger

**Non-Goals**
- No MIDI editing
- No piano-roll
- No waveform manipulation

---

### zt-band (Musical Brain)
- Generates deterministic MIDI
- Applies harmonic logic
- Produces DAW-safe files
- Remains DAW-agnostic

---

### DAW (Sound Engine)
- Renders MIDI into audio
- Handles instruments, FX, mixing
- Provides recording and export

**zt-band never assumes a specific DAW.**

---

## Design Principle

> **zt-band generates music.  
> The DAW makes sound.  
> The UI controls intent.**

This separation preserves:
- portability
- reliability
- long-term maintainability

---

## Why This Matters (Engineering Insight)

You've now:
- ✅ avoided writing a DAW
- ✅ avoided UI bloat
- ✅ preserved Linux + Pi viability
- ✅ created a clean production boundary

**That's how real ecosystems survive.**

---

## High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    SMART GUITAR PLATFORM                         │
└──────────────────────────────────────────────────────────────────┘
         │
         ├─────────────────────────────────────────────────────────┐
         │                                                         │
    [Theory Core]                                         [Practice Tools]
         │                                                         │
         ├─── shared/zone_tritone/                               ├─── zt_band/
         │    ├─ pc.py                                           │    ├─ cli.py
         │    ├─ zones.py                                        │    ├─ engine.py
         │    ├─ tritones.py                                     │    ├─ patterns.py
         │    ├─ gravity.py                                      │    ├─ daw_export.py
         │    ├─ corpus.py                                       │    └─ (future modules)
         │    ├─ markov.py                                       │
         │    ├─ cli.py (zt-gravity)                            │
         │    └─ types.py                                        │
         │                                                         │
         ▼                                                         ▼
   [Analysis Tools]                                      [Accompaniment Engine]
         │                                                         │
         ├─ zt-gravity CLI                                       ├─ zt-band CLI
         │  ├─ gravity chain                                     │  ├─ create (generate)
         │  ├─ analyze progression                               │  ├─ play (preview)
         │  ├─ explain (3 formats)                               │  ├─ ex-run (exercises)
         │  └─ markov analysis                                   │  └─ daw-export
         │                                                         │
         ▼                                                         ▼
   [Educational Output]                                  [MIDI Output]
         │                                                         │
         ├─ Text reports                                         ├─ Standard MIDI files
         ├─ HTML visualizations                                  │  (SMF Type 1, 480 PPQN)
         ├─ Markdown analysis                                    │
         └─ Transition matrices                                  │
                                                                  ▼
                                                         [DAW Integration]
                                                                  │
                                                                  ├─ Ardour (Pi)
                                                                  ├─ Reaper
                                                                  ├─ Ableton
                                                                  ├─ Logic
                                                                  └─ (any DAW)
                                                                  │
                                                                  ▼
                                                              [Audio Output]
```

---

## Component Relationships

### 1. Theory Core → Analysis Tools

```
shared/zone_tritone/
    │
    ├─ pc.py              ──→  Pitch class operations
    ├─ zones.py           ──→  Zone membership & crossing
    ├─ tritones.py        ──→  Tritone axes & partners
    ├─ gravity.py         ──→  Dominant cycles (cycle of 4ths)
    ├─ corpus.py          ──→  Chord parsing
    ├─ markov.py          ──→  Transition probability
    └─ types.py           ──→  Type aliases (PitchClass, etc.)
           │
           ▼
    zt-gravity CLI
           │
           ├─ gravity --root C --steps 7
           ├─ analyze --chords "Dm7 G7 Cmaj7"
           └─ explain --chords "Dm7 G7 C" --format markdown
           │
           ▼
    Output: text, HTML, markdown
```

---

### 2. Theory Core → Accompaniment Engine

```
shared/zone_tritone/
    │
    ├─ gravity.py         ──→  Generates bass lines (descending 4ths)
    ├─ zones.py           ──→  Validates zone-crossing motion
    ├─ corpus.py          ──→  Parses chord symbols
    └─ markov.py          ──→  Predicts next chords
           │
           ▼
    zt_band/
           │
           ├─ engine.py          (progression → MIDI conversion)
           ├─ patterns.py        (voicing templates)
           ├─ daw_export.py      (DAW-ready export)
           └─ cli.py             (user interface)
           │
           ▼
    zt-band CLI
           │
           ├─ create --chords "Dm7 G7 C" --style swing
           ├─ daw-export backing.mid
           └─ ex-run exercises/cycle_fifths_roots.ztex
           │
           ▼
    Output: Standard MIDI files
```

---

### 3. MIDI → DAW → Audio

```
zt-band CLI
    │
    ├─ create --chords "Dm7 G7 Cmaj7" --tempo 120
    │       │
    │       ▼
    │   backing.mid (root directory)
    │       │
    │       ▼
    ├─ daw-export backing.mid
            │
            ▼
    exports/daw/YYYY-MM-DD_HHMMSS/
            ├─ backing.mid
            └─ IMPORT_DAW.md
            │
            ▼
    [User Action: Import to DAW]
            │
            ├─ Drag & drop into Ardour/Reaper/Ableton
            ├─ 3 MIDI tracks created (Comp, Bass, Drums)
            ├─ Assign virtual instruments
            │       │
            │       ▼
            │   Piano (Channel 0)
            │   Bass  (Channel 1)
            │   Drums (Channel 9)
            │
            ▼
    Audio Playback
            │
            ├─ Practice improvisation
            ├─ Record takes
            └─ Export audio mix
```

---

## Data Flow: Theory Analysis

### zt-gravity CLI Workflow

```
User Input
    │
    ▼
[zt-gravity analyze --chords "Dm7 G7 Cmaj7"]
    │
    ├─ Parse chord symbols      (corpus.py)
    │       │
    │       ▼
    │   [2, 7, 0]  (D, G, C pitch classes)
    │
    ├─ Identify zones           (zones.py)
    │       │
    │       ▼
    │   Dm7 → Zone 2
    │   G7  → Zone 2
    │   Cmaj7 → Zone 1
    │
    ├─ Detect zone-crossing     (zones.py)
    │       │
    │       ▼
    │   G7 → Cmaj7: Yes (B→C, F→E)
    │
    ├─ Find tritone anchors     (tritones.py)
    │       │
    │       ▼
    │   G7: B-F tritone
    │
    └─ Generate gravity chain   (gravity.py)
            │
            ▼
        G → C → F → Bb → Eb...
            │
            ▼
    Output: Analysis report
        ├─ Text format
        ├─ HTML visualization
        └─ Markdown documentation
```

---

## Data Flow: Accompaniment Generation

### zt-band CLI Workflow

```
User Input
    │
    ▼
[zt-band create --chords "Dm7 G7 Cmaj7" --style swing --tempo 120]
    │
    ├─ Parse progression        (corpus.py)
    │       │
    │       ▼
    │   [Dm7, G7, Cmaj7] → [2, 7, 0]
    │
    ├─ Load style template      (patterns.py)
    │       │
    │       ▼
    │   Swing: comp pattern, walking bass, swing drums
    │
    ├─ Generate MIDI tracks     (engine.py)
    │       │
    │       ├─ Comp:   Shell voicings (root, 3rd, 7th)
    │       ├─ Bass:   Walking line (gravity chain)
    │       └─ Drums:  Swing pattern (ride, hi-hat)
    │               │
    │               ▼
    │           backing.mid (root directory)
    │
    └─ Export for DAW           (daw_export.py)
            │
            ├─ Create timestamped folder
            ├─ Inject GM program changes
            ├─ Write IMPORT_DAW.md guide
            │       │
            │       ▼
            │   exports/daw/2025-12-29_143022/
            │       ├─ backing.mid
            │       └─ IMPORT_DAW.md
            │
            ▼
    Ready for DAW import
```

---

## Import Protocol

### Critical: Relative vs Absolute Imports

```
src/
├── shared/
│   └── zone_tritone/
│       ├── pc.py                 [Use RELATIVE imports]
│       │   from .zones import zone
│       │   from .types import PitchClass
│       │
│       ├── gravity.py            [Use RELATIVE imports]
│       │   from .pc import pc_from_name
│       │   from .tritones import tritone_partner
│       │
│       └── cli.py                [Use RELATIVE imports]
│           from .gravity import gravity_chain
│           from .corpus import chord_sequence_to_roots
│
└── zt_band/
    ├── engine.py                 [Use ABSOLUTE imports]
    │   from shared.zone_tritone.pc import pc_from_name
    │   from shared.zone_tritone.gravity import gravity_chain
    │
    └── daw_export.py             [Use ABSOLUTE imports]
        from shared.zone_tritone.zones import zone_name
        from shared.zone_tritone.types import PitchClass

tests/
└── test_*.py                     [Use ABSOLUTE imports]
    from shared.zone_tritone import pc_from_name, zone
```

**Rule:** Within `zone_tritone/` → relative; outside → absolute.

---

## File Format Ecosystem

### .ztprog (Chord Progressions)

```yaml
name: "Autumn Leaves - Ballad"
chords: [Cm7, F7, Bbmaj7, Ebmaj7, Am7b5, D7, Gm7]
style: "ballad_basic"
tempo: 70
bars_per_chord: 2
tritone_mode: "probabilistic"
outfile: "autumn_leaves_ballad.mid"
```

**Used by:** `zt-band create --program programs/autumn_leaves.ztprog`

---

### .ztex (Exercises)

```yaml
name: "Cycle of Fifths — Roots"
program: "../programs/cycle_fifths_all_keys.ztprog"
exercise_type: "cycle_fifths_roots"
task:
  mode: "play_roots"
  instructions: "Play root of each chord..."
```

**Used by:** `zt-band ex-run exercises/cycle_fifths_roots.ztex`

---

### .ztplay (Playlists)

```yaml
name: "Zone Theory Session"
exercises:
  - exercises/cycle_fifths_roots.ztex
  - exercises/cycle_fourths_ii_v_i_guidetones.ztex
description: "Progressive zone awareness training"
```

**Used by:** Future playlist runner (not yet implemented)

---

## Future System Flow (Roadmap)

### Vision: Pi Touchscreen Integration

```
┌─────────────────────────────────────────────────────────────┐
│  Raspberry Pi Touch Display (7" or 10")                     │
│                                                              │
│  [Zone-Tritone Practice App]                                │
│                                                              │
│  ┌──────────────────┐  ┌──────────────────┐               │
│  │ Select Program   │  │ Choose Style     │               │
│  │ • Autumn Leaves  │  │ • Swing          │               │
│  │ • ii-V-I Workout │  │ • Bossa Nova     │               │
│  │ • Cycle of 5ths  │  │ • Ballad         │               │
│  └──────────────────┘  └──────────────────┘               │
│                                                              │
│  Tempo: [────●────────]  120 BPM                            │
│                                                              │
│  [▶ Play] [⏹ Stop] [⏭ Next] [💾 Export]                   │
└─────────────────────────────────────────────────────────────┘
         │
         ├─ zt-band (background process)
         │       │
         │       ▼
         │   backing.mid
         │       │
         │       ▼
         ├─ Auto-export to DAW watch folder
         │       │
         │       ▼
         └─ Ardour (or JACK-routed FluidSynth)
                 │
                 ▼
             Audio output → speakers/headphones
```

**Status:** Not yet implemented (zt-band CLI is current MVP)

---

## Module Dependencies

### Theory Core (Internal)

```
pc.py          [no dependencies]
    │
    ▼
zones.py       depends on: pc.py
    │
    ▼
tritones.py    depends on: pc.py
    │
    ▼
gravity.py     depends on: tritones.py, pc.py
    │
    ▼
corpus.py      depends on: pc.py
    │
    ▼
markov.py      depends on: None (standalone)
    │
    ▼
cli.py         depends on: ALL (main entry point)
```

---

### Accompaniment Engine (External Dependencies)

```
zt_band/engine.py
    │
    ├─ depends on: shared.zone_tritone.pc
    ├─ depends on: shared.zone_tritone.gravity
    ├─ depends on: shared.zone_tritone.corpus
    └─ depends on: mido (MIDI library)

zt_band/daw_export.py
    │
    ├─ depends on: shared.zone_tritone.zones
    ├─ depends on: shared.zone_tritone.types
    └─ depends on: mido

zt_band/cli.py
    │
    ├─ depends on: zt_band.engine
    ├─ depends on: zt_band.daw_export
    └─ depends on: argparse, pathlib
```

---

## Testing Architecture

```
tests/
├── test_pc.py              → tests shared/zone_tritone/pc.py
├── test_zones.py           → tests shared/zone_tritone/zones.py
├── test_tritones.py        → tests shared/zone_tritone/tritones.py
├── test_gravity.py         → tests shared/zone_tritone/gravity.py
├── test_markov.py          → tests shared/zone_tritone/markov.py
└── test_cli_smoke.py       → tests CLI entry points

Run: python -m pytest tests/ -v
Expected: 15 tests passing
```

---

## Entry Points (CLI)

### Defined in pyproject.toml

```toml
[project.scripts]
zt-gravity = "shared.zone_tritone.cli:main"
zt-band = "zt_band.cli:main"
```

### Invocation Methods

```bash
# Method 1: Entry point (after pip install -e .)
zt-gravity gravity --root C --steps 7
zt-band create --chords "Dm7 G7 C"

# Method 2: Python module invocation
python -m shared.zone_tritone.cli gravity --root C
python -m zt_band.cli create --chords "Dm7 G7 C"
```

---

## Package Metadata

```
Package Name:  smart-guitar
Version:       0.1.0
Python:        ≥3.10
Dependencies:  mido>=1.2.10, pyyaml>=6.0
License:       MIT (code), Protected IP (theory)
Homepage:      https://github.com/HanzoRazer/string_master_v.4.0
```

---

## Deployment Scenarios

### Scenario 1: Development Workstation

```
Windows/Mac/Linux Desktop
    │
    ├─ Python 3.10+ virtual environment
    ├─ pip install -e . (editable mode)
    ├─ Run zt-gravity for analysis
    ├─ Run zt-band for MIDI generation
    └─ Import MIDI into DAW (any platform)
```

---

### Scenario 2: Raspberry Pi Practice Station

```
Raspberry Pi 4/5 (8GB)
    │
    ├─ Pi OS (Debian-based Linux)
    ├─ Python 3.10+ (pre-installed)
    ├─ smart-guitar package installed
    ├─ Ardour for audio playback
    ├─ Optional: 7" touch display
    └─ MIDI over USB to external sound module
```

---

### Scenario 3: Headless Server (Future)

```
Linux Server (cloud or local)
    │
    ├─ Flask/FastAPI web interface
    ├─ zt-band as API endpoint
    ├─ Generate MIDI on demand
    ├─ Return MIDI files via HTTP
    └─ Users download for local DAW import
```

---

## Security & Governance

### Protected Components

**Theory Framework:**
- CANON.md (immutable axioms)
- GLOSSARY.md (frozen terminology)
- PEDAGOGY.md (pedagogical sequence)
- GOVERNANCE.md (change control)

**Changes require:** Governance approval (see GOVERNANCE.md)

---

### Open Components

**Code:**
- All Python modules (MIT License)
- CLI tools
- MIDI generation
- DAW export

**Contributions:** Welcome via pull requests (follow DEVELOPER_GUIDE.md)

---

## Performance Characteristics

### zt-gravity CLI

**Typical execution time:**
- gravity chain: <10ms
- analyze progression: <50ms
- explain (with HTML): <100ms
- markov analysis: <200ms (scales with corpus size)

**Bottlenecks:** None for typical use cases

---

### zt-band CLI

**Typical execution time:**
- create (4-bar progression): <500ms
- daw-export: <100ms
- ex-run (exercise): <1s (varies with exercise length)

**Bottlenecks:**
- MIDI file I/O (minimal impact)
- Large progressions (100+ chords): 1-2s

**Optimization:** All operations deterministic, no network calls

---

## Error Handling Patterns

### Theory Core

```python
# pc.py
def pc_from_name(note: str) -> int:
    """Convert note name to pitch class.
    
    Raises:
        ValueError: If note name is invalid
    """
    if note not in VALID_NOTES:
        raise ValueError(f"Invalid note: {note}")
    return NOTE_TO_PC[note]
```

---

### CLI Layer

```python
# cli.py
def cmd_gravity(args):
    try:
        root_pc = pc_from_name(args.root)
        chain = gravity_chain(root_pc, args.steps)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    return 0
```

**Pattern:** Raise specific exceptions in core, catch and format in CLI.

---

## Logging & Debugging

### Current Status

**Logging:** Minimal (CLI output only)  
**Debug mode:** Not implemented  
**Verbose flag:** Not implemented  

### Future Enhancement

```bash
# Proposed
zt-band create --chords "Dm7 G7 C" --verbose
zt-band create --chords "Dm7 G7 C" --debug
```

**Would show:**
- Parsed chord sequence
- Generated MIDI events
- Track assignments
- File write operations

---

## Validation & Testing

### Pre-Commit Checklist

```bash
# 1. Run all tests
python -m pytest tests/ -v

# 2. Verify CLI entry points
zt-gravity gravity --root C --steps 3
zt-band create --chords "C F G" --tempo 100

# 3. Check MIDI output
ls -lh backing.mid

# 4. Validate DAW export
zt-band daw-export backing.mid
ls exports/daw/
```

**Expected:** All tests pass, MIDI files generated, no errors.

---

## Related Documentation

- [DEVELOPER_GUIDE.md](../DEVELOPER_GUIDE.md) — Code architecture & import protocol
- [ARCHITECTURE.md](../ARCHITECTURE.md) — High-level system design
- [CLI_DOCUMENTATION.md](../CLI_DOCUMENTATION.md) — CLI reference
- [DAW_WORKFLOW.md](DAW_WORKFLOW.md) — MIDI export & import workflow
- [ARDOUR_QUICKSTART.md](ARDOUR_QUICKSTART.md) — Pi-specific DAW setup

---

**Last Updated:** December 29, 2025  
**Status:** Production — smart-guitar v0.1.0  
**Architecture:** Stable — modular, extensible, governed
