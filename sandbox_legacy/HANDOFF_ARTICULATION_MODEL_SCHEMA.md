# Handoff: Articulation Model Schema Field (Checklist Item 7)

> **Source**: Barry Harris Jazz Workshop analysis + blues exercise audit
> **Goal**: Add `articulation_model` field to the .ztex schema
> **Effort**: Schema + metadata enrichment — no new MIDI files needed

---

## Concept

Exercises currently declare WHAT to play but not HOW to articulate it.
Adding an `articulation_model` field lets .ztex files declare the required
articulation technique, enabling future assessment features to verify
correct execution.

---

## Schema Change

### File: `schemas/ztex.schema.json`

Add `articulation_model` to the `packExercise` properties block
(after `category`, around line 66):

```json
"articulation_model": {
  "type": "string",
  "description": "Required articulation technique for this exercise.",
  "enum": [
    "3-2-1_pulloff",
    "hammer_on_triplet",
    "chromatic_slide",
    "ghost_note_accent",
    "rake_mute",
    "bend_release",
    "vibrato_sustain",
    "fingerpick_shuffle",
    "hybrid_pick",
    "legato_slur"
  ]
}
```

**Location in the schema** — insert inside `packExercise.properties`:

```json
"properties": {
    "id": { ... },
    "title": { ... },
    "level": { ... },
    "category": { ... },
    "articulation_model": {    // ← INSERT HERE
      "type": "string",
      "description": "Required articulation technique for this exercise.",
      "enum": [
        "3-2-1_pulloff",
        "hammer_on_triplet",
        "chromatic_slide",
        "ghost_note_accent",
        "rake_mute",
        "bend_release",
        "vibrato_sustain",
        "fingerpick_shuffle",
        "hybrid_pick",
        "legato_slur"
      ]
    },
    "concept": { ... },
    ...
}
```

The field is optional (not in `required`). Existing exercises remain valid.

---

## Exercises to Tag

After adding the schema field, tag these existing exercises:

### Bucket A exercises

| File | articulation_model | Reason |
|------|--------------------|--------|
| `exercises/bucket_a/voodoo_child_intro_etude_Em.ztex` | `bend_release` | Hendrix expressive bends |
| `exercises/bucket_a/dorian_intro_etude_Cm.ztex` | `legato_slur` | Modal phrasing, smooth connections |
| `exercises/bucket_a/walkin_blues_riff_C.ztex` | `ghost_note_accent` | Delta shuffle ghost notes |
| `exercises/bucket_a/when_you_have_a_good_friend_C.ztex` | `vibrato_sustain` | Slow blues vocal phrasing |
| `exercises/bucket_a/gospel_chromatic_lick_C.ztex` | `chromatic_slide` | Chromatic passing tone fill |
| `exercises/bucket_a/dorian_chromatic_lick_Cm.ztex` | `chromatic_slide` | Dorian chromatic fill |

### Chromatic triplet exercises

| File | articulation_model | Reason |
|------|--------------------|--------|
| `exercises/chromatic_triplets/chromatic_triplet_chain_dim7_C.ztex` | `hammer_on_triplet` | Triplet cell articulation |
| `exercises/chromatic_triplets/chromatic_triplet_chain_maj6_C.ztex` | `hammer_on_triplet` | Triplet cell articulation |
| `exercises/chromatic_triplets/chromatic_triplet_chain_ii_V_I_C.ztex` | `hammer_on_triplet` | Triplet cell articulation |

### Enclosure exercises

| File | articulation_model | Reason |
|------|--------------------|--------|
| `exercises/enclosures/bebop_enclosure_descending.ztex` | `legato_slur` | Smooth descending line |
| `exercises/got_rhythm/got_rhythm_enclosure_study2.ztex` | `hammer_on_triplet` | Barry Harris triplet enclosures |
| `exercises/got_rhythm/got_rhythm_bb7_eb7_study1.ztex` | `hammer_on_triplet` | Chromatic triplet technique |

---

## How to Apply

For each exercise, add a single line after `category:` (or after `exercise_type:` if no category):

```yaml
articulation_model: "hammer_on_triplet"
```

Example patch for `chromatic_triplet_chain_dim7_C.ztex`:

```diff
 id: chromatic_triplet_chain_dim7_C
 title: "Chromatic Triplet Chain -- Cdim7 (Pure Diminished)"
 program_ref: chromatic_triplet_chain_dim7_C.ztprog
 exercise_type: melodic_motion
+articulation_model: "hammer_on_triplet"

 phrase_type: chromatic_cells
```

---

## Enum Definitions

| Value | Technique | When to Use |
|-------|-----------|-------------|
| `3-2-1_pulloff` | Descending pull-off pattern (3 fingers to open) | Classical/flamenco descending runs |
| `hammer_on_triplet` | Hammer-on groups of 3 (triplet cells) | Barry Harris triplet chains, enclosures |
| `chromatic_slide` | Chromatic half-step slides between notes | Gospel fills, chromatic licks |
| `ghost_note_accent` | Muted ghost notes between accented notes | Delta shuffle, funk grooves |
| `rake_mute` | Muted rake across strings before attack | Blues intros, SRV style |
| `bend_release` | Pitch bend up + controlled release | Hendrix, BB King, expressive blues |
| `vibrato_sustain` | Sustained notes with finger vibrato | Slow blues, vocal phrasing |
| `fingerpick_shuffle` | Alternating bass + treble fingerpicking | Robert Johnson, country blues |
| `hybrid_pick` | Pick + fingers simultaneously | Country, bluegrass, modern jazz |
| `legato_slur` | Smooth hammer/pull without re-picking | Modal phrasing, bebop lines |

---

## Summary

| Action | File | What |
|--------|------|------|
| UPDATE | `schemas/ztex.schema.json` | Add `articulation_model` enum field to packExercise |
| UPDATE | 12 `.ztex` files (see table above) | Add `articulation_model:` line |

No new files, no MIDI, no .ztprog changes.

After applying, update `sandbox_legacy/SANDBOX_PICKUP_CHECKLIST.md` item 7 → DONE.
