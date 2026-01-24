# tests/test_arranger_intent_adapter.py
"""
Tests for ArrangerControlPlan adapter: determinism and mapping rules.
"""
from __future__ import annotations

from zt_band.adapters import build_arranger_control_plan


class TestModeMapping:
    """Verify mode priority and selection."""

    def test_recover_has_highest_priority(self) -> None:
        intent = {
            "control_modes": ["follow", "recover", "assist"],
            "tempo": {"lock_strength": 0.8},
            "dynamics": {"assist_gain": 0.4, "expression_window": 0.3},
            "timing": {"anticipation_bias": "neutral"},
        }
        plan = build_arranger_control_plan(intent)
        assert plan.mode == "recover"

    def test_challenge_beats_stabilize(self) -> None:
        intent = {
            "control_modes": ["stabilize", "challenge", "assist"],
            "tempo": {"lock_strength": 0.5},
            "dynamics": {"assist_gain": 0.6, "expression_window": 0.5},
            "timing": {},
        }
        plan = build_arranger_control_plan(intent)
        assert plan.mode == "challenge"

    def test_empty_modes_defaults_to_follow(self) -> None:
        intent = {
            "control_modes": [],
            "tempo": {"lock_strength": 0.5},
            "dynamics": {"assist_gain": 0.6, "expression_window": 0.5},
            "timing": {},
        }
        plan = build_arranger_control_plan(intent)
        assert plan.mode == "follow"


class TestPatternFamilyMapping:
    """Verify pattern family selection rules."""

    def test_recover_maps_to_free(self) -> None:
        intent = {
            "control_modes": ["recover"],
            "tempo": {"lock_strength": 0.8},
            "dynamics": {"assist_gain": 0.4, "expression_window": 0.3},
            "timing": {"anticipation_bias": "neutral"},
        }
        plan = build_arranger_control_plan(intent)
        assert plan.pattern_family == "free"

    def test_challenge_maps_to_shuffle(self) -> None:
        intent = {
            "control_modes": ["challenge"],
            "tempo": {"lock_strength": 0.5},
            "dynamics": {"assist_gain": 0.8, "expression_window": 0.7},
            "timing": {"anticipation_bias": "behind"},
        }
        plan = build_arranger_control_plan(intent)
        assert plan.pattern_family == "shuffle"

    def test_stabilize_low_expression_maps_to_straight(self) -> None:
        intent = {
            "control_modes": ["stabilize"],
            "tempo": {"lock_strength": 0.9},
            "dynamics": {"assist_gain": 0.5, "expression_window": 0.3},
            "timing": {},
        }
        plan = build_arranger_control_plan(intent)
        assert plan.pattern_family == "straight"

    def test_stabilize_high_expression_maps_to_swing(self) -> None:
        intent = {
            "control_modes": ["stabilize"],
            "tempo": {"lock_strength": 0.7},
            "dynamics": {"assist_gain": 0.5, "expression_window": 0.7},
            "timing": {},
        }
        plan = build_arranger_control_plan(intent)
        assert plan.pattern_family == "swing"

    def test_follow_low_expression_maps_to_straight(self) -> None:
        intent = {
            "control_modes": ["follow"],
            "tempo": {"lock_strength": 0.2},
            "dynamics": {"assist_gain": 0.6, "expression_window": 0.2},
            "timing": {"anticipation_bias": "ahead"},
        }
        plan = build_arranger_control_plan(intent)
        assert plan.pattern_family == "straight"

    def test_follow_high_expression_maps_to_swing(self) -> None:
        intent = {
            "control_modes": ["follow"],
            "tempo": {"lock_strength": 0.2},
            "dynamics": {"assist_gain": 0.6, "expression_window": 0.6},
            "timing": {},
        }
        plan = build_arranger_control_plan(intent)
        assert plan.pattern_family == "swing"


