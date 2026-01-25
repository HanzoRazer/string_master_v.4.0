# Zone–Tritone System
*A unified framework for understanding harmony through whole-tone zones, tritone gravity, and chromatic motion.*

**Now available as a Python library!** 🎉  
**Complete with command-line tools for musicians and educators!** 🎸

[![CI](https://github.com/HanzoRazer/string_master_v.4.0/actions/workflows/ci.yml/badge.svg)](https://github.com/HanzoRazer/string_master_v.4.0/actions/workflows/ci.yml)
[![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)](CHANGELOG.md)
[![Tests](https://img.shields.io/badge/tests-159%20passing-brightgreen.svg)](#testing)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)
[![License](https://img.shields.io/badge/license-Theory%20Protected-orange.svg)](LICENSE-THEORY.md)
[![Proof-of-Sound Verified — Raspberry Pi](https://img.shields.io/badge/Proof--of--Sound-Verified%20(Raspberry%20Pi)-brightgreen)](#proof-of-sound-verification)
[![Core Locked](https://img.shields.io/badge/Core-Locked%20%26%20Stable-blue)](#core-stability)

📖 **[Quick Start Guide](PROJECT_COMPLETE.md)** | 🔧 **[API Reference](PYTHON_PACKAGE.md)** | 🎸 **[CLI Documentation](CLI_DOCUMENTATION.md)** | 🏛️ **[Architecture](ARCHITECTURE.md)** | 🔒 **[Core Lock Report](CORE_LOCK_REPORT.md)**

---

## Overview

The **Zone–Tritone System** is a formal harmonic framework designed to unify:

- jazz harmony
- melodic & harmonic function
- improvisation
- composition
- ear training
- voice-leading

It is built on three fundamental principles:

1. **Zones define color**  
   The 12-tone system divides into two whole-tone families (zones). Staying inside a zone preserves tonal color without directional gravity.

2. **Tritones define gravity**  
   Tritones express the harmonic backbone of dominant function. They anchor resolution direction.

3. **Half-steps define motion**  
   Half-step movement transfers energy between zones and generates harmonic forward motion — including dominant cycles descending in 4ths.

---

## 🐍 Python Library (NEW!)

The Zone-Tritone System is now available as a production-ready Python package:

### Installation

```bash
pip install -e .
```

### Quick Start

```python
from zone_tritone import (
    pc_from_name,
    zone,
    all_tritone_axes,
    gravity_chain,
)

# Check what zone a note belongs to
c = pc_from_name("C")
print(f"C is in zone {zone(c)}")  # Zone 0 (Zone 1)

# Get all six tritone pairs
axes = all_tritone_axes()
# [(0, 6), (1, 7), (2, 8), (3, 9), (4, 10), (5, 11)]

# Generate a dominant gravity chain
chain = gravity_chain(7, steps=3)  # G → C → F → Bb
```

### Demo

Run the included demonstration:

```bash
python demo.py
```

### Command-Line Tool

After installation, the `zt-gravity` command becomes available:

```bash
# Generate a gravity chain (dominant cycle in fourths)
zt-gravity gravity --root G --steps 7

# Analyze a chord progression
zt-gravity analyze --chords "Dm7 G7 Cmaj7 A7 Dm7"

# Analyze from a file with transition matrix
zt-gravity analyze --file my_chords.txt --show-matrix
```

See [CLI_DOCUMENTATION.md](CLI_DOCUMENTATION.md) for complete CLI reference.

### Practice Presets (NEW!)

Use presets to instantly change how the band feels—no config files required.

```bash
# Tight, metronomic practice
zt-band rt-play song.yaml --preset tight --midi-out LoopBe

# Loose pocket with swing and human feel
zt-band rt-play song.yaml --preset loose --midi-out LoopBe

# Push yourself (more energy + challenge)
zt-band rt-play song.yaml --preset challenge --midi-out LoopBe

# Recovery / support mode after mistakes
zt-band rt-play song.yaml --preset recover --midi-out LoopBe
```

**Fine-tune with explicit controls** — presets are shortcuts, you can override any part:

```bash
# Start loose, but pull timing slightly ahead
zt-band rt-play song.yaml --preset loose --bias ahead --tightness 0.4 --midi-out LoopBe
```

**Live groove adaptation** (if analyzer is available):

```bash
zt-band rt-play song.yaml --intent-source analyzer --profile-id gp_my_device --midi-out LoopBe
```

If the analyzer isn't available, playback continues normally—no errors, no surprises.

List available presets:

```bash
zt-band rt-play --list-presets
```

---

## How the Band Listens (and What It Never Does)

The adaptive band system listens to *how* you play, not just *what* you play.
Its goal is to support practice, groove, and consistency—without ever surprising or fighting you.

### What the Band Listens To

When enabled, the band may adapt based on patterns in your playing over time:

| Signal | What It Measures |
|--------|-----------------|
| **Timing tendencies** | Are you consistently ahead, behind, or centered? How stable is your microtiming? |
| **Tempo stability** | Is your tempo drifting? Do you recover quickly after mistakes? |
| **Consistency** | Are note onsets steady or erratic? Do you rush dense passages? |
| **Context** | Practice mode (tight vs loose), support vs challenge intent |

These signals are summarized into a **Groove Profile** (persistent) and a short-lived **Control Intent** (ephemeral, expires quickly). The band then decides how to accompany you *right now*.

### What the Band Can Change

Depending on mode and preset, the band may:

- **Choose a different accompaniment pattern** — e.g. straight → swing, sparse → normal density
- **Adjust timing feel** — tighter lock or more humanized looseness
- **Apply subtle velocity support** — especially in assist/recover modes
- **Add a small anticipation bias** — only on note_on, bounded and deterministic (milliseconds, not feel-breaking)

All changes are: **bounded**, **deterministic**, **reversible**, and **validated under CI**.

### What the Band Never Does

The band is explicitly designed **not** to do the following:

| ❌ Never | Why |
|----------|-----|
| Stealing, dropping, or reordering your notes | Your performance is sacred |
| Sudden tempo jumps | Feels wrong, breaks flow |
| Learning state leaks between sessions | Privacy and predictability |
| "AI surprise" behavior | You stay in control |
| Irreversible adaptation | Always recoverable |

If something goes wrong, the system **fails closed** and falls back to the YAML style you chose.

### Manual vs Analyzer Modes

**Manual (default)** — `--intent-source manual`
- Presets and flags fully control behavior
- Deterministic and repeatable
- No analyzer required

**Analyzer (adaptive)** — `--intent-source analyzer --profile-id gp_my_device`
- Uses your Groove Profile (if available)
- Adapts feel over time
- If unavailable → silently falls back to manual/YAML behavior

**None (pure YAML)** — `--intent-source none`
- Disables all adaptive behavior
- Band plays exactly what's in the song file

### Validating a Playlist (Dry Run)

Inspect what the band *would* do—without playing audio:

```bash
# Single program
zt-band rt-play song.yaml --preset tight --dry-run

# Entire playlist
zt-band rt-play --playlist set.ztplay --dry-run --all-programs

# Compact validation (best for CI or scanning)
zt-band rt-play --playlist set.ztplay --dry-run --all-programs --compact
```

Example compact output:

```
[dry-run] 3/5 OK Verse: style=swing_basic
[dry-run] 4/5 FAIL Bridge: style=straight_basic→swing_basic reasons=['style_overridden']
[dry-run] summary: programs=5 ok=4 fail=1 overridden=1 intent_none=0
[dry-run] exit: fail
```

- Exit code `0` = all good
- Exit code `1` = at least one mismatch or error

This makes playlists **auditable** and **safe to refactor**.

### Transparency by Design

At startup, the engine prints its identity:

```
[engine] groove=v1 arranger=v1 pkg=0.4.0
```

When using analyzer services, requests include:
- `X-Request-Id` (attempt-aware, deterministic)
- `X-Engine-Identity` (schema + engine + package version)

This makes debugging and rollouts traceable and safe.

### How to Opt Out (Always Safe)

At any time: `--intent-source none`

The band becomes a traditional, static accompaniment engine.
No state is lost. No cleanup required.

### Philosophy (One Sentence)

> **The band adapts to support your practice—but you always stay in control.**

---

## Quick Practice Guide

This guide shows how to use the band system for common practice goals in **one command each**.
You don't need to understand the internals—everything here is safe, reversible, and deterministic.

### 1) Lock in Your Time (Metronomic Practice)

Use this when you want **maximum timing clarity**.

```bash
zt-band rt-play song.yaml --preset tight --midi-out LoopBe
```

What this feels like:
- Very stable time
- Minimal swing or looseness
- Great for working on accuracy, subdivisions, and endurance

### 2) Work on Groove and Feel

Use this when you want the band to **sit back and breathe** with you.

```bash
zt-band rt-play song.yaml --preset loose --midi-out LoopBe
```

What this feels like:
- More swing / expression
- Less rigid timing
- Good for pocket, phrasing, and relaxed playing

### 3) Push Yourself (Challenge Mode)

Use this when you want the band to **expose inconsistencies**.

```bash
zt-band rt-play song.yaml --preset challenge --midi-out LoopBe
```

What this feels like:
- Less assistance
- Higher energy patterns
- Timing mistakes are more obvious

This is ideal for focused practice once you're warmed up.

### 4) Recover After Mistakes (Support Mode)

Use this when you've drifted off time and want help re-locking.

```bash
zt-band rt-play song.yaml --preset recover --midi-out LoopBe
```

What this feels like:
- Strong rhythmic support
- Smoother transitions
- Helps you get back into the groove without stopping

### 5) Fine-Tune Any Preset

Presets are shortcuts. You can override any part:

```bash
zt-band rt-play song.yaml --preset loose --tightness 0.4 --bias ahead --midi-out LoopBe
```

Common tweaks:
- `--tightness 0..1` → how locked the timing feels
- `--expression 0..1` → how loose / expressive the band is
- `--bias ahead|behind|neutral` → subtle push or layback

### 6) Validate Before You Play (Dry Run)

You can see exactly what the band *would* do—without playing audio.

```bash
# Check one section
zt-band rt-play song.yaml --preset loose --dry-run

# Check the entire playlist
zt-band rt-play --playlist set.ztplay --dry-run --all-programs

# Compact scan (best for quick checks)
zt-band rt-play --playlist set.ztplay --dry-run --all-programs --compact
```

If anything unexpected happens, it will be printed clearly—and nothing is played.

### 7) Turn Adaptation Off Completely

If you ever want the band to behave **exactly like a traditional backing track**:

```bash
zt-band rt-play song.yaml --intent-source none --midi-out LoopBe
```

This disables all adaptive behavior instantly.

### Mental Model (One Line)

> **Use presets to choose the kind of practice you want; use flags to fine-tune; use dry-run to stay in control.**

That's it. No setup, no hidden state, no surprises.

---

### Testing

```bash
pip install pytest
pytest
```

See [src/zone_tritone/](src/zone_tritone/) for the complete API.

---

## Canonical Objectives

This project exists to:

✔ preserve the integrity of the Zone–Tritone framework  
✔ provide structured educational materials  
✔ prevent theoretical drift and terminology sprawl  
✔ develop tools, analytics, and SaaS applications  
✔ support musicians, educators & students  

The theory itself is **frozen at the canonical level** (see `CANON.md`).  
Extensions must **not contradict axioms**.

---

## Proof-of-Sound Verification (Raspberry Pi)

This repository has been manually verified to produce **audible sound**
on a Raspberry Pi using the documented workflow.

### Verified Configuration
- Hardware: Raspberry Pi 5
- OS: Raspberry Pi OS (64-bit) / Debian 12
- Audio: I2S or USB audio interface
- DAW: Ardour (Linux)
- Output: MIDI → DAW → audible playback

### Verification Criteria
The badge applies only if all conditions below are met:

- zt-band generates a valid MIDI file
- MIDI imports cleanly into Ardour
- Tempo and timing are correct
- No stuck or hanging notes
- Audible sound is produced via a software instrument

### Verification Method
```bash
zt-band play <program>.ztprog
zt-band daw-export --midi output.mid
```

Drag the exported MIDI into Ardour and press Play.

### Scope

This badge does **not** guarantee:
- specific instrument sounds
- real-time latency performance
- external hardware compatibility

It guarantees **proof-of-sound** only.

---

## Core Stability

The `zt-band` MIDI generator core is **locked and stable** as of v0.1.0.

### What This Means

✅ **Deterministic output**: Same inputs always produce byte-identical MIDI files  
✅ **Contract enforcement**: Runtime validation prevents invalid MIDI generation  
✅ **Collision-safe timing**: Deterministic rounding ensures DAW compatibility  
✅ **Expressive layer**: Velocity shaping adds musical feel without timing edits

### Verification

Run the comprehensive stability tests:

```bash
python verify_lock.py
```

Expected result: **5/5 tests pass** ✅

See [CORE_LOCK_REPORT.md](CORE_LOCK_REPORT.md) for complete verification details.

### Development Philosophy

**Core changes are frozen** — only stability improvements enter the locked core.

New expressive features (swing, humanize, etc.) will be **layered on top** as optional transforms that:
- Preserve determinism (require seed when randomized)
- Pass contract validation
- Can be disabled to reproduce core output

This ensures the foundation remains stable while allowing creative exploration.

---

## Learning Path

The system is taught in layers:

1. Zone Awareness  
2. Gravity Recognition  
3. Motion Training  
4. Dual-Zone Harmony  
5. Composition in Gravity  
6. Mastery Philosophy

Details: `PEDAGOGY.md`

---

## Governance & Versioning

The theory canon is version-controlled and protected.

See: `GOVERNANCE.md`

---

## Licensing

The *software* you build may be open-source.

The **theory framework remains intellectual property** and is licensed separately
to prevent unauthorized reinterpretation.

See: `LICENSE-THEORY.md`

---

## Documentation

### Core Canon
- [`CANON.md`](CANON.md) — Immutable axioms (Version 1.0)
- [`GLOSSARY.md`](GLOSSARY.md) — Frozen terminology
- [`PEDAGOGY.md`](PEDAGOGY.md) — Six-level teaching sequence
- [`GOVERNANCE.md`](GOVERNANCE.md) — Change control & versioning

### Educational Materials
- [`INSTRUCTOR_CERTIFICATION.md`](INSTRUCTOR_CERTIFICATION.md) — Three-tier certification program
- [`STUDENT_ASSESSMENT_RUBRICS.md`](STUDENT_ASSESSMENT_RUBRICS.md) — Standardized evaluation criteria
- [`FAQ.md`](FAQ.md) — Questions from skeptics, students & educators

### Python Library & Tools
- [`PYTHON_PACKAGE.md`](PYTHON_PACKAGE.md) — Complete API reference (~500 lines)
- [`CLI_DOCUMENTATION.md`](CLI_DOCUMENTATION.md) — Command-line tool user guide (~400 lines)
- [`ARCHITECTURE.md`](ARCHITECTURE.md) — System design & data flow (~400 lines)
- [`PROJECT_COMPLETE.md`](PROJECT_COMPLETE.md) — Comprehensive project overview
- [`CHANGELOG.md`](CHANGELOG.md) — Version history & future roadmap
- [`demo.py`](demo.py) — Interactive demonstration script

### Standards & Guidelines
- [`BRAND_STYLE_GUIDE.md`](BRAND_STYLE_GUIDE.md) — Visual identity & design standards
- [`NOTATION_CONVENTIONS.md`](NOTATION_CONVENTIONS.md) — Musical notation & chord symbols
- [`THEORY_DIAGRAMS.md`](THEORY_DIAGRAMS.md) — Diagram design standards
- [`.github/copilot-instructions.md`](.github/copilot-instructions.md) — AI agent guidelines

### Academic & Formal Work
- [`papers/`](papers/) — Peer-reviewable academic papers and LaTeX documents
- [`ACADEMIC_PAPER.md`](ACADEMIC_PAPER.md) — Academic paper planning and structure
- [`FORMAL_PROOFS.md`](FORMAL_PROOFS.md) — Mathematical proofs appendix
- [`LATEX_COMPILATION_GUIDE.md`](LATEX_COMPILATION_GUIDE.md) — Compilation instructions

### Examples
- [`examples/`](examples/) — Practical demonstrations and applications

---

## Status

**Version 0.1.0 - Production Ready** ✅

This repository includes:
- ✅ Canonical theory framework (immutable axioms)
- ✅ Production Python library (10 modules, 100% tested)
- ✅ Command-line tools (zt-gravity CLI)
- ✅ Academic papers (short + extended monograph)
- ✅ Comprehensive documentation (20+ files)

Your participation is welcome — but must follow governance rules.
