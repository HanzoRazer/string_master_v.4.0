# MIDI Generator Specification — Developer Answers

> **Context**: Answers to engineering questions for building a clean, modular 12-key jazz practice generator. Aligned with the zt-band pedagogy (see `PEDAGOGY_AND_TAXONOMY_MAP.md`).

---

## 1. Musical Phrases and Structure

### Base Phrase(s)

| Question | Answer |
|----------|--------|
| More resolutions beyond C7→F, Gb7→B? | **No** — keep exactly 2 tritone pairs. They are complementary (C7 and Gb7 are tritone substitutes of each other). Transposition generates all 12 keys from these 2 base phrases. |
| Format | ✅ Current format is correct: lick + bass + 2-4 chords per phrase |

**Rationale**: Tritone pairs are pedagogically complete. C7→F and Gb7→B cover the "home" and "away" tritone relationship. Transposing both through all 12 keys gives 24 total phrase instances (2 phrases × 12 keys).

### Phrase Length

| Question | Answer |
|----------|--------|
| Bar length | **4 beats per phrase** (1 bar in 4/4). Each phrase = 1 bar of dominant → 1 bar of resolution = **2 bars total per phrase pair**. |
| Pickup notes | **No** — start on beat 1. Keeps timing predictable for practice. |
| Rests | **Yes** — half-bar rest between phrases (already implemented as `ticks_quarter() * 2`). |

---

## 2. Musical Content Style

### Lick Style

| Question | Answer |
|----------|--------|
| Style | **Chromatic / bebop-influenced** — this is a tritone substitution trainer. Bebop vocabulary (chromatic approach, enclosures) is the target skill. |
| Same lick transposed or different per key? | **Same lick transposed**. This is deliberate: learn one pattern, internalize it in all keys. Muscle memory transfer is the goal. |

**Current licks** (in C):
```
C7→F:  [48, 51, 53, 55, 56, 60, 61, 63, 69]  — chromatic bebop line resolving to A
Gb7→B: [42, 46, 49, 51, 53, 54, 58, 63]      — chromatic bebop line resolving to Eb
```

### Chord Voicing Preferences

| Question | Answer |
|----------|--------|
| Voicing type | **Shell voicings (root-3rd-7th)** only. No extensions. |
| Spacing | **Close position**, piano-style. Root in bass register, 3rd and 7th in middle register. |
| Why no extensions? | Extensions (9, 13) add harmonic color but obscure the core tritone resolution (3rd↔7th voice leading). Shell voicings keep focus on the pedagogical target. |

**Example** (C7 shell):
```
[48, 52, 58]  →  C3, E3, Bb3  (root, 3rd, 7th)
```

### Bass Style

| Question | Answer |
|----------|--------|
| Pattern | **Root-5-walk-up** — root on beat 1, fifth on beat 2, chromatic approach on beats 3-4. |
| Chromatic approach? | **Yes** — walk-up to the resolution chord's root. |

**Example** (C7→F bass):
```
[36, 43, 45, 46]  →  C2, G2, A2, Bb2 (walk-up to F)
```

---

## 3. Code + Output Preferences

### Output Format

| Question | Answer |
|----------|--------|
| One file or 12 files? | **Both modes supported** (already implemented): |
| | • `--all-keys` → 12 separate files (`tritone_practice_C.mid`, etc.) |
| | • Single file (default) → one key per invocation |
| | **Recommended default**: 12 separate files. Allows focused practice on one key. |

### Looping

| Question | Answer |
|----------|--------|
| Repeats per key | **Configurable via `--loops N`**. Default = 1. Recommended practice: 4 loops per key. |
| Loop scope | Each key loops **independently**. In `--all-keys` mode, each file contains `N` loops of that key only. |

### Swing

| Question | Answer |
|----------|--------|
| Default feel | **Straight 8ths** — keeps grid-locked timing for beginners. |
| Swing option | **Not yet implemented**. Add as future `--swing` flag. |
| Implementation hint | See `MIDI_GENERATOR_HANDOFF.md` Section 7 for swing implementation pattern. |

**Future CLI flag**:
```bash
python -m zt_band.midi_backing_generator --swing 0.67  # triplet swing
python -m zt_band.midi_backing_generator --swing 0.58  # light swing
```

### DAW Marker Style

| Question | Answer |
|----------|--------|
| Format | `"Loop {N}: {chord_name}"` — e.g., `"Loop 1: C7 → F"` |
| Key marker | In conductor track: `"Key: {note}"` when transposed |
| Disable option | `--no-markers` flag (already implemented) |

---

## 4. Extensibility / Future Goals

| Feature | Support? | Priority | Notes |
|---------|----------|----------|-------|
| Minor resolutions (E7→Am) | **Future** | Medium | Requires new phrase type with minor target chord |
| Modal licks (Dorian, Mixolydian) | **Future** | Low | Better suited for Dance Pack integration, not this module |
| User-defined licks from file | **Future** | Medium | JSON/YAML phrase definitions, loaded at runtime |
| Swing feel | **Future** | High | Next feature to add |
| Variable tempo per key | **No** | — | Over-engineering; use `--tempo` per invocation if needed |

---

## 5. Definitive Specification Summary

```yaml
# MIDI Generator v1 Specification
phrases:
  count: 2 (C7→F, Gb7→B)
  length: 1 bar each (4 beats)
  style: bebop chromatic
  transposition: automatic to all 12 keys

chords:
  voicing: shell (root-3rd-7th)
  spacing: close position
  extensions: none

bass:
  pattern: root-5-walk-up
  approach: chromatic

rhythm:
  feel: straight 8ths (swing = future)
  tempo: 120 BPM default (configurable)
  rest_between_phrases: half bar

output:
  format: SMF Type 1
  tracks: [conductor, guitar, bass, chords, drums]
  all_keys_mode: 12 separate files
  circle_of_fourths: [C, F, Bb, Eb, Ab, Db, Gb, B, E, A, D, G]

cli_flags:
  implemented:
    - --output, -o
    - --tempo
    - --loops
    - --transpose
    - --all-keys
    - --no-drums
    - --no-markers
  future:
    - --swing
    - --phrases-file
    - --minor
```

---

## 6. Non-Goals (Explicitly Out of Scope)

| Feature | Why Out of Scope |
|---------|------------------|
| Real-time MIDI playback | Use a DAW or external player |
| Audio rendering | MIDI only; use DAW for audio export |
| Interactive mode | CLI batch tool, not interactive |
| Fretboard-specific voicings | Generic MIDI; instrument-specific voicings are UI concern |
| Tempo automation | Static tempo; use DAW for tempo curves |

---

## 7. Quick Reference: What's Already Done

| Feature | Status | Location |
|---------|--------|----------|
| Timing bug fix | ✅ Done | `midi_backing_generator.py:196-207` |
| Transposition | ✅ Done | `Phrase.transpose()` |
| All-keys mode | ✅ Done | `generate_all_keys()` |
| Circle of fourths | ✅ Done | `CIRCLE_OF_FOURTHS` constant |
| DAW markers | ✅ Done | `build_guitar_track()` |
| Kick/snare drums | ✅ Done | `build_drum_track()` |
| Shell voicings | ✅ Done | `get_base_phrases()` |
| Walk-up bass | ✅ Done | `get_base_phrases()` |

---

## Changelog

| Date | Change |
|------|--------|
| 2025-01-25 | Initial spec answers document |
