# Developer Guide: Smart Guitar Platform

**Executive Summary for Developers**

This document provides the canonical reference for code architecture, namespace protocols, and development patterns in the Smart Guitar monorepo.

---

## 🏗️ **Repository Schema**

### Package Identity
- **Package Name**: `smart-guitar`
- **PyPI Install**: `pip install -e .` (editable mode for development)
- **Python Version**: ≥3.10
- **Version**: 0.1.0

### Directory Structure

```
smart-guitar/
├── pyproject.toml           # Package configuration (CANONICAL)
├── src/                     # All Python modules live here
│   ├── shared/              # Reusable core libraries
│   │   ├── __init__.py
│   │   └── zone_tritone/    # Music theory engine
│   │       ├── __init__.py
│   │       ├── __about__.py
│   │       ├── __main__.py
│   │       ├── cli.py       # zt-gravity CLI implementation
│   │       ├── pc.py        # Pitch class utilities
│   │       ├── zones.py     # Zone membership & crossing logic
│   │       ├── tritones.py  # Tritone axis calculations
│   │       ├── gravity.py   # Gravity chain (cycle of 4ths)
│   │       ├── corpus.py    # Chord parsing & root extraction
│   │       ├── markov.py    # Transition probability analysis
│   │       └── types.py     # Type aliases (PitchClass, etc.)
│   │
│   └── zt_band/             # Accompaniment engine (NEW)
│       ├── __init__.py
│       └── cli.py           # zt-band CLI implementation
│
├── tests/                   # pytest test suite
│   ├── test_pc.py
│   ├── test_zones.py
│   ├── test_tritones.py
│   ├── test_gravity.py
│   ├── test_markov.py
│   └── test_cli_smoke.py    # CLI integration tests
│
├── docs/                    # Theory documentation
│   └── (canonical theory docs)
│
└── examples/                # Generated analysis examples
    └── (markdown/html outputs)
```

---

## 📦 **Namespace Protocol**

### ✅ **CORRECT Import Patterns**

#### For Code in `src/shared/zone_tritone/`
```python
# Within zone_tritone module - use RELATIVE imports
from .pc import pc_from_name, name_from_pc
from .zones import zone_name, is_zone_cross
from .tritones import tritone_axis
from .gravity import gravity_chain
from .types import PitchClass
```

#### For Code in `src/zt_band/`
```python
# Importing from shared theory - use ABSOLUTE imports
from shared.zone_tritone.pc import pc_from_name, name_from_pc
from shared.zone_tritone.zones import zone_name, is_zone_cross
from shared.zone_tritone.gravity import gravity_chain
from shared.zone_tritone.types import PitchClass
```

#### For Tests in `tests/`
```python
# Tests always use ABSOLUTE imports from top-level package
from shared.zone_tritone import pc_from_name, name_from_pc
from shared.zone_tritone import zone, is_zone_cross
from shared.zone_tritone import tritone_axis, all_tritone_axes
from shared.zone_tritone import gravity_chain
```

#### For External Consumers
```python
# After pip install smart-guitar
from shared.zone_tritone import pc_from_name
from shared.zone_tritone.zones import zone_name
```

---

## 🎯 **CLI Entry Points**

Defined in `pyproject.toml`:

```toml
[project.scripts]
zt-gravity = "shared.zone_tritone.cli:main"
zt-band = "zt_band.cli:main"
```

### Usage
```bash
# Theory analysis CLI
zt-gravity gravity --root C --steps 7
zt-gravity analyze --chords "Dm7 G7 Cmaj7"
zt-gravity explain --chords "Dm7 G7 C" --format markdown --save output.md

# Accompaniment CLI (skeleton)
zt-band play --chords "Dm7 G7 Cmaj7" --tempo 120
zt-band generate --progression "ii-V-I" --key C
```

### Running via Python Module
```bash
# Alternate invocation methods
python -m shared.zone_tritone.cli gravity --root C
python -m zt_band.cli play --chords "Dm7 G7 C"
```

---

## 🧪 **Testing Protocol**

### Running Tests
```bash
# All tests
python -m pytest tests/ -v

# Specific test file
python -m pytest tests/test_gravity.py -v

# With coverage
python -m pytest tests/ --cov=src --cov-report=html
```

### Test Structure
All tests use **absolute imports** from `shared.zone_tritone`:

