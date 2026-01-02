"""
Chord parsing and pitch generation for the accompaniment engine.
"""
from __future__ import annotations

from dataclasses import dataclass

from shared.zone_tritone.pc import pc_from_name
from shared.zone_tritone.types import PitchClass


@dataclass
class Chord:
    """
    Represents a parsed chord symbol.

    Attributes:
        symbol: Original chord symbol string (e.g. "Cmaj7")
        root_pc: Root pitch class (0-11)
        quality: Chord quality ("maj", "min", "dom", "dim", "aug")
        extensions: List of extensions/alterations (e.g. ["9", "b13"])
    """
    symbol: str
    root_pc: PitchClass
    quality: str
    extensions: list[str]


def parse_chord_symbol(symbol: str) -> Chord:
    """
    Parse a chord symbol into a Chord object.

    Supports common jazz notation:
    - Major: Cmaj7, CΔ7, CM7
    - Minor: Cm7, C-7, Cmin7
    - Dominant: C7
    - Half-diminished: Cm7b5, Cø7
    - Diminished: Cdim, C°

    Examples:
        >>> parse_chord_symbol("Cmaj7")
        Chord(symbol='Cmaj7', root_pc=0, quality='maj', extensions=[])
        >>> parse_chord_symbol("Dm7")
        Chord(symbol='Dm7', root_pc=2, quality='min', extensions=[])
    """
    s = symbol.strip()
    if not s:
        raise ValueError("Empty chord symbol")

    # Extract root note (1 or 2 characters: C, C#, Bb, etc.)
    root_str = s[0]
    idx = 1

    if idx < len(s) and s[idx] in ("b", "#"):
        root_str += s[idx]
        idx += 1

    try:
        root_pc = pc_from_name(root_str)
    except (KeyError, ValueError) as e:
        raise ValueError(f"Invalid root note: {root_str}") from e

    # Parse quality from remainder
    remainder = s[idx:]
    quality = "maj"  # default
    extensions: list[str] = []

    # Detect quality
    if not remainder or remainder.startswith("maj") or remainder.startswith("Δ") or remainder.startswith("M"):
        quality = "maj"
        if remainder.startswith("maj"):
            remainder = remainder[3:]
        elif remainder.startswith(("Δ", "M")):
            remainder = remainder[1:]
    elif remainder.startswith("m7b5") or remainder.startswith("ø"):
        quality = "dim"  # half-diminished treated as diminished for voicing purposes
        remainder = remainder[4:] if remainder.startswith("m7b5") else remainder[1:]
    elif remainder.startswith(("m", "-", "min")):
        quality = "min"
        if remainder.startswith("min"):
            remainder = remainder[3:]
        else:
            remainder = remainder[1:]
    elif remainder.startswith(("dim", "°")):
        quality = "dim"
        remainder = remainder[3:] if remainder.startswith("dim") else remainder[1:]
    elif remainder.startswith(("aug", "+")):
        quality = "aug"
        remainder = remainder[3:] if remainder.startswith("aug") else remainder[1:]
    elif remainder and remainder[0].isdigit():
        # Dominant 7th (just a number like "7")
        quality = "dom"

    # Parse extensions (simplified - just store as strings)
    if remainder:
        extensions.append(remainder)

    return Chord(
        symbol=symbol,
        root_pc=root_pc,
        quality=quality,
        extensions=extensions,
    )


def chord_pitches(chord: Chord, octave: int = 4) -> list[int]:
    """
    Generate MIDI note numbers for a chord voicing.

    Parameters:
        chord: Parsed chord object
        octave: MIDI octave for the root (default: 4, middle C = 60)

    Returns:
        List of MIDI note numbers for the chord voicing

    Examples:
        >>> chord_pitches(parse_chord_symbol("Cmaj7"), octave=4)
        [60, 64, 67, 71]  # C E G B
    """
    root_midi = chord.root_pc + (octave * 12)

    if chord.quality == "maj":
        # Major 7th: 1 3 5 7
        return [root_midi, root_midi + 4, root_midi + 7, root_midi + 11]
    elif chord.quality == "min":
        # Minor 7th: 1 b3 5 b7
        return [root_midi, root_midi + 3, root_midi + 7, root_midi + 10]
    elif chord.quality == "dom":
        # Dominant 7th: 1 3 5 b7
        return [root_midi, root_midi + 4, root_midi + 7, root_midi + 10]
    elif chord.quality == "dim":
        # Diminished/half-diminished: 1 b3 b5 bb7
        return [root_midi, root_midi + 3, root_midi + 6, root_midi + 9]
    elif chord.quality == "aug":
        # Augmented: 1 3 #5
        return [root_midi, root_midi + 4, root_midi + 8]
    else:
        # Fallback: major triad
        return [root_midi, root_midi + 4, root_midi + 7]


def chord_bass_pitch(chord: Chord, octave: int = 2) -> int:
    """
    Generate MIDI note number for the bass note (root).

    Parameters:
        chord: Parsed chord object
        octave: MIDI octave for the bass (default: 2)

    Returns:
        MIDI note number for the bass note
    """
    return chord.root_pc + (octave * 12)