class TestDensityMapping:
    """Verify density selection rules."""

    def test_recover_maps_to_sparse(self) -> None:
        intent = {
            "control_modes": ["recover"],
            "tempo": {"lock_strength": 0.5},
            "dynamics": {"assist_gain": 0.9, "expression_window": 0.9},
            "timing": {},
        }
        plan = build_arranger_control_plan(intent)
        assert plan.density == "sparse"

    def test_challenge_maps_to_dense(self) -> None:
        intent = {
            "control_modes": ["challenge"],
            "tempo": {"lock_strength": 0.5},
            "dynamics": {"assist_gain": 0.5, "expression_window": 0.5},
            "timing": {},
        }
        plan = build_arranger_control_plan(intent)
        assert plan.density == "dense"

    def test_stabilize_maps_to_normal(self) -> None:
        intent = {
            "control_modes": ["stabilize"],
            "tempo": {"lock_strength": 0.7},
            "dynamics": {"assist_gain": 0.5, "expression_window": 0.5},
            "timing": {},
        }
        plan = build_arranger_control_plan(intent)
        assert plan.density == "normal"

    def test_follow_low_assist_maps_to_sparse(self) -> None:
        intent = {
            "control_modes": ["follow"],
            "tempo": {"lock_strength": 0.5},
            "dynamics": {"assist_gain": 0.2, "expression_window": 0.5},
            "timing": {},
        }
        plan = build_arranger_control_plan(intent)
        assert plan.density == "sparse"

    def test_follow_normal_assist_maps_to_normal(self) -> None:
        intent = {
            "control_modes": ["follow"],
            "tempo": {"lock_strength": 0.5},
            "dynamics": {"assist_gain": 0.6, "expression_window": 0.5},
            "timing": {},
        }
        plan = build_arranger_control_plan(intent)
        assert plan.density == "normal"


class TestEnergyMapping:
    """Verify energy selection (assist_gain + inverse tightness)."""

    def test_low_energy_tight_low_assist(self) -> None:
        intent = {
            "control_modes": ["follow"],
            "tempo": {"lock_strength": 0.9},  # high tightness
            "dynamics": {"assist_gain": 0.2, "expression_window": 0.5},
            "timing": {},
        }
        plan = build_arranger_control_plan(intent)
        assert plan.energy == "low"

    def test_high_energy_loose_high_assist(self) -> None:
        intent = {
            "control_modes": ["follow"],
            "tempo": {"lock_strength": 0.1},  # low tightness
            "dynamics": {"assist_gain": 0.9, "expression_window": 0.5},
            "timing": {},
        }
        plan = build_arranger_control_plan(intent)
        assert plan.energy == "high"

    def test_mid_energy_balanced(self) -> None:
        intent = {
            "control_modes": ["follow"],
            "tempo": {"lock_strength": 0.5},
            "dynamics": {"assist_gain": 0.5, "expression_window": 0.5},
            "timing": {},
        }
        plan = build_arranger_control_plan(intent)
        assert plan.energy == "mid"


class TestDeterminism:
    """Verify same inputs produce identical outputs."""

    def test_determinism_same_input_same_output(self) -> None:
        intent = {
            "control_modes": ["assist", "stabilize"],
            "tempo": {"lock_strength": 0.7},
            "dynamics": {"assist_gain": 0.9, "expression_window": 0.6},
            "timing": {"anticipation_bias": "neutral"},
        }
        a = build_arranger_control_plan(intent)
        b = build_arranger_control_plan(intent)
        assert a == b

    def test_continuous_values_passthrough(self) -> None:
        intent = {
            "control_modes": ["follow"],
            "tempo": {"lock_strength": 0.73},
            "dynamics": {"assist_gain": 0.42, "expression_window": 0.88},
            "timing": {"anticipation_bias": "ahead"},
        }
        plan = build_arranger_control_plan(intent)
        assert plan.tightness == 0.73
        assert plan.assist_gain == 0.42
        assert plan.expression_window == 0.88
        assert plan.anticipation_bias == "ahead"


class TestEdgeCases:
    """Verify edge case handling."""

    def test_missing_sections_use_defaults(self) -> None:
        intent = {}
        plan = build_arranger_control_plan(intent)
        assert plan.mode == "follow"
        assert plan.tightness == 0.7  # default lock_strength
        assert plan.anticipation_bias == "neutral"

    def test_invalid_anticipation_bias_defaults_to_neutral(self) -> None:
        intent = {
            "control_modes": ["follow"],
            "tempo": {"lock_strength": 0.5},
            "dynamics": {"assist_gain": 0.5, "expression_window": 0.5},
            "timing": {"anticipation_bias": "invalid_value"},
        }
        plan = build_arranger_control_plan(intent)
        assert plan.anticipation_bias == "neutral"

    def test_values_clamped_to_01(self) -> None:
        intent = {
            "control_modes": ["follow"],
            "tempo": {"lock_strength": 1.5},  # over 1
            "dynamics": {"assist_gain": -0.3, "expression_window": 2.0},
            "timing": {},
        }
        plan = build_arranger_control_plan(intent)
        assert plan.tightness == 1.0
        assert plan.assist_gain == 0.0
        assert plan.expression_window == 1.0