```python
# Example: tests/test_gravity.py
from shared.zone_tritone import dominant_roots_from_tritone, gravity_chain

def test_gravity_chain_fourths():
    chain = gravity_chain(0, 3)  # C, F, Bb, Eb
    assert chain == [0, 5, 10, 3]
```

### Smoke Tests (CLI)
CLI tests use `subprocess.run()` with module invocation:

```python
# Example: tests/test_cli_smoke.py
result = subprocess.run(
    [sys.executable, "-m", "shared.zone_tritone.cli", "gravity", "--root", "C"],
    capture_output=True,
    text=True,
    timeout=5,
)
assert result.returncode == 0
```

---

## 🔧 **Development Workflow**

### 1. **Clone & Setup**
```bash
git clone https://github.com/HanzoRazer/string_master_v.4.0.git
cd string_master_v.4.0
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -e .         # Editable install
```

### 2. **Add New Module to `shared/`**
```bash
# Example: Adding a new tuner module
mkdir src/shared/tuner
touch src/shared/tuner/__init__.py
touch src/shared/tuner/pitch_detection.py
```

**Import from other shared modules:**
```python
# src/shared/tuner/pitch_detection.py
from shared.zone_tritone.pc import pc_from_name  # ✅ CORRECT
```

### 3. **Add New Top-Level Module (like zt_band)**
```bash
mkdir src/practice_tools
touch src/practice_tools/__init__.py
touch src/practice_tools/cli.py
```

**Update pyproject.toml:**
```toml
[project.scripts]
zt-gravity = "shared.zone_tritone.cli:main"
zt-band = "zt_band.cli:main"
practice = "practice_tools.cli:main"  # NEW
```

**Import from shared:**
```python
# src/practice_tools/cli.py
from shared.zone_tritone.gravity import gravity_chain  # ✅ CORRECT
```

### 4. **Reinstall After Schema Changes**
```bash
pip install -e .  # Refresh entry points
```

---

## 📚 **LaTeX Academic Papers**

Refer to [LATEX_COMPILATION_GUIDE.md](LATEX_COMPILATION_GUIDE.md).
AI agents should not modify LaTeX build tooling unless a compilation failure is reproduced and documented.

---

## 🎼 **Core Theory API**

### Pitch Class (PC) Operations
```python
from shared.zone_tritone.pc import pc_from_name, name_from_pc

pc = pc_from_name("F#")  # Returns: 6
name = name_from_pc(6)   # Returns: "F#"
```

### Zone Operations
```python
from shared.zone_tritone.zones import (
    zone, zone_name, is_same_zone, is_zone_cross,
    is_half_step, is_whole_step, interval
)

z = zone(0)                          # 1 (C is Zone 1)
name = zone_name(0)                  # "Zone 1"
crossing = is_zone_cross(0, 1)       # True (C→C# crosses zones)
same = is_same_zone(0, 2)            # True (C→D both Zone 1)
half = is_half_step(0, 1)            # True (C→C# is half-step)
whole = is_whole_step(0, 2)          # True (C→D is whole-step)
dist = interval(0, 7)                # 7 (C→G = 7 semitones)
```

### PitchClass Pitfalls & Debug Patterns

**Pitfalls:**
- PitchClass is always int in [0..11]. Never store note names as internal truth.
- Normalize with `% 12` at all boundaries (input parsing, transposition, interval math).
- Beware negative intervals: always normalize `((pc + delta) % 12)`.
- Avoid mixing enharmonic spelling concerns into numeric core logic.

**Debug patterns:**
- Log both (pc) and (pc_name) for readability, but compute only on pc.
- When results seem "off by one," inspect:
  - accidental parsing
  - interval direction (ascending vs descending)
  - normalization points

**Performance:**
- Keep hot loops integer-only.
- Cache parsed chord tokens if iterating long sequences.

### Tritone Operations
```python
from shared.zone_tritone.tritones import (
    tritone_partner, tritone_axis, is_tritone_pair, all_tritone_axes
)

partner = tritone_partner(0)         # 6 (C→F# is a tritone)
axis = tritone_axis(4)               # (4, 10) = E–Bb tritone
is_tt = is_tritone_pair(0, 6)        # True (C–F# is tritone)
all_axes = all_tritone_axes()        # Returns all 6 tritone pairs
```

