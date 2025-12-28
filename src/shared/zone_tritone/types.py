from __future__ import annotations
from typing import Tuple, List, Sequence, Dict

PitchClass = int              # 0–11
TritoneAxis = Tuple[int, int] # sorted pitch-class pair
RootSequence = Sequence[int]
Matrix = List[List[float]]

__all__ = [
    "PitchClass",
    "TritoneAxis",
    "RootSequence",
    "Matrix",
]
