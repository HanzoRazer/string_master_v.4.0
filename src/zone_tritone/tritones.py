from __future__ import annotations
from .types import PitchClass, TritoneAxis
from .zones import is_same_zone, interval


def tritone_partner(pc: PitchClass) -> PitchClass:
    """
    Return the pitch class at tritone distance from pc (pc + 6 mod 12).
    """
    return (pc + 6) % 12


def tritone_axis(pc: PitchClass) -> TritoneAxis:
    """
    Return the canonical tritone axis containing pc as a sorted pair (low, high).

    Note: Both members of the axis always lie in the same zone (parity).
    """
    partner = tritone_partner(pc)
    return tuple(sorted((pc % 12, partner)))  # type: ignore[return-value]


def is_tritone_pair(a: PitchClass, b: PitchClass) -> bool:
    """
    Return True if (a, b) form a tritone, i.e. differ by 6 semitones mod 12.
    """
    return interval(a, b) in (6,)


def all_tritone_axes() -> list[TritoneAxis]:
    """
    Return the six unique tritone axes in Z_12 as sorted pairs.

    Example: [(0,6), (1,7), (2,8), (3,9), (4,10), (5,11)]
    """
    axes: list[TritoneAxis] = []
    seen: set[TritoneAxis] = set()
    for pc in range(12):
        axis = tritone_axis(pc)
        if axis not in seen:
            seen.add(axis)
            axes.append(axis)
    axes.sort()
    return axes


def validate_tritone_axis(axis: TritoneAxis) -> None:
    """
    Raise ValueError if a pair is not a valid tritone axis.
    """
    a, b = axis
    if not is_tritone_pair(a, b):
        raise ValueError(f"{axis!r} is not a tritone pair.")
    if not is_same_zone(a, b):
        # This should never happen in Z_12 with parity-based zones.
        raise ValueError(f"{axis!r} does not lie in a single zone.")
