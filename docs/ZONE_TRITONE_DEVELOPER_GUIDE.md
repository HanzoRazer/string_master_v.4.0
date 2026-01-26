# Zone-Tritone Circle Theory: Developer Presentation

## Overview

The `string_master_v.4.0` codebase implements a music theory framework called **Zone-Tritone Theory** - a systematic approach to understanding harmony through two core concepts:

1. **Two Whole-Tone Zones** - The 12 chromatic notes split into two alternating groups
2. **Tritone Anchors** - The 6 tritone pairs that drive harmonic resolution

---

## Core Theory Module: `src/shared/zone_tritone/`

### File Structure

```
src/shared/zone_tritone/
├── types.py        # Type aliases (PitchClass, TritoneAxis)
├── pc.py           # Pitch-class ↔ name conversion
├── zones.py        # Zone membership + interval functions
├── tritones.py     # Tritone axis calculations
└── gravity.py      # Circle of fifths / dominant chains
```

---

### 1. Pitch Class (`pc.py:28-53`)

```python
# Maps note names to pitch classes (0-11)
_name_to_pc = {
    "C": 0, "B#": 0,
    "C#": 1, "Db": 1,
    "D": 2,
    # ... (all enharmonics)
}

def pc_from_name(name: str) -> PitchClass:
    """Convert 'C', 'Db', 'F#' → 0-11"""
    return _name_to_pc[name.strip()]

def name_from_pc(pc: PitchClass) -> str:
    """Convert 0-11 → canonical name"""
    return NOTES[pc % 12]
```

---

### 2. The Two Zones (`zones.py:6-28`)

**The Core Insight:** Every chromatic note belongs to exactly one of two zones based on parity (odd/even).

```python
def zone(pc: PitchClass) -> int:
    """
    Zone 1 (even pc): {C, D, E, F#, G#, A#} = {0,2,4,6,8,10}
    Zone 2 (odd pc):  {C#, D#, F, G, A, B}  = {1,3,5,7,9,11}
    """
    return pc % 2  # Simple: even=Zone1, odd=Zone2

def is_zone_cross(a: PitchClass, b: PitchClass) -> bool:
    """Half-steps ALWAYS cross zones. Whole-steps stay in zone."""
    return zone(a) != zone(b)

def is_half_step(a: PitchClass, b: PitchClass) -> bool:
    d = (b - a) % 12
    return d in (1, 11)  # semitone up or down
```

**Musical Meaning:**
- **Half-step motion = zone-crossing = harmonic tension/direction**
- **Whole-step motion = zone-stable = color without gravity**

---

### 3. Tritone System (`tritones.py:7-45`)

**The Six Tritones** anchor dominant harmony:

```python
def tritone_partner(pc: PitchClass) -> PitchClass:
    """The note 6 semitones away"""
    return (pc + 6) % 12

def all_tritone_axes() -> list[TritoneAxis]:
    """Returns the 6 unique tritone pairs:
    [(0,6), (1,7), (2,8), (3,9), (4,10), (5,11)]
      C-F#  C#-G  D-G#  D#-A   E-A#   F-B
    """
```

**Key Property:** Both notes in a tritone pair are **always in the same zone** (both even or both odd). This is why tritone resolution creates zone-crossing.

---

### 4. Gravity / Circle of Fifths (`gravity.py:33-71`)

```python
def gravity_chain(root: PitchClass, steps: int) -> list[PitchClass]:
    """
    Generate dominant cycle by descending 5ths:
    G(7) → C(0) → F(5) → Bb(10) → Eb(3) → ...
    """
    r = root % 12
    chain = [r]
    for _ in range(steps):
        r = (r - 7) % 12  # Down perfect 5th (7 semitones)
        chain.append(r)
    return chain

def dominant_roots_from_tritone(axis: TritoneAxis) -> list[PitchClass]:
    """
    Given a tritone (e.g., B-F), find which dominant chords use it.
    B-F is the 3rd & 7th of both G7 AND Db7 (tritone substitution!)
    """
```

**Circle of Fourths Constant:**
```python
CIRCLE_OF_FOURTHS = [0, 5, 10, 3, 8, 1, 6, 11, 4, 9, 2, 7]
# C → F → Bb → Eb → Ab → Db → Gb → B → E → A → D → G
```

---

## Exercise Generators: `src/zt_band/`

### Barry Harris Generators

Two generators implement Barry Harris pedagogy:

| File | Scale | Notes | Key Rule |
|------|-------|-------|----------|
| `barry_harris_maj7_generator.py` | Major 7th | 7 notes | "7 resolves to 1 by half-step" |
| `barry_harris_dom7_generator.py` | Dominant Bebop | 8 notes | "Chord tones on downbeats" |

