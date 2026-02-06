# string_master_v.4.0 (Zone-Tritone System) — 1% Critical Design Review

**Reviewer posture:** Skeptical outside evaluator. No credit for intent — only what the artifact proves.

**Date:** 2026-02-05  
**Artifact:** `string_master_v.4.0-master` (snapshot, ~6.7 MB)  
**Stack:** Python 3.10+, mido (MIDI), PyYAML, Pydantic  
**Quantitative profile:**
- 48,488 lines of Python across 242 files
- 13,766 lines of tests across 83 test files (28% test ratio)
- 661 individual test functions
- 241 KB of documentation across 25+ docs files
- 169 items in the root directory
- 0 bare `except:` clauses, 0 broad `except Exception` blocks

---

## Stated Assumptions

1. **Target user is a musician/educator** who wants to understand harmonic theory through the Zone-Tritone framework, generate practice materials, and use real-time accompaniment tools.

2. **This is primarily a music theory framework** with software implementation — the theoretical content (axioms, terminology, pedagogical sequence) is as important as the code.

3. **The project serves multiple roles:** theoretical reference, Python library, CLI tool, MIDI generator, and real-time practice companion. I'm evaluating all roles.

4. **"Smart Guitar" branding** (in pyproject.toml) indicates this is part of a larger product ecosystem, likely the same Smart Guitar product from the Luthier's ToolBox universe.

5. **The code has undergone significant AI-assisted development** (CBSP21.md files, session logs) — I'm evaluating the end artifact, not the development process.

---

## Category Scores

### 1. Purpose Clarity — 9/10

**What's good:** The Zone-Tritone System is articulated with exceptional rigor. The README opens with a precise thesis:

> "Every dominant 7th chord contains exactly one tritone — between its 3rd and 7th. That tritone is unstable and wants to resolve. **If you can find the tritone, you can predict the resolution.** That's the entire engine of tonal harmony reduced to a single, testable claim."

The framework makes three computable claims:
1. `zone(pc) = pc % 2` — pitch class parity defines tonal color
2. Tritones define gravitational anchors (6 axes, each shared by tritone-substitute dominants)
3. Half-step motion crosses zones and creates resolution gravity

These are bold, falsifiable claims with mathematical formulas. The CANON.md, GLOSSARY.md, and PEDAGOGY.md form a coherent theoretical stack. The terminology is frozen ("Zone-Crossing", "Tritone Anchor", "Gravity Chain") and enforced via governance.

**What's wrong:** The project identity is fragmented:
- pyproject.toml says `name = "smart-guitar"`
- The repo is `string_master_v.4.0`
- The CLI tools are `zt-gravity` and `zt-band`
- The package imports from `zone_tritone`
- The README title is "Zone-Tritone System"

This is five different names for one project. A newcomer cannot tell what to call it.

**Concrete improvements:**
- Pick one name and use it everywhere. "Zone-Tritone" is the clearest — update pyproject.toml to match.
- Create a one-paragraph "elevator pitch" in README that explains what a user can *do* with this system in 30 seconds.
- Move theoretical documentation (CANON.md, GLOSSARY.md) to a `theory/` subdirectory to separate product from philosophy.

---

### 2. User Fit — 7/10

**What's good:** The domain expertise is authentic and deep. The framework spans jazz harmony, Afro-Cuban clave patterns, bluegrass, flamenco, Barry Harris methodology, and gospel voicings. The canonical JSON files encode real musical knowledge.

The CLI tools are musician-oriented:
```bash
zt-gravity gravity --root G --steps 7    # Generate gravity chain
zt-band rt-play song.yaml --preset loose  # Real-time accompaniment
```

The preset system (`tight`, `loose`, `challenge`, `recover`) is excellent — it maps to real practice scenarios without requiring configuration knowledge.

**What's wrong:** The happy path for a first-time user is unclear. There are 169 items in the root directory including:
- 24 MIDI files (Etude_1 through Etude_21, plus duplicates with `(1)` suffixes)
- 17 `*_canonical.json` files
- 8 `groove_layer_v0_stage_*` directories (development archaeology)
- 1 `backup_pre_migration/` directory
- Session logs (`SESSION_2026-01-14.md`)

A musician wanting to practice jazz changes must navigate this clutter to find the actual entry point. QUICK_REFERENCE.md exists but is buried among 37 other markdown files.

The dependency on an external package (`sg-spec @ git+https://...`) adds friction. The real-time features require MIDI hardware setup that isn't explained until deep in the documentation.

