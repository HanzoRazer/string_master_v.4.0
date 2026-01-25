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


# =============================================================================
# E2E / RUNTIME PERFORMANCE CONTROLS (for scheduling + velocity)
# =============================================================================


def _clamp(x: float, lo: float, hi: float) -> float:
    x = float(x)
    if x < lo:
        return lo
    if x > hi:
        return hi
    return x


@dataclass(frozen=True)
class RuntimePerformanceControls:
    """
    Runtime-facing performance controls derived from arranger plan signals.
    These are not contracts; they are deterministic policy outputs for
    scheduler (humanize) and sender (velocity).
    """
    effective_humanize_ms: float
    velocity_mul: float
    note_bias_ms: float  # signed; applied to note events only (ahead=-/behind=+)


def derive_runtime_performance_controls(
    *,
    base_humanize_ms: float,
    tightness: float,            # 0..1
    expression_window: float,    # 0..1
    assist_gain: float,          # 0..1
    anticipation_bias: str = "neutral",  # "ahead" | "behind" | "neutral"
) -> RuntimePerformanceControls:
    """
    Deterministic policy:

    - Humanize decreases with tightness and increases with expression_window.
    - Velocity assistance increases modestly with assist_gain and decreases with tightness.
    - Note bias applies a subtle push/lay-back offset to note events only.

    All outputs are bounded to stay musically sane and testable.
    """
    tightness = _clamp(tightness, 0.0, 1.0)
    expression_window = _clamp(expression_window, 0.0, 1.0)
    assist_gain = _clamp(assist_gain, 0.0, 1.0)

    # Humanize scaling:
    #   loose factor rises with expression and with (1-tightness)
    loose = 0.5 * expression_window + 0.5 * (1.0 - tightness)
    loose = _clamp(loose, 0.0, 1.0)

    # Keep a small floor so "humanize=on" never fully collapses unless base is 0
    floor = 0.15
    humanize_scale = floor + (1.0 - floor) * loose

    effective_humanize_ms = float(base_humanize_ms) * humanize_scale
    effective_humanize_ms = _clamp(effective_humanize_ms, 0.0, 30.0)

    # Velocity assistance: subtle lift, bounded
    # More assist + more looseness => slightly more energy/clarity.
    raw_mul = 1.0 + 0.25 * assist_gain * (0.6 + 0.4 * (1.0 - tightness))
    velocity_mul = _clamp(raw_mul, 0.85, 1.25)

    # ---- E2E.3: note-only anticipation bias micro-offset (deterministic, bounded) ----
    # Target range: 2..6 ms scaled by looseness, with a tiny floor so it's perceptible.
    # Tightness reduces it; expression/looseness increases it.
    # ahead  => negative (earlier)
    # behind => positive (later)
    # neutral => 0
    bias = anticipation_bias if anticipation_bias in ("ahead", "behind", "neutral") else "neutral"

    # 2–6ms scale driven by loose (0..1)
    amp_ms = 2.0 + 4.0 * loose

    if bias == "ahead":
        note_bias_ms = -amp_ms
    elif bias == "behind":
        note_bias_ms = amp_ms
    else:
        note_bias_ms = 0.0

    # Absolute bound (extra safety)
    note_bias_ms = _clamp(note_bias_ms, -6.0, 6.0)

    return RuntimePerformanceControls(
        effective_humanize_ms=effective_humanize_ms,
        velocity_mul=velocity_mul,
        note_bias_ms=float(note_bias_ms),
    )

