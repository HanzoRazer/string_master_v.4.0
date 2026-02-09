# AI Agent Instructions for Zone–Tritone System

## Project Identity

**Dual-nature project**: Music theory framework + Python library (`smart-guitar` v0.1.0).

- **Theory side**: Immutable axioms (CANON.md), frozen terminology (GLOSSARY.md)
- **Code side**: Python ≥3.10 (`setuptools` build), CLIs `zt-gravity`, `zt-band`, `sgc`
- **Ecosystem**: Depends on `sg-spec` (Pydantic v2 schema contracts + coach logic)

**Protected files** (require governance approval): `CANON.md`, `GLOSSARY.md`, `PEDAGOGY.md`, `GOVERNANCE.md`

---

## Quick Start

```bash
pip install -e ".[dev]"             # Editable install with dev deps
python -m pytest tests/ -v          # Full suite
python verify_lock.py               # Core stability (5 lock tests)
zt-gravity gravity --root G --steps 7
zt-band play --program autumn_leaves.ztprog
```

---

## Architecture

```
src/
├── shared/zone_tritone/    # Core theory engine (15 modules, STABLE)
│   ├── pc.py               # Pitch class: int 0-11 (C=0)
│   ├── zones.py            # Zone 1 (even) / Zone 2 (odd)
│   ├── tritones.py         # 6 tritone axes
│   ├── gravity.py          # Dominant chains (cycle of 4ths)
│   ├── generator.py        # Etude/phrase generator
│   ├── corpus.py           # Chord symbol parsing
│   ├── andalusian.py       # Andalusian cadence logic
│   ├── backdoor.py         # Backdoor ii-V resolution
│   └── dominant.py, markov.py, types.py, cli.py
│
├── zt_band/                # MIDI accompaniment engine (75+ modules, 7 subpackages)
│   ├── engine.py           # Main pipeline: .ztprog → .mid (returns NoteEvent list + writes file)
│   ├── midi_out.py         # LOCKED: deterministic writer (tpb=480)
│   ├── musical_contract.py # LOCKED: runtime validation (frozen dataclass)
│   ├── expressive_layer.py # LOCKED: velocity-only shaping
│   ├── patterns.py         # Style registry (composed: local + salsa + flamenco + afro-cuban)
│   ├── dance_pack.py       # Declarative dance form bundles (Pydantic v2)
│   ├── bundle_writer.py    # Atomic write: temp dir → rename, collision policy (fail|overwrite|rename)
│   ├── realtime.py         # RT MIDI playback + scheduler
│   ├── adapters/           # Groove → MIDI/Arranger adapters + replay gates (7 modules)
│   ├── groove/             # IntentProvider protocol (Manual, Analyzer, 7 modules)
│   ├── arranger/           # Deterministic hash-based pattern selection (engine, runtime, 6 modules)
│   ├── midi/               # MidiClockMaster, DeterministicHumanizer (4 modules)
│   ├── e2e/                # End-to-end replay gates
│   └── ui/                 # Manual intent UI controls
│
├── sg_agentd/              # Embedded HTTP stubs (for monorepo dev — mostly empty)
└── sg_coach/               # Embedded coach stubs (for monorepo dev — mostly empty)
```

**Data flow**: `.ztprog` YAML/JSON → `engine.py` → contract validation → expressive layer → `midi_out.py` → `.mid`

**Engine pipeline detail**: chord parsing → tritone substitutions → per-bar comp/bass hits from `StylePattern` → ghost hits → velocity contour → determinism gate → validate → expressive velocity → validate again → optional swing → density thinning (Knuth hash, no RNG) → syncopation offsets → MIDI write

---

## Import Protocol (Critical)

**Inside `src/shared/zone_tritone/`** — use RELATIVE:
```python
from .pc import pc_from_name
```

**Inside `src/zt_band/`** — use RELATIVE within the package:
```python
from .chords import Chord, chord_bass_pitch, parse_chord_symbol
from .expressive_layer import apply_velocity_profile
from .patterns import STYLE_REGISTRY, StylePattern
```

**In `tests/`** — use ABSOLUTE:
```python
from shared.zone_tritone.pc import pc_from_name
from zt_band.engine import generate_accompaniment
from zt_band.adapters.midi_control_plan import build_midi_control_plan
```

**Cross-repo schemas** (from `sg-spec`) — use try/except guard:
```python
try:
    from sg_spec.schemas.clip_bundle import ClipBundle
    SG_SPEC_AVAILABLE = True
except ImportError:
    SG_SPEC_AVAILABLE = False
```

---

## Locked Modules (Do Not Modify)

Changes require `python verify_lock.py` passing (5 tests):
- `musical_contract.py` — validates events before MIDI write
- `midi_out.py` — deterministic beat→tick (`int(round(beat * 480))`, collision-safe note ordering)
- `expressive_layer.py` — velocity-only shaping (no timing edits)

---

## Determinism Contract

**Critical invariant**: Same inputs → byte-identical MIDI output.

- Probabilistic mode MUST provide `tritone_seed`
- Tick conversion: `int(round(event.start_beats * ticks_per_beat))` (Python's banker's rounding)
- Density thinning / syncopation use Knuth multiplicative hash — never stdlib `random`
- All random operations require explicit seeds

---

## Three Replay Gate Systems

Each gate enforces byte-identical output. Different gates have different file structures:

