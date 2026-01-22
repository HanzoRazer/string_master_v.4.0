# AI Agent Instructions for Zone–Tritone System

## Project Identity

**Dual-nature project**: Music theory framework + Python library (`smart-guitar` v0.1.0).

- **Theory side**: Immutable axioms (CANON.md), frozen terminology (GLOSSARY.md)
- **Code side**: Python ≥3.10 with CLIs `zt-gravity` (analysis) and `zt-band` (MIDI generation)

**Protected files** (require governance approval): `CANON.md`, `GLOSSARY.md`, `PEDAGOGY.md`, `GOVERNANCE.md`

---

## Quick Start

```bash
pip install -e .                    # Editable install
python -m pytest tests/ -v          # Run test suite
python verify_lock.py               # Verify core stability
zt-gravity gravity --root G --steps 7
zt-band play --program autumn_leaves.ztprog
```

---

## Architecture

```
src/
├── shared/zone_tritone/    # Core theory engine (STABLE)
│   ├── pc.py               # Pitch class: int 0-11 (C=0)
│   ├── zones.py            # Zone 1 (even) / Zone 2 (odd)
│   ├── tritones.py         # 6 tritone axes
│   ├── gravity.py          # Dominant chains (cycle of 4ths)
│   └── corpus.py           # Chord symbol parsing
│
└── zt_band/                # MIDI accompaniment engine
    ├── engine.py           # Main pipeline: .ztprog → .mid
    ├── midi_out.py         # LOCKED: deterministic writer (tpb=480)
    ├── musical_contract.py # LOCKED: runtime validation
    └── patterns.py         # Style registry (swing, bossa, salsa)
```

**Data flow**: `.ztprog` YAML → `engine.py` → contract validation → `midi_out.py` → `.mid`

---

## Import Protocol (Critical)

**Inside `src/shared/zone_tritone/`** — use RELATIVE:
```python
from .pc import pc_from_name
```

**In `src/zt_band/` and `tests/`** — use ABSOLUTE:
```python
from shared.zone_tritone.pc import pc_from_name
from shared.zone_tritone import gravity_chain
```

---

## Locked Modules (Do Not Modify)

Changes to these require `verify_lock.py` passing:
- `musical_contract.py` — validates events before MIDI write
- `midi_out.py` — deterministic beat→tick (same inputs = identical bytes)
- `expressive_layer.py` — velocity-only shaping (no timing edits)

---

## Domain Conventions

**Pitch classes**: Always `int % 12` (0=C, 11=B)
```python
pc_from_name("F#")  # → 6
zone(0)             # → 1 (Zone 1 = even PCs: C,D,E,F#,G#,A#)
zone(7)             # → 2 (Zone 2 = odd PCs: C#,D#,F,G,A,B)
```

**Tritone mode**: `"none"` = deterministic, `"probabilistic"` requires `tritone_seed`

---

## File Formats

**`.ztprog`** (YAML):
```yaml
chords: [Dm7, G7, Cmaj7]
style: swing_basic
tempo: 140
tritone_mode: none
outfile: output.mid
```

**`.ztex`**: Practice exercises | **`.ztplay`**: Playlists

---

## Canonical Terminology (Never Redefine)

- **Zone-Crossing** = half-step motion between zones
- **Tritone Anchor** = active tritone defining gravity  
- **Gravity Chain** = chromatic tritone drift → dominant cycles in 4ths
- **Anchor Exchange** = tritone substitution

---

## Adding Code

1. Create file in `src/zt_band/` (use absolute imports from `shared.zone_tritone`)
2. Add test in `tests/test_<module>.py`
3. Run `pytest tests/` before committing

New `.ztprog` files go in `programs/` — validate with `zt-band validate`

---

## Testing & Verification

**Always run before committing:**
```bash
python -m pytest tests/ -v           # Full suite (35+ tests)
python verify_lock.py                # Core stability (5 tests)
```

**Test naming**: `tests/test_<module>.py` mirrors `src/zt_band/<module>.py`

**Contract tests** (`test_musical_contract.py`): Verify `ContractViolation` is raised for invalid events (negative start, zero duration, out-of-range MIDI).

---

## MIDI Generation Invariants

All generated MIDI must satisfy (enforced by `musical_contract.py`):
- `start_beats ≥ 0`, `duration_beats > 0`
- `midi_note` in 0–127, `velocity` in 1–127, `channel` in 0–15
- Probabilistic mode (`tritone_mode: probabilistic`) MUST provide `tritone_seed`
- Deterministic rounding: `int(beat * 480 + 0.5)` for tick conversion

---

## Key References

| Doc | Purpose |
|-----|---------|
| [DEVELOPER_GUIDE.md](../DEVELOPER_GUIDE.md) | Full architecture |
| [CLI_DOCUMENTATION.md](../CLI_DOCUMENTATION.md) | CLI reference |
| [docs/contracts/CORE_LOCK_REPORT.md](../docs/contracts/CORE_LOCK_REPORT.md) | Stability guarantees |
| [CANON.md](../CANON.md) | 5 immutable axioms |
| [GLOSSARY.md](../GLOSSARY.md) | Frozen terminology |
