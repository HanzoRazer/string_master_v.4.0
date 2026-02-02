# Arranger Feature Gap Analysis

**Date:** 2025-01-28
**Status:** Planning
**Purpose:** Compare Smart Guitar accompaniment engine against industry-standard digital arranger keyboards to identify feature gaps and prioritize development.

---

## Executive Summary

Smart Guitar's accompaniment engine differentiates through **teaching intelligence** (coaching AI, adaptive difficulty, practice modes) rather than sound library size. However, to be viable as an arranger engine, certain baseline features are required.

**Current State:**
- 9 rhythm styles (industry standard: 200+)
- No arrangement sections (intro/fill/ending)
- No MIDI input chord detection
- No velocity touch curves
- Strong teaching/coaching capabilities (unique differentiator)

---

## Feature Comparison: Your System vs Industry Standard

| Feature | Industry Standard | Your System | Gap |
|---------|------------------|-------------|-----|
| **Tones/Sounds** | 238+ GM sounds | 0 (MIDI out only) | By design - relies on external sound module |
| **Rhythms/Styles** | 200 styles | 9 dance packs | **Need ~50-100 more** |
| **Polyphony** | 128 voices | Unlimited (MIDI) | N/A |
| **Demo Songs** | 100 demos | Exercises/etudes | Different paradigm (teaching vs showcase) |
| **Velocity Curves** | 3 (light/std/heavy) | Contour system | **Need touch response curves** |
| **Metronome** | Yes | `--click` flag | Present |
| **Tempo Control** | 30-280 BPM | Yes | Present |
| **MIDI I/O** | In + Out | Out only | **Need MIDI input for chord detection** |
| **Audio I/O** | Line in/out, MP3 | None | By design - MIDI focused |
| **Transpose** | +/- 12 semitones | Per-exercise key | **Need global transpose** |
| **Intro/Fill/Ending** | Yes | Not implemented | **Critical gap** |
| **Sync Start** | Yes | Not implemented | **Important gap** |
| **Registration Memory** | 8-16 slots | Not implemented | Nice-to-have |
| **Chord Detection** | Left-hand sensing | Not implemented | **Critical for live play** |

---

## Competitive Landscape

| Category | Yamaha PSR | Roland BK | Korg Pa | **Smart Guitar** |
|----------|------------|-----------|---------|------------------|
| Teaching Focus | Basic | Basic | Basic | **Advanced** |
| Coaching AI | No | No | No | **Yes** |
| Style Count | 200+ | 300+ | 400+ | 9 |
| Intro/Fill/End | Yes | Yes | Yes | No |
| Chord Detect | Yes | Yes | Yes | No |
| MIDI Learn | No | No | No | **Yes** |
| Practice Modes | Basic | Basic | Basic | **Rich** |
| Adaptive Difficulty | No | No | No | **Yes** |

---

## Critical Gaps (Priority Order)

### 1. Rhythm/Style Library Expansion

**Current:** 9 styles
**Target:** 100 styles
**Priority:** HIGH

```
Current packs:
├── bossa_nova_classic_v1
├── country_train_beat_v1
├── disco_four_on_floor_v1
├── funk_16th_pocket_v1
├── gospel_shout_shuffle_v1
├── hiphop_half_time_v1
├── neo_soul_laidback_pocket_v1
├── samba_traditional_v1
└── swing_basic_v1

Missing families:
├── Jazz (bebop, cool, latin jazz, fusion)         ~15 styles
├── Latin (salsa, merengue, cumbia, tango, cha-cha) ~20 styles
├── Rock (8-beat, 16-beat, shuffle, ballad)        ~15 styles
├── Pop (modern, 80s, ballad, dance)               ~15 styles
├── Blues (slow, shuffle, boogie)                  ~10 styles
├── World (reggae, afrobeat, celtic, polka)        ~15 styles
└── Waltz/3-4 (jazz waltz, viennese, country)      ~10 styles
                                            Total: ~100 styles
```

### 2. Arrangement Sections (Intro/Fill/Ending)

**Current:** Main pattern only
**Target:** Full arrangement structure
**Priority:** HIGH

