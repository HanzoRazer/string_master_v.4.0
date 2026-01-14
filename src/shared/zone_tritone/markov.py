from __future__ import annotations

import random

from .types import Matrix, PitchClass, RootSequence


def build_transition_counts(roots: RootSequence) -> list[list[int]]:
    """
    Build a 12x12 count matrix from a sequence of root pitch classes.

    counts[i][j] = number of observed transitions i -> j.

    roots: sequence of integers 0-11.
    """
    counts: list[list[int]] = [[0 for _ in range(12)] for _ in range(12)]
    if len(roots) < 2:
        return counts

    prev = roots[0] % 12
    for r in roots[1:]:
        cur = r % 12
        counts[prev][cur] += 1
        prev = cur
    return counts


def normalize_transition_matrix(
    counts: list[list[int]],
    smoothing: float = 0.0,
) -> Matrix:
    """
    Convert a 12x12 count matrix into a row-stochastic probability matrix.

    Parameters
    ----------
    counts:
        12x12 non-negative integer counts.
    smoothing:
        Optional Laplace smoothing value added to each cell before normalization.
    """
    matrix: Matrix = [[0.0 for _ in range(12)] for _ in range(12)]
    for i in range(12):
        row = counts[i]
        row_sum = float(sum(row) + smoothing * 12)
        if row_sum == 0.0:
            # Default to uniform distribution if no transitions observed
            for j in range(12):
                matrix[i][j] = 1.0 / 12.0
        else:
            for j in range(12):
                matrix[i][j] = (row[j] + smoothing) / row_sum
    return matrix


def sample_next_root(
    current: PitchClass,
    matrix: Matrix,
    rng: random.Random | None = None,
) -> PitchClass:
    """
    Sample the next dominant root from a Markov transition matrix.

    Parameters
    ----------
    current:
        Current root pitch class (0-11).
    matrix:
        Row-stochastic 12x12 probability matrix.
    rng:
        Optional Random instance for reproducible sampling.

    Returns
    -------
    int:
        Next root pitch class (0-11).
    """
    if rng is None:
        rng = random

    row = matrix[current % 12]
    # Sampling via cumulative sum
    x = rng.random()
    cumulative = 0.0
    for j, p in enumerate(row):
        cumulative += p
        if x <= cumulative:
            return j
    # Fallback in case of floating point quirks
    return 11
