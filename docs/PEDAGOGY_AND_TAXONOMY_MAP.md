# Pedagogy and Taxonomy Map

> **Purpose**: Single source of truth for where pedagogical and taxonomic material lives, how it's structured, and how to extend it.

---

## Quick Reference

| What | Where | Format |
|------|-------|--------|
| Dance form definitions | `sg_spec/ai/coach/dance_packs/**/*.yaml` | YAML (DancePackV1) |
| Product bundles | `sg_spec/ai/coach/pack_sets/*.yaml` | YAML (DancePackSetV1) |
| Schema (locked) | `sg_spec/ai/coach/dance_pack.py` | Pydantic model |
| Pack set schema | `sg_spec/ai/coach/dance_pack_set.py` | Pydantic model |
| Coach integration | `sg_spec/ai/coach/pack_set_policy.py` | Python helpers |
| Authoring tools | `zt_band/dance_pack_tools.py` | CLI + validators |

---

## 1. Dance Form Taxonomy

Dance Packs encode **groove systems** (not genres). Each pack defines:
- Rhythmic feel (subdivision, swing, accents)
- Harmonic constraints (rhythm, dominant behavior, tritone usage)
- Performance profile (velocity, articulation, contour)
- Practice mapping (focus areas, difficulty, prerequisites)

### Current Dance Families

| Family | Packs | Subdivision | Characteristics |
|--------|-------|-------------|-----------------|
| **afro_brazilian** | bossa_canonical_v1, samba_traditional_v1 | binary | Syncopated, layered polyrhythm |
| **jazz_american** | jazz_blues_12bar_v1, rhythm_changes_v1 | ternary | Swing feel, harmonic sophistication |
| **latin_american** | salsa_clave_locked_v1 | binary | Clave-locked, high tempo |
| **blues_american** | funk_16th_pocket_v1, gospel_shout_shuffle_v1, neo_soul_laidback_pocket_v1 | binary/ternary | Pocket-focused, expressive dynamics |
| **rock_american** | rock_straight_v1 | binary | Grid-locked, driving |
| **country_american** | country_train_beat_v1 | binary | Train beat, steady pulse |
| **fusion** | disco_four_on_floor_v1, house_grid_v1, hiphop_half_time_v1 | binary | Cross-genre synthesis |

### Full Pack Index

| Pack ID | Family | Subdivision | Tempo (BPM) | Difficulty |
|---------|--------|-------------|-------------|------------|
| rock_straight_v1 | rock_american | binary | 90-140 | beginner |
| country_train_beat_v1 | country_american | binary | 100-140 | beginner |
| disco_four_on_floor_v1 | fusion | binary | 110-130 | easy |
| house_grid_v1 | fusion | binary | 118-132 | easy |
| hiphop_half_time_v1 | fusion | binary | 70-95 | medium |
| samba_traditional_v1 | afro_brazilian | binary | 88-104 | medium |
| jazz_blues_12bar_v1 | jazz_american | ternary | 80-160 | medium |
| bossa_canonical_v1 | afro_brazilian | binary | 120-145 | hard |
| funk_16th_pocket_v1 | blues_american | binary | 90-115 | hard |
| gospel_shout_shuffle_v1 | blues_american | ternary | 70-110 | hard |
| salsa_clave_locked_v1 | latin_american | binary | 160-210 | hard |
| neo_soul_laidback_pocket_v1 | blues_american | binary | 65-90 | advanced |
| rhythm_changes_v1 | jazz_american | ternary | 140-280 | advanced |

---

## 2. Pedagogical Progression

### Difficulty Levels

| Level | Meaning | Example Packs |
|-------|---------|---------------|
| **beginner** | Grid-locked, forgiving timing | rock_straight_v1, country_train_beat_v1 |
| **easy** | Steady pulse, minimal syncopation | disco_four_on_floor_v1, house_grid_v1 |
| **medium** | Introduces swing or syncopation | jazz_blues_12bar_v1, samba_traditional_v1 |
| **hard** | Complex rhythm, tight pocket | funk_16th_pocket_v1, salsa_clave_locked_v1 |
| **advanced** | Maximum complexity, virtuosic | rhythm_changes_v1, neo_soul_laidback_pocket_v1 |

### Recommended Learning Path