**Concrete improvements:**
- Create a `getting-started.md` with exactly three commands: install, demo, first practice session.
- Move all MIDI files to `exports/midi/` or `examples/midi/`. Delete duplicates (`Etude_12_Taranta_Dense_Backdoor3 (1).mid`).
- Delete or archive the `groove_layer_v0_stage_*` directories — these are development iterations, not user artifacts.
- Move `backup_pre_migration/` out of the repo or into `.gitignore`.
- Reduce root directory to <30 items.

---

### 3. Usability — 7/10

**What's good:** The CLI design is thoughtful. Commands are verb-noun structured (`zt-gravity gravity`, `zt-band rt-play`). Help text is comprehensive. The schema-based configuration (`.ztprog`, `.ztplay`, `.ztex` files) is well-documented with JSON Schema validation.

The preset system is excellent UX:
```bash
zt-band rt-play song.yaml --preset tight     # Metronomic practice
zt-band rt-play song.yaml --preset loose     # Human feel
zt-band rt-play song.yaml --preset challenge # Push yourself
zt-band rt-play song.yaml --preset recover   # After mistakes
```

The MIDI generation invariants are documented and enforced:
> "Every note_on must have a corresponding note_off. No stuck notes."

**What's wrong:** The package structure has three top-level modules in `src/`:
- `shared/zone_tritone/` — core theory
- `zt_band/` — accompaniment engine
- `sg_coach/` — coaching/evaluation

The import paths are confusing:
```python
from shared.zone_tritone.cli import main  # zt-gravity
from zt_band.cli import main               # zt-band
from sg_spec.ai.coach.cli import main      # sgc (external!)
```

The third CLI (`sgc`) imports from an external package, breaking the single-repo mental model.

The CLI documentation (CLI_DOCUMENTATION.md at 11KB) is comprehensive but lives in a different file than the Python Package documentation (PYTHON_PACKAGE.md at 7.5KB). Users must cross-reference.

**Concrete improvements:**
- Unify the package namespace: `zone_tritone.core`, `zone_tritone.band`, `zone_tritone.coach` instead of three different roots.
- Merge CLI and API documentation into a single reference or link them explicitly.
- Add shell tab-completion for CLI commands.
- Add a `--dry-run` flag to all generators that shows what would be created without writing files.

---

### 4. Reliability — 9/10

**What's good:** This is the project's strongest technical dimension.

- **661 tests** with 28% test-to-production ratio (excellent)
- **0 bare `except:` clauses** (perfect discipline)
- **0 broad `except Exception` blocks** (exceptional for a Python codebase)
- Schema validation for all configuration formats
- Determinism guarantees documented and tested (`test_determinism.py`)
- Golden file testing for MIDI output stability
- Replay gates for regression detection

The MIDI invariants are enforced:
> "No stuck notes: every note_on must have a corresponding note_off."
> "Deterministic outputs when seed/inputs are identical."

The late-drop policy for real-time scheduling is carefully designed:
```python
@dataclass(frozen=True)
class LateDropPolicy:
    """
    - never destabilize core timing/contract
    - preserve telemetry and core musical hits
    - drop ornaments first (click + low-velocity ghost note-ons)
    - never drop note_off (prevents stuck notes)
    """
```

**What's wrong:** The external dependency (`sg-spec @ git+https://github.com/HanzoRazer/sg-spec.git`) is a reliability risk. If that repo is unavailable or breaks API, this project breaks. The dependency isn't pinned to a version.

Some tests reference fixtures that may not exist in all environments (`fixtures/sessions/minimal_3pt`).

**Concrete improvements:**
- Pin the `sg-spec` dependency to a specific commit hash or version tag.
- Consider vendoring `sg-spec` if it's small, or extracting just the needed interfaces.
- Add a CI smoke test that verifies the GitHub dependency is accessible.
- Document which tests require which fixtures and add skip markers for CI.

---

### 5. Maintainability — 6/10

**What's good:** The source code is well-organized within `src/`. Type hints are used consistently. Frozen dataclasses provide immutability. The largest file is 2,100 lines (`src/zt_band/cli.py`) which is large but not pathological for a CLI with many subcommands.

The schema registry pattern is good: all JSON Schemas are in `schemas/` with versioned IDs.

