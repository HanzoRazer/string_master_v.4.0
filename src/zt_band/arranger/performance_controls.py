# zt_band/arranger/performance_controls.py
"""
Performance controls derived from selection request.

These are runtime controls directly actionable by the engine,
not contracts. Keep it small and directly actionable.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class PerformanceControls:
    """
    Engine/runtime controls, not a contract.
    Keep it small and directly actionable.
    """

    # 0..1 — copied from request
    tightness: float
    assist_gain: float
    expression_window: float

    # Timing flavor
    anticipation_bias: Literal["ahead", "behind", "neutral"]

    # Convenience knobs derived from above
    humanize_scale: float  # 0..1 (how much to humanize notes)
    accent_strength: float  # 0..1


def derive_controls(
    *,
    tightness: float,
    assist_gain: float,
    expression_window: float,
    anticipation_bias: str,
) -> PerformanceControls:
    """
    Derive performance controls from continuous inputs.

    Derivations:
    - humanize_scale: more tightness = less humanize, more expression = more humanize
    - accent_strength: rises with assist_gain, damped by tightness

    Args:
        tightness: Lock strength 0..1
        assist_gain: Assist gain 0..1
        expression_window: Expression window 0..1
        anticipation_bias: ahead | behind | neutral

    Returns:
        PerformanceControls with derived convenience knobs.
    """
    # Clamp inputs
    tightness = max(0.0, min(1.0, float(tightness)))
    assist_gain = max(0.0, min(1.0, float(assist_gain)))
    expression_window = max(0.0, min(1.0, float(expression_window)))

    if anticipation_bias not in ("ahead", "behind", "neutral"):
        anticipation_bias = "neutral"

    # Derivations:
    # - more tightness = less humanize
    # - more expression window = more humanize
    humanize_scale = max(
        0.0, min(1.0, (1.0 - tightness) * 0.7 + expression_window * 0.3)
    )

    # - accent strength rises with assist_gain, but damped by tightness
    accent_strength = max(
        0.0, min(1.0, assist_gain * (0.6 + 0.4 * (1.0 - tightness)))
    )

    return PerformanceControls(
        tightness=tightness,
        assist_gain=assist_gain,
        expression_window=expression_window,
        anticipation_bias=anticipation_bias,  # type: ignore[arg-type]
        humanize_scale=humanize_scale,
        accent_strength=accent_strength,
    )
