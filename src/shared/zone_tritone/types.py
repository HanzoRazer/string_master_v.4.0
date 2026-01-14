from __future__ import annotations

from collections.abc import Sequence

PitchClass = int              # 0-11
TritoneAxis = tuple[int, int] # sorted pitch-class pair
RootSequence = Sequence[int]
Matrix = list[list[float]]

__all__ = [
    "PitchClass",
    "TritoneAxis",
    "RootSequence",
    "Matrix",
]