### Gravity Chain (Cycle of 4ths)
```python
from shared.zone_tritone.gravity import gravity_chain, dominant_roots_from_tritone

chain = gravity_chain(0, 7)          # C→F→Bb→Eb→Ab→Db→Gb→Cb
roots = dominant_roots_from_tritone(0, 6)  # (7, 1) = G7 or Db7 resolve to C
```

### Chord Parsing
```python
from shared.zone_tritone.corpus import chord_sequence_to_roots

chords = ["Dm7", "G7", "Cmaj7"]
roots = chord_sequence_to_roots(chords)  # [2, 7, 0] (D, G, C)
```

### Markov Analysis
```python
from shared.zone_tritone.markov import (
    build_transition_counts, normalize_transition_matrix, sample_next_root
)

roots = [0, 5, 10, 3, 8]  # C F Bb Eb Ab
counts = build_transition_counts(roots)
probs = normalize_transition_matrix(counts, smoothing=0.1)
next_root = sample_next_root(8, probs)  # Predict next root after Ab
```

---

## 🚀 **Adding Features to `zt_band`**

### Example: Adding Chord Pattern Generation

**File**: `src/zt_band/patterns.py`

```python
"""
Chord voicing patterns for accompaniment.
"""
from shared.zone_tritone.pc import name_from_pc
from shared.zone_tritone.zones import zone
from shared.zone_tritone.types import PitchClass

def generate_jazz_voicing(root: PitchClass, chord_type: str) -> list[int]:
    """Generate MIDI notes for a jazz chord voicing."""
    if chord_type == "m7":
        # Shell voicing: root, b3, b7
        return [root + 36, root + 39, root + 46]  # MIDI octave 3
    elif chord_type == "7":
        # Shell voicing: root, 3, b7
        return [root + 36, root + 40, root + 46]
    elif chord_type == "maj7":
        # Shell voicing: root, 3, 7
        return [root + 36, root + 40, root + 47]
    return [root + 36]
```

**File**: `src/zt_band/cli.py` (update)

```python
from shared.zone_tritone.corpus import chord_sequence_to_roots
from .patterns import generate_jazz_voicing

def cmd_play(args):
    chords = args.chords.split()
    roots = chord_sequence_to_roots(chords)
    
    for chord, root in zip(chords, roots):
        # Parse chord type (simplified)
        if "m7" in chord:
            notes = generate_jazz_voicing(root, "m7")
        elif "maj7" in chord:
            notes = generate_jazz_voicing(root, "maj7")
        else:
            notes = generate_jazz_voicing(root, "7")
        
        print(f"{chord}: MIDI notes {notes}")
```

---

## ⚠️ **Common Import Mistakes**

### ❌ WRONG: Importing from old namespace
```python
from zone_tritone import pc_from_name  # FAILS - old namespace
```

### ❌ WRONG: Absolute imports within same module
```python
# In src/shared/zone_tritone/cli.py
from shared.zone_tritone.pc import pc_from_name  # VERBOSE, use relative
```

### ❌ WRONG: Relative imports from different top-level module
```python
# In src/zt_band/cli.py
from ..shared.zone_tritone.pc import pc_from_name  # FAILS - not sibling
```

### ✅ CORRECT: Patterns by location

**Within `shared/zone_tritone/`:**
```python
from .pc import pc_from_name         # ✅ Relative import
```

**In `zt_band/` or other top-level module:**
```python
from shared.zone_tritone.pc import pc_from_name  # ✅ Absolute import
```

**In `tests/`:**
```python
from shared.zone_tritone import pc_from_name  # ✅ Absolute import
```

---

## 📋 **Type System**

### Core Type Aliases
```python
# From shared.zone_tritone.types
PitchClass = int  # 0-11 (C=0, C#=1, ..., B=11)
```

### Type Hints in Function Signatures
```python
from shared.zone_tritone.types import PitchClass

def my_function(root: PitchClass) -> list[PitchClass]:
    """Process a pitch class and return related pitch classes."""
    return [root, (root + 7) % 12]  # root and fifth
```

---

## 🔄 **Git Workflow**

### Branch Strategy
```bash
# Feature branches off master
git checkout -b feature/band-midi-output
# Make changes
git add -A
git commit -m "feat: Add MIDI output to zt-band"
git push origin feature/band-midi-output
# Create PR on GitHub
```

### Commit Message Format
```
type: Short description (50 chars max)

Longer explanation if needed.

- Bullet points for details
- Multiple lines OK

Breaking changes noted here if applicable.
```

