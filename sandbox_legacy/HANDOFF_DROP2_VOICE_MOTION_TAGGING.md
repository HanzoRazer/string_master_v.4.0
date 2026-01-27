# Handoff: Drop-2 Voice Motion Tagging (Checklist Item 5)

> **Source**: Barry Harris Drop-2 Exercises PDF (`341495925-Barry-Harris-Drop-2-Exercises.pdf`)
> **Goal**: Add `voice_motion` metadata to existing voicing exercises
> **Effort**: Metadata enrichment — no new MIDI files needed

---

## Concept

Barry Harris Drop-2 voicings move in predictable voice-motion patterns:

- **v6**: soprano and tenor move (voices 1 & 3 in SATB)
- **b6**: bass and alto move (voices 4 & 2 in SATB)
- **String set**: top 4 (strings 1-4) vs middle 4 (strings 2-5)
- **Motion type**: contrary, parallel, oblique

These labels allow exercises to be filtered and grouped by which voices
are moving, enabling focused practice on specific hand movements.

---

## Existing Files to Update

### 1. `exercises/voicings/diminished_drop2_cycle.ztex`

Current content (no voice_motion tags):
```yaml
id: diminished_drop2_cycle
title: "Diminished Drop-2 Cycle (12 Keys)"
program_ref: ../../programs/voicing_diminished_drop2_cycle.ztprog
exercise_type: voicing_memory

goals:
  - "Smooth transitions between root-position chords"
  - "Internalize minor → dominant cycling across keys"

practice_steps:
  - "Start at 80 BPM"
  - "Play each voicing twice"
  - "Increase tempo gradually"

assessment:
  what_to_measure:
    - timing_consistency_ms
    - loop_accuracy
  pass_criteria:
    max_timing_deviation_ms: 40
```

**Add** a `tags:` block and `voice_motion:` metadata:
```yaml
tags:
  voicing_type: drop2
  origin: barry_harris_class

voice_motion:
  primary: "v6"
  description: "Soprano and tenor voices move; alto and bass hold."
  string_set: "top_four"
  motion_type: "parallel"
  moving_voices: ["soprano", "tenor"]
  static_voices: ["alto", "bass"]
```

### 2. `exercises/voicings/v6_contrary_top4.ztex`

Already has tags — add `voice_motion:` block:
```yaml
# Existing tags (keep):
tags:
  voicing_type: drop2
  motion_type: contrary
  string_set: top_four
  voicing_progression: ["C6", "E°", "Ebm6"]

# ADD:
voice_motion:
  primary: "v6"
  description: "Soprano and tenor move in contrary motion over top 4 strings."
  string_set: "top_four"
  motion_type: "contrary"
  moving_voices: ["soprano", "tenor"]
  static_voices: ["alto", "bass"]
```

---

## New Files to Create

### 3. `exercises/voicings/b6_parallel_top4.ztex` (NEW)

```yaml
id: b6_parallel_top4
title: "Drop-2 Top 4 Motion: b6 Parallel (Bass + Alto Move)"
program_ref: b6_parallel_top4.ztprog
exercise_type: voicing_motion

goals:
  - "Track bass & alto parallel motion across drop-2 top string set"
  - "Keep soprano and tenor stationary while lower voices move"
  - "Contrast with v6 exercises -- opposite voices"

practice_steps:
  - "Play C6 voicing on top 4 strings"
  - "Move only the bass and alto notes down by half-step"
  - "Loop slowly -- feel which fingers move and which stay planted"
  - "Compare to v6_contrary_top4 -- hear the difference"

tags:
  voicing_type: drop2
  motion_type: parallel
  string_set: top_four
  origin: barry_harris_class

voice_motion:
  primary: "b6"
  description: "Bass and alto voices move in parallel; soprano and tenor hold."
  string_set: "top_four"
  motion_type: "parallel"
  moving_voices: ["bass", "alto"]
  static_voices: ["soprano", "tenor"]

assessment:
  what_to_measure:
    - timing_consistency_ms
    - voicing_change_accuracy
  pass_criteria:
    max_timing_deviation_ms: 40
```

### 4. `exercises/voicings/b6_parallel_top4.ztprog` (NEW)

