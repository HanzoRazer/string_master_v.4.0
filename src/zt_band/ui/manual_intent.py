"""
Manual Band Controls → GrooveControlIntentV1 builder.

This module lets end-users drive the arranger and humanizer
via simple UI knobs (mode, tightness, expression, etc.)
without requiring a Groove Profile analyzer.

Usage:
    controls = ManualBandControls(mode="stabilize", tightness=0.9)
    intent = build_groove_intent_from_controls(
        controls=controls,
        profile_id="my_session",
        target_bpm=120.0,
    )
    # intent is now a GrooveControlIntentV1-shaped dict
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Literal


Mode = Literal["follow", "assist", "stabilize", "challenge", "recover"]
Bias = Literal["ahead", "behind", "neutral"]
Drift = Literal["none", "soft", "aggressive"]


def _clamp01(x: float) -> float:
    """Clamp value to [0.0, 1.0]."""
    x = float(x)
    if x < 0.0:
        return 0.0
    if x > 1.0:
        return 1.0
    return x


def _stable_intent_id(profile_id: str, salt: str = "manual_ui_v1") -> str:
    """Generate a stable intent_id from profile_id."""
    h = hashlib.sha256(f"{salt}:{profile_id}".encode("utf-8")).hexdigest()[:12]
    return f"gci_{h}"


@dataclass(frozen=True)
class ManualBandControls:
    """
    End-user controls (UI knobs). These are *not* the contract.
    We convert these into a GrooveControlIntentV1-shaped dict.

    Attributes:
        mode: Control mode (follow/assist/stabilize/challenge/recover)
        tightness: Maps to lock_strength (0=loose, 1=tight)
        assist: Maps to assist_gain (0=no assist, 1=full assist)
        expression: Maps to expression_window (0=rigid, 1=expressive)
        humanize_ms: Jitter amount for scheduler (not part of intent contract)
        anticipation_bias: Timing feel hint (ahead/behind/neutral)
        horizon_ms: Intent validity window
        confidence: Intent confidence level
    """
    mode: Mode = "follow"
    tightness: float = 0.6          # maps to lock_strength
    assist: float = 0.6             # maps to assist_gain
    expression: float = 0.5         # maps to expression_window
    humanize_ms: float = 7.5        # used by scheduler; not part of intent contract
    anticipation_bias: Bias = "neutral"
    horizon_ms: int = 2000
    confidence: float = 0.85


def build_groove_intent_from_controls(
    *,
    controls: ManualBandControls,
    profile_id: str,
    target_bpm: float,
) -> Dict[str, Any]:
    """
    Build a GrooveControlIntentV1-shaped dict from UI controls.

    This is intentionally minimal: enough for adapters and runtime.
    The output can be consumed by:
    - build_arranger_control_plan()
    - build_midi_control_plan()
    - _maybe_override_style_with_intent()

    Args:
        controls: User-facing knob settings
        profile_id: Identifier for this session/user
        target_bpm: Current tempo

    Returns:
        A dict matching GrooveControlIntentV1 schema shape
    """
    mode = controls.mode
    lock_strength = _clamp01(controls.tightness)
    assist_gain = _clamp01(controls.assist)
    expression_window = _clamp01(controls.expression)

    # Drift correction: simple policy tied to mode (can be tuned later)
    if mode == "stabilize":
        drift_correction: Drift = "soft"
    elif mode == "challenge":
        drift_correction = "soft"
    elif mode == "recover":
        drift_correction = "aggressive"
    else:
        drift_correction = "none" if lock_strength < 0.35 else "soft"

    # control_modes list: keep deterministic and compatible with existing adapters
    control_modes = [mode]
    if mode not in ("assist",) and assist_gain >= 0.55:
        # allow assist to be "on" as a secondary behavior
        control_modes.append("assist")
    if mode != "recover" and mode != "challenge" and mode != "stabilize" and lock_strength >= 0.65:
        control_modes.append("stabilize")
    if mode == "recover":
        control_modes.append("recover")

    # Recovery enabled if mode is recover (manual)
    recovery_enabled = mode == "recover"

    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    return {
        "schema_id": "groove_control_intent",
        "schema_version": "v1",
        "intent_id": _stable_intent_id(profile_id),
        "profile_id": profile_id,
        "generated_at_utc": now,
        "horizon_ms": int(controls.horizon_ms),
        "confidence": _clamp01(controls.confidence),
        "control_modes": control_modes,
        "tempo": {
            "target_bpm": float(target_bpm),
            "lock_strength": float(lock_strength),
            "drift_correction": drift_correction,
        },
        "timing": {
            "microshift_ms": 0.0,
            "anticipation_bias": controls.anticipation_bias,
        },
        "dynamics": {
            "assist_gain": float(assist_gain),
            "expression_window": float(expression_window),
        },
        "recovery": {
            "enabled": bool(recovery_enabled),
            "grace_beats": 2.0 if recovery_enabled else 1.0,
        },
        "reason_codes": ["manual_ui"],
        "extensions": {},
    }
