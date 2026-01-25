# MIDI Backing Generator - Engineering Handoff

> **Purpose**: Technical reference for maintaining and extending the MIDI backing track generator. Documents the timing bugs found in prior implementations and the correct patterns to follow.

---

## Quick Reference

| What | Where |
|------|-------|
| Module | `src/zt_band/midi_backing_generator.py` |
| Entry point | `python -m zt_band.midi_backing_generator` |
| Dependency | `mido` (MIDI library) |
| Output | Standard MIDI File (SMF) Type 1 |

---

## 1. The Timing Bug (Critical)

### What Was Wrong

Two prior implementations had the same critical bug: **all notes stacked at time=0**.

```python
# BROKEN CODE (from prior uploads)
for pitch in phrase.lick_notes:
    track.append(Message('note_on', note=pitch, velocity=80, time=0))   # ← Always 0!
    track.append(Message('note_off', note=pitch, velocity=0, time=240)) # ← Duration only
```

**Result**: Every note starts at tick 0. The `time` parameter on `note_off` only determines how long *that specific note* rings—it doesn't advance the timeline for the *next* note.

### Why It's Wrong

In MIDI, `time` is a **delta** (offset from previous event), not an absolute timestamp:

```
Event 1: note_on  C4, time=0    → starts at tick 0
Event 2: note_off C4, time=240  → ends at tick 240
Event 3: note_on  E4, time=0    → starts at tick 240 (0 after event 2)
Event 4: note_off E4, time=240  → ends at tick 480
```

If Event 3 has `time=0`, it fires immediately after Event 2—which is correct. But the broken code set `time=0` on ALL `note_on` events, including the very first one in each phrase, causing notes to overlap.

### The Fix

Track whether we're emitting the first note, and use proper delta times:

```python
# CORRECT CODE
first_note = True
for pitch in phrase.lick_notes:
    if first_note:
        delta = 0  # First note starts immediately
        first_note = False
    else:
        delta = 0  # Subsequent notes start right after previous note_off

    track.append(Message('note_on', note=pitch, velocity=80, time=delta))
    track.append(Message('note_off', note=pitch, velocity=0, time=note_duration))
```

The key insight: `note_off` with `time=note_duration` advances the clock. The next `note_on` with `time=0` fires at that new position.

### Chord Timing (Multiple Simultaneous Notes)

For chords, all notes must start together and end together:

```python
# All notes ON (delta=0 for all after first)
for j, pitch in enumerate(chord_pitches):
    delta = chord_duration if j == 0 else 0  # Only first note has gap from previous chord
    track.append(Message('note_on', note=pitch, velocity=60, time=delta))

# All notes OFF (first note_off has duration, rest are delta=0)
for j, pitch in enumerate(chord_pitches):
    delta = chord_duration if j == 0 else 0
    track.append(Message('note_off', note=pitch, velocity=0, time=delta))
```

---

## 2. Transposition Architecture

### Phrase Dataclass

```python
@dataclass
class Phrase:
    name: str                           # "C7 → F" (display name)
    root_note: int                      # MIDI note of root (for reference)
    lick_notes: List[int]               # Melody pitches
    bass_notes: List[int]               # Bass line pitches
    chord_voicings: List[List[int]]     # List of chords (each chord = list of pitches)
    resolution_note: int                # Target note of phrase

    def transpose(self, semitones: int) -> "Phrase":
        """Return new Phrase shifted by N semitones."""
        return Phrase(
            name=self._transpose_name(semitones),
            root_note=self.root_note + semitones,
            lick_notes=[n + semitones for n in self.lick_notes],
            bass_notes=[n + semitones for n in self.bass_notes],
            chord_voicings=[[n + semitones for n in chord] for chord in self.chord_voicings],
            resolution_note=self.resolution_note + semitones,
        )
```

### Name Transposition

The `_transpose_name()` method parses chord names like `"C7 → F"` and shifts them:

```python
def _transpose_name(self, semitones: int) -> str:
    NOTE_NAMES = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']

    if "→" in self.name:
        # Parse "C7 → F" into root="C", target="F"
        parts = self.name.split("→")
        root_name = parts[0].strip().replace("7", "")
        target_name = parts[1].strip()

        root_idx = NOTE_NAMES.index(root_name)
        target_idx = NOTE_NAMES.index(target_name)

        new_root = NOTE_NAMES[(root_idx + semitones) % 12]
        new_target = NOTE_NAMES[(target_idx + semitones) % 12]

        return f"{new_root}7 → {new_target}"
    return self.name
```

### Circle of Fourths

For `--all-keys` mode, we generate in circle-of-fourths order (standard jazz practice progression):

