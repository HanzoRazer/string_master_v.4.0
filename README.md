# Zone–Tritone System
*A unified framework for understanding harmony through whole-tone zones, tritone gravity, and chromatic motion.*

**Now available as a Python library!** 🎉  
**Complete with command-line tools for musicians and educators!** 🎸

[![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)](CHANGELOG.md)
[![Tests](https://img.shields.io/badge/tests-28%2F28%20passing-brightgreen.svg)](#testing)
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