```
                    ┌─────────────────────┐
                    │  GROOVE FOUNDATIONS │
                    │       (core)        │
                    └──────────┬──────────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         │                     │                     │
         ▼                     ▼                     ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   SYNCOPATION   │  │    DOMINANT     │  │   (future)      │
│   & GHOSTS      │  │    TENSION      │  │   MODAL         │
│    (plus)       │  │     (plus)      │  │   EXPLORATION   │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

### Pack Set Products

| Set ID | Display Name | Tier | Packs |
|--------|--------------|------|-------|
| groove_foundations_v1 | Groove Foundations | core | rock_straight_v1, disco_four_on_floor_v1, house_grid_v1, country_train_beat_v1, hiphop_half_time_v1 |
| dominant_tension_v1 | Dominant Motion & Tension | plus | jazz_blues_12bar_v1, rhythm_changes_v1, gospel_shout_shuffle_v1, bossa_canonical_v1 |
| syncopation_ghosts_v1 | Syncopation & Ghost Notes | plus | funk_16th_pocket_v1, samba_traditional_v1, salsa_clave_locked_v1, neo_soul_laidback_pocket_v1 |

---

## 3. Core Taxonomy Concepts

### Rhythmic Primitives

| Concept | Values | Meaning |
|---------|--------|---------|
| **subdivision** | binary, ternary, compound | How beats divide (2s vs 3s) |
| **swing_ratio** | 0.0 - 0.67 | Triplet feel amount (0 = straight) |
| **clave.type** | none, son, rumba, bossa | Underlying rhythmic key |
| **accent_grid** | strong_beats, secondary_beats | Where emphasis falls |

### Harmonic Primitives

| Concept | Meaning |
|---------|---------|
| **harmonic_rhythm** | How often chords change relative to cycle |
| **dominant_behavior** | V-I resolution rules |
| **tritone_usage** | When/if b5 intervals are allowed |
| **modal_constraints** | Parallel minor, modal interchange limits |

### Practice Primitives

| Concept | Meaning |
|---------|---------|
| **primary_focus** | What skill this pack trains |
| **evaluation_weights** | How to score performance |
| **difficulty_rating** | Skill level required |
| **prerequisite_forms** | What packs should come first |

---

## 4. Three-Layer Architecture

### Layer 1: Canonical Pedagogy (docs)

**Location**: `docs/`

**Contains**: Concepts, intent, philosophy, non-negotiables

**Examples**:
- Why "feel before theory"
- Why constraint-driven learning
- Why groove integrity matters

**Rule**: Human-readable, not executable. Informs design, doesn't run.

### Layer 2: Executable Taxonomy (code)

**Location**: `sg_spec/ai/coach/dance_packs/`, `zt_band/dance_packs/`

**Contains**: Dance Pack YAML files, Pydantic schemas, validators

**Examples**:
- `samba_traditional_v1.yaml` defines exact groove constraints
- `DancePackV1` enforces schema compliance
- `pack_to_assignment_defaults()` derives practice parameters

**Rule**: Machine-readable, schema-locked. Taxonomy becomes enforceable.

### Layer 3: Runtime Learning State (user data)

**Location**: Smart Guitar app, sg-coach runtime

**Contains**: Session records, evaluations, assignments, telemetry

**Examples**:
- What the player did (SessionRecord)
- What matters about it (CoachEvaluation)
- What to do next (PracticeAssignment)

**Rule**: User-specific, non-canonical. Never feeds back into core taxonomy.

---

## 5. How to Add New Content

### Adding a New Dance Pack

1. **Create YAML file**:
   ```
   sg_spec/ai/coach/dance_packs/{family}/{pack_id}.yaml
   ```

2. **Follow schema** (see existing packs for template):
   ```yaml
   schema_id: dance_pack
   schema_version: v1

   metadata:
     id: {pack_id}
     display_name: "Human Name"
     dance_family: {family}
     version: "1.0.0"
     author: "your_name"
     license: core
     engine_compatibility: ">=0.2.0"
     tags: [tag1, tag2]

   groove:
     meter: "4/4"
     cycle_bars: 4
     subdivision: binary
     tempo_range_bpm: [80, 120]
     swing_ratio: 0.0
     accent_grid:
       strong_beats: [1]
       secondary_beats: [3]
     clave:
       type: none

   harmony_constraints:
     harmonic_rhythm:
       max_changes_per_cycle: 4
       min_beats_between_changes: 2.0
     # ... (see existing packs)

   performance_profile:
     velocity_range:
       min: 45
       max: 95
     # ... (see existing packs)

   practice_mapping:
     primary_focus: [timing, groove]
     evaluation_weights:
       timing_accuracy: 0.4
       harmonic_choice: 0.2
       dynamic_control: 0.2
       groove_feel: 0.2
     difficulty_rating: medium

   extensions: {}
   ```

3. **Validate**:
   ```bash
   zt-band dance-pack-validate sg_spec/ai/coach/dance_packs/{family}/{pack_id}.yaml
   ```

4. **Build canonical JSON** (optional, for zt_band):
   ```bash
   zt-band dance-pack-build-json sg_spec/ai/coach/dance_packs/{family}/{pack_id}.yaml
   ```

5. **Add tests** in `sg_spec/tests/test_dance_pack_loading.py`

6. **Update this document** (add to pack index table)

### Adding a New Pack Set

1. **Create YAML file**:
   ```
   sg_spec/ai/coach/pack_sets/{set_id}.yaml
   ```

2. **Follow schema**:
   ```yaml
   schema_id: dance_pack_set
   schema_version: v1

   metadata:
     id: {set_id}
     display_name: "Human Name"
     version: "1.0.0"
     tier: core  # or plus, pro
     sku: packs.{set_id}
     tags: [tag1, tag2]

   packs:
     - pack_id_1
     - pack_id_2
     - pack_id_3

   extensions: {}
   ```

3. **Validate references** (all pack IDs must exist):
   ```python
   from sg_spec.ai.coach.dance_pack_set import load_set_from_file
   ps = load_set_from_file("path/to/set.yaml")  # raises if pack missing
   ```

4. **Add tests** in `sg_spec/tests/test_dance_pack_set_loading.py`

5. **Update this document** (add to pack set table)

### Adding a New Dance Family

1. Create directory: `sg_spec/ai/coach/dance_packs/{new_family}/`
2. Add `__init__.py` (empty)
3. Add at least one pack YAML
4. Update `dance_pack.py` → `list_pack_paths()` to include new family
5. Update this document (add to family table)

---

## 6. What Must Never Change

### Schema Lock (DancePackV1)

The following are **frozen**:
- Field names and types
- Enum values (subdivision, license, difficulty_rating, etc.)
- Validation rules (weights sum to 1.0, tempo min < max, etc.)

**Why**: Downstream consumers depend on exact schema. Changes break compatibility.

**How to extend**: Use `extensions: {}` for experimental fields.

### Pedagogical Non-Negotiables

| Principle | Meaning |
|-----------|---------|
| **Feel before theory** | Practice precedes explanation |
| **Constraint-driven** | Limits create learning |
| **Groove integrity** | Rhythm is non-negotiable |
| **Determinism** | Same input → same output |
| **Guitar-first UX** | Designed for instrument in hand |

---

## 7. Quick Commands

### zt-band CLI (authoring)

```bash
# Validate all packs
zt-band dance-pack-validate sg_spec/ai/coach/dance_packs/

