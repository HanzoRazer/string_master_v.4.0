from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class CompEventSpec:
    """
    A simple comping "hit" specification relative to the bar.

    beat:         0-based index in beats (e.g. 0, 1.5, 2.5)
    length_beats: duration in beats
    velocity:     MIDI velocity (0–127)
    """
    beat: float
    length_beats: float
    velocity: int


@dataclass
class StylePattern:
    """
    Encodes a basic accompaniment style pattern.

    name:        human-readable style name
    description: short description for CLI/UI
    comp_hits:   list of comping events (for chord instrument)
    bass_pattern: list of (beat, length, velocity) for bass notes

    Ghost hit params (all default OFF):
    ghost_vel:       velocity for ghost taps (0 = disabled, typically 10-25)
    ghost_steps:     tuple of 16th-note grid steps to ghost (e.g., (1,5,9,13) = "e" of each beat)
    ghost_len_beats: duration of ghost notes in beats (default: 1/16)

    Pickup params:
    pickup_beat:     beat position for anticipation hit before chord change (None = disabled)
    pickup_vel:      velocity for pickup hit
    """
    name: str
    description: str
    comp_hits: List[CompEventSpec]
    bass_pattern: List[Tuple[float, float, int]]
    # Ghost hit params (OFF by default)
    ghost_vel: int = 0
    ghost_steps: Tuple[int, ...] = ()
    ghost_len_beats: float = 0.0625
    # Pickup params (OFF by default)
    pickup_beat: Optional[float] = None
    pickup_vel: int = 70


# --- Styles -------------------------------------------------------------

# 1) Swing-ish comp: hit on 1, and of 2, and of 3; straight 4-to-the-bar bass.
SWING_BASIC = StylePattern(
    name="swing_basic",
    description="Swing-like comping: hits on 1 and the 'and' of 2 & 3, 4-to-the-bar bass.",
    comp_hits=[
        CompEventSpec(beat=0.0, length_beats=1.0, velocity=90),
        CompEventSpec(beat=1.5, length_beats=0.5, velocity=80),
        CompEventSpec(beat=2.5, length_beats=0.5, velocity=80),
    ],
    bass_pattern=[
        (0.0, 1.0, 80),
        (1.0, 1.0, 80),
        (2.0, 1.0, 80),
        (3.0, 1.0, 80),
    ],
)



# 2) Bossa-like pattern: light, even comp on 1 & 3, bass on 1 & 3 with pick-up.
BOSSA_BASIC = StylePattern(
    name="bossa_basic",
    description="Simple bossa feel: light off-beat comping and 1\u20133 bass pattern with pickup.",
    comp_hits=[
        CompEventSpec(beat=0.0, length_beats=0.75, velocity=80),
        CompEventSpec(beat=2.0, length_beats=0.75, velocity=80),
        CompEventSpec(beat=2.75, length_beats=0.25, velocity=70),
    ],
    bass_pattern=[
        (0.0, 1.0, 75),   # beat 1
        (1.75, 0.25, 70), # pickup into 3
        (2.0, 1.0, 75),   # beat 3
    ],
)


# 3) Ballad pattern: long held chord on 1, soft re-hit on 3, sparse bass.
BALLAD_BASIC = StylePattern(
    name="ballad_basic",
    description="Slow ballad: long chord on 1, soft re-hit on 3, sparse bass.",
    comp_hits=[
        CompEventSpec(beat=0.0, length_beats=2.5, velocity=85),
        CompEventSpec(beat=2.0, length_beats=2.0, velocity=70),
    ],
    bass_pattern=[
        (0.0, 2.0, 70),
        (2.0, 2.0, 65),
    ],
)


# 4) Samba 4/4 (partido alto feel): syncopated Brazilian groove.
#    Comp: hits on "and" of 1, beat 2, "and" of 3, beat 4 — classic partido alto bounce.
#    Bass: surdo-style with strong beat 2, anticipation into beat 1.
SAMBA_4_4 = StylePattern(
    name="samba_4_4",
    description="Brazilian samba in 4/4: partido alto comp, surdo-style bass.",
    comp_hits=[
        CompEventSpec(beat=0.5, length_beats=0.5, velocity=85),   # "and" of 1
        CompEventSpec(beat=1.0, length_beats=0.5, velocity=90),   # beat 2 (strong)
        CompEventSpec(beat=2.5, length_beats=0.5, velocity=85),   # "and" of 3
        CompEventSpec(beat=3.0, length_beats=0.5, velocity=80),   # beat 4
    ],
    bass_pattern=[
        (0.0, 0.75, 75),   # beat 1 (lighter)
        (1.0, 1.0, 90),    # beat 2 (surdo strong hit)
        (2.5, 0.5, 70),    # "and" of 3 (anticipation)
        (3.0, 0.75, 80),   # beat 4 (pickup into next bar)
    ],
)