**What's wrong:** The root directory is a disaster. 169 items including:
- Development archaeology: `groove_layer_v0_stage_2_5` through `groove_layer_v0_stage_3_0_clean_skeleton (1)` (8 directories of iteration history)
- Duplicate MIDI files: `Etude_8_PorArriba_Backdoor3.mid` and `Etude_8_PorArriba_Backdoor3 (1).mid`
- Backup directory: `backup_pre_migration/` (145 KB of old JSON)
- Session logs: `SESSION_2026-01-14.md`
- Raw text dumps: `Mode 1_Coach v1_models_policies_serializer_tests.txt` (78 KB)
- Space in filename: `Etude_12_Taranta_Dense_Backdoor3 (1).mid`

There are 17 `*_canonical.json` files at root level that should be in `data/` or `corpus/`.

The `emit_*.py` scripts (15 of them) are loose in the root instead of in `scripts/`.

**Concrete improvements:**
- **Immediate cleanup:** Delete `groove_layer_v0_stage_*` directories, `backup_pre_migration/`, session logs, and `.txt` dumps. These are development artifacts, not product.
- Move `*_canonical.json` to `data/corpus/`.
- Move `emit_*.py` to `scripts/generators/`.
- Move all `.mid` files to `exports/midi/` and delete duplicates.
- Enforce a root-level item limit: <30 items or CI fails.
- Fix the filename with space: rename `Etude_12_Taranta_Dense_Backdoor3 (1).mid`.

---

### 6. Cost (Resource Efficiency) — 8/10

**What's good:** Dependencies are minimal and appropriate:
- `mido` — MIDI file handling (lightweight, pure Python)
- `pyyaml` — YAML parsing
- `pydantic` — schema validation

No heavyweight frameworks. No cloud dependencies for core functionality. Runs on Raspberry Pi (mentioned in badges). The real-time scheduler is designed for low-latency operation with configurable lookahead and tick timing.

The development dependencies are standard (`pytest`, `ruff`, `mypy`).

**What's wrong:** The optional `agentd` dependencies (`fastapi`, `uvicorn`, `httpx`) suggest a server mode that isn't clearly documented. Users may install unnecessary dependencies.

The `sg-spec` external dependency adds network overhead during installation and version uncertainty.

**Concrete improvements:**
- Document what `pip install -e ".[agentd]"` enables and when users need it.
- Consider making the coaching features (`sg_coach`) optional to reduce core dependency footprint.
- Add a minimal install mode that excludes real-time features for users who only want theory analysis.

---

### 7. Safety — 7/10

**What's good:** The theory claims are testable and falsifiable. The axioms are mathematical, not mystical. The pedagogical documentation explicitly warns against skipping levels:

> "The Zone-Tritone System must be taught in layered progression. Skipping levels risks misunderstanding or drift."

The INSTRUCTOR_CERTIFICATION.md establishes standards for teaching the framework, preventing unqualified instruction.

The MIDI output has invariants to prevent stuck notes (safety for downstream DAWs and hardware):
> "No stuck notes: every note_on must have a corresponding note_off."

**What's wrong:** The real-time features interact with external MIDI hardware. There's no documentation of:
- What happens if MIDI output disconnects mid-playback
- How to recover from a stuck-note state if something goes wrong
- Whether the panic handling actually sends all-notes-off

The late-drop policy silently discards events when the scheduler falls behind. Users may not realize notes are being dropped unless they enable telemetry.

**Concrete improvements:**
- Add a `--verbose` mode that logs when events are dropped due to lateness.
- Document the panic recovery procedure and ensure all-notes-off is sent on exit/crash.
- Add a health check command: `zt-band check-midi` that verifies the MIDI connection before starting playback.
- Consider adding a "safe mode" that refuses to drop note-off events even if late.

---

### 8. Scalability — 7/10

**What's good:** The design scales horizontally: more `.ztprog` files, more style packs, more canonical JSON datasets. The pack catalog system (`pack_catalog.json`, `*.dpack.json`) supports extensibility.

The Markov model for chord transitions is O(n²) in pitch classes (12×12 matrix) — constant regardless of corpus size.

The schema versioning system supports evolution without breaking existing files.

**What's wrong:** The current design is single-user, single-device. There's no concept of:
- Cloud sync for practice data
- Multi-device session continuity
- Shared practice playlists

The `sg-agentd` server (mentioned in optional deps) suggests a client-server architecture, but it's not documented or clearly integrated.

The corpus of canonical JSON files is committed to git. Adding significant musical content (e.g., transcriptions of standards) would bloat the repo.

