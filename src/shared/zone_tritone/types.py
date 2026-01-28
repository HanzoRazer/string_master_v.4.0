from __future__ import annotations

from collections.abc import Sequence
from enum import Enum

PitchClass = int              # 0-11
TritoneAxis = tuple[int, int] # sorted pitch-class pair
RootSequence = Sequence[int]
Matrix = list[list[float]]


class BackdoorMode(str, Enum):
    """Backdoor bar insertion mode for 12-bar blues."""
    OFF = "off"
    TURNAROUND = "turnaround"   # bar 12 = bVII7 (best for looping)
    CADENCE = "cadence"         # bar 11 = bVII7, bar 12 = I7 (best for ending)
    TAG = "tag"                 # bars 11-12 = bVII7, I7 (strongest gospel/jazz)


class ResolutionMode(str, Enum):
    """Dominant resolution mode."""
    FRONT_DOOR = "front_door"   # V -> I (clear, functional)
    TRITONE = "tritone"         # bII7 -> I (color, tension)
    MIXED = "mixed"             # contextual blend


class StyleMode(str, Enum):
    """Zone-Tritone style toggle."""
    HIDDEN = "hidden"   # blues vocab present, chord-tone resolution enforced
    BLUESY = "bluesy"   # blue notes allowed as destinations


class Difficulty(str, Enum):
    """Rhythmic density difficulty level."""
    EASY = "easy"       # 8th notes
    MEDIUM = "medium"   # triplet 8ths
    HARD = "hard"       # 16th notes


__all__ = [
    "PitchClass",
    "TritoneAxis",
    "RootSequence",
    "Matrix",
    "BackdoorMode",
    "ResolutionMode",
    "StyleMode",
    "Difficulty",
]
