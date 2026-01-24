# tests/test_arranger_runtime_select_pattern.py
"""
Tests for the arranger runtime one-call glue functions.

These tests verify the full chain:
    GrooveControlIntentV1 → ArrangerControlPlan → PatternSelectionRequest → choose_pattern()
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pytest

from zt_band.arranger.runtime import select_pattern_from_intent, select_pattern_with_controls


@dataclass(frozen=True)
class P:
    """Mock pattern for testing."""
    id: str
    family: Literal["straight", "swing", "shuffle", "free"]
    max_density: int = 2
    min_energy: int = 0
    max_energy: int = 2


# ============================================================================
# select_pattern_from_intent tests
# ============================================================================


class TestSelectPatternFromIntent:
    def test_filters_family_density_energy(self):
        """Full chain correctly filters by family, density, and energy."""
        patterns = [
            P(id="A", family="straight", max_density=1, min_energy=0, max_energy=2),
            P(id="B", family="swing", max_density=2, min_energy=0, max_energy=2),
            P(id="C", family="swing", max_density=0, min_energy=0, max_energy=1),
        ]

        # Intent crafted to map to swing family:
        # - follow mode + expression_window >= 0.5 → swing
        # - density should be "normal" (density=1), rejecting C (max_density=0)
        intent = {
            "profile_id": "gp_test",
            "control_modes": ["follow"],
            "tempo": {"lock_strength": 0.4},
            "dynamics": {"assist_gain": 0.7, "expression_window": 0.7},
            "timing": {"anticipation_bias": "neutral"},
        }

        chosen = select_pattern_from_intent(intent, patterns=patterns, seed="seed1")
        assert chosen.family == "swing"
        # C has max_density=0 (too low for normal), so only B remains
        assert chosen.id == "B"

    def test_deterministic_for_same_seed(self):
        """Same seed produces same pattern selection."""
        patterns = [
            P(id="B", family="swing", max_density=2),
            P(id="D", family="swing", max_density=2),
            P(id="E", family="swing", max_density=2),
        ]

        intent = {
            "profile_id": "gp_test",
            "control_modes": ["follow"],
            "tempo": {"lock_strength": 0.4},
            "dynamics": {"assist_gain": 0.7, "expression_window": 0.7},
            "timing": {"anticipation_bias": "neutral"},
        }

        a = select_pattern_from_intent(intent, patterns=patterns, seed="seed1").id
        b = select_pattern_from_intent(intent, patterns=patterns, seed="seed1").id
        assert a == b

    def test_different_seeds_may_differ(self):
        """Different seeds may produce different selections (not guaranteed but likely)."""
        patterns = [
            P(id="B", family="swing", max_density=2),
            P(id="D", family="swing", max_density=2),
            P(id="E", family="swing", max_density=2),
        ]

        intent = {
            "profile_id": "gp_test",
            "control_modes": ["follow"],
            "tempo": {"lock_strength": 0.4},
            "dynamics": {"assist_gain": 0.7, "expression_window": 0.7},
            "timing": {"anticipation_bias": "neutral"},
        }

        a = select_pattern_from_intent(intent, patterns=patterns, seed="seed1").id
        c = select_pattern_from_intent(intent, patterns=patterns, seed="seed2").id
        # Just verify both are valid swing patterns
        assert a in ("B", "D", "E")
        assert c in ("B", "D", "E")

    def test_uses_profile_id_as_default_seed(self):
        """Without explicit seed, falls back to profile_id."""
        patterns = [P(id="X", family="straight", max_density=2)]

        intent = {
            "profile_id": "gp_unique_123",
            "control_modes": ["stabilize"],
            "tempo": {"lock_strength": 0.8},
            "dynamics": {"assist_gain": 0.5, "expression_window": 0.3},
            "timing": {"anticipation_bias": "neutral"},
        }

        # Should work without explicit seed
        chosen = select_pattern_from_intent(intent, patterns=patterns)
        assert chosen.id == "X"

    def test_recover_mode_selects_free_family(self):
        """Recover mode maps to 'free' pattern family."""
        patterns = [
            P(id="straight_1", family="straight"),
            P(id="free_1", family="free"),
        ]

        intent = {
            "profile_id": "gp_test",
            "control_modes": ["recover"],
            "tempo": {"lock_strength": 0.5},
            "dynamics": {"assist_gain": 0.5, "expression_window": 0.5},
            "timing": {"anticipation_bias": "neutral"},
        }

        chosen = select_pattern_from_intent(intent, patterns=patterns, seed="test")
        assert chosen.family == "free"

    def test_challenge_mode_selects_shuffle_family(self):
        """Challenge mode maps to 'shuffle' pattern family."""
        patterns = [
            P(id="straight_1", family="straight"),
            P(id="shuffle_1", family="shuffle"),
        ]

        intent = {
            "profile_id": "gp_test",
            "control_modes": ["challenge"],
            "tempo": {"lock_strength": 0.5},
            "dynamics": {"assist_gain": 0.5, "expression_window": 0.5},
            "timing": {"anticipation_bias": "neutral"},
        }

        chosen = select_pattern_from_intent(intent, patterns=patterns, seed="test")
        assert chosen.family == "shuffle"


# ============================================================================
# select_pattern_with_controls tests
# ============================================================================


class TestSelectPatternWithControls:
    def test_returns_pattern_and_controls(self):
        """Returns both pattern and derived performance controls."""
        patterns = [P(id="X", family="straight", max_density=2)]

        intent = {
            "profile_id": "gp_test",
            "control_modes": ["stabilize"],
            "tempo": {"lock_strength": 0.7},
            "dynamics": {"assist_gain": 0.6, "expression_window": 0.4},
            "timing": {"anticipation_bias": "ahead"},
        }

        pattern, controls = select_pattern_with_controls(intent, patterns=patterns, seed="test")

        assert pattern.id == "X"
        assert controls.tightness == 0.7
        assert controls.assist_gain == 0.6
        assert controls.expression_window == 0.4
        assert controls.anticipation_bias == "ahead"

    def test_controls_humanize_scale_derived(self):
        """Performance controls include derived humanize_scale."""
        patterns = [P(id="X", family="straight")]

        intent = {
            "profile_id": "gp_test",
            "control_modes": ["follow"],
            "tempo": {"lock_strength": 0.0},  # tightness=0 → max humanize
            "dynamics": {"assist_gain": 0.5, "expression_window": 1.0},
            "timing": {"anticipation_bias": "neutral"},
        }

        _, controls = select_pattern_with_controls(intent, patterns=patterns, seed="test")

        # humanize_scale = (1-0)*0.7 + 1.0*0.3 = 1.0
        assert controls.humanize_scale == pytest.approx(1.0)

    def test_controls_accent_strength_derived(self):
        """Performance controls include derived accent_strength."""
        patterns = [P(id="X", family="straight")]

        intent = {
            "profile_id": "gp_test",
            "control_modes": ["assist"],
            "tempo": {"lock_strength": 0.5},
            "dynamics": {"assist_gain": 0.8, "expression_window": 0.5},
            "timing": {"anticipation_bias": "neutral"},
        }

        _, controls = select_pattern_with_controls(intent, patterns=patterns, seed="test")

        # accent = 0.8 * (0.6 + 0.4*(1-0.5)) = 0.8 * 0.8 = 0.64
        assert controls.accent_strength == pytest.approx(0.64)