**Types**: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`

---

## 🧩 **Future Module Additions**

### Planned Structure
```
src/
├── shared/
│   ├── zone_tritone/    # ✅ EXISTS - Core theory
│   ├── tuner/           # 🔮 PLANNED - Pitch detection
│   └── audio_utils/     # 🔮 PLANNED - Audio processing
│
├── zt_band/             # ✅ EXISTS - Accompaniment (skeleton)
├── practice_tools/      # 🔮 PLANNED - Practice routines
└── smart_controller/    # 🔮 PLANNED - Hardware integration
```

### Adding New Shared Module Template
```python
# src/shared/new_module/__init__.py
"""
Module description.
"""
from .core import main_function

__all__ = ["main_function"]
```

### Adding New CLI Tool Template
```python
# src/new_tool/cli.py
"""CLI for new tool."""
import argparse
from shared.zone_tritone.gravity import gravity_chain  # Import shared

def main(argv=None):
    parser = argparse.ArgumentParser(prog="new-tool")
    # ... define commands
    args = parser.parse_args(argv)
    return args.func(args)
```

**Update pyproject.toml:**
```toml
[project.scripts]
zt-gravity = "shared.zone_tritone.cli:main"
zt-band = "zt_band.cli:main"
new-tool = "new_tool.cli:main"  # ADD THIS
```

---

## 📊 **Package Metadata**

From `pyproject.toml`:

```toml
[project]
name = "smart-guitar"
version = "0.1.0"
description = "Smart Guitar Platform: Zone-Tritone theory engine, accompaniment tools, and practice utilities for guitarists."
authors = [{ name = "Greg Brown" }]
requires-python = ">=3.10"
license = { text = "MIT" }
```

**Homepage**: https://github.com/HanzoRazer/string_master_v.4.0

---

## 🎯 **Quick Reference Checklist**

### Before Adding Code:
- [ ] Determine if code belongs in `shared/` (reusable) or top-level module (application)
- [ ] Use **relative imports** within same module tree
- [ ] Use **absolute imports** from `shared.zone_tritone` when in different module
- [ ] Add type hints using `PitchClass` and standard types
- [ ] Write corresponding tests in `tests/`

### Before Committing:
- [ ] Run `python -m pytest tests/ -v` (all tests pass)
- [ ] Run CLI commands to verify functionality
- [ ] Update this guide if adding new modules/patterns
- [ ] Use conventional commit message format

### Before Pushing:
- [ ] Verify `pip install -e .` works cleanly
- [ ] Check that CLI entry points work: `zt-gravity`, `zt-band`
- [ ] Ensure no import errors in production paths

---

## 🆘 **Troubleshooting**

### "ModuleNotFoundError: No module named 'zone_tritone'"
**Cause**: Using old namespace  
**Fix**: Change imports to `from shared.zone_tritone import ...`

### "ModuleNotFoundError: No module named 'shared'"
**Cause**: Package not installed in editable mode  
**Fix**: Run `pip install -e .` from repo root

### CLI commands not found after changes
**Cause**: Entry points not refreshed  
**Fix**: Run `pip install -e .` again

### Tests failing with import errors
**Cause**: Tests using wrong import path  
**Fix**: Update test imports to `from shared.zone_tritone import ...`

### Relative import beyond top-level package
**Cause**: Trying to use `..` to import from parent of `src/`  
**Fix**: Use absolute imports: `from shared.zone_tritone.xxx import ...`

---

## 📚 **Additional Documentation**

- **Theory**: See `CANON.md`, `GLOSSARY.md`, `PEDAGOGY.md`
- **CLI**: See `CLI_DOCUMENTATION.md`, `FORMAT_GUIDE.md`
- **Architecture**: See `ARCHITECTURE.md`, `PROJECT_STRUCTURE.md`
- **API**: Auto-generated from docstrings (future: use `pdoc` or `sphinx`)

---

## Proof-of-Sound Badge Governance

Any change that breaks the Proof-of-Sound workflow
invalidates the Raspberry Pi verification badge.

Before removing or modifying the badge:
- Reproduce the failure
- Document the cause
- Update the verification section accordingly

---

**Last Updated**: December 28, 2025  
**Version**: Monorepo v0.1.0  
**Status**: Active Development — `zt_band` skeleton in place, theory core stable

---

**For questions or contributions**: Open an issue or PR on GitHub