---

### Dom7 Bebop Scale (`barry_harris_dom7_generator.py:52-55`)

```python
# The 8-note "6th diminished" scale
# 1-2-3-4-5-b6-6-b7 (b6 is the chromatic passing tone)
DOM7_BEBOP_SCALE_INTERVALS = [0, 2, 4, 5, 7, 8, 9, 10]
```

**Why 8 notes?** In continuous 8th notes, chord tones (1-3-5-b7) land on **downbeats** automatically:

```
Beat:  1   &   2   &   3   &   4   &
Note:  1   2   3   4   5  b6   6  b7
       ↑       ↑       ↑           ↑
      CT      CT      CT          CT  (chord tones)
```

---

### Exercise Patterns (`barry_harris_dom7_generator.py:107-263`)

```python
def pattern_bebop_ascending(exercise, octaves=2):
    """Scale up - chord tones land on downbeats"""

def pattern_enclosure(exercise):
    """Surround each chord tone: above-below-target
    Enclosure to 1: 2-b7-1
    Enclosure to 3: 4-2-3
    """

def pattern_guide_tone_line(exercise):
    """Target the guide tones (3rd and b7)"""

def pattern_chromatic_approach(exercise):
    """Approach chord tones by half-step from below"""
```

---

### Enclosure Generator (`enclosure_generator.py:59-149`)

```python
ENCLOSURE_EXAMPLES = [
    EnclosureExample(
        id="enclosure_major_C6_target_3",
        degrees=["4", "#3", "2", "#2", "3"],  # F-E#-D-D#-E
        chord="C6",
        description="Enclosure to 3rd from above (4) and below (#2)",
        target_degree="3"
    ),

    # Double enclosure (Barry Harris classic)
    EnclosureExample(
        id="enclosure_double_to_1",
        degrees=["2", "b2", "7", "1"],  # D-Db-B-C
        chord="Cmaj7",
        description="Double enclosure: above, below, below, target",
    ),
]
```

---

## Theory Diagrams (`THEORY_DIAGRAMS.md`)

10 standard diagrams for teaching:

| # | Diagram | Concept |
|---|---------|---------|
| 1 | Two Whole-Tone Zones | Zone 1 (even) vs Zone 2 (odd) |
| 2 | Tritone Anchors | The 6 unique tritone pairs |
| 3 | Zone-Crossing | Half-steps cross zones |
| 4 | Dominant Resolution | G7 → C (B-F tritone resolves) |
| 5 | Tritone Substitution | G7 and Db7 share B-F tritone |
| 6 | Descending Dominant Cycle | Tritones shift, roots descend in 4ths |
| 9 | Gravity Map (ii-V-I) | Zone-crossing at resolution |
| 10 | The Zone Circle | Chromatic circle with zone alternation |

---

## The Zone Circle (Diagram 10)

```
           C [Z1]
        /         \
 A# [Z1]           C# [Z2]
   |                 |
 A [Z2]             D [Z1]
   |                 |
 G# [Z1]           D# [Z2]
   |                 |
 G [Z2]             E [Z1]
    \              /
       F [Z2] – F# [Z1]
         \     /
            B [Z2]

Zones alternate around the circle.
Each half-step = zone-crossing.
```

---

## Key Takeaways for Developers

### 1. The Math is Simple
```python
zone(pc) = pc % 2           # Zone membership
tritone_partner(pc) = (pc + 6) % 12  # Tritone
gravity_step = (root - 7) % 12       # Circle of 5ths
```

### 2. Musical Rules Map to Code
| Musical Rule | Code Implementation |
|--------------|---------------------|
| "Half-steps create direction" | `is_zone_cross(a, b)` |
| "Dominant resolves by tritone" | `dominant_roots_from_tritone()` |
| "Chord tones on downbeats" | 8-note scale ensures this |
| "Approach from above and below" | `pattern_enclosure()` |

### 3. MIDI Generation Pipeline
```
Theory Rules → Exercise Pattern → MIDI Notes → .mid File
                   ↓
           pattern_bebop_ascending()
                   ↓
           build_melody_track()
                   ↓
           MidiFile.save()
```

---

## Running the Generators

```bash
# Generate Maj7 exercise in C
python -m zt_band.barry_harris_maj7_generator --key C

# Generate Dom7 bebop in all 12 keys
python -m zt_band.barry_harris_dom7_generator --all-keys --pattern enclosure

# Generate enclosure examples
python -m zt_band.enclosure_generator
```

---

This framework provides a mathematically rigorous foundation for jazz pedagogy - turning abstract harmony concepts into executable code that generates practice materials.

---

*Generated: 2026-01-26*