**Concrete improvements:**
- Document the `agentd` server mode and its use cases.
- Consider a separate `zone-tritone-corpus` package for large musical datasets.
- Add an import/export format for practice sessions that enables sharing.
- Design a lightweight sync protocol for practice statistics (can be file-based initially).

---

### 9. Aesthetics (UX Design) — 6/10

**What's good:** The CLI output is clean and informative. The gravity chain display is readable:
```
 0: G    (pc= 7, Zone 2)
 1: C    (pc= 0, Zone 1)
 2: F    (pc= 5, Zone 2)
```

The preset names (`tight`, `loose`, `challenge`, `recover`) are memorable and meaningful.

**What's wrong:** The root directory is visually overwhelming: 169 items, no clear entry point. The naming conventions are inconsistent:
- `blues_canonical.json` vs `blues_40_motives_canonical.json` vs `blues_40_motives_index.xlsx`
- `emit_blues_pack.py` vs `emit_motive_midi.py` vs `build_canonical_motives.py`
- `CBSP21.md` vs `CBSP21_old.md` (what is CBSP21?)

The badge wall in README (7 badges) is dense. The documentation has good content but poor information hierarchy — 37 markdown files with no clear reading order.

**Concrete improvements:**
- Create a `docs/READING_ORDER.md` that sequences the documentation for different audiences (musicians, developers, educators).
- Establish naming conventions: `{domain}_{type}_{variant}.{ext}` (e.g., `blues_canonical_40motives.json`).
- Reduce badge wall to 4 essential badges. Move others to a "Badges" section.
- Create visual diagrams for the zone/tritone concepts (currently described in text only).

---

## Summary Scorecard

| Category | Score | Weight | Weighted |
|---|---|---|---|
| Purpose Clarity | 9/10 | 1.0 | 9.0 |
| User Fit | 7/10 | 1.5 | 10.5 |
| Usability | 7/10 | 1.5 | 10.5 |
| Reliability | 9/10 | 1.5 | 13.5 |
| Maintainability | 6/10 | 1.5 | 9.0 |
| Cost / Resource Efficiency | 8/10 | 1.0 | 8.0 |
| Safety | 7/10 | 2.0 | 14.0 |
| Scalability | 7/10 | 0.5 | 3.5 |
| Aesthetics | 6/10 | 0.5 | 3.0 |
| **Weighted Average** | | | **7.45/10** |

---

## Comparison to Other Projects

| Dimension | string_master | tap_tone_pi | luthiers-toolbox |
|---|---|---|---|
| Lines of Python | 48,488 | 20,834 | 227,136 |
| Test ratio | 28% | 24% | ~17% |
| Bare excepts | 0 | 0 | 1 |
| Broad excepts | 0 | 34 | 700 |
| Root directory items | 169 | ~50 | ~100 |
| Weighted score | **7.45** | **7.68** | **5.15** |

The Zone-Tritone System scores between tap_tone_pi and luthiers-toolbox. Its exceptional reliability (zero exception abuse, 661 tests) is offset by severe maintainability issues (169 root items, development archaeology). The theoretical framework is its greatest asset; the file organization is its greatest liability.

---

## Top 5 Actions (Ranked by Impact)

1. **Clean the root directory.** Delete `groove_layer_v0_stage_*`, `backup_pre_migration/`, session logs, `.txt` dumps, and duplicate MIDI files. Move `*_canonical.json` to `data/`, `emit_*.py` to `scripts/`, and `.mid` files to `exports/`. Target: <30 root items.

2. **Unify the project identity.** Pick one name (suggest: "Zone-Tritone" or `zt`). Update pyproject.toml `name` from "smart-guitar", align repo name, package imports, and CLI commands.

3. **Create a single getting-started path.** Write a `getting-started.md` that takes a musician from zero to hearing their first generated accompaniment in under 5 minutes.

4. **Pin or vendor the external dependency.** The `sg-spec @ git+https://...` pattern is fragile. Pin to a commit hash or extract the needed interfaces into this repo.

5. **Unify the package namespace.** Replace `shared/zone_tritone/`, `zt_band/`, and `sg_coach/` with a single `zone_tritone/` namespace containing `core`, `band`, and `coach` subpackages.

---

*This project earns a 7.45/10 — a solid B grade. The theoretical framework is exceptional, and the code quality (zero exception abuse, 28% test coverage) demonstrates real engineering discipline. The main issue is file organization: the repo looks like an active development workspace rather than a shippable product. A focused cleanup sprint could raise this to 8.5+.*