| Gate | Location | Vector Files |
|------|----------|-------------|
| **E2E** | `fixtures/golden/e2e_vectors/` | `events.json`, `expected.json`, `intent.json`, `meta.json` |
| **Arranger** | `fixtures/golden/arranger_vectors/` | `intent.json`, `expected_plan.json`, `meta.json` |
| **Analyzer** | `fixtures/golden/analyzer_smoke/` | Smoke test vectors |

```bash
python -m zt_band.e2e.e2e_replay_gate_v1 fixtures/golden/e2e_vectors
python -m zt_band.adapters.arranger_replay_gate_v1 fixtures/golden/arranger_vectors
# Update goldens (requires changelog entry):
python -m zt_band.e2e.e2e_replay_gate_v1 fixtures/golden/e2e_vectors --update-golden
```

Each vector system has its own `CHANGELOG.md`. Bump `ENGINE_IDENTITY` salt for intentional mapping changes.

---

## Testing & Verification

```bash
python -m pytest tests/ -v                          # Full suite
python verify_lock.py                                # Core lock (5 tests)
python -m pytest tests/test_e2e_replay_gate_v1.py    # E2E determinism
python -m pytest tests/test_arranger_replay_gate_v1.py  # Arranger determinism
```

Pytest configured with `addopts = "-v --tb=short"` in `pyproject.toml`. Uses `tmp_path` fixture for hermetic file I/O tests.

**Test categories** (~73 test files):
- `test_musical_contract.py` — Contract violation detection
- `test_*_replay_gate*.py` — Determinism gates (e2e, arranger, groove)
- `test_realtime_*.py`, `test_rt_*.py` — Realtime playback
- `test_arranger_*.py` — Pattern selection engine
- `test_groove_*.py` — Intent providers
- `test_dance_pack.py`, `test_clave.py` — Style/pack validation
- `test_bundle_writer.py` — Atomic bundle output
- `test_velocity_contour*.py`, `test_ghost_layer.py` — Expressive transforms

---

## CI Gates (`scripts/ci/`)

| Gate | Purpose |
|------|---------|
| `check_e2e_replay_determinism.py` | E2E replay gate |
| `check_arranger_replay_determinism.py` | Arranger replay gate |
| `check_e2e_vectors_complete.py` | Vector file completeness |
| `check_guardrails.py` | **Cross-contamination guard** — forbids cloud SDK imports (`openai`, `anthropic`, `boto3`) in embedded code |
| `check_style_registry_metadata.py` | Style registry validation |
| `run_analyzer_smoke.py` | Analyzer smoke test |

**Guardrail exemption**: Add `# guardrail-exempt: <reason>` comment (requires review).

---

## Release Pipeline (`scripts/release/`)

~28 scripts (Python + shell) for attestation-verified releases:
- `build_lab_pack.py` — Deterministic Lab Pack zip for Reaper
- `build_reaper_bundle.py` — Reaper script bundle
- `verify_attestation_receipt.py` — GitHub sigstore attestation against JSON Schema
- `generate_policy_receipts_index.py` — SHA256 manifest of canonical receipts
- `diff_receipts.py` / `guard_receipt_drift.py` — Block releases on protected field drift
- `verify_release.ps1` / `.sh` — Cross-platform release verification

---

## Linting & Type Checking

- **Ruff**: `pyproject.toml` — target `py310`, line-length 100, rules E/W/F/I/B/C4/UP, known first-party `shared` + `zt_band`
- **Mypy**: `pyproject.toml` — `python_version = "3.10"`, `warn_return_any = true`, `ignore_missing_imports = true`

---

## Key Abstractions

- **StylePattern** (`patterns.py`): Rhythm patterns with ghost hits, clave alignment, velocity contours. Registry built by dict-merging: local + salsa + flamenco + afro-cuban modules
- **DancePackV1** (`dance_pack.py`): Declarative dance form bundles (Pydantic v2, `ConfigDict(extra="forbid")`)
- **IntentProvider** (`groove/intent_provider.py`): Protocol — `get_intent(ctx) → dict | None` (fail-closed, never raises)
- **BundleWriter** (`bundle_writer.py`): Atomic write with collision policy (`fail` default | `overwrite` | `rename`)
- **DeterministicHumanizer** (`midi/humanizer.py`): Seedable jitter for human feel
- **MidiClockMaster** (`midi/midi_clock.py`): Bounded slew-rate tempo changes

---

## Programs Library

`.ztprog` files in `programs/` — swing, bossa, salsa, andalusian, enclosure, Barry Harris, etc. Format supports JSON and YAML; style can be string or dict with nested overrides.

---

## Cross-Repo Ecosystem

```
sg-spec (schemas + coach logic)
    ↓
string_master_v.4.0 / zt-band (MIDI engine) ←→ sg-agentd (HTTP bridge)
                                                    ↓
                                               Reaper DAW scripts
```

**Install order**: `sg-spec` → `string_master_v.4.0` → `sg-agentd`

---

## Reaper DAW Integration

**Scripts**: `scripts/reaper/` (~19 Lua scripts) — copy as bundle into Reaper's scripts folder.
**Server target**: `reaper.SetExtState("SG_AGENTD", "host_port", "127.0.0.1:8420", true)`
**Dependencies**: `curl` in PATH, `json.lua` in same folder, `sg-agentd` running.

---

## Key References

| Doc | Purpose |
|-----|---------|
| `DEVELOPER_GUIDE.md` | Full architecture & imports |
| `docs/contracts/CORE_LOCK_REPORT.md` | Stability guarantees |
| `CANON.md` | 5 immutable axioms (theory) |
| `GLOSSARY.md` | Frozen terminology |
| `scripts/reaper/README.md` | Reaper integration guide |
