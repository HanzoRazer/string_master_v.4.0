# MIDI Handoff: Chromatic Triplet Chain Exercises

> **Purpose**: Feed this into a sandbox session to generate MIDI files for the
> chromatic triplet chain exercises created 2026-01-27.
>
> **Requires**: `pip install mido` (MIDI library)
>
> **Output directory**: `exercises/chromatic_triplets/`

---

## Global MIDI Settings

```python
TICKS_PER_BEAT = 480
DEFAULT_CHANNEL = 0
DEFAULT_VELOCITY = 90
ACCENT_VELOCITY = 110  # chord tones on strong beats

# Triplet eighth note = 1/3 of a quarter note
TRIPLET_EIGHTH = TICKS_PER_BEAT // 3  # 160 ticks

# Each triplet group (3 notes) = 1 beat = 480 ticks
# 4 groups per bar = 12 triplet eighths per bar
```

---

## File 1: `chromatic_triplet_chain_dim7_C.mid`

**Tempo**: 72 BPM
**Time Signature**: 4/4
**Bars**: 4 (descending 2 bars + ascending 2 bars)
**Articulation**: Triplet eighth notes, accent first note of each group

### Bar 1–2: Descending Cdim7 chain

Each chord tone (A, Gb, Eb, C) starts a triplet group and descends
chromatically 2 half-steps to reach the next chord tone.

```
Bar 1:                           Bar 2:
Beat:  1       2       3    4    1       2       3    4
Group: [1    ] [2    ] [3    ]   [4    ] [rest          ]
Notes: A Ab G  Gb F E  Eb D Db  C  —    —  —    —  —
MIDI:  69 68 67 66 65 64 63 62 61 60
```

**Note sequence** (triplet eighths):
```python
descending = [
    # (midi_note, duration_ticks, velocity)
    (69, TRIPLET_EIGHTH, ACCENT_VELOCITY),   # A  - chord tone (accent)
    (68, TRIPLET_EIGHTH, DEFAULT_VELOCITY),   # Ab - passing
    (67, TRIPLET_EIGHTH, DEFAULT_VELOCITY),   # G  - passing
    (66, TRIPLET_EIGHTH, ACCENT_VELOCITY),   # Gb - chord tone (accent)
    (65, TRIPLET_EIGHTH, DEFAULT_VELOCITY),   # F  - passing
    (64, TRIPLET_EIGHTH, DEFAULT_VELOCITY),   # E  - passing
    (63, TRIPLET_EIGHTH, ACCENT_VELOCITY),   # Eb - chord tone (accent)
    (62, TRIPLET_EIGHTH, DEFAULT_VELOCITY),   # D  - passing
    (61, TRIPLET_EIGHTH, DEFAULT_VELOCITY),   # Db - passing
    (60, TICKS_PER_BEAT * 3, ACCENT_VELOCITY), # C - chord tone (held, resolve)
]
# Total: 9 triplet eighths (3 beats) + dotted half (3 beats) = 6 beats
# Pad remaining 2 beats with rest to fill 2 bars
```

### Bar 3–4: Ascending Cdim7 chain

```
Bar 3:                           Bar 4:
Beat:  1       2       3    4    1       2       3    4
Group: [1    ] [2    ] [3    ]   [4    ] [rest          ]
Notes: C Db D  Eb E F  Gb G Ab  A  —    —  —    —  —
MIDI:  60 61 62 63 64 65 66 67 68 69
```

**Note sequence**:
```python
ascending = [
    (60, TRIPLET_EIGHTH, ACCENT_VELOCITY),   # C  - chord tone
    (61, TRIPLET_EIGHTH, DEFAULT_VELOCITY),   # Db - passing
    (62, TRIPLET_EIGHTH, DEFAULT_VELOCITY),   # D  - passing
    (63, TRIPLET_EIGHTH, ACCENT_VELOCITY),   # Eb - chord tone
    (64, TRIPLET_EIGHTH, DEFAULT_VELOCITY),   # E  - passing
    (65, TRIPLET_EIGHTH, DEFAULT_VELOCITY),   # F  - passing
    (66, TRIPLET_EIGHTH, ACCENT_VELOCITY),   # Gb - chord tone
    (67, TRIPLET_EIGHTH, DEFAULT_VELOCITY),   # G  - passing
    (68, TRIPLET_EIGHTH, DEFAULT_VELOCITY),   # Ab - passing
    (69, TICKS_PER_BEAT * 3, ACCENT_VELOCITY), # A - chord tone (held)
]
```

