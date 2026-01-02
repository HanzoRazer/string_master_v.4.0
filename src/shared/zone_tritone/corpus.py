from __future__ import annotations

from collections.abc import Sequence

from .pc import pc_from_name
from .types import PitchClass, RootSequence


# Very simple root extraction: read leading letter + optional #/b
# This is intentionally conservative and can be improved later.
def extract_root_symbol(chord: str) -> str:
    """
    Extract a root symbol like 'C', 'Db', 'F#' from a chord symbol string.

    Examples:
        'G7' -> 'G'
        'C#maj7' -> 'C#'
        'Eb7alt' -> 'Eb'
    """
    chord = chord.strip()
    if not chord:
        raise ValueError("Empty chord symbol.")
    root = chord[0]
    if len(chord) > 1 and chord[1] in ("b", "#"):
        root += chord[1]
    return root


def chord_sequence_to_roots(chords: Sequence[str]) -> RootSequence:
    """
    Convert a sequence of chord symbol strings into a sequence of pitch-class roots.

    This function intentionally ignores chord quality; it only extracts roots.
    """
    roots: list[PitchClass] = []
    for ch in chords:
        symbol = extract_root_symbol(ch)
        roots.append(pc_from_name(symbol))
    return roots
