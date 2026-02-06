# AI Agent Instructions for Zone–Tritone System

## Project Identity

**Dual-nature project**: Music theory framework + Python library (`smart-guitar` v0.1.0).

- **Theory side**: Immutable axioms (CANON.md), frozen terminology (GLOSSARY.md)
- **Code side**: Python ≥3.10 with CLIs `zt-gravity` (analysis), `zt-band` (MIDI generation), `sgc` (coach)
- **Ecosystem**: Depends on `sg-spec` (Pydantic schema contracts + coach logic via `sg_spec.ai.coach`)

**Protected files** (require governance approval): `CANON.md`, `GLOSSARY.md`, `PEDAGOGY.md`, `GOVERNANCE.md`

---

## Quick Start

```bash
pip install -e ".[dev]"             # Editable install with dev deps
python -m pytest tests/ -v          # Run test suite (~160 tests)
python verify_lock.py               # Verify core stability (5 tests)
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
│   ├── generator.py        # Etude/phrase generator
│   └── corpus.py           # Chord symbol parsing
│
└── zt_band/                # MIDI accompaniment engine
    ├── engine.py           # Main pipeline: .ztprog → .mid
    ├── midi_out.py         # LOCKED: deterministic writer (tpb=480)
    ├── musical_contract.py # LOCKED: runtime validation
    ├── patterns.py         # Style registry (swing, bossa, salsa)
    ├── dance_pack.py       # Declarative dance form bundles (Pydantic)
    ├── adapters/           # Groove → MIDI/Arranger adapters
    ├── groove/             # Intent providers (Manual, Analyzer)
    ├── arranger/           # Pattern selection engine
    └── e2e/                # End-to-end replay gates
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
from zt_band.engine import generate_accompaniment
from zt_band.adapters import build_midi_control_plan
```

**Cross-repo schemas and coach** (from `sg-spec`):
```python
from sg_spec.schemas.groove_layer import GrooveProfileV1, GrooveControlIntentV1
from sg_spec.ai.coach.schemas import SessionRecord, CoachEvaluation
from sg_spec.ai.coach.policy import evaluate_session  # Coach logic lives here
```

---

## Locked Modules (Do Not Modify)

Changes to these require `verify_lock.py` passing:
- `musical_contract.py` — validates events before MIDI write
- `midi_out.py` — deterministic beat→tick (same inputs = identical bytes)
- `expressive_layer.py` — velocity-only shaping (no timing edits)

---

## Determinism Contract

**Critical invariant**: Same inputs → byte-identical MIDI output.

- Probabilistic mode (`tritone_mode: probabilistic`) MUST provide `tritone_seed`
- Use `int(beat * 480 + 0.5)` for tick conversion (round half up)
- All random operations require explicit seeds

---

## Golden Vector & Replay Gates

**Replay gates** enforce byte-identical output for regression prevention:

```bash
# Run e2e replay gate
python -m zt_band.e2e.e2e_replay_gate_v1 fixtures/golden/e2e_vectors

# Update goldens (requires changelog entry)
python -m zt_band.e2e.e2e_replay_gate_v1 fixtures/golden/e2e_vectors --update-golden
```

**Vector structure** (`fixtures/golden/*/vector_*/`):
- `input.json` — Input profile/request
- `expected_output.json` — Expected deterministic output
- `vector_meta_v1.json` — Provenance + ENGINE_IDENTITY

---

## Testing & Verification

```bash
python -m pytest tests/ -v           # Full suite (~160 tests)
python verify_lock.py                # Core stability (5 tests)
python -m pytest tests/test_e2e_replay_gate_v1.py  # E2E determinism
```

**Test categories**:
- `test_musical_contract.py` — Contract violation detection
- `test_*_replay_gate*.py` — Determinism gates
- `test_dance_pack.py` — Dance pack loading/validation
- `test_groove_*.py` — Groove layer integration

---

## Key Abstractions

**StylePattern** (`patterns.py`): Encodes rhythm patterns with ghost hits, clave alignment, velocity contours.

**DancePackV1** (`dance_pack.py`): Declarative dance form bundles (groove, harmony constraints, behavioral nuance).

**Adapters** (`adapters/`):
- `build_midi_control_plan()` — GrooveControlIntentV1 → CC messages, clock mode
- `build_arranger_control_plan()` — GrooveControlIntentV1 → style, density, energy

---

## CLI Commands

```bash
zt-band play --program <name.ztprog>  # Play/generate from program
zt-band validate <file.ztprog>        # Validate program file
zt-band daw-export --midi out.mid     # Export DAW-ready MIDI
zt-band pack validate <pack.json>     # Validate dance pack
zt-gravity analyze --chords "Dm7 G7"  # Analyze chord progression
```

---

## Reaper DAW Integration

**Scripts location**: `scripts/reaper/` — designed to be copied as a bundle into Reaper's scripts folder.

**Key scripts**:
- `reaper_sg_setup_doctor_autorun.lua` — Guided first-run setup with action ID prompts
- `reaper_sg_panel.lua` — Main control panel
- `reaper_sg_pass_and_regen.lua` / `reaper_sg_struggle_and_regen.lua` — Verdict hotkeys (F9/F10)
- `reaper_sg_bundle_shipper_set_all.lua` — Canonical host/port configurator

**Server target** stored in Reaper ExtState:
```lua
reaper.SetExtState("SG_AGENTD", "host_port", "127.0.0.1:8420", true)
```

**Dependencies**: `curl` in PATH, `json.lua` in same folder, `sg-agentd` running.

**Contract**: Scripts follow `SG_REAPER_CONTRACT_V1` (see header comments for spec).

---

## Cross-Repo Ecosystem

```
sg-spec (schemas + coach logic via sg_spec.ai.coach)
    ↓
string_master_v.4.0 / zt-band (MIDI engine) ←→ sg-agentd (HTTP bridge)
                                                    ↓
                                               Reaper scripts
```

**Install order**: `sg-spec` → `string_master_v.4.0` → `sg-agentd`

---

## Key References

| Doc | Purpose |
|-----|---------|
| [DEVELOPER_GUIDE.md](../DEVELOPER_GUIDE.md) | Full architecture & imports |
| [CLI_DOCUMENTATION.md](../CLI_DOCUMENTATION.md) | CLI reference |
| [docs/contracts/CORE_LOCK_REPORT.md](../docs/contracts/CORE_LOCK_REPORT.md) | Stability guarantees |
| [CANON.md](../CANON.md) | 5 immutable axioms (theory) |
| [GLOSSARY.md](../GLOSSARY.md) | Frozen terminology |
| [scripts/reaper/README.md](../scripts/reaper/README.md) | Reaper integration guide |
