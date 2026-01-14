"""
Bridge between Zone-Tritone theory and the accompaniment engine.

This module annotates chord progressions with gravity/zone metadata
and provides tritone substitution utilities.
"""
from __future__ import annotations

import random
from dataclasses import dataclass

from shared.zone_tritone.gravity import gravity_chain
from shared.zone_tritone.pc import name_from_pc
from shared.zone_tritone.tritones import tritone_axis
from shared.zone_tritone.types import PitchClass
from shared.zone_tritone.zones import interval, zone_name

from .chords import Chord, parse_chord_symbol


@dataclass
class GravityAnnotatedChord:
    """
    A single chord annotated with Zone-Tritone metadata.

    - chord: original parsed chord
    - root_pc: pitch class of the root (0-11)
    - zone: zone label from the Zone-Tritone system (e.g. 'Zone 1', 'Zone 2')
    - axis: the tritone axis implied by the chord's 3rd/7th
    - gravity_target: the "ideal" next root in a pure descending-4ths gravity chain
    - is_on_chain: whether this chord's root matches the ideal gravity chain step
    """
    chord: Chord
    root_pc: PitchClass
    zone: str
    axis: tuple[PitchClass, PitchClass]
    gravity_target: PitchClass | None
    is_on_chain: bool


@dataclass
class GravityTransition:
    """
    A transition between two adjacent chords, with gravity + zone diagnostics.
    """
    index_from: int
    from_root: PitchClass
    to_root: PitchClass
    interval_semitones: int
    from_zone: str
    to_zone: str
    is_desc_fourth: bool
    is_asc_fourth: bool
    is_half_step: bool
    is_whole_step: bool


def annotate_progression(chord_symbols: list[str]) -> list[GravityAnnotatedChord]:
    """
    Annotate a chord progression with Zone-Tritone information.

    This does not change the chords -- it only adds metadata that can be used
    by the engine, CLI, or UI for analysis or display.
    """
    if not chord_symbols:
        return []

    chords = [parse_chord_symbol(s) for s in chord_symbols]
    roots = [c.root_pc for c in chords]

    # Ideal gravity chain (cycle of descending 4ths) from the first chord
    # For N chords, there are N-1 "next" steps in the chain.
    if len(roots) > 1:
        chain = [roots[0]] + gravity_chain(roots[0], len(roots) - 1)
    else:
        chain = [roots[0]]

    annotated: list[GravityAnnotatedChord] = []

    for idx, c in enumerate(chords):
        root_pc = c.root_pc
        zname = zone_name(root_pc)

        # Use 3rd of the chord to define the tritone axis.
        # Major/dom: 1-3-5-7 -> 3 is root+4
        # Minor: 1-b3-5-b7 -> 3 is root+3
        if c.quality in ("maj", "dom"):
            third_pc = (root_pc + 4) % 12
        else:
            third_pc = (root_pc + 3) % 12

        axis = tritone_axis(third_pc)

        gravity_target: PitchClass | None = None
        if idx < len(chain) - 1:
            gravity_target = chain[idx + 1]

        expected_root = chain[idx] if idx < len(chain) else None
        is_on_chain = False
        if expected_root is not None and (expected_root - root_pc) % 12 == 0:
            is_on_chain = True

        annotated.append(
            GravityAnnotatedChord(
                chord=c,
                root_pc=root_pc,
                zone=zname,
                axis=axis,
                gravity_target=gravity_target,
                is_on_chain=is_on_chain,
            )
        )

    return annotated


def compute_transitions(
    annotated: list[GravityAnnotatedChord],
) -> list[GravityTransition]:
    """
    Compute stepwise motion diagnostics between annotated chords.

    Returns one GravityTransition for each pair (i -> i+1).
    """
    transitions: list[GravityTransition] = []
    if len(annotated) < 2:
        return transitions

    for idx in range(len(annotated) - 1):
        a = annotated[idx]
        b = annotated[idx + 1]

        # Calculate interval between roots
        d = interval(a.root_pc, b.root_pc)
        abs_d = abs(d)

        # Detect descending/ascending fourths (5 semitones)
        is_desc_fourth = abs_d == 5 and d < 0
        is_asc_fourth = abs_d == 5 and d > 0
        is_half_step = abs_d == 1
        is_whole_step = abs_d == 2

        transitions.append(
            GravityTransition(
                index_from=idx,
                from_root=a.root_pc,
                to_root=b.root_pc,
                interval_semitones=abs_d,
                from_zone=a.zone,
                to_zone=b.zone,
                is_desc_fourth=is_desc_fourth,
                is_asc_fourth=is_asc_fourth,
                is_half_step=is_half_step,
                is_whole_step=is_whole_step,
            )
        )

    return transitions


def tritone_sub_root(root_pc: PitchClass) -> PitchClass:
    """
    Basic tritone-substitution mapping for a dominant root:
    move the root by +6 semitones (mod 12).

    Example:
        G (7)  -> Db (1)
        C (0)  -> F# (6)
        D (2)  -> Ab (8)
    """
    return (root_pc + 6) % 12


def apply_tritone_substitutions(
    chords: list[Chord],
    mode: str = "none",
    strength: float = 1.0,
    seed: int | None = None,
) -> list[Chord]:
    """
    Apply tritone substitutions to a chord progression.

    Parameters
    ----------
    chords:
        List of parsed Chord objects.
    mode:
        - "none":          no substitutions (identity).
        - "all_doms":      every dominant chord (quality == 'dom') gets a tritone sub.
        - "probabilistic": each dominant chord has `strength` chance to be substituted.
    strength:
        Probability in [0.0, 1.0] for 'probabilistic' mode.
    seed:
        Optional random seed for reproducible reharmonizations.

    Returns
    -------
    List[Chord]:
        New chord list (may reuse original Chord instances when unchanged).
    """
    if mode == "none":
        return list(chords)

    rng = random.Random(seed)
    out: list[Chord] = []

    for chord in chords:
        new_chord = chord

        if chord.quality == "dom" and mode in ("all_doms", "probabilistic"):
            apply = mode == "all_doms" or rng.random() < max(0.0, min(1.0, strength))

            if apply:
                # Compute tritone-sub root
                sub_pc = tritone_sub_root(chord.root_pc)
                sub_root_name = name_from_pc(sub_pc)

                # Preserve the chord "suffix" (7, 9, etc.) by reusing the symbol tail
                s = chord.symbol.strip()
                if not s:
                    out.append(chord)
                    continue

                root = s[0]
                accidental = ""
                if len(s) >= 2 and s[1] in ("b", "#"):
                    accidental = s[1]
                suffix = s[len(root + accidental) :]

                new_symbol = sub_root_name + suffix or "7"

                try:
                    new_chord = parse_chord_symbol(new_symbol)
                except Exception:
                    # Fallback: if parsing fails, keep original chord.
                    new_chord = chord

        out.append(new_chord)

    return out
