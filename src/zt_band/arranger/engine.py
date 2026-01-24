# zt_band/arranger/engine.py
"""
Pattern selection engine.

Deterministic selection: filter by family/density, then stable-pick using hash.
"""
from __future__ import annotations

import hashlib
from typing import Any, Protocol, Sequence, runtime_checkable

from zt_band.arranger.selection_request import PatternSelectionRequest


@runtime_checkable
class PatternLike(Protocol):
    """
    Minimal protocol for patterns. Your actual Pattern class
    should have at least these attributes (or adapt as needed).
    """

    @property
    def family(self) -> str:
        ...

    @property
    def id(self) -> str:
        ...


def choose_pattern(
    patterns: Sequence[Any],
    req: PatternSelectionRequest,
) -> Any:
    """
    Deterministic pattern selection: filter then stable-pick.

    Args:
        patterns: Sequence of pattern objects (should have 'family' attribute).
        req: PatternSelectionRequest from arranger adapter.

    Returns:
        Selected pattern (or first pattern if no match).

    Raises:
        ValueError: If patterns is empty.
    """
    if not patterns:
        raise ValueError("patterns sequence cannot be empty")

    # 1) Filter by family
    candidates = [p for p in patterns if getattr(p, "family", None) == req.family]
    if not candidates:
        candidates = list(patterns)

    # 2) Filter by density capability if available
    # Patterns may have max_density: 0=sparse, 1=normal, 2=dense
    density_level = {"sparse": 0, "normal": 1, "dense": 2}.get(req.density, 1)
    filtered_by_density = [
        p
        for p in candidates
        if density_level <= getattr(p, "max_density", 2)
    ]
    if filtered_by_density:
        candidates = filtered_by_density

    # 3) Filter by energy if available
    # Patterns may have min_energy/max_energy
    energy_level = {"low": 0, "mid": 1, "high": 2}.get(req.energy, 1)
    filtered_by_energy = [
        p
        for p in candidates
        if getattr(p, "min_energy", 0) <= energy_level <= getattr(p, "max_energy", 2)
    ]
    if filtered_by_energy:
        candidates = filtered_by_energy

    # 4) Deterministic pick among equals using a stable hash
    h = hashlib.sha256(
        f"{req.seed}|{req.family}|{req.density}|{req.energy}".encode("utf-8")
    ).hexdigest()
    idx = int(h[:8], 16) % max(1, len(candidates))

    return candidates[idx]


def choose_pattern_id(
    patterns: Sequence[Any],
    req: PatternSelectionRequest,
) -> str:
    """
    Like choose_pattern, but returns the pattern's id.

    Useful for testing and governance.
    """
    pattern = choose_pattern(patterns, req)
    return getattr(pattern, "id", str(patterns.index(pattern)))
