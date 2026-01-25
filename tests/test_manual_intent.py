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


class TestCLIParsing:
    """Test CLI argument parsing for band controls."""

    def test_parse_mode(self):
        from zt_band.rt_playlist import _parse_band_control_args

        args = _parse_band_control_args(["--mode", "challenge"])
        assert args.mode == "challenge"

    def test_parse_tightness(self):
        from zt_band.rt_playlist import _parse_band_control_args

        args = _parse_band_control_args(["--tightness", "0.95"])
        assert args.tightness == 0.95

    def test_parse_humanize_ms(self):
        from zt_band.rt_playlist import _parse_band_control_args

        args = _parse_band_control_args(["--humanize-ms", "3.5"])
        assert args.humanize_ms == 3.5

    def test_parse_multiple_args(self):
        from zt_band.rt_playlist import _parse_band_control_args

        args = _parse_band_control_args([
            "--mode", "stabilize",
            "--tightness", "0.9",
            "--expression", "0.3",
            "--assist", "0.7",
        ])
        assert args.mode == "stabilize"
        assert args.tightness == 0.9
        assert args.expression == 0.3
        assert args.assist == 0.7

    def test_unknown_args_ignored(self):
        from zt_band.rt_playlist import _parse_band_control_args

        # Should not raise
        args = _parse_band_control_args(["playlist.yaml", "--unknown-flag", "value", "--mode", "follow"])
        assert args.mode == "follow"

    def test_cli_controls_from_args(self):
        from zt_band.rt_playlist import _manual_controls_from_cli

        controls = _manual_controls_from_cli([
            "--mode", "challenge",
            "--tightness", "0.2",
            "--expression", "0.85",
            "--assist", "0.95",
            "--humanize-ms", "6.0",
        ])

        assert controls.mode == "challenge"
        assert controls.tightness == 0.2
        assert controls.expression == 0.85
        assert controls.assist == 0.95
        assert controls.humanize_ms == 6.0

    def test_cli_defaults(self):
        from zt_band.rt_playlist import _manual_controls_from_cli

        # With no args, should get defaults
        controls = _manual_controls_from_cli([])

        assert controls.mode == "follow"
        assert controls.tightness == 0.6
        assert controls.expression == 0.5


class TestPresets:
    """Test preset expansion and override behavior."""

    def test_preset_tight(self):
        from zt_band.rt_playlist import _manual_controls_from_cli

        controls = _manual_controls_from_cli(["--preset", "tight"])

        assert controls.mode == "stabilize"
        assert controls.tightness == 0.95
        assert controls.expression == 0.30
        assert controls.humanize_ms == 2.0

    def test_preset_loose(self):
        from zt_band.rt_playlist import _manual_controls_from_cli

        controls = _manual_controls_from_cli(["--preset", "loose"])

        assert controls.mode == "follow"
        assert controls.tightness == 0.45
        assert controls.expression == 0.60
        assert controls.humanize_ms == 9.0

    def test_preset_challenge(self):
        from zt_band.rt_playlist import _manual_controls_from_cli

        controls = _manual_controls_from_cli(["--preset", "challenge"])

        assert controls.mode == "challenge"
        assert controls.tightness == 0.20
        assert controls.expression == 0.85
        assert controls.assist == 0.95

    def test_preset_recover(self):
        from zt_band.rt_playlist import _manual_controls_from_cli

        controls = _manual_controls_from_cli(["--preset", "recover"])

        assert controls.mode == "recover"
        assert controls.tightness == 0.70
        assert controls.expression == 0.20
        assert controls.assist == 0.80

    def test_preset_with_override(self):
        from zt_band.rt_playlist import _manual_controls_from_cli

        # Preset + explicit override: override wins
        controls = _manual_controls_from_cli([
            "--preset", "tight",
            "--expression", "0.55",
        ])

        # From preset
        assert controls.mode == "stabilize"
        assert controls.tightness == 0.95
        # Overridden
        assert controls.expression == 0.55

    def test_preset_with_multiple_overrides(self):
        from zt_band.rt_playlist import _manual_controls_from_cli

        controls = _manual_controls_from_cli([
            "--preset", "loose",
            "--humanize-ms", "12.0",
            "--tightness", "0.3",
        ])

        # From preset
        assert controls.mode == "follow"
        assert controls.expression == 0.60
        # Overridden
        assert controls.humanize_ms == 12.0
        assert controls.tightness == 0.3

    def test_list_presets_exits(self):
        from zt_band.rt_playlist import _manual_controls_from_cli
        import pytest

        with pytest.raises(SystemExit) as exc_info:
            _manual_controls_from_cli(["--list-presets"])

        assert exc_info.value.code == 0

    def test_list_presets_prints_all_presets(self, capsys):
        from zt_band.rt_playlist import _print_presets_and_exit
        import pytest

        with pytest.raises(SystemExit):
            _print_presets_and_exit()

        captured = capsys.readouterr()
        assert "tight" in captured.out
        assert "loose" in captured.out
        assert "challenge" in captured.out
        assert "recover" in captured.out
        assert "mode:" in captured.out
        assert "tightness:" in captured.out
