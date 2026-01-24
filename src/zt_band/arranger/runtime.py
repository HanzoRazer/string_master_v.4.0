# zt_band/arranger/runtime.py
"""
Runtime entrypoint for arranger pattern selection.

One-call glue for the full chain:
    GrooveControlIntentV1 → ArrangerControlPlan → PatternSelectionRequest → choose_pattern()
"""
from __future__ import annotations

from typing import Any, Sequence

from zt_band.adapters.arranger_intent_adapter import build_arranger_control_plan
from zt_band.arranger.arranger_engine_adapter import to_selection_request
from zt_band.arranger.engine import choose_pattern
from zt_band.arranger.performance_controls import PerformanceControls, derive_controls


def select_pattern_from_intent(
    intent: dict,
    *,
    patterns: Sequence[Any],
    seed: str | None = None,
) -> Any:
    """
    One-call glue for the runtime loop:

        intent → ArrangerControlPlan → PatternSelectionRequest → choose_pattern()

    Deterministic by default: seed falls back to intent.profile_id if present.

    Args:
        intent: GrooveControlIntentV1 dict.
        patterns: Sequence of pattern objects (must have 'family' attribute).
        seed: Optional explicit seed. Falls back to intent["profile_id"] or "default".

    Returns:
        Selected pattern object.
    """
    plan = build_arranger_control_plan(intent)
    effective_seed = seed or str(intent.get("profile_id", "default"))
    req = to_selection_request(plan, seed=effective_seed)
    return choose_pattern(patterns, req)


def select_pattern_with_controls(
    intent: dict,
    *,
    patterns: Sequence[Any],
    seed: str | None = None,
) -> tuple[Any, PerformanceControls]:
    """
    Like select_pattern_from_intent, but also returns derived PerformanceControls.

    Useful when you need both pattern selection AND runtime knobs (humanize_scale,
    accent_strength, etc.) in one call.

    Args:
        intent: GrooveControlIntentV1 dict.
        patterns: Sequence of pattern objects.
        seed: Optional explicit seed.

    Returns:
        Tuple of (selected_pattern, PerformanceControls).
    """
    plan = build_arranger_control_plan(intent)
    effective_seed = seed or str(intent.get("profile_id", "default"))
    req = to_selection_request(plan, seed=effective_seed)

    pattern = choose_pattern(patterns, req)

    controls = derive_controls(
        tightness=req.tightness,
        assist_gain=req.assist_gain,
        expression_window=req.expression_window,
        anticipation_bias=req.anticipation_bias,
    )

    return pattern, controls
