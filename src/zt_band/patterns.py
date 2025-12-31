from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple


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
    """
    name: str
    description: str
    comp_hits: List[CompEventSpec]
    bass_pattern: List[Tuple[float, float, int]]


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


STYLE_REGISTRY = {
    "swing_basic": SWING_BASIC,
    "bossa_basic": BOSSA_BASIC,
    "ballad_basic": BALLAD_BASIC,
    "samba_4_4": SAMBA_4_4,
}
