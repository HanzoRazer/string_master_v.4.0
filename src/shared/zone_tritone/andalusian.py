"""
Andalusian cadence engine for flamenco / Phrygian harmony.

The Andalusian cadence is the harmonic backbone of flamenco music:
    iv → ♭III → ♭II → I(♭2)

Bass motion is a descending tetrachord (whole-whole-half):
    +5 → +3 → +1 → +0 semitones from tonic

Key concepts:
- Phrygian tonic gravity (♭2 → 1 resolution, not V → I)
- Tonic is often MAJOR with ♭2/♭9 color (not minor)
- ♭II is the cadential driver (half-step down to tonic)

Flamenco styles (position/tonic):
- Por Medio: A (5th string bass)
- Por Arriba: E (6th string bass)
- Granaina: B (free time)
- Taranta: F# (free time)
- Mina: Ab/G# (free time)
- Eb Modern: Eb (jazz-influenced)

Reference: docs/Por Medio_A flamenco_Andalusian cadence.txt
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .types import PitchClass
from .pc import pc_from_name, name_from_pc


# ============================================================================
# CONSTANTS
# ============================================================================

# Bass motion: semitone offsets from tonic for Andalusian cadence
ANDALUSIAN_OFFSETS: tuple[int, ...] = (5, 3, 1, 0)  # iv, ♭III, ♭II, I

# Roman numeral labels for each position
ANDALUSIAN_ROMANS: tuple[str, ...] = ("iv", "bIII", "bII", "I")

# Descending step pattern (for validation/debug)
ANDALUSIAN_STEPS: tuple[int, ...] = (2, 2, 1)  # whole, whole, half


# ============================================================================
# STYLE PACKS (extension hints per flamenco style)
# ============================================================================

@dataclass(frozen=True)
class AndalusianStylePack:
    """Extension hints for a flamenco style (does not change bass motion)."""
    name: str
    tonic_pc: PitchClass
    iv_extensions: tuple[str, ...]
    bIII_extensions: tuple[str, ...]
    bII_extensions: tuple[str, ...]
    I_extensions: tuple[str, ...]


STYLE_PACKS: dict[str, AndalusianStylePack] = {
    "por_medio": AndalusianStylePack(
        name="por_medio",
        tonic_pc=9,  # A
        iv_extensions=(),
        bIII_extensions=("9",),
        bII_extensions=("6", "#4"),
        I_extensions=("b2",),
    ),
    "por_arriba": AndalusianStylePack(
        name="por_arriba",
        tonic_pc=4,  # E
        iv_extensions=(),
        bIII_extensions=("6",),
        bII_extensions=("maj7", "#11"),
        I_extensions=("b2",),
    ),
    "granaina": AndalusianStylePack(
        name="granaina",
        tonic_pc=11,  # B
        iv_extensions=(),
        bIII_extensions=("add2",),
        bII_extensions=("add2",),
        I_extensions=("b2", "4"),
    ),
    "taranta": AndalusianStylePack(
        name="taranta",
        tonic_pc=6,  # F#
        iv_extensions=("add4",),
        bIII_extensions=(),
        bII_extensions=("13",),
        I_extensions=("11",),
    ),
    "mina": AndalusianStylePack(
        name="mina",
        tonic_pc=8,  # Ab/G#
        iv_extensions=(),
        bIII_extensions=("add4",),
        bII_extensions=(),
        I_extensions=("b2",),
    ),
    "eb_modern": AndalusianStylePack(
        name="eb_modern",
        tonic_pc=3,  # Eb
        iv_extensions=("11",),
        bIII_extensions=("11",),
        bII_extensions=(),
        I_extensions=("b2",),
    ),
    "traditional": AndalusianStylePack(
        name="traditional",
        tonic_pc=4,  # E (default)
        iv_extensions=(),
        bIII_extensions=(),
        bII_extensions=(),
        I_extensions=("b2",),
    ),
    "jazzy": AndalusianStylePack(
        name="jazzy",
        tonic_pc=4,  # E (default)
        iv_extensions=("9",),
        bIII_extensions=("9",),
        bII_extensions=("9", "#11"),
        I_extensions=("b9",),
    ),
}


# ============================================================================
# CORE FUNCTIONS
# ============================================================================

def andalusian_bass_pcs(tonic_pc: PitchClass) -> list[PitchClass]:
    """
    Compute bass root pitch classes for the Andalusian cadence.

    Parameters:
        tonic_pc: Tonic pitch class (0-11)

    Returns:
        List of 4 pitch classes: [iv, ♭III, ♭II, I]

    Example:
        >>> andalusian_bass_pcs(4)  # E
        [9, 7, 5, 4]  # A, G, F, E
    """
    return [(tonic_pc + offset) % 12 for offset in ANDALUSIAN_OFFSETS]


def andalusian_bass_names(tonic_pc: PitchClass) -> list[str]:
    """
    Get note names for Andalusian cadence bass motion.

    Parameters:
        tonic_pc: Tonic pitch class (0-11)

    Returns:
        List of 4 note names: [iv_root, ♭III_root, ♭II_root, I_root]

    Example:
        >>> andalusian_bass_names(4)  # E
        ['A', 'G', 'F', 'E']
    """
    return [name_from_pc(pc) for pc in andalusian_bass_pcs(tonic_pc)]


@dataclass(frozen=True)
class AndalusianChord:
    """
    A chord in the Andalusian cadence.

    Attributes:
        symbol: Chord symbol string (e.g., "Am", "Fmaj7#11")
        root_pc: Root pitch class (0-11)
        quality: Chord quality ("maj", "min", "dom", "dim", "aug")
        extensions: List of extensions (e.g., ["9", "b2"])
        roman: Roman numeral function (e.g., "iv", "bII")
        position: Position in cadence (0-3)
    """
    symbol: str
    root_pc: PitchClass
    quality: str
    extensions: tuple[str, ...]
    roman: str
    position: int


def build_andalusian_cadence(
    tonic_pc: PitchClass,
    style_pack: str = "traditional",
    force_bII_quality: Literal["maj", "dom"] | None = None,
) -> list[AndalusianChord]:
    """
    Build the Andalusian cadence chord sequence.

    Parameters:
        tonic_pc: Tonic pitch class (0-11)
        style_pack: Extension hints ("por_medio", "por_arriba", "traditional", etc.)
        force_bII_quality: Override ♭II quality ("maj" or "dom" for ♭II7)

    Returns:
        List of 4 AndalusianChord objects: [iv, ♭III, ♭II, I]

    Example:
        >>> chords = build_andalusian_cadence(4, style_pack="por_arriba")
        >>> [c.symbol for c in chords]
        ['Am', 'G6', 'Fmaj7#11', 'Eaddb2']
    """
    bass_pcs = andalusian_bass_pcs(tonic_pc)
    bass_names = [name_from_pc(pc) for pc in bass_pcs]

    pack = STYLE_PACKS.get(style_pack, STYLE_PACKS["traditional"])

    # Default qualities: iv=min, ♭III=maj, ♭II=maj, I=maj
    qualities = ["min", "maj", "maj", "maj"]
    extension_sets = [
        pack.iv_extensions,
        pack.bIII_extensions,
        pack.bII_extensions,
        pack.I_extensions,
    ]

    # Override ♭II quality if requested
    if force_bII_quality == "dom":
        qualities[2] = "dom"

    chords = []
    for i, (root_name, root_pc, quality, exts, roman) in enumerate(
        zip(bass_names, bass_pcs, qualities, extension_sets, ANDALUSIAN_ROMANS)
    ):
        # Build symbol
        if quality == "min":
            symbol = f"{root_name}m"
        elif quality == "dom":
            symbol = f"{root_name}7"
        else:
            symbol = root_name

        if exts:
            symbol += "".join(exts)

        chords.append(AndalusianChord(
            symbol=symbol,
            root_pc=root_pc,
            quality=quality,
            extensions=exts,
            roman=roman,
            position=i,
        ))

    return chords


def build_andalusian_cadence_from_key(
    key: str,
    style_pack: str | None = None,
    force_bII_quality: Literal["maj", "dom"] | None = None,
) -> list[AndalusianChord]:
    """
    Build Andalusian cadence from key name.

    Parameters:
        key: Key name ("A", "E", "B", "F#", "C#", "Ab", "Eb")
        style_pack: Extension hints (auto-detected from key if None)
        force_bII_quality: Override ♭II quality

    Returns:
        List of 4 AndalusianChord objects

    Example:
        >>> chords = build_andalusian_cadence_from_key("A")
        >>> [c.symbol for c in chords]
        ['Dm', 'C9', 'Bb6#4', 'Aaddb2']
    """
    tonic_pc = pc_from_name(key)

    # Auto-detect style pack from tonic if not specified
    if style_pack is None:
        key_to_style = {
            9: "por_medio",   # A
            4: "por_arriba",  # E
            11: "granaina",   # B
            6: "taranta",     # F#
            8: "mina",        # Ab/G#
            3: "eb_modern",   # Eb
        }
        style_pack = key_to_style.get(tonic_pc, "traditional")

    return build_andalusian_cadence(tonic_pc, style_pack, force_bII_quality)


# ============================================================================
# BACKDOOR CADENCE TAG (IV → ♭VII7 → I)
# ============================================================================

def backdoor_tag_pcs(tonic_pc: PitchClass) -> list[PitchClass]:
    """
    Compute bass pitch classes for the backdoor cadence tag.

    The backdoor cadence is: IV → ♭VII7 → I

    Parameters:
        tonic_pc: Tonic pitch class (0-11)

    Returns:
        List of 3 pitch classes: [IV, ♭VII, I]
    """
    return [
        (tonic_pc + 5) % 12,   # IV
        (tonic_pc + 10) % 12,  # ♭VII
        tonic_pc,              # I
    ]


def build_backdoor_tag(tonic_pc: PitchClass) -> list[AndalusianChord]:
    """
    Build the backdoor cadence tag: IV → ♭VII7 → I

    Parameters:
        tonic_pc: Tonic pitch class (0-11)

    Returns:
        List of 3 AndalusianChord objects
    """
    bass_pcs = backdoor_tag_pcs(tonic_pc)

    return [
        AndalusianChord(
            symbol=f"{name_from_pc(bass_pcs[0])}",
            root_pc=bass_pcs[0],
            quality="maj",
            extensions=(),
            roman="IV",
            position=0,
        ),
        AndalusianChord(
            symbol=f"{name_from_pc(bass_pcs[1])}7",
            root_pc=bass_pcs[1],
            quality="dom",
            extensions=(),
            roman="bVII7",
            position=1,
        ),
        AndalusianChord(
            symbol=f"{name_from_pc(bass_pcs[2])}",
            root_pc=bass_pcs[2],
            quality="maj",
            extensions=("b2",),
            roman="I",
            position=2,
        ),
    ]


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "ANDALUSIAN_OFFSETS",
    "ANDALUSIAN_ROMANS",
    "ANDALUSIAN_STEPS",
    "STYLE_PACKS",
    "AndalusianStylePack",
    "AndalusianChord",
    "andalusian_bass_pcs",
    "andalusian_bass_names",
    "build_andalusian_cadence",
    "build_andalusian_cadence_from_key",
    "backdoor_tag_pcs",
    "build_backdoor_tag",
]