**Full file = descending (2 bars) + ascending (2 bars) = 4 bars**

---

## File 2: `chromatic_triplet_chain_maj6_C.mid`

**Tempo**: 76 BPM
**Time Signature**: 4/4
**Bars**: 4 (descending 2 bars + ascending 2 bars)
**Scale**: C6 diminished = C - D - E - F - G - Ab - A - B

### Bar 1–2: Descending C6 diminished scale in triplet groups

```
Bar 1:                           Bar 2:
Beat:  1       2       3    4    1       2       3    4
Group: [1    ] [2    ] [3    ]   [hold C               ]
Notes: C  B  A Ab G  F  E  D  C
MIDI:  72 71 69 68 67 65 64 62 60
```

Note: Uses octave 4–5 range. Starts on C5 (72), ends on C4 (60).

**Note sequence**:
```python
# CT = chord tone (C, E, G, A), PT = diminished passing tone (B, D, F, Ab)
desc_maj6 = [
    (72, TRIPLET_EIGHTH, ACCENT_VELOCITY),   # C5 - root (CT)
    (71, TRIPLET_EIGHTH, DEFAULT_VELOCITY),   # B4 - passing (PT)
    (69, TRIPLET_EIGHTH, DEFAULT_VELOCITY),   # A4 - 6th (CT)
    (68, TRIPLET_EIGHTH, ACCENT_VELOCITY),   # Ab4 - passing (PT)
    (67, TRIPLET_EIGHTH, DEFAULT_VELOCITY),   # G4 - 5th (CT)
    (65, TRIPLET_EIGHTH, DEFAULT_VELOCITY),   # F4 - passing (PT)
    (64, TRIPLET_EIGHTH, ACCENT_VELOCITY),   # E4 - 3rd (CT)
    (62, TRIPLET_EIGHTH, DEFAULT_VELOCITY),   # D4 - passing (PT)
    (60, TICKS_PER_BEAT * 4, ACCENT_VELOCITY), # C4 - root (CT, whole note)
]
```

**IMPORTANT**: The scale skips semitones — this is NOT a chromatic scale.
Intervals: C→B (1), B→A (2), A→Ab (1), Ab→G (1), G→F (2), F→E (1), E→D (2), D→C (2).
These are the 6th diminished scale steps, not chromatic half-steps.

### Bar 3–4: Ascending C6 diminished scale in triplet groups

```
Bar 3:                           Bar 4:
Beat:  1       2       3    4    1       2       3    4
Group: [1    ] [2    ] [3    ]   [hold C5              ]
Notes: C  D  E  F  G  Ab A  B  C
MIDI:  60 62 64 65 67 68 69 71 72
```

**Note sequence**:
```python
asc_maj6 = [
    (60, TRIPLET_EIGHTH, ACCENT_VELOCITY),   # C4 - root (CT)
    (62, TRIPLET_EIGHTH, DEFAULT_VELOCITY),   # D4 - passing (PT)
    (64, TRIPLET_EIGHTH, DEFAULT_VELOCITY),   # E4 - 3rd (CT)
    (65, TRIPLET_EIGHTH, ACCENT_VELOCITY),   # F4 - passing (PT)
    (67, TRIPLET_EIGHTH, DEFAULT_VELOCITY),   # G4 - 5th (CT)
    (68, TRIPLET_EIGHTH, DEFAULT_VELOCITY),   # Ab4 - passing (PT)
    (69, TRIPLET_EIGHTH, ACCENT_VELOCITY),   # A4 - 6th (CT)
    (71, TRIPLET_EIGHTH, DEFAULT_VELOCITY),   # B4 - passing (PT)
    (72, TICKS_PER_BEAT * 4, ACCENT_VELOCITY), # C5 - root (CT, whole note)
]
```

---

## File 3: `chromatic_triplet_chain_ii_V_I_C.mid`

**Tempo**: 80 BPM
**Time Signature**: 4/4
**Bars**: 4 (one chord per bar)
**Progression**: Dm7 – G7 – Cmaj7 – Cmaj7

### Voice-leading logic
- Dm7 chain: start on C (b7), descend chromatically → land on B (3rd of G7)
- G7 chain: start on F (b7), descend chromatically → land on E (3rd of Cmaj7)
- Cmaj7 chain: start on B (7th), descend through full chain → land on C (root)

### Bar 1: Dm7 — descending chromatic chain

```
Beat:  1       2       3       4
Group: [1    ] [2    ] [hold B        ]
Notes: C  B  Bb A  Ab G  ... → B (hold into next bar)
MIDI:  72 71 70 69 68 67         71
```

