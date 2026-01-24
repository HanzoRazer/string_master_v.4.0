# zt_band/adapters/arranger_control_plan.py
"""
ArrangerControlPlan: Output of the Arranger Intent adapter.

This plan provides arranger-facing controls derived from GrooveControlIntentV1,
bridging the Groove Layer to pattern selection and style density.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


Density = Literal["sparse", "normal", "dense"]
Energy = Literal["low", "mid", "high"]
PatternFamily = Literal["straight", "swing", "shuffle", "free"]
Mode = Literal["follow", "assist", "stabilize", "challenge", "recover"]


@dataclass(frozen=True)
class ArrangerControlPlan:
    """
    Minimal arranger-facing plan derived from GrooveControlIntentV1.

    This is intentionally 'stubby' but stable:
    - stable shape for downstream code
    - deterministic mapping from intent signals
    """
    mode: Mode
    density: Density
    energy: Energy
    pattern_family: PatternFamily

    # continuous controls (0..1 unless noted)
    tightness: float           # alias of lock_strength
    expression_window: float   # from intent.dynamics.expression_window
    assist_gain: float         # from intent.dynamics.assist_gain

    # optional microtiming info for arranger swing choices
    anticipation_bias: Literal["ahead", "behind", "neutral"]
