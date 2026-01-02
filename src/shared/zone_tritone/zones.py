from __future__ import annotations

from .types import PitchClass


def zone(pc: PitchClass) -> int:
    """
    Return the whole-tone zone index for a pitch class.

    0 = Zone 1 (even pc): {0,2,4,6,8,10}
    1 = Zone 2 (odd pc) : {1,3,5,7,9,11}
    """
    return pc % 2


def zone_name(pc: PitchClass) -> str:
    """Human-readable zone label."""
    return "Zone 1" if zone(pc) == 0 else "Zone 2"


def is_same_zone(a: PitchClass, b: PitchClass) -> bool:
    """Return True if both pitch classes lie in the same zone."""
    return zone(a) == zone(b)


def is_zone_cross(a: PitchClass, b: PitchClass) -> bool:
    """Return True if the interval crosses zones (i.e. a semitone offset)."""
    return not is_same_zone(a, b)


def interval(pc1: PitchClass, pc2: PitchClass) -> int:
    """Return interval from pc1 to pc2 in semitones modulo 12."""
    return (pc2 - pc1) % 12


def is_half_step(a: PitchClass, b: PitchClass) -> bool:
    """Return True if the interval between a and b is a semitone (↑ or ↓)."""
    d = interval(a, b)
    return d in (1, 11)


def is_whole_step(a: PitchClass, b: PitchClass) -> bool:
    """Return True if the interval between a and b is a whole step (↑ or ↓)."""
    d = interval(a, b)
    return d in (2, 10)