```python
bar1_dm7 = [
    (72, TRIPLET_EIGHTH, ACCENT_VELOCITY),   # C5 - b7 of Dm7
    (71, TRIPLET_EIGHTH, DEFAULT_VELOCITY),   # B4 - chromatic
    (70, TRIPLET_EIGHTH, DEFAULT_VELOCITY),   # Bb4 - chromatic
    (69, TRIPLET_EIGHTH, ACCENT_VELOCITY),   # A4 - 5th of Dm7
    (68, TRIPLET_EIGHTH, DEFAULT_VELOCITY),   # Ab4 - chromatic
    (67, TRIPLET_EIGHTH, DEFAULT_VELOCITY),   # G4 - chromatic
    # Beat 3-4: resolution setup
    (66, TRIPLET_EIGHTH, DEFAULT_VELOCITY),   # F#4 - leading tone to G
    (65, TRIPLET_EIGHTH, DEFAULT_VELOCITY),   # F4 - 3rd of Dm7
    (64, TRIPLET_EIGHTH, DEFAULT_VELOCITY),   # E4 - chromatic
    # Final triplet group lands on target
    (63, TRIPLET_EIGHTH, DEFAULT_VELOCITY),   # Eb4 - chromatic
    (62, TRIPLET_EIGHTH, DEFAULT_VELOCITY),   # D4 - root of Dm7
    (71, TRIPLET_EIGHTH, ACCENT_VELOCITY),   # B4 - TARGET: 3rd of G7 (leap up)
]
# 12 triplet eighths = 4 beats = 1 bar
```

**Alternative (simpler, recommended for v1)**:
```python
# 6 triplet eighths (2 beats) + quarter note target + rest
bar1_dm7_simple = [
    (72, TRIPLET_EIGHTH, ACCENT_VELOCITY),   # C5 - b7 of Dm7
    (71, TRIPLET_EIGHTH, DEFAULT_VELOCITY),   # B4
    (70, TRIPLET_EIGHTH, DEFAULT_VELOCITY),   # Bb4
    (69, TRIPLET_EIGHTH, ACCENT_VELOCITY),   # A4 - 5th of Dm7
    (68, TRIPLET_EIGHTH, DEFAULT_VELOCITY),   # Ab4
    (67, TRIPLET_EIGHTH, DEFAULT_VELOCITY),   # G4
    # Beats 3-4: target + rest
    (71, TICKS_PER_BEAT, ACCENT_VELOCITY),   # B4 - TARGET: 3rd of G7
    # rest for 1 beat (no note_on)
]
```

### Bar 2: G7 — descending chromatic chain

```python
bar2_g7 = [
    (65, TRIPLET_EIGHTH, ACCENT_VELOCITY),   # F4 - b7 of G7
    (64, TRIPLET_EIGHTH, DEFAULT_VELOCITY),   # E4
    (63, TRIPLET_EIGHTH, DEFAULT_VELOCITY),   # Eb4
    (62, TRIPLET_EIGHTH, ACCENT_VELOCITY),   # D4 - 5th of G7
    (61, TRIPLET_EIGHTH, DEFAULT_VELOCITY),   # Db4
    (60, TRIPLET_EIGHTH, DEFAULT_VELOCITY),   # C4
    # Beats 3-4: target + rest
    (64, TICKS_PER_BEAT, ACCENT_VELOCITY),   # E4 - TARGET: 3rd of Cmaj7
    # rest for 1 beat
]
```

### Bar 3: Cmaj7 — full descending chain

```python
bar3_cmaj7 = [
    (71, TRIPLET_EIGHTH, ACCENT_VELOCITY),   # B4 - 7th of Cmaj7
    (70, TRIPLET_EIGHTH, DEFAULT_VELOCITY),   # Bb4
    (69, TRIPLET_EIGHTH, DEFAULT_VELOCITY),   # A4
    (68, TRIPLET_EIGHTH, ACCENT_VELOCITY),   # Ab4
    (67, TRIPLET_EIGHTH, DEFAULT_VELOCITY),   # G4 - 5th of Cmaj7
    (65, TRIPLET_EIGHTH, DEFAULT_VELOCITY),   # F4
    (64, TRIPLET_EIGHTH, ACCENT_VELOCITY),   # E4 - 3rd of Cmaj7
    (62, TRIPLET_EIGHTH, DEFAULT_VELOCITY),   # D4
    (60, TICKS_PER_BEAT, ACCENT_VELOCITY),   # C4 - ROOT (resolve)
    # rest remaining
]
```

