# zt_band/adapters/groove_intent_adapter.py
"""
Groove Intent Adapter: Maps GrooveControlIntentV1 to MidiControlPlan.

This is the canonical translation layer between the Groove Layer's
prescriptive intent and zt-band's MIDI output.

Usage:
    from zt_band.adapters import build_midi_control_plan

    plan = build_midi_control_plan(intent_dict)
    # plan.cc_messages -> send to MIDI port
    # plan.clock_mode -> configure clock behavior
    # plan.humanize_ms -> scheduler jitter
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Tuple

from .default_map import MidiControlMap, DEFAULT_MAP
from .midi_control_plan import MidiControlPlan


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _to_cc_0_127(x01: float) -> int:
    """
    Convert 0..1 float to MIDI CC 0..127, rounding safely.
    """
    x01 = _clamp(x01, 0.0, 1.0)
    return int(round(x01 * 127.0))


def _to_cc_signed_ms(ms: float, max_abs_ms: float = 250.0) -> int:
    """
    Map signed ms in [-max_abs_ms, +max_abs_ms] to CC [0..127] with 64 as center.
    -max => 0, 0 => 64, +max => 127
    """
    ms = _clamp(ms, -max_abs_ms, max_abs_ms)
    # normalize to 0..1
    x01 = (ms + max_abs_ms) / (2.0 * max_abs_ms)
    return _to_cc_0_127(x01)


def _drift_mode_to_cc(mode: str) -> int:
    """
    Encode drift correction mode as coarse CC:
      none=0, soft=64, aggressive=127
    """
    if mode == "none":
        return 0
    if mode == "soft":
        return 64
    return 127


def build_midi_control_plan(
    intent: Dict[str, Any],
    control_map: MidiControlMap = DEFAULT_MAP,
    *,
    # Policy knobs (safe defaults)
    max_humanize_ms: float = 30.0,
    max_microshift_ms: float = 30.0,
) -> MidiControlPlan:
    """
    Convert GrooveControlIntentV1 payload -> MidiControlPlan.

    Assumptions:
      - intent schema matches groove_control_intent_v1
      - zt-band will apply this plan at bar boundaries (recommended) to avoid jitter.

    Args:
        intent: Dict matching groove_control_intent_v1.schema.json
        control_map: MIDI CC assignment map (default: DEFAULT_MAP)
        max_humanize_ms: Maximum humanization jitter in ms
        max_microshift_ms: Maximum microshift offset in ms

    Returns:
        MidiControlPlan ready for zt-band to apply
    """
    # --- Required sections per schema ---
    tempo = intent["tempo"]
    timing = intent["timing"]
    dynamics = intent["dynamics"]
    recovery = intent["recovery"]

    control_modes: List[str] = intent.get("control_modes", ["follow"])
    reason_codes: List[str] = intent.get("reason_codes", []) or []

    target_bpm = float(tempo["target_bpm"])
    lock_strength = float(tempo["lock_strength"])
    drift_correction = str(tempo["drift_correction"])

    microshift_ms = float(timing["microshift_ms"])
    anticipation_bias = str(timing["anticipation_bias"])  # noqa: F841 (reserved for future)

    assist_gain = float(dynamics["assist_gain"])
    expression_window = float(dynamics["expression_window"])

    recovery_enabled = bool(recovery["enabled"])
    grace_beats = float(recovery["grace_beats"])

    # --- Choose clock mode ---
    # follow = do not generate clock; master = generate clock
    # Practical: use master when stabilize/challenge/recover, follow when follow/assist.
    if "stabilize" in control_modes or "challenge" in control_modes or "recover" in control_modes:
        clock_mode: Literal["none", "midi_clock_follow", "midi_clock_master"] = "midi_clock_master"
    else:
        clock_mode = "midi_clock_follow"

    # --- Derive humanize + microshift knobs ---
    # humanize_ms correlates with expression_window and reduced lock_strength:
    # - tight lock => small humanize
    # - higher expression_window => larger humanize
    humanize_ms = (expression_window * (1.0 - lock_strength)) * max_humanize_ms
    humanize_ms = _clamp(humanize_ms, 0.0, max_humanize_ms)

    # global microshift bounded (separate from CC encoding)
    global_microshift_ms = _clamp(microshift_ms, -max_microshift_ms, max_microshift_ms)

    # --- Derive humanize seed and enable flag ---
    # Stable seed from profile_id (consistent jitter across intents for same player)
    profile_id = str(intent.get("profile_id", "gp_unknown"))
    humanize_seed = profile_id

    # Auto-disable humanize when hard locked (lock_strength >= 0.95)
    humanize_enabled = lock_strength < 0.95

    # --- Emit CC messages ---
    st = control_map.status_cc()
    cc_msgs: List[Tuple[int, int, int]] = []

    # Tightness: 0 loose .. 127 tight
    cc_msgs.append((st, control_map.cc_tightness, _to_cc_0_127(lock_strength)))

    # Humanize: 0 none .. 127 max_humanize_ms
    cc_msgs.append((st, control_map.cc_humanize, _to_cc_0_127(humanize_ms / max_humanize_ms if max_humanize_ms else 0.0)))

    # Assist gain: 0..1 -> 0..127
    cc_msgs.append((st, control_map.cc_assist_gain, _to_cc_0_127(assist_gain)))

    # Expression window: 0..1 -> 0..127
    cc_msgs.append((st, control_map.cc_expression_window, _to_cc_0_127(expression_window)))

    # Drift correction mode -> coarse CC
    cc_msgs.append((st, control_map.cc_drift_correction, _drift_mode_to_cc(drift_correction)))

    # Recovery enable -> CC on/off (0 or 127)
    cc_msgs.append((st, control_map.cc_recovery_enable, 127 if recovery_enabled else 0))

    # Optional: encode signed microshift to a spare CC via extensions if you want later.
    # For now: use global_microshift_ms internally (scheduler offsets), not CC.

    # Routing hint (optional): the adapter can include where to apply (e.g., "band", "click", "bass")
    routing = intent.get("extensions", {}).get("routing", {}) if isinstance(intent.get("extensions", {}), dict) else {}

    return MidiControlPlan(
        clock_mode=clock_mode,
        target_bpm=target_bpm,
        humanize_ms=humanize_ms,
        humanize_seed=humanize_seed,
        humanize_enabled=humanize_enabled,
        global_microshift_ms=global_microshift_ms,
        assist_gain=assist_gain,
        expression_window=expression_window,
        recovery_enabled=recovery_enabled,
        grace_beats=grace_beats,
        cc_messages=cc_msgs,
        reason_codes=list(reason_codes),
        routing=routing if isinstance(routing, dict) else {},
    )