```python
CIRCLE_OF_FOURTHS = [0, 5, 10, 3, 8, 1, 6, 11, 4, 9, 2, 7]
# Maps to:          C  F  Bb  Eb Ab Db Gb  B  E  A  D  G
```

Each key is a transposition offset in semitones from C.

---

## 3. Track Architecture

### Multi-Track Layout (SMF Type 1)

| Track | Channel | Content | GM Patch |
|-------|---------|---------|----------|
| 0 | — | Conductor (tempo, markers) | — |
| 1 | 0 | Guitar licks | 24 (Nylon Guitar) |
| 2 | 1 | Bass line | 33 (Acoustic Bass) |
| 3 | 2 | Chord voicings | 1 (Acoustic Piano) |
| 4 | 9 | Drums | — (GM drum channel) |

### Tempo Conversion

```python
MICROSECONDS_PER_MINUTE = 60_000_000

def tempo_to_microseconds(bpm: int) -> int:
    return MICROSECONDS_PER_MINUTE // bpm

# Usage in conductor track:
conductor.append(MetaMessage('set_tempo', tempo=tempo_to_microseconds(120), time=0))
```

### DAW Markers

Markers help with navigation in DAWs like Ableton, Logic, Reaper:

```python
track.append(MetaMessage('marker', text=f"Loop {loop_num + 1}: {phrase.name}", time=0))
```

---

## 4. CLI Flags

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--output`, `-o` | str | `jazz_tritone_practice.mid` | Output file path |
| `--tempo` | int | 120 | BPM |
| `--loops` | int | 1 | Repeat count |
| `--transpose` | int | 0 | Semitones (0-11) |
| `--all-keys` | flag | — | Generate 12 files |
| `--no-drums` | flag | — | Exclude drum track |
| `--no-markers` | flag | — | Exclude DAW markers |

### All-Keys Output

When `--all-keys` is set, generates 12 files:
```
tritone_practice_C.mid
tritone_practice_F.mid
tritone_practice_Bb.mid
tritone_practice_Eb.mid
... (circle of fourths order)
```

---

## 5. Testing Checklist

### Timing Verification

1. **Open in DAW**: Notes should be sequential, not stacked
2. **Visual check**: Piano roll shows staircase pattern, not vertical lines
3. **Playback**: Each note audible separately (no chord blob)

### Transposition Verification

1. **Check pitch**: `--transpose 5` should shift all notes up a fourth
2. **Check names**: Markers should show transposed chord names
3. **All-keys**: 12 files, each in different key

### Drum Pattern Verification

1. **Hi-hat**: Every beat
2. **Kick**: Beats 1 and 3
3. **Snare**: Beats 2 and 4

---

## 6. Common Mistakes to Avoid

| Mistake | Symptom | Fix |
|---------|---------|-----|
| `time=0` on all note_on | Notes stack vertically | Track first note, use delta times |
| Forgetting `% 12` in transposition | Note names overflow | Always mod 12 for note names |
| Wrong channel for drums | Drums play as pitched notes | Use channel 9 (GM standard) |
| Hardcoded ticks | Tempo changes break timing | Use `TICKS_PER_BEAT` constant |
| Missing program_change | Wrong instrument sounds | Add at start of each track |

---

## 7. Extension Points

### Adding New Phrases

1. Define in `get_base_phrases()`:
```python
Phrase(
    name="G7 → C",
    root_note=43,  # G2
    lick_notes=[...],
    bass_notes=[...],
    chord_voicings=[[...], [...], [...], [...]],
    resolution_note=60,  # C4
)
```

2. Transposition happens automatically via `Phrase.transpose()`

### Adding New Instruments

1. Add channel constant: `CH_STRINGS = 3`
2. Add GM patch: `PATCH_STRINGS = 48`
3. Create builder: `build_strings_track(phrases, loops)`
4. Wire into `generate_practice_midi()`

### Adding Swing

Modify note durations for swing feel:
```python
SWING_RATIO = 0.67  # Triplet swing

def swing_8ths(beat_position: int) -> int:
    """Return duration for swung 8th note."""
    if beat_position % 2 == 0:  # Downbeat
        return int(TICKS_PER_BEAT * SWING_RATIO)
    else:  # Upbeat
        return int(TICKS_PER_BEAT * (1 - SWING_RATIO))
```

---

## Changelog

| Date | Change |
|------|--------|
| 2025-01-25 | Add transposition, all-keys mode, DAW markers, kick/snare pattern |
| 2025-01-25 | Fix timing bug (notes stacking at time=0) |
| 2025-01-25 | Initial module creation |
