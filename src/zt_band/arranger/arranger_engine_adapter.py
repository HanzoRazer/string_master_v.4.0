# zt_band/arranger/arranger_engine_adapter.py
"""
Mapper: ArrangerControlPlan → PatternSelectionRequest.

Single-purpose bridge:
- keeps engine insulated from contracts
- keeps mapping logic centralized and governed
"""
from __future__ import annotations

from zt_band.adapters.arranger_control_plan import ArrangerControlPlan
from zt_band.arranger.selection_request import PatternSelectionRequest


def to_selection_request(
    plan: ArrangerControlPlan,
    *,
    seed: str = "default",
) -> PatternSelectionRequest:
    """
    Convert ArrangerControlPlan to engine-facing PatternSelectionRequest.

    Args:
        plan: Governed arranger control plan from intent adapter.
        seed: Deterministic seed for pattern selection (typically profile_id).

    Returns:
        PatternSelectionRequest ready for engine consumption.
    """
    return PatternSelectionRequest(
        family=plan.pattern_family,
        density=plan.density,
        energy=plan.energy,
        tightness=plan.tightness,
        assist_gain=plan.assist_gain,
        expression_window=plan.expression_window,
        anticipation_bias=plan.anticipation_bias,
        seed=seed,
    )
