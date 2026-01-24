# zt_band/adapters/arranger_intent_adapter.py
"""
Arranger Intent Adapter: Maps GrooveControlIntentV1 to ArrangerControlPlan.

This is the canonical translation layer between the Groove Layer's
prescriptive intent and arranger-facing controls (style/density/pattern).

Usage:
    from zt_band.adapters import build_arranger_control_plan

    plan = build_arranger_control_plan(intent_dict)
    # plan.mode          -> primary mode by priority
    # plan.density       -> sparse/normal/dense
    # plan.pattern_family -> straight/swing/shuffle/free
    # plan.energy        -> low/mid/high
"""
from __future__ import annotations

from typing import Any, Dict, List

from .arranger_control_plan import ArrangerControlPlan


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


def _pick_primary_mode(control_modes: List[str]) -> str:
    """
    Deterministic priority: recover > challenge > stabilize > assist > follow.
    """
    priority = ["recover", "challenge", "stabilize", "assist", "follow"]
    s = set(control_modes or [])
    for p in priority:
        if p in s:
            return p
    return "follow"


def build_arranger_control_plan(intent: Dict[str, Any]) -> ArrangerControlPlan:
    """
    GrooveControlIntentV1 -> ArrangerControlPlan (stub v1)

    Deterministic mapping rules:
    - mode: primary mode by priority
    - tightness: intent.tempo.lock_strength
    - expression_window/assist_gain: pass-through
    - pattern_family:
        * stabilize -> straight (or swing only if expression_window high)
        * challenge -> shuffle (more movement)
        * follow/assist -> swing if expression_window >= 0.5 else straight
        * recover -> free (reduce complexity)
    - density:
        * recover -> sparse
        * stabilize -> normal
        * challenge -> dense
        * follow/assist -> normal (or sparse if very low assist_gain)
    - energy:
        * derived from assist_gain + (1 - tightness)
    """
    tempo = intent.get("tempo", {}) or {}
    dynamics = intent.get("dynamics", {}) or {}
    timing = intent.get("timing", {}) or {}

    modes = intent.get("control_modes", []) or []
    mode = _pick_primary_mode([str(m) for m in modes])

    tightness = _clamp01(tempo.get("lock_strength", 0.7))
    expression_window = _clamp01(dynamics.get("expression_window", 0.3))
    assist_gain = _clamp01(dynamics.get("assist_gain", 0.6))

    anticipation_bias = str(timing.get("anticipation_bias", "neutral"))
    if anticipation_bias not in ("ahead", "behind", "neutral"):
        anticipation_bias = "neutral"

    # Pattern family selection
    if mode == "recover":
        pattern_family = "free"
    elif mode == "challenge":
        pattern_family = "shuffle"
    elif mode == "stabilize":
        pattern_family = "swing" if expression_window >= 0.65 else "straight"
    else:  # follow/assist
        pattern_family = "swing" if expression_window >= 0.5 else "straight"

    # Density selection
    if mode == "recover":
        density = "sparse"
    elif mode == "challenge":
        density = "dense"
    elif mode == "stabilize":
        density = "normal"
    else:
        density = "sparse" if assist_gain < 0.35 else "normal"

    # Energy selection (simple continuous heuristic)
    energy_score = (0.6 * assist_gain) + (0.4 * (1.0 - tightness))
    if energy_score < 0.35:
        energy = "low"
    elif energy_score < 0.7:
        energy = "mid"
    else:
        energy = "high"

    return ArrangerControlPlan(
        mode=mode,  # type: ignore[arg-type]
        density=density,  # type: ignore[arg-type]
        energy=energy,  # type: ignore[arg-type]
        pattern_family=pattern_family,  # type: ignore[arg-type]
        tightness=tightness,
        expression_window=expression_window,
        assist_gain=assist_gain,
        anticipation_bias=anticipation_bias,  # type: ignore[arg-type]
    )