# Build canonical JSON for all packs
zt-band dance-pack-build-json sg_spec/ai/coach/dance_packs/
```

### sgc CLI (sg-spec)

```bash
# List all dance packs
sgc dance-pack-list
sgc dance-pack-list --json

# List all pack sets
sgc dance-pack-set-list
sgc dance-pack-set-list --json

# Validate a pack set (checks all pack IDs exist)
sgc dance-pack-set-validate groove_foundations_v1
sgc dance-pack-set-validate --path custom_set.yaml

# Show detailed pack set summary
sgc dance-pack-set-show groove_foundations_v1
sgc dance-pack-set-show groove_foundations_v1 --json
```

### Python API

```python
# List all pack IDs
from sg_spec.ai.coach.dance_pack import list_pack_ids
print(list_pack_ids())

# Get assignment defaults for a pack set
from sg_spec.ai.coach.pack_set_policy import summarize_pack_set
print(summarize_pack_set("groove_foundations_v1"))
```

### Tests

```bash
# Run all dance pack tests
cd sg-spec && python -m pytest sg_spec/tests/test_dance_pack*.py sg_spec/tests/test_pack_set_policy.py -v
```

---

## Changelog

| Date | Change |
|------|--------|
| 2025-01-25 | Add sgc CLI commands for pack sets (list, validate, show). |
| 2025-01-25 | Initial creation. 13 packs, 3 sets, full taxonomy index. |
