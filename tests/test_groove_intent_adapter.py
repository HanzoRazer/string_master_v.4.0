# tests/test_groove_intent_adapter.py
"""
Tests for the Groove Intent -> MIDI Control Plan adapter.
"""
from zt_band.adapters.groove_intent_adapter import build_midi_control_plan
from zt_band.adapters.midi_control_plan import MidiControlPlan
from zt_band.adapters.default_map import DEFAULT_MAP


def _make_intent(
    *,
    control_modes=None,
    target_bpm=92,
    lock_strength=0.75,
    drift_correction="soft",
    microshift_ms=-18.0,
    anticipation_bias="ahead",
    assist_gain=0.6,
    expression_window=0.4,
    recovery_enabled=True,
    grace_beats=2.0,
    reason_codes=None,
):
    """Helper to build test intent payloads."""
    return {
        "schema_id": "groove_control_intent",
        "schema_version": "v1",
        "intent_id": "gci_000001",
        "profile_id": "gp_000001",
        "generated_at_utc": "2026-01-22T22:41:10Z",
        "horizon_ms": 2000,
        "confidence": 0.8,
        "control_modes": control_modes or ["stabilize"],
        "tempo": {
            "target_bpm": target_bpm,
            "lock_strength": lock_strength,
            "drift_correction": drift_correction,
        },
        "timing": {
            "microshift_ms": microshift_ms,
            "anticipation_bias": anticipation_bias,
        },
        "dynamics": {
            "assist_gain": assist_gain,
            "expression_window": expression_window,
        },
        "recovery": {
            "enabled": recovery_enabled,
            "grace_beats": grace_beats,
        },
        "reason_codes": reason_codes or ["tempo_drift"],
    }


def test_intent_to_plan_ccs_and_bounds():
    """Basic adapter test: CC messages present and values in range."""
    intent = _make_intent()
    plan = build_midi_control_plan(intent)

    assert isinstance(plan, MidiControlPlan)
    assert plan.clock_mode == "midi_clock_master"
    assert plan.target_bpm == 92.0
    assert -30.0 <= plan.global_microshift_ms <= 30.0
    assert 0.0 <= plan.humanize_ms <= 30.0

    # CC messages present
    assert len(plan.cc_messages) >= 6
    status, cc, val = plan.cc_messages[0]
    assert (status & 0xF0) == 0xB0
    assert 0 <= val <= 127


def test_clock_mode_follow_for_passive_modes():
    """Follow/assist modes should use midi_clock_follow."""
    intent = _make_intent(control_modes=["follow"])
    plan = build_midi_control_plan(intent)
    assert plan.clock_mode == "midi_clock_follow"

    intent = _make_intent(control_modes=["assist"])
    plan = build_midi_control_plan(intent)
    assert plan.clock_mode == "midi_clock_follow"


def test_clock_mode_master_for_active_modes():
    """Stabilize/challenge/recover modes should use midi_clock_master."""
    for mode in ["stabilize", "challenge", "recover"]:
        intent = _make_intent(control_modes=[mode])
        plan = build_midi_control_plan(intent)
        assert plan.clock_mode == "midi_clock_master", f"Expected master for {mode}"


def test_recovery_cc_encoding():
    """Recovery enabled/disabled maps to CC 0 or 127."""
    intent_on = _make_intent(recovery_enabled=True)
    plan_on = build_midi_control_plan(intent_on)

    intent_off = _make_intent(recovery_enabled=False)
    plan_off = build_midi_control_plan(intent_off)

    # Find recovery CC in messages
    recovery_cc = DEFAULT_MAP.cc_recovery_enable
    val_on = next(v for (_, c, v) in plan_on.cc_messages if c == recovery_cc)
    val_off = next(v for (_, c, v) in plan_off.cc_messages if c == recovery_cc)

    assert val_on == 127
    assert val_off == 0


def test_drift_correction_cc_encoding():
    """Drift correction modes encode to 0/64/127."""
    for mode, expected in [("none", 0), ("soft", 64), ("aggressive", 127)]:
        intent = _make_intent(drift_correction=mode)
        plan = build_midi_control_plan(intent)

        drift_cc = DEFAULT_MAP.cc_drift_correction
        val = next(v for (_, c, v) in plan.cc_messages if c == drift_cc)
        assert val == expected, f"Expected {expected} for {mode}, got {val}"


def test_humanize_scales_with_expression_and_lock():
    """Humanize should be higher with high expression_window and low lock_strength."""
    # High lock = low humanize
    intent_tight = _make_intent(lock_strength=1.0, expression_window=1.0)
    plan_tight = build_midi_control_plan(intent_tight)
    assert plan_tight.humanize_ms == 0.0

    # Low lock + high expression = high humanize
    intent_loose = _make_intent(lock_strength=0.0, expression_window=1.0)
    plan_loose = build_midi_control_plan(intent_loose)
    assert plan_loose.humanize_ms == 30.0  # max_humanize_ms default


def test_microshift_clamping():
    """Microshift should be clamped to max_microshift_ms bounds."""
    intent_extreme = _make_intent(microshift_ms=500.0)
    plan = build_midi_control_plan(intent_extreme)
    assert plan.global_microshift_ms == 30.0  # clamped to max

    intent_negative = _make_intent(microshift_ms=-500.0)
    plan = build_midi_control_plan(intent_negative)
    assert plan.global_microshift_ms == -30.0  # clamped to -max


def test_reason_codes_passthrough():
    """Reason codes should pass through to the plan."""
    intent = _make_intent(reason_codes=["tempo_drift", "fatigue"])
    plan = build_midi_control_plan(intent)
    assert plan.reason_codes == ["tempo_drift", "fatigue"]


def test_as_dict_serialization():
    """Plan should serialize to dict cleanly."""
    intent = _make_intent()
    plan = build_midi_control_plan(intent)
    d = plan.as_dict()

    assert d["clock_mode"] == "midi_clock_master"
    assert d["target_bpm"] == 92.0
    assert isinstance(d["cc_messages"], list)
    assert "reason_codes" in d