```python
# Required structure per style:
class StyleArrangement:
    intro_a: Pattern      # 2-4 bar intro
    intro_b: Pattern      # Alternate intro
    main_a: Pattern       # Primary groove
    main_b: Pattern       # Variation
    main_c: Pattern       # Build variation
    main_d: Pattern       # Breakdown variation
    fill_1: Pattern       # 1-bar fill (to A)
    fill_2: Pattern       # 1-bar fill (to B)
    fill_3: Pattern       # 1-bar fill (to C)
    fill_4: Pattern       # 1-bar fill (to D)
    ending_a: Pattern     # 2-bar ending (immediate)
    ending_b: Pattern     # 4-bar ending (ritardando)
```

**Trigger Model:**
- INTRO button: Play intro, then Main A
- MAIN A/B/C/D buttons: Switch variation (after fill)
- FILL button: Insert 1-bar fill, continue current main
- ENDING button: Play ending and stop

### 3. MIDI Input + Chord Detection

**Current:** Output only
**Target:** Real-time chord recognition from MIDI input
**Priority:** HIGH

```python
# Required capabilities:
class ChordDetector:
    """Detect chords from MIDI input (left-hand zone)."""

    def detect(self, notes: list[int]) -> Chord:
        """
        Recognize chord from held notes.

        Supported types:
        - Major, minor, 7th, maj7, min7
        - Diminished, augmented
        - Suspended (sus2, sus4)
        - Add9, 6th chords
        - Slash chords (C/E)
        """
        pass

    def set_split_point(self, midi_note: int):
        """Set keyboard split point (default: 54 / F#3)."""
        pass

# Integration:
- Trigger style changes on chord change
- Sync start: begin accompaniment on first chord
- Bass follows detected root
- Voicings adapt to detected extensions
```

### 4. Velocity Touch Curves

**Current:** Velocity contour (per-beat shaping)
**Target:** Input sensitivity curves
**Priority:** MEDIUM

```python
from enum import Enum

class TouchCurve(str, Enum):
    """Velocity response curves for different playing styles."""

    LIGHT = "light"
    # Soft touch -> high velocity
    # Good for: beginners, expressive ballads
    # Curve: logarithmic boost

    STANDARD = "standard"
    # Linear 1:1 response
    # Good for: general use
    # Curve: linear

    HEAVY = "heavy"
    # Hard touch required for high velocity
    # Good for: dynamics practice, rock/funk
    # Curve: logarithmic compression

    FIXED = "fixed"
    # Constant velocity regardless of input
    # Good for: timing practice, click tracks
    # Value: configurable (default 80)


def apply_touch_curve(
    input_velocity: int,
    curve: TouchCurve,
    fixed_value: int = 80
) -> int:
    """Transform input velocity through selected curve."""
    if curve == TouchCurve.FIXED:
        return fixed_value
    elif curve == TouchCurve.LIGHT:
        # Logarithmic boost: soft touch feels responsive
        return min(127, int(127 * (input_velocity / 127) ** 0.6))
    elif curve == TouchCurve.HEAVY:
        # Logarithmic compression: requires firm touch
        return min(127, int(127 * (input_velocity / 127) ** 1.6))
    else:  # STANDARD
        return input_velocity
```

### 5. Global Transpose

**Current:** Per-exercise key setting
**Target:** Real-time global transpose
**Priority:** MEDIUM

```python
class GlobalTranspose:
    """Real-time key transposition for all MIDI output."""

    semitones: int  # Range: -12 to +12

    def transpose_note(self, note: int) -> int:
        """Shift MIDI note number."""
        return max(0, min(127, note + self.semitones))

    def transpose_chord(self, chord: Chord) -> Chord:
        """Shift chord root while preserving quality."""
        new_root = (chord.root + self.semitones) % 12
        return Chord(root=new_root, quality=chord.quality)
```

**UI Integration:**
- Transpose +/- buttons or knob
- Display shows current transposition
- Affects all output in real-time (no regeneration needed)

### 6. Sync Start/Stop

**Current:** Manual start
**Target:** Start on first note/chord
**Priority:** MEDIUM

