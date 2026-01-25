"""
Tests for zt_band.ui.manual_intent module.

Tests the ManualBandControls → GrooveControlIntentV1 builder.
"""

import pytest

from zt_band.ui.manual_intent import (
    ManualBandControls,
    build_groove_intent_from_controls,
    _clamp01,
    _stable_intent_id,
)


class TestClamp01:
    def test_clamp_normal(self):
        assert _clamp01(0.5) == 0.5

    def test_clamp_below_zero(self):
        assert _clamp01(-0.5) == 0.0

    def test_clamp_above_one(self):
        assert _clamp01(1.5) == 1.0

    def test_clamp_zero(self):
        assert _clamp01(0.0) == 0.0

    def test_clamp_one(self):
        assert _clamp01(1.0) == 1.0


class TestStableIntentId:
    def test_deterministic(self):
        id1 = _stable_intent_id("profile_a")
        id2 = _stable_intent_id("profile_a")
        assert id1 == id2

    def test_different_profiles(self):
        id1 = _stable_intent_id("profile_a")
        id2 = _stable_intent_id("profile_b")
        assert id1 != id2

    def test_format(self):
        id1 = _stable_intent_id("test")
        assert id1.startswith("gci_")
        assert len(id1) == 16  # "gci_" + 12 hex chars


class TestManualBandControls:
    def test_defaults(self):
        c = ManualBandControls()
        assert c.mode == "follow"
        assert c.tightness == 0.6
        assert c.assist == 0.6
        assert c.expression == 0.5
        assert c.humanize_ms == 7.5
        assert c.anticipation_bias == "neutral"
        assert c.horizon_ms == 2000
        assert c.confidence == 0.85

    def test_custom_values(self):
        c = ManualBandControls(
            mode="stabilize",
            tightness=0.9,
            assist=0.4,
            expression=0.3,
            humanize_ms=3.0,
            anticipation_bias="ahead",
            horizon_ms=1000,
            confidence=0.95,
        )
        assert c.mode == "stabilize"
        assert c.tightness == 0.9
        assert c.anticipation_bias == "ahead"

    def test_frozen(self):
        c = ManualBandControls()
        with pytest.raises(Exception):  # FrozenInstanceError
            c.mode = "stabilize"  # type: ignore


class TestBuildGrooveIntentFromControls:
    def test_basic_follow(self):
        c = ManualBandControls(mode="follow", tightness=0.5, assist=0.5, expression=0.5)
        intent = build_groove_intent_from_controls(
            controls=c,
            profile_id="test_profile",
            target_bpm=120.0,
        )

        assert intent["schema_id"] == "groove_control_intent"
        assert intent["schema_version"] == "v1"
        assert intent["profile_id"] == "test_profile"
        assert "follow" in intent["control_modes"]
        assert intent["tempo"]["target_bpm"] == 120.0
        assert intent["tempo"]["lock_strength"] == 0.5
        assert intent["dynamics"]["assist_gain"] == 0.5
        assert intent["dynamics"]["expression_window"] == 0.5
        assert intent["timing"]["anticipation_bias"] == "neutral"

    def test_stabilize_mode(self):
        c = ManualBandControls(mode="stabilize", tightness=0.9)
        intent = build_groove_intent_from_controls(
            controls=c,
            profile_id="test",
            target_bpm=100.0,
        )

        assert "stabilize" in intent["control_modes"]
        assert intent["tempo"]["drift_correction"] == "soft"

    def test_recover_mode(self):
        c = ManualBandControls(mode="recover")
        intent = build_groove_intent_from_controls(
            controls=c,
            profile_id="test",
            target_bpm=80.0,
        )

        assert "recover" in intent["control_modes"]
        assert intent["recovery"]["enabled"] is True
        assert intent["tempo"]["drift_correction"] == "aggressive"

    def test_challenge_mode(self):
        c = ManualBandControls(mode="challenge", expression=0.8, assist=0.9)
        intent = build_groove_intent_from_controls(
            controls=c,
            profile_id="test",
            target_bpm=140.0,
        )

        assert "challenge" in intent["control_modes"]
        assert intent["tempo"]["drift_correction"] == "soft"

    def test_assist_mode(self):
        c = ManualBandControls(mode="assist", assist=0.7, expression=0.6)
        intent = build_groove_intent_from_controls(
            controls=c,
            profile_id="test",
            target_bpm=110.0,
        )

        assert "assist" in intent["control_modes"]

    def test_clamping(self):
        c = ManualBandControls(tightness=1.5, assist=-0.2, expression=2.0)
        intent = build_groove_intent_from_controls(
            controls=c,
            profile_id="test",
            target_bpm=120.0,
        )

        assert intent["tempo"]["lock_strength"] == 1.0
        assert intent["dynamics"]["assist_gain"] == 0.0
        assert intent["dynamics"]["expression_window"] == 1.0

    def test_reason_codes(self):
        c = ManualBandControls()
        intent = build_groove_intent_from_controls(
            controls=c,
            profile_id="test",
            target_bpm=120.0,
        )

        assert "manual_ui" in intent["reason_codes"]

    def test_extensions_present(self):
        c = ManualBandControls()
        intent = build_groove_intent_from_controls(
            controls=c,
            profile_id="test",
            target_bpm=120.0,
        )

        assert "extensions" in intent
        assert intent["extensions"] == {}

    def test_secondary_assist_added(self):
        # When assist_gain >= 0.55 and mode is not assist, should add assist to control_modes
        c = ManualBandControls(mode="follow", assist=0.6)
        intent = build_groove_intent_from_controls(
            controls=c,
            profile_id="test",
            target_bpm=120.0,
        )

        assert "follow" in intent["control_modes"]
        assert "assist" in intent["control_modes"]

    def test_secondary_stabilize_added(self):
        # When lock_strength >= 0.65 and mode is follow/assist, should add stabilize
        c = ManualBandControls(mode="follow", tightness=0.7, assist=0.3)
        intent = build_groove_intent_from_controls(
            controls=c,
            profile_id="test",
            target_bpm=120.0,
        )

        assert "follow" in intent["control_modes"]
        assert "stabilize" in intent["control_modes"]


class TestIntentCompatibility:
    """Test that built intents work with arranger adapter."""

    def test_intent_works_with_arranger_adapter(self):
        from zt_band.adapters import build_arranger_control_plan

        c = ManualBandControls(mode="stabilize", tightness=0.9, expression=0.3)
        intent = build_groove_intent_from_controls(
            controls=c,
            profile_id="compat_test",
            target_bpm=120.0,
        )

        plan = build_arranger_control_plan(intent)

        assert plan.mode == "stabilize"
        assert plan.tightness == 0.9
        assert plan.expression_window == 0.3

    def test_all_modes_produce_valid_plans(self):
        from zt_band.adapters import build_arranger_control_plan

        for mode in ("follow", "assist", "stabilize", "challenge", "recover"):
            # Use low assist to prevent secondary modes being added
            c = ManualBandControls(mode=mode, assist=0.3, tightness=0.3)  # type: ignore[arg-type]
            intent = build_groove_intent_from_controls(
                controls=c,
                profile_id=f"test_{mode}",
                target_bpm=120.0,
            )
            plan = build_arranger_control_plan(intent)
            assert plan.mode == mode, f"Expected mode={mode}, got {plan.mode}"
