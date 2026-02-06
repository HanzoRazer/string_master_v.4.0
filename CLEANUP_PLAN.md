# String Master v4.0 — Cleanup Plan

**Created:** 2026-02-06
**Based on:** Design Review (Score: 7.45/10)
**Goal:** Reduce root from 171 items to <30 items

---

## Phase 0: Delete Development Archaeology (HIGH PRIORITY)

These directories are iteration history with no production value:

```bash
# 8 groove_layer staging directories
rm -rf groove_layer_v0_stage_2_5/
rm -rf groove_layer_v0_stage_2_6/
rm -rf groove_layer_v0_stage_2_7/
rm -rf groove_layer_v0_stage_2_8/
rm -rf groove_layer_v0_stage_2_8_fixed/
rm -rf groove_layer_v0_stage_2_8a_tempo_only_spike/
rm -rf groove_layer_v0_stage_2_9/
rm -rf "groove_layer_v0_stage_3_0_clean_skeleton (1)/"

# Pre-migration backup
rm -rf backup_pre_migration/

# Legacy sandbox
rm -rf sandbox_legacy/
```

**Impact:** -11 directories

---

## Phase 1: Relocate MIDI Files

30 MIDI files scattered in root. Move to `exports/midi/`:

```bash
mkdir -p exports/midi/etudes
mkdir -p exports/midi/backdoor

# Etude series (21 files)
mv Etude_*.mid exports/midi/etudes/

# Backdoor etudes (3 files)
mv backdoor_etude_*.mid exports/midi/backdoor/

# Demo files
mv demo_Bb.mid exports/midi/
mv test_*.mid exports/midi/  # if any test MIDIs
```

**Impact:** -30 files from root

---

## Phase 2: Relocate Canonical JSON

Move `*_canonical.json` corpus files to `data/corpus/`:

```bash
mkdir -p data/corpus

mv barry_harris_canonical.json data/corpus/
mv bluegrass_canonical.json data/corpus/
mv blues_40_motives_canonical.json data/corpus/
mv blues_canonical.json data/corpus/
mv chromatic_triplets_canonical.json data/corpus/
mv cycles_canonical.json data/corpus/
mv enclosures_canonical.json data/corpus/
mv flamenco_canonical.json data/corpus/
mv gospel_canonical.json data/corpus/
mv got_rhythm_canonical.json data/corpus/
mv latin_canonical.json data/corpus/
mv minor_gravity_canonical.json data/corpus/
mv phrygian_gravity_canonical.json data/corpus/
mv pivot_canonical.json data/corpus/
mv phrases_canonical.json data/corpus/
mv rock_canonical.json data/corpus/
mv voicings_canonical.json data/corpus/
```

**Impact:** -17 files from root

---

## Phase 3: Relocate Design Specs + Delete True Dumps

**KEEP (relocate to docs/design_specs/):**
```bash
mkdir -p docs/design_specs

mv "Backdoor Cadence Engine.txt" docs/design_specs/backdoor_cadence_engine_spec.md
mv "Por Medio_A flamenco_Andalusian cadence.txt" docs/design_specs/andalusian_cadence_engine_spec.md

# PENDING REVIEW - see docs/BOOKMARK_SG_COACH_SPEC_REVIEW.md
mv "Mode 1_Coach v1_models_policies_serializer_tests.txt" docs/design_specs/sg_coach_v1_spec.md
```

**DELETE (true ephemeral dumps):**
```bash
rm progression.txt
rm test_chords.txt
rm text_output.txt
```

**Impact:** -3 files deleted, 3 files relocated

---

## Phase 4: Consolidate Documentation

37 markdown files in root is sprawl. Keep only:

| Keep in Root | Move to docs/ |
|--------------|---------------|
| README.md | ACADEMIC_PAPER.md |
| LICENSE | ARCHETYPE_DICTIONARY.md |
| CHANGELOG.md | ARCHITECTURE.md |
| | ARCHIVE_INDEX.md |
| | BRAND_STYLE_GUIDE.md |
| | CANON.md, Canon v1.md |
| | CBSP21.md, CBSP21_old.md |
| | CLI_DOCUMENTATION.md |
| | DEVELOPER_GUIDE.md |
| | EXAMPLES_HTML.md |
| | FAQ.md |
| | FORMAL_PROOFS.md |
| | FORMAT_GUIDE.md |
| | GLOSSARY.md |
| | GOVERNANCE.md |
| | INSTRUCTOR_CERTIFICATION.md |
| | LATEX_COMPILATION_GUIDE.md |
| | LICENSE-THEORY.md |
| | NOTATION_CONVENTIONS.md |
| | PEDAGOGY.md |
| | PROJECT_COMPLETE.md |
| | PROJECT_STRUCTURE.md |
| | PYTHON_PACKAGE.md |
| | QUICK_REFERENCE.md |
| | SESSION_*.md |
| | SNAPSHOT_v1.md |
| | STUDENT_ASSESSMENT_RUBRICS.md |
| | THEORY_DIAGRAMS.md |
| | blue_bossa_analysis.md |
| | c_major_analysis.md |
| | dominant_example.md |

```bash
# Move all non-essential docs
mv ACADEMIC_PAPER.md docs/
mv ARCHETYPE_DICTIONARY.md docs/
mv ARCHITECTURE.md docs/
# ... (remaining 30+ files)
```

**Impact:** -30+ files from root

---

## Phase 5: Consolidate Pack Directories

Three pack directories should merge:

```bash
# Move contents to packs/
mv motivic_etudes_pack/* packs/motivic_etudes/
mv zone_tritone_pack/* packs/zone_tritone/
rmdir motivic_etudes_pack/
rmdir zone_tritone_pack/
```

**Impact:** -2 directories

---

## Phase 6: Gitignore Runtime Artifacts

Add to `.gitignore`:

```gitignore
# Runtime
logs/
*.coverage
.pytest_cache/
.ruff_cache/
__pycache__/
dist/
*.egg-info/

# Generated
*.html
dominant_cycle.html
```

Then:
```bash
git rm -r --cached logs/
git rm dominant_cycle.html
```

**Impact:** -2 items

---

## Phase 7: Relocate Scripts

Move loose scripts to `scripts/`:

```bash
mv build_canonical_motives.py scripts/corpus/
mv emit_12key_packs.py scripts/generators/
mv compile-paper.sh scripts/build/
mv compile-paper.ps1 scripts/build/
mv demo.py scripts/examples/
```

**Impact:** -5 files from root

---

## Summary

| Phase | Action | Items Removed |
|-------|--------|---------------|
| 0 | Delete staging dirs | -11 dirs |
| 1 | Move MIDIs | -30 files |
| 2 | Move canonical JSON | -17 files |
| 3 | Relocate specs + delete dumps | -3 files (3 relocated) |
| 4 | Move docs | -30+ files |
| 5 | Consolidate packs | -2 dirs |
| 6 | Gitignore runtime | -2 items |
| 7 | Move scripts | -5 files |
| **Total** | | **~103 items** |

**Expected Result:** 171 - 103 = **~68 items** (further consolidation needed)

---

## Target Root Structure (Final)

```
string_master_v.4.0/
├── .github/
├── .gitignore
├── CHANGELOG.md
├── LICENSE
├── README.md
├── pyproject.toml
├── data/
│   └── corpus/           ← canonical JSON files
├── docs/                  ← all documentation
├── examples/
├── exercises/
├── exports/
│   └── midi/             ← all MIDI files
├── fixtures/
├── packs/
├── playlists/
├── programs/
├── schemas/
├── scripts/
├── seeds/
├── src/
├── tests/
└── tools/
```

**Target:** 20 root items (currently 171)

---

## Execution Order

1. **Phase 0 first** — removes 11 directories of dead weight
2. **Phase 3 next** — quick wins, delete session dumps
3. **Phase 1-2** — relocate MIDIs and JSON (bulk reduction)
4. **Phase 4** — consolidate docs (biggest impact)
5. **Phase 5-7** — finish cleanup

---

## Identity Decision (Blocking)

Before cleanup, decide on ONE project name:

| Current Names | Recommendation |
|---------------|----------------|
| string_master_v.4.0 | Rename repo to `string-master` |
| Zone-Tritone | Keep as subpackage name only |
| Groove Layer | Delete (development archaeology) |
| CBSP21 | Keep as theory module name |
| Smart Guitar Coach | External branding only |

**Action:** Rename GitHub repo from `string_master_v.4.0` to `string-master`

---

*Estimated time: 2-3 hours for full execution*
