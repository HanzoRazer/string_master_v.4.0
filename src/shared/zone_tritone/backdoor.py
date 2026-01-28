"""
Backdoor mode logic for 12-bar blues construction.

The backdoor cadence (bVII7 -> I7) creates a smooth, gospel-inflected resolution
that avoids the tension of the standard V7 -> I7. This module handles:
- Standard 12-bar blues root sequence generation
- Backdoor bar insertion based on mode (turnaround, cadence, tag)
- Soft guardrail logic for looping phrases
"""
from __future__ import annotations

from .types import BackdoorMode, PitchClass


def build_12bar_roots(I: PitchClass) -> list[PitchClass]:
    """
    Build standard 12-bar blues root sequence.

    Pattern: I I I I | IV IV I I | V IV I V

    Args:
        I: Tonic pitch class (0-11)

    Returns:
        List of 12 root pitch classes
    """
    IV = (I + 5) % 12   # perfect 4th
    V = (I + 7) % 12    # perfect 5th
    return [I, I, I, I, IV, IV, I, I, V, IV, I, V]


def get_bVII(I: PitchClass) -> PitchClass:
    """
    Calculate bVII (flat-seven) from tonic.

    bVII is a whole step below I (10 semitones up, or 2 down).
    Example: I=C(0) -> bVII=Bb(10)

    Args:
        I: Tonic pitch class

    Returns:
        bVII pitch class
    """
    return (I - 2) % 12


def add_backdoor_bars(
    roots_12: list[PitchClass],
    I: PitchClass,
    mode: BackdoorMode
) -> list[PitchClass]:
    """
    Insert backdoor cadence bars into 12-bar sequence.

    Modes:
    - OFF: No modification
    - TURNAROUND: Bar 12 = bVII7 (loops smoothly back to I)
    - CADENCE: Bar 11 = bVII7, Bar 12 = I7 (clear ending)
    - TAG: Bars 11-12 = bVII7, I7 (strongest gospel/jazz feel)

    Args:
        roots_12: Standard 12-bar root sequence
        I: Tonic pitch class
        mode: Backdoor insertion mode

    Returns:
        Modified root sequence
    """
    if mode == BackdoorMode.OFF:
        return roots_12[:]

    bVII = get_bVII(I)
    out = roots_12[:]

    if mode == BackdoorMode.TURNAROUND:
        # Bar 12 becomes bVII7 - loops back to I smoothly
        out[11] = bVII
    elif mode == BackdoorMode.CADENCE:
        # Bar 11 = bVII7, Bar 12 = I7 - clear cadential ending
        out[10] = bVII
        out[11] = I
    elif mode == BackdoorMode.TAG:
        # Same as CADENCE structurally, but implies 2-bar tag
        # (strongest gospel/jazz feel when repeated)
        out[10] = bVII
        out[11] = I

    return out


def build_backdoor_blues(I: PitchClass, mode: BackdoorMode) -> list[PitchClass]:
    """
    Build complete 12-bar blues with backdoor cadence.

    Convenience function combining build_12bar_roots and add_backdoor_bars.

    Args:
        I: Tonic pitch class (0-11)
        mode: Backdoor insertion mode

    Returns:
        12-bar root sequence with backdoor bars applied

    Example:
        >>> build_backdoor_blues(0, BackdoorMode.TURNAROUND)  # C blues
        [0, 0, 0, 0, 5, 5, 0, 0, 7, 5, 0, 10]  # bVII=Bb in bar 12
    """
    roots = build_12bar_roots(I)
    return add_backdoor_bars(roots, I, mode)


def needs_soft_guardrail(mode: BackdoorMode) -> bool:
    """
    Check if mode requires soft guardrail for looping.

    TURNAROUND mode ends on bVII7 which resolves TO the I7 at the top
    of the next chorus. The phrase generator should prefer frame-tone
    endings that set up the loop.

    CADENCE and TAG modes end on I7, so no special handling needed.

    Args:
        mode: Backdoor mode

    Returns:
        True if soft guardrail should be applied to bar 12
    """
    return mode == BackdoorMode.TURNAROUND


def describe_mode(mode: BackdoorMode) -> str:
    """
    Get human-readable description of backdoor mode.

    Args:
        mode: Backdoor mode

    Returns:
        Description string for UI/documentation
    """
    descriptions = {
        BackdoorMode.OFF: "Standard 12-bar blues (no backdoor)",
        BackdoorMode.TURNAROUND: "Backdoor turnaround: bar 12 = bVII7 (best for looping)",
        BackdoorMode.CADENCE: "Backdoor cadence: bar 11 = bVII7, bar 12 = I7 (clear ending)",
        BackdoorMode.TAG: "Backdoor tag: bars 11-12 = bVII7 -> I7 (gospel/jazz)",
    }
    return descriptions.get(mode, "Unknown mode")


__all__ = [
    "build_12bar_roots",
    "get_bVII",
    "add_backdoor_bars",
    "build_backdoor_blues",
    "needs_soft_guardrail",
    "describe_mode",
]