```python
class SyncMode(str, Enum):
    OFF = "off"              # Manual start/stop only
    SYNC_START = "sync_start" # Start on first MIDI input
    SYNC_STOP = "sync_stop"   # Stop when keys released
    SYNC_BOTH = "sync_both"   # Both behaviors

class SyncController:
    mode: SyncMode
    armed: bool  # Ready to start on next input

    def arm(self):
        """Arm sync start - next MIDI input triggers playback."""
        self.armed = True

    def on_midi_input(self, msg: MidiMessage):
        """Handle incoming MIDI for sync triggers."""
        if self.armed and msg.type == 'note_on':
            self.start_playback()
            self.armed = False
```

### 7. Registration Memory

**Current:** No preset storage
**Target:** Save/recall complete configurations
**Priority:** LOW

```python
@dataclass
class Registration:
    """Complete system state snapshot."""

    # Identity
    name: str
    slot: int  # 1-16

    # Style settings
    style_id: str
    tempo_bpm: int
    variation: str  # main_a, main_b, etc.

    # Performance settings
    transpose: int
    touch_curve: TouchCurve
    split_point: int

    # Coaching settings (unique to Smart Guitar)
    coaching_mode: str
    difficulty: str
    assist_level: float

# Storage: JSON files in user config directory
# registrations/
# ├── slot_01.json
# ├── slot_02.json
# └── ...
```

---

## Features to Skip (Not Core to Mission)

| Standard Feature | Reason to Skip |
|------------------|----------------|
| Built-in sounds (238 tones) | MIDI-out design is cleaner; user picks sound module |
| MP3 playback | Not core to teaching mission |
| USB audio interface | External DAW handles this better |
| 100 demo songs | Your exercises ARE the content |
| Recording to USB | External recording is more flexible |
| Karaoke/lyrics display | Not relevant to instrument practice |
| Sampling/user sounds | Complexity without teaching value |

---

## Recommended Development Roadmap

### Phase 1: Minimum Viable Arranger
**Goal:** Feature parity with entry-level arrangers
**Scope:**

1. Add 50 more styles across 7 families
2. Implement Intro/Main/Fill/Ending structure
3. Add velocity touch curves (3 presets + fixed)
4. Add global transpose (-12 to +12)

### Phase 2: Live Performance Ready
**Goal:** Usable for live accompaniment
**Scope:**

5. MIDI input with chord detection
6. Sync start/stop
7. Registration memory (8 slots)
8. Style favorites/quick access

### Phase 3: Teaching Differentiation
**Goal:** Unique value proposition
**Scope:**

9. AI-guided style suggestions based on skill level
10. Automatic fill insertion at phrase boundaries
11. Teaching modes:
    - **Shadow Mode:** AI leads, student follows
    - **Challenge Mode:** AI follows, student leads
    - **Adaptive Mode:** Difficulty adjusts in real-time
12. Practice analytics: timing accuracy, chord changes, dynamics

---

## Success Metrics

| Metric | Current | Phase 1 | Phase 2 | Phase 3 |
|--------|---------|---------|---------|---------|
| Style count | 9 | 60 | 100 | 150 |
| Arrangement sections | 1 | 8 | 12 | 12 |
| MIDI input | No | No | Yes | Yes |
| Touch curves | 0 | 4 | 4 | 4 |
| Chord types detected | 0 | 0 | 12 | 20 |
| Teaching modes | 3 | 3 | 5 | 8 |

---

## Appendix: Current Style Inventory

```
packs/
├── bossa_nova_classic_v1.dpack.json
├── country_train_beat_v1.dpack.json
├── disco_four_on_floor_v1.dpack.json
├── funk_16th_pocket_v1.dpack.json
├── gospel_shout_shuffle_v1.dpack.json
├── hiphop_half_time_v1.dpack.json
├── neo_soul_laidback_pocket_v1.dpack.json
├── samba_traditional_v1.dpack.json
└── swing_basic_v1.dpack.json

Total: 9 styles
```

---

## Document History

| Date | Author | Changes |
|------|--------|---------|
| 2025-01-28 | Claude | Initial analysis |
