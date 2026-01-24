# zt_band/arranger/selection_request.py
"""
Engine-facing pattern selection request.

This is the stable bridge between governed ArrangerControlPlan
and internal pattern selection logic.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Density = Literal["sparse", "normal", "dense"]
Energy = Literal["low", "mid", "high"]
PatternFamily = Literal["straight", "swing", "shuffle", "free"]


@dataclass(frozen=True)
class PatternSelectionRequest:
    """
    Engine-facing request derived from ArrangerControlPlan.
    This object is the stable bridge to pattern selection.
    """

    family: PatternFamily
    density: Density
    energy: Energy

    # Continuous controls
    tightness: float  # 0..1
    assist_gain: float  # 0..1
    expression_window: float  # 0..1

    # Timing flavor hint
    anticipation_bias: Literal["ahead", "behind", "neutral"]

    # Optional: for deterministic choice among equals (keep stable across runs)
    seed: str = "default"
