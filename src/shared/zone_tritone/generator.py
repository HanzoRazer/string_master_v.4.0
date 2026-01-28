"""
Phrase and etude generator for Zone-Tritone Hidden Blues Resolution engine.

Core rule: Blues vocabulary is allowed everywhere, but blues notes are
forbidden as points of rest. Resolution is constrained to chord tones
(especially 3rds & 7ths).

This produces lines that feel lyrical and playful rather than overtly bluesy.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Optional

from .backdoor import build_backdoor_blues, needs_soft_guardrail
from .dominant import Dominant7, transpose
from .types import BackdoorMode, Difficulty, PitchClass, StyleMode


# ---------------------------------------------------------------------------
# Difficulty → Density Mapping
# ---------------------------------------------------------------------------

DENSITY_MAP = {
    Difficulty.EASY: 4,     # ~4 notes per bar (8th note feel)
    Difficulty.MEDIUM: 6,   # ~6 notes per bar (triplet 8th feel)
    Difficulty.HARD: 8,     # ~8 notes per bar (16th note feel)
}


# ---------------------------------------------------------------------------
# Difficulty → Tritone Substitution Policy
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SubstitutionPolicy:
    """Policy for tritone substitution probability."""
    base: float           # Base probability of tritone sub
    cadence_mult: float   # Multiplier for cadence bars
    final_mult: float     # Multiplier for final chorus


DIFF_POLICY = {
    Difficulty.EASY: SubstitutionPolicy(base=0.00, cadence_mult=0.00, final_mult=0.10),
    Difficulty.MEDIUM: SubstitutionPolicy(base=0.12, cadence_mult=2.00, final_mult=1.50),
    Difficulty.HARD: SubstitutionPolicy(base=0.28, cadence_mult=1.60, final_mult=1.30),
}


def tritone_probability(
    difficulty: Difficulty,
    is_cadence_bar: bool = False,
    is_final_chorus: bool = False
) -> float:
    """
    Calculate tritone substitution probability based on context.

    Args:
        difficulty: Current difficulty level
        is_cadence_bar: True if bar resolves to I
        is_final_chorus: True if this is the final chorus

    Returns:
        Probability [0.0, 0.95] of using tritone sub
    """
    policy = DIFF_POLICY[difficulty]
    p = policy.base

    if is_cadence_bar:
        p *= policy.cadence_mult
    if is_final_chorus:
        p *= policy.final_mult

    return max(0.0, min(0.95, p))


# ---------------------------------------------------------------------------
# Phrase Generator
# ---------------------------------------------------------------------------

def generate_phrase(
    chord: Dominant7,
    length: int = 4,
    style: StyleMode = StyleMode.HIDDEN,
    color_prob: float = 0.4
) -> list[PitchClass]:
    """
    Generate a phrase over a dominant chord.

    In HIDDEN mode: phrase-final note MUST be a frame tone.
    In BLUESY mode: blue notes are allowed as destinations.

    Args:
        chord: Dominant7 chord for this phrase
        length: Number of notes in phrase (3-8 typical)
        style: HIDDEN enforces chord-tone resolution, BLUESY allows blue notes
        color_prob: Probability of inserting a color tone (0.0-1.0)

    Returns:
        List of pitch classes forming the phrase
    """
    phrase: list[PitchClass] = []
    frame_list = list(chord.frame)
    color_list = list(chord.color)

    # Start on a frame tone
    current = random.choice(frame_list)
    phrase.append(current)

    for _ in range(length - 1):
        if random.random() < color_prob:
            # Insert color tone (must move in hidden mode!)
            next_note = random.choice(color_list)
        else:
            # Move through frame
            next_note = random.choice(frame_list)
        phrase.append(next_note)
        current = next_note

    # Enforce resolution constraint
    if style == StyleMode.HIDDEN:
        # Final note MUST be a frame tone
        phrase[-1] = random.choice(frame_list)
    elif style == StyleMode.BLUESY:
        # Blue notes allowed as destinations - slight bias toward color
        if random.random() < 0.35:
            phrase[-1] = random.choice(color_list)
        else:
            phrase[-1] = random.choice(frame_list)

    return phrase


def generate_phrase_with_guide_tones(
    chord: Dominant7,
    length: int = 4,
    style: StyleMode = StyleMode.HIDDEN,
    prefer_guide_tone_ending: bool = True
) -> list[PitchClass]:
    """
    Generate phrase with preference for guide tone (3rd/7th) endings.

    Guide tones create stronger voice leading into the next chord.

    Args:
        chord: Dominant7 chord
        length: Number of notes
        style: Resolution mode
        prefer_guide_tone_ending: If True, prefer 3rd or 7th as final note

    Returns:
        Phrase as list of pitch classes
    """
    phrase = generate_phrase(chord, length, style)

    if style == StyleMode.HIDDEN and prefer_guide_tone_ending:
        # Override final note to be a guide tone (3rd or 7th)
        phrase[-1] = random.choice(chord.guide_tones)

    return phrase


# ---------------------------------------------------------------------------
# Soft Guardrail for Looping
# ---------------------------------------------------------------------------

def apply_soft_guardrail(
    phrase: list[PitchClass],
    chord: Dominant7,
    mode: BackdoorMode,
    is_bar_12: bool
) -> list[PitchClass]:
    """
    Apply soft guardrail for looping modes.

    In TURNAROUND mode, bar 12 ends on bVII7 which resolves TO the I7
    at the top of the next chorus. The phrase ending should set up
    that resolution smoothly.

    Args:
        phrase: Generated phrase
        chord: Current chord
        mode: Backdoor mode
        is_bar_12: True if this is bar 12

    Returns:
        Phrase with guardrail applied (may be modified)
    """
    if not is_bar_12:
        return phrase

    if not needs_soft_guardrail(mode):
        return phrase

    # For TURNAROUND looping: prefer 7th of bVII7 (which is 6th scale degree)
    # or 3rd of bVII7 (which becomes chromatic approach to tonic)
    # Both create smooth resolution to I7
    phrase_copy = phrase[:]
    phrase_copy[-1] = chord.seventh  # b7 of bVII7 resolves nicely to root of I
    return phrase_copy


# ---------------------------------------------------------------------------
# 12-Bar Etude Generator
# ---------------------------------------------------------------------------

@dataclass
class EtudeBar:
    """Single bar of an etude."""
    bar_number: int         # 1-12
    root: PitchClass        # Root of dominant chord
    chord: Dominant7        # Full chord object
    phrase: list[PitchClass]  # Generated phrase


@dataclass
class Etude:
    """Complete 12-bar etude."""
    key: PitchClass         # Tonic pitch class
    mode: BackdoorMode      # Backdoor insertion mode
    style: StyleMode        # Resolution style
    difficulty: Difficulty  # Density/complexity
    bars: list[EtudeBar]    # 12 bars


def generate_etude(
    key: PitchClass = 0,
    mode: BackdoorMode = BackdoorMode.TURNAROUND,
    style: StyleMode = StyleMode.HIDDEN,
    difficulty: Difficulty = Difficulty.MEDIUM,
    chorus_number: int = 1,
    total_choruses: int = 1,
) -> Etude:
    """
    Generate a complete 12-bar blues etude.

    Args:
        key: Tonic pitch class (0=C, 1=Db, ..., 11=B)
        mode: Backdoor bar insertion mode
        style: HIDDEN (chord-tone resolution) or BLUESY (blue note destinations)
        difficulty: Affects note density and tritone probability
        chorus_number: Current chorus (1-indexed)
        total_choruses: Total choruses (for soft guardrails)

    Returns:
        Etude object with 12 bars of generated phrases

    Example:
        >>> etude = generate_etude(key=0, mode=BackdoorMode.TURNAROUND)
        >>> for bar in etude.bars:
        ...     print(f"Bar {bar.bar_number}: {bar.phrase}")
    """
    # Build root sequence with backdoor bars
    roots = build_backdoor_blues(key, mode)

    # Determine phrase length from difficulty
    base_length = DENSITY_MAP[difficulty]

    # Check if this is the final chorus (for soft guardrails)
    is_final = (chorus_number == total_choruses)

    bars: list[EtudeBar] = []
    for i, root in enumerate(roots):
        bar_number = i + 1
        chord = Dominant7(root)

        # Vary phrase length slightly
        length = base_length + random.randint(-1, 1)
        length = max(3, min(10, length))

        # Check if this is a cadence bar (bar 11 or 12)
        is_cadence = bar_number >= 11

        # Apply tritone sub probability (affects chord voicing, not root)
        # This is logged but not changing the root sequence here
        tri_prob = tritone_probability(difficulty, is_cadence, is_final)

        # Generate phrase
        phrase = generate_phrase_with_guide_tones(
            chord=chord,
            length=length,
            style=style,
            prefer_guide_tone_ending=(bar_number in (4, 8, 12))
        )

        # Apply soft guardrail for bar 12 in looping modes
        if bar_number == 12:
            phrase = apply_soft_guardrail(phrase, chord, mode, True)

        bars.append(EtudeBar(
            bar_number=bar_number,
            root=root,
            chord=chord,
            phrase=phrase,
        ))

    return Etude(
        key=key,
        mode=mode,
        style=style,
        difficulty=difficulty,
        bars=bars,
    )


def generate_multi_chorus_etude(
    key: PitchClass = 0,
    mode: BackdoorMode = BackdoorMode.TURNAROUND,
    style: StyleMode = StyleMode.HIDDEN,
    difficulty: Difficulty = Difficulty.MEDIUM,
    num_choruses: int = 2,
) -> list[Etude]:
    """
    Generate multiple choruses with soft guardrails applied.

    In CADENCE/TAG modes, earlier choruses use TURNAROUND behavior
    and only the final chorus uses the requested mode.

    Args:
        key: Tonic pitch class
        mode: Backdoor mode (may be overridden for early choruses)
        style: Resolution style
        difficulty: Note density
        num_choruses: Number of 12-bar choruses

    Returns:
        List of Etude objects (one per chorus)
    """
    choruses: list[Etude] = []

    for chorus_num in range(1, num_choruses + 1):
        # Soft guardrail: cadence modes only apply to final chorus
        effective_mode = mode
        if mode in (BackdoorMode.CADENCE, BackdoorMode.TAG):
            if chorus_num < num_choruses:
                effective_mode = BackdoorMode.TURNAROUND

        etude = generate_etude(
            key=key,
            mode=effective_mode,
            style=style,
            difficulty=difficulty,
            chorus_number=chorus_num,
            total_choruses=num_choruses,
        )
        choruses.append(etude)

    return choruses


# ---------------------------------------------------------------------------
# Utility Functions
# ---------------------------------------------------------------------------

def etude_to_pitch_sequence(etude: Etude) -> list[PitchClass]:
    """Flatten etude to single pitch sequence."""
    return [pc for bar in etude.bars for pc in bar.phrase]


def etude_summary(etude: Etude) -> str:
    """Generate human-readable summary of etude."""
    from .pc import name_from_pc
    key_name = name_from_pc(etude.key)
    return (
        f"12-bar blues in {key_name}\n"
        f"Mode: {etude.mode.value}\n"
        f"Style: {etude.style.value}\n"
        f"Difficulty: {etude.difficulty.value}\n"
        f"Total notes: {sum(len(b.phrase) for b in etude.bars)}"
    )


__all__ = [
    "generate_phrase",
    "generate_phrase_with_guide_tones",
    "generate_etude",
    "generate_multi_chorus_etude",
    "apply_soft_guardrail",
    "tritone_probability",
    "etude_to_pitch_sequence",
    "etude_summary",
    "Etude",
    "EtudeBar",
    "SubstitutionPolicy",
    "DENSITY_MAP",
    "DIFF_POLICY",
]