# 5) Samba 2/4 (authentic Brazilian): true samba feel in 2/4 meter.
#    Pattern per 2-beat bar (half-notes = beats in 2/4):
#    Comp: tamborim-style syncopation — hit on beat 1, "and" of 1, "and" of 2
#    Bass: surdo pattern with strong beat 2 (characteristic of samba batucada)
SAMBA_2_4 = StylePattern(
    name="samba_2_4",
    description="Authentic Brazilian samba in 2/4: tamborim comp, surdo bass (use time_signature: 2/4).",
    comp_hits=[
        CompEventSpec(beat=0.0, length_beats=0.25, velocity=85),   # beat 1 (accent)
        CompEventSpec(beat=0.5, length_beats=0.25, velocity=80),   # "and" of 1
        CompEventSpec(beat=0.75, length_beats=0.25, velocity=75),  # "a" of 1 (16th)
        CompEventSpec(beat=1.5, length_beats=0.25, velocity=80),   # "and" of 2
    ],
    bass_pattern=[
        (0.0, 0.5, 70),    # beat 1 (lighter surdo — "surdo de primeira")
        (1.0, 0.75, 95),   # beat 2 (heavy surdo — "surdo de segunda")
    ],
)


# 6) Samba-funk / Samba-rock: Brazilian fusion groove in 4/4.
#    Heavier backbeat with funk influence, popularized in 70s Brazil.
SAMBA_FUNK = StylePattern(
    name="samba_funk",
    description="Brazilian samba-funk/samba-rock: 4/4 groove with funk backbeat.",
    comp_hits=[
        CompEventSpec(beat=0.0, length_beats=0.5, velocity=85),    # beat 1
        CompEventSpec(beat=0.75, length_beats=0.25, velocity=70),  # 16th before 2
        CompEventSpec(beat=1.0, length_beats=0.5, velocity=90),    # beat 2 (backbeat)
        CompEventSpec(beat=2.0, length_beats=0.5, velocity=80),    # beat 3
        CompEventSpec(beat=2.75, length_beats=0.25, velocity=70),  # 16th before 4
        CompEventSpec(beat=3.0, length_beats=0.5, velocity=90),    # beat 4 (backbeat)
    ],
    bass_pattern=[
        (0.0, 0.75, 85),   # beat 1
        (1.0, 0.5, 90),    # beat 2 (strong)
        (1.75, 0.25, 75),  # 16th pickup
        (2.0, 0.75, 85),   # beat 3
        (3.0, 0.5, 90),    # beat 4 (strong)
        (3.5, 0.25, 70),   # "and" of 4 (anticipation)
    ],
)


# ============================================================================
# BUCKET A — SAMBA STYLES (nuanced, document-specified)
# ============================================================================

# 7) samba_basic — 2/4 comp pattern (tamborim-inspired)
#    Short attack on beat 1, syncopated push on "and" of 2.
#    Designed for authentic Brazilian samba in 2/4.
SAMBA_BASIC = StylePattern(
    name="samba_basic",
    description="2/4 samba comp: short stab on 1, syncopated push on &2.",
    comp_hits=[
        CompEventSpec(beat=0.0, length_beats=0.25, velocity=80),   # beat 1 (short stab)
        CompEventSpec(beat=0.5, length_beats=0.25, velocity=75),   # "and" of 1 (ghost)
        CompEventSpec(beat=1.5, length_beats=0.25, velocity=90),   # "and" of 2 (main push)
    ],
    bass_pattern=[],  # bass handled separately by samba_two_feel
)


# 8) samba_two_feel — 2/4 bass pattern (surdo-inspired)
#    Light touch on 1 ("surdo de primeira"), heavy on 2 ("surdo de segunda").
SAMBA_TWO_FEEL = StylePattern(
    name="samba_two_feel",
    description="2/4 samba bass: light beat 1, heavy beat 2 (surdo feel).",
    comp_hits=[],  # comp handled separately by samba_basic
    bass_pattern=[
        (0.0, 0.5, 65),    # beat 1 — light ("primeira")
        (1.0, 0.75, 95),   # beat 2 — heavy ("segunda", the lift)
    ],
)