### Bar 4: Cmaj7 — resolution hold

```python
bar4_resolve = [
    (60, TICKS_PER_BEAT * 4, ACCENT_VELOCITY),  # C4 whole note — home
]
```

---

## Complete Generation Script

```python
"""
Generate MIDI files for Barry Harris chromatic triplet chain exercises.
Run in a sandbox with: pip install mido
Output: 3 .mid files in exercises/chromatic_triplets/
"""
import mido
from mido import MidiFile, MidiTrack, Message, MetaMessage

TICKS = 480
TRIP = TICKS // 3  # 160 ticks = triplet eighth
VEL = 90
ACC = 110


def note(pitch, dur, vel=VEL):
    """Return (pitch, duration_ticks, velocity) tuple."""
    return (pitch, dur, vel)


def write_track(track, notes, channel=0):
    """Write a sequence of (pitch, dur, vel) to a MIDI track."""
    for pitch, dur, vel in notes:
        if pitch is None:
            # Rest: just advance time
            track.append(Message('note_on', note=60, velocity=0, time=dur, channel=channel))
        else:
            track.append(Message('note_on', note=pitch, velocity=vel, time=0, channel=channel))
            track.append(Message('note_off', note=pitch, velocity=0, time=dur, channel=channel))


def make_midi(filename, tempo_bpm, notes_list):
    """Create a single-track MIDI file."""
    mid = MidiFile(ticks_per_beat=TICKS)
    track = MidiTrack()
    mid.tracks.append(track)

    track.append(MetaMessage('set_tempo', tempo=mido.bpm2tempo(tempo_bpm)))
    track.append(MetaMessage('time_signature', numerator=4, denominator=4))

    write_track(track, notes_list)

    track.append(MetaMessage('end_of_track', time=0))
    mid.save(filename)
    print(f"Wrote {filename}")


# ── File 1: dim7_C ──────────────────────────────────────────────
desc_dim = [
    note(69, TRIP, ACC),  # A  (CT)
    note(68, TRIP),        # Ab
    note(67, TRIP),        # G
    note(66, TRIP, ACC),  # Gb (CT)
    note(65, TRIP),        # F
    note(64, TRIP),        # E
    note(63, TRIP, ACC),  # Eb (CT)
    note(62, TRIP),        # D
    note(61, TRIP),        # Db
    note(60, TICKS * 3, ACC),  # C (CT, held dotted half)
    (None, TICKS),         # 1 beat rest
]

asc_dim = [
    note(60, TRIP, ACC),  # C  (CT)
    note(61, TRIP),        # Db
    note(62, TRIP),        # D
    note(63, TRIP, ACC),  # Eb (CT)
    note(64, TRIP),        # E
    note(65, TRIP),        # F
    note(66, TRIP, ACC),  # Gb (CT)
    note(67, TRIP),        # G
    note(68, TRIP),        # Ab
    note(69, TICKS * 3, ACC),  # A (CT, held dotted half)
    (None, TICKS),         # 1 beat rest
]

make_midi(
    "exercises/chromatic_triplets/chromatic_triplet_chain_dim7_C.mid",
    72,
    desc_dim + asc_dim
)


# ── File 2: maj6_C ─────────────────────────────────────────────
# C6 diminished scale: C-D-E-F-G-Ab-A-B (NOT chromatic -- uses scale steps)
desc_maj6 = [
    note(72, TRIP, ACC),  # C5 (CT)
    note(71, TRIP),        # B4 (PT)
    note(69, TRIP),        # A4 (CT)  -- skip Ab here, scale step
    note(68, TRIP, ACC),  # Ab4 (PT)
    note(67, TRIP),        # G4 (CT)
    note(65, TRIP),        # F4 (PT)  -- skip to F, scale step
    note(64, TRIP, ACC),  # E4 (CT)
    note(62, TRIP),        # D4 (PT)
    note(60, TICKS * 4, ACC),  # C4 (CT, whole note)
]

asc_maj6 = [
    note(60, TRIP, ACC),  # C4 (CT)
    note(62, TRIP),        # D4 (PT)
    note(64, TRIP),        # E4 (CT)
    note(65, TRIP, ACC),  # F4 (PT)
    note(67, TRIP),        # G4 (CT)
    note(68, TRIP),        # Ab4 (PT)
    note(69, TRIP, ACC),  # A4 (CT)
    note(71, TRIP),        # B4 (PT)
    note(72, TICKS * 4, ACC),  # C5 (CT, whole note)
]

make_midi(
    "exercises/chromatic_triplets/chromatic_triplet_chain_maj6_C.mid",
    76,
    desc_maj6 + asc_maj6
)


# ── File 3: ii_V_I_C ───────────────────────────────────────────
# Bar 1: Dm7 chain → B (3rd of G7)
bar1 = [
    note(72, TRIP, ACC),  # C5 - b7 of Dm7
    note(71, TRIP),        # B4
    note(70, TRIP),        # Bb4
    note(69, TRIP, ACC),  # A4 - 5th of Dm7
    note(68, TRIP),        # Ab4
    note(67, TRIP),        # G4
    note(71, TICKS, ACC), # B4 - TARGET: 3rd of G7
    (None, TICKS),         # rest
]

# Bar 2: G7 chain → E (3rd of Cmaj7)
bar2 = [
    note(65, TRIP, ACC),  # F4 - b7 of G7
    note(64, TRIP),        # E4
    note(63, TRIP),        # Eb4
    note(62, TRIP, ACC),  # D4 - 5th of G7
    note(61, TRIP),        # Db4
    note(60, TRIP),        # C4
    note(64, TICKS, ACC), # E4 - TARGET: 3rd of Cmaj7
    (None, TICKS),         # rest
]

# Bar 3: Cmaj7 full descent
bar3 = [
    note(71, TRIP, ACC),  # B4 - 7th
    note(70, TRIP),        # Bb4
    note(69, TRIP),        # A4
    note(68, TRIP, ACC),  # Ab4
    note(67, TRIP),        # G4 - 5th
    note(65, TRIP),        # F4
    note(64, TRIP, ACC),  # E4 - 3rd
    note(62, TRIP),        # D4
    note(60, TICKS, ACC), # C4 - ROOT
    (None, TRIP),          # rest (fill bar)
]

# Bar 4: Resolve
bar4 = [
    note(60, TICKS * 4, ACC),  # C4 whole note -- home
]

make_midi(
    "exercises/chromatic_triplets/chromatic_triplet_chain_ii_V_I_C.mid",
    80,
    bar1 + bar2 + bar3 + bar4
)

print("\nDone. 3 MIDI files written to exercises/chromatic_triplets/")
```

