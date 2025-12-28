from __future__ import annotations
from typing import Dict
from .types import PitchClass

# Canonical sharp-based pitch names
NOTES: list[str] = [
    "C", "C#", "D", "Eb", "E", "F",
    "F#", "G", "Ab", "A", "Bb", "B",
]

_name_to_pc: Dict[str, PitchClass] = {
    "C": 0,
    "B#": 0,
    "C#": 1, "Db": 1,
    "D": 2,
    "D#": 3, "Eb": 3,
    "E": 4, "Fb": 4,
    "F": 5, "E#": 5,
    "F#": 6, "Gb": 6,
    "G": 7,
    "G#": 8, "Ab": 8,
    "A": 9,
    "A#": 10, "Bb": 10,
    "B": 11, "Cb": 11,
}


def pc_from_name(name: str) -> PitchClass:
    """
    Convert a pitch name (e.g. 'C', 'Db', 'F#', 'Bb') to a pitch class (0–11).

    Normalizes enharmonic equivalents via a small name dictionary.
    Raises ValueError for unknown names.
    """
    name = name.strip()
    if name not in _name_to_pc:
        raise ValueError(f"Unrecognized pitch name: {name!r}")
    return _name_to_pc[name]


def name_from_pc(pc: PitchClass, prefer_sharps: bool = True) -> str:
    """
    Convert a pitch class (0–11) to a canonical name.

    Parameters
    ----------
    pc:
        Pitch class integer (0–11). Values outside range are reduced modulo 12.
    prefer_sharps:
        Currently unused (future extension for flat-preference).
    """
    return NOTES[pc % 12]