# 9) samba_basic_4_4 — 4/4 samba comp pattern
#    Hits: 1 (light) &2 (strong) 3 (light) &4 (strong)
#    "Push-pull" feel without rock backbeat.
SAMBA_BASIC_4_4 = StylePattern(
    name="samba_basic_4_4",
    description="4/4 samba comp: 1 (light), &2 (push), 3 (light), &4 (push).",
    comp_hits=[
        CompEventSpec(beat=0.0, length_beats=0.25, velocity=75),   # beat 1 (light)
        CompEventSpec(beat=1.5, length_beats=0.25, velocity=90),   # "and" of 2 (strong push)
        CompEventSpec(beat=2.0, length_beats=0.25, velocity=75),   # beat 3 (light)
        CompEventSpec(beat=3.5, length_beats=0.25, velocity=90),   # "and" of 4 (strong push)
    ],
    bass_pattern=[],  # bass handled separately by samba_four_feel
)


# 10) samba_four_feel — 4/4 bass pattern (stretched surdo)
#     Surdo-style with light 1 & 3, heavy syncopated pushes before 2 & 4.
SAMBA_FOUR_FEEL = StylePattern(
    name="samba_four_feel",
    description="4/4 samba bass: light 1/3, surdo-style push into 2/4.",
    comp_hits=[],  # comp handled separately by samba_basic_4_4
    bass_pattern=[
        (0.0, 0.5, 70),    # beat 1 (light)
        (1.0, 0.75, 90),   # beat 2 (surdo lift)
        (2.0, 0.5, 70),    # beat 3 (light)
        (3.0, 0.75, 90),   # beat 4 (surdo lift)
    ],
)


# ============================================================================
# BUCKET A — BRAZILIAN FEEL: PICKUP + GHOST HITS
# ============================================================================

# 11) samba_basic_4_4_pickup — 4/4 samba with anticipation + ghost taps
#     Main hits: 1 (light), &2 (push), 3 (light), &4 (push)
#     Pickup: &4 anticipation into next chord (classic samba/bossa move)
#     Ghosts: subtle "e" taps (steps 1, 5, 9, 13) at low velocity
SAMBA_BASIC_4_4_PICKUP = StylePattern(
    name="samba_basic_4_4_pickup",
    description="4/4 samba comp with pickup anticipation + ghost taps (Brazilian feel).",
    comp_hits=[
        CompEventSpec(beat=0.0, length_beats=0.25, velocity=75),   # beat 1 (light)
        CompEventSpec(beat=1.5, length_beats=0.25, velocity=90),   # "and" of 2 (strong push)
        CompEventSpec(beat=2.0, length_beats=0.25, velocity=75),   # beat 3 (light)
        CompEventSpec(beat=3.5, length_beats=0.25, velocity=85),   # "and" of 4 (push, slightly softer for pickup feel)
    ],
    bass_pattern=[],  # bass handled separately
    # Ghost hits: "e" of each beat (subtle Brazilian air)
    ghost_vel=14,
    ghost_steps=(1, 5, 9, 13),
    ghost_len_beats=0.0625,
    # Pickup: anticipation on &4 of previous bar
    pickup_beat=3.5,
    pickup_vel=65,
)


# 12) samba_four_feel_pickup — 4/4 bass with anticipation
#     Same surdo feel but with bass pickup on &4.
SAMBA_FOUR_FEEL_PICKUP = StylePattern(
    name="samba_four_feel_pickup",
    description="4/4 samba bass with anticipation (surdo + pickup).",
    comp_hits=[],
    bass_pattern=[
        (0.0, 0.5, 70),    # beat 1 (light)
        (1.0, 0.75, 90),   # beat 2 (surdo lift)
        (2.0, 0.5, 70),    # beat 3 (light)
        (3.0, 0.75, 90),   # beat 4 (surdo lift)
        (3.5, 0.25, 60),   # &4 pickup (anticipation into next chord)
    ],
)


STYLE_REGISTRY = {
    "swing_basic": SWING_BASIC,
    "bossa_basic": BOSSA_BASIC,
    "ballad_basic": BALLAD_BASIC,
    "samba_4_4": SAMBA_4_4,
    "samba_2_4": SAMBA_2_4,
    "samba_funk": SAMBA_FUNK,
    # Bucket A — nuanced samba (split comp/bass)
    "samba_basic": SAMBA_BASIC,
    "samba_two_feel": SAMBA_TWO_FEEL,
    "samba_basic_4_4": SAMBA_BASIC_4_4,
    "samba_four_feel": SAMBA_FOUR_FEEL,
    # Bucket A — Brazilian feel (pickup + ghost)
    "samba_basic_4_4_pickup": SAMBA_BASIC_4_4_PICKUP,
    "samba_four_feel_pickup": SAMBA_FOUR_FEEL_PICKUP,
}