```yaml
id: b6_parallel_top4
title: "Drop-2 b6 Parallel Motion Backing"
tempo_bpm: 72
tempo_range: [50, 110]
root: C
loop_bars: 4

levels:
  beginner:
    tempo_bpm: 50
    comping: whole_notes
  intermediate:
    tempo_bpm: 72
    comping: rhythmic
  advanced:
    tempo_bpm: 110
    comping: syncopated

instruments:
  - type: drum_kit
    pattern:
      kick:   [1, 3]
      snare:  [2, 4]
      hihat:  ["1&", "2&", "3&", "4&"]
  - type: bass_pedal
    note: C
    octave: 2
    pattern: [1, 3]
```

### 5. `exercises/voicings/v6_oblique_mid4.ztex` (NEW)

```yaml
id: v6_oblique_mid4
title: "Drop-2 Mid 4 Motion: v6 Oblique (Soprano Moves, Tenor Holds)"
program_ref: v6_oblique_mid4.ztprog
exercise_type: voicing_motion

goals:
  - "Practice oblique motion: one voice moves, others hold"
  - "Middle 4 string set (strings 2-5)"
  - "Soprano resolves stepwise while tenor sustains"

practice_steps:
  - "Play Dm7 drop-2 on middle 4 strings"
  - "Move soprano voice down by step while tenor holds"
  - "Feel the voice independence -- oblique motion trains finger independence"

tags:
  voicing_type: drop2
  motion_type: oblique
  string_set: middle_four
  origin: barry_harris_class

voice_motion:
  primary: "v6"
  description: "Soprano moves stepwise; tenor, alto, bass hold."
  string_set: "middle_four"
  motion_type: "oblique"
  moving_voices: ["soprano"]
  static_voices: ["tenor", "alto", "bass"]

assessment:
  what_to_measure:
    - timing_consistency_ms
    - voicing_change_accuracy
  pass_criteria:
    max_timing_deviation_ms: 40
```

### 6. `exercises/voicings/v6_oblique_mid4.ztprog` (NEW)

Same structure as b6_parallel_top4.ztprog but with `root: D` and shell_voicings on `im7`.

---

## Optional: `data/voicing_motion_ruleset.yaml` (NEW)

Central index of voice motion rules for lookup/validation:

```yaml
# Voice Motion Ruleset v1
# Source: Barry Harris Drop-2 Exercises PDF

voice_labels:
  v6:
    name: "Voice 6 motion"
    moving: ["soprano", "tenor"]
    static: ["alto", "bass"]
    description: "Outer voices of the soprano-tenor pair move."
  b6:
    name: "Bass 6 motion"
    moving: ["bass", "alto"]
    static: ["soprano", "tenor"]
    description: "Lower voices of the SATB stack move."

motion_types:
  contrary:
    description: "Moving voices go in opposite directions."
  parallel:
    description: "Moving voices go in the same direction."
  oblique:
    description: "One voice moves, the other holds."

string_sets:
  top_four:
    strings: [1, 2, 3, 4]
    description: "High E, B, G, D"
  middle_four:
    strings: [2, 3, 4, 5]
    description: "B, G, D, A"

exercises:
  - id: diminished_drop2_cycle
    voice_motion: v6
    motion_type: parallel
    string_set: top_four
  - id: v6_contrary_top4
    voice_motion: v6
    motion_type: contrary
    string_set: top_four
  - id: b6_parallel_top4
    voice_motion: b6
    motion_type: parallel
    string_set: top_four
  - id: v6_oblique_mid4
    voice_motion: v6
    motion_type: oblique
    string_set: middle_four
```

---

## Summary of Changes

| Action | File | What |
|--------|------|------|
| UPDATE | `exercises/voicings/diminished_drop2_cycle.ztex` | Add `tags:` + `voice_motion:` block |
| UPDATE | `exercises/voicings/v6_contrary_top4.ztex` | Add `voice_motion:` block |
| CREATE | `exercises/voicings/b6_parallel_top4.ztex` | New b6 parallel exercise |
| CREATE | `exercises/voicings/b6_parallel_top4.ztprog` | Backing for b6 exercise |
| CREATE | `exercises/voicings/v6_oblique_mid4.ztex` | New v6 oblique exercise |
| CREATE | `exercises/voicings/v6_oblique_mid4.ztprog` | Backing for oblique exercise |
| CREATE | `data/voicing_motion_ruleset.yaml` | Central motion rule index (optional) |

No MIDI generation needed. No schema changes needed (packExercise allows additionalProperties).

After applying, update `sandbox_legacy/SANDBOX_PICKUP_CHECKLIST.md` item 5 → DONE.