---

## Verification Checklist

After running the script, verify:

- [ ] `chromatic_triplet_chain_dim7_C.mid` — 4 bars, 72 BPM
  - Descending: A-Ab-G | Gb-F-E | Eb-D-Db | C (hold)
  - Ascending: C-Db-D | Eb-E-F | Gb-G-Ab | A (hold)
  - All intervals are half-steps (chromatic)

- [ ] `chromatic_triplet_chain_maj6_C.mid` — 4 bars, 76 BPM
  - Descending: C-B-A | Ab-G-F | E-D-C (hold)
  - Ascending: C-D-E | F-G-Ab | A-B-C (hold)
  - **NOT chromatic** — uses 6th diminished scale intervals (mix of whole and half steps)

- [ ] `chromatic_triplet_chain_ii_V_I_C.mid` — 4 bars, 80 BPM
  - Bar 1 (Dm7): C-B-Bb | A-Ab-G → B (target)
  - Bar 2 (G7): F-E-Eb | D-Db-C → E (target)
  - Bar 3 (Cmaj7): B-Bb-A | Ab-G-F | E-D-C
  - Bar 4: C whole note (home)
  - Target notes (B and E) should be accented

---

## Context for the Sandbox

These exercises live in `exercises/chromatic_triplets/` alongside their
`.ztex` and `.ztprog` files (already committed). The `.ztex` files reference
these MIDI files but they don't exist yet.

The exercises are part of the Barry Harris chromatic triplet chain series:
1. **dim7_C** — pure diminished (all minor 3rds, perfect triplet alignment)
2. **maj6_C** — 6th diminished scale (C6 + interleaved dim passing tones)
3. **ii_V_I_C** — applied over Dm7-G7-Cmaj7 with voice-leading targets

Related existing exercises (already committed):
- `exercises/enclosures/barry_harris_enclosure_examples.ztex`
- `exercises/got_rhythm/got_rhythm_bb7_eb7_study1.ztex` (chromatic_triplet technique)
- `exercises/got_rhythm/got_rhythm_enclosure_study2.ztex` (triplet_enclosure technique)
- `exercises/barry_harris_maj7/` (7th scale, 8th-note version)
- `exercises/barry_harris_dom7/` (dom7 bebop scale)

After generating, commit:
```bash
git add exercises/chromatic_triplets/*.mid
git commit -m "feat: add MIDI files for chromatic triplet chain exercises"
git push
```
