from __future__ import annotations

from .tritones import is_tritone_pair
from .types import PitchClass, TritoneAxis


def dominant_roots_from_tritone(axis: TritoneAxis) -> list[PitchClass]:
    """
    Infer dominant roots whose (3,7) tritone matches the given axis.

    In 12-TET, a tritone pair {a,b} can act as 3rd and 7th of two different
    dominant chords a tritone apart (the classical tritone-substitution pair).

    We find all roots r in 0..11 such that:
        { (r+4) mod 12, (r+10) mod 12 } == axis

    Returns a list of pitch classes (usually length 2).
    """
    a, b = sorted((axis[0] % 12, axis[1] % 12))
    if not is_tritone_pair(a, b):
        raise ValueError(f"Not a valid tritone axis: {axis!r}")

    roots: list[PitchClass] = []
    for r in range(12):
        third = (r + 4) % 12
        seventh = (r + 10) % 12
        if sorted((third, seventh)) == [a, b]:
            roots.append(r)

    return sorted(set(roots))


def gravity_chain(root: PitchClass, steps: int) -> list[PitchClass]:
    """
    Generate a functional gravity chain by descending perfect fourths:

        R_{n+1} = (R_n - 5) mod 12  [descending perfect 4th]

    This corresponds to the classical dominant cycle:
        G(7) -> C(2) -> F(9) -> Bb(4) -> ...

    Wait, let me recalculate:
    - G (7) down a perfect 4th (5 semitones) = 7-5 = 2 (D), not C!

    Actually, the traditional cycle of fifths DESCENDS:
    - C -> F (down 5 semitones, or up 7 semitones)

    But in jazz theory, we often talk about "descending in fourths" meaning
    roots moving DOWN by 5 semitones: G -> C -> F -> Bb

    G(7) - 7 = 0 (C) ✓
    C(0) - 7 = -7 = 5 (F) ✓
    F(5) - 7 = -2 = 10 (Bb) ✓

    Parameters
    ----------
    root:
        Starting root pitch class (0-11).
    steps:
        Number of steps to generate (non-negative).

    Returns
    -------
    list of pitch classes representing the chain.
    """
    r = root % 12
    chain: list[PitchClass] = [r]
    for _ in range(steps):
        r = (r - 7) % 12  # Move down by perfect 5th (7 semitones)
        chain.append(r)
    return chain
