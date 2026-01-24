# tests/test_arranger_engine.py
"""
Tests for the arranger engine wiring (Ship D.1).

Tests cover:
- PatternSelectionRequest creation from ArrangerControlPlan
- PerformanceControls derivation
- Deterministic pattern selection
"""
from __future__ import annotations

import pytest
from dataclasses import dataclass
from typing import Literal

from zt_band.adapters.arranger_control_plan import ArrangerControlPlan
from zt_band.arranger import (
    PatternSelectionRequest,
    to_selection_request,
    PerformanceControls,
    derive_controls,
    choose_pattern,
)


# ============================================================================
# Test fixtures
# ============================================================================


@dataclass(frozen=True)
class MockPattern:
    """Mock pattern for testing."""
    id: str
    family: str
    max_density: int = 2  # 0=sparse, 1=normal, 2=dense
    min_energy: int = 0
    max_energy: int = 2


MOCK_PATTERNS = [
    MockPattern(id="straight_sparse", family="straight", max_density=0),
    MockPattern(id="straight_normal", family="straight", max_density=1),
    MockPattern(id="straight_dense", family="straight", max_density=2),
    MockPattern(id="swing_mid", family="swing", max_density=1, min_energy=1, max_energy=2),
    MockPattern(id="shuffle_any", family="shuffle", max_density=2),
    MockPattern(id="free_sparse", family="free", max_density=0),
    MockPattern(id="free_expressive", family="free", max_density=2, min_energy=1, max_energy=2),
]


def make_plan(
    mode: str = "follow",
    density: str = "normal",
    energy: str = "mid",
    pattern_family: str = "straight",
    tightness: float = 0.5,
    expression_window: float = 0.4,
    assist_gain: float = 0.6,
    anticipation_bias: str = "neutral",
) -> ArrangerControlPlan:
    return ArrangerControlPlan(
        mode=mode,  # type: ignore[arg-type]
        density=density,  # type: ignore[arg-type]
        energy=energy,  # type: ignore[arg-type]
        pattern_family=pattern_family,  # type: ignore[arg-type]
        tightness=tightness,
        expression_window=expression_window,
        assist_gain=assist_gain,
        anticipation_bias=anticipation_bias,  # type: ignore[arg-type]
    )


# ============================================================================
# to_selection_request tests
# ============================================================================


class TestToSelectionRequest:
    def test_basic_conversion(self):
        plan = make_plan(pattern_family="swing", density="dense", energy="high")
        req = to_selection_request(plan, seed="test_seed")

        assert req.family == "swing"
        assert req.density == "dense"
        assert req.energy == "high"
        assert req.seed == "test_seed"

    def test_continuous_controls_passed_through(self):
        plan = make_plan(tightness=0.8, assist_gain=0.3, expression_window=0.7)
        req = to_selection_request(plan)

        assert req.tightness == 0.8
        assert req.assist_gain == 0.3
        assert req.expression_window == 0.7

    def test_anticipation_bias_passed_through(self):
        plan = make_plan(anticipation_bias="ahead")
        req = to_selection_request(plan)
        assert req.anticipation_bias == "ahead"

    def test_default_seed(self):
        plan = make_plan()
        req = to_selection_request(plan)
        assert req.seed == "default"


# ============================================================================
# derive_controls tests
# ============================================================================


class TestDeriveControls:
    def test_high_tightness_low_humanize(self):
        """High tightness → low humanize scale."""
        controls = derive_controls(
            tightness=1.0,
            assist_gain=0.5,
            expression_window=0.0,
            anticipation_bias="neutral",
        )
        # humanize_scale = (1-1.0)*0.7 + 0.0*0.3 = 0.0
        assert controls.humanize_scale == pytest.approx(0.0)

    def test_low_tightness_high_humanize(self):
        """Low tightness + high expression → high humanize scale."""
        controls = derive_controls(
            tightness=0.0,
            assist_gain=0.5,
            expression_window=1.0,
            anticipation_bias="neutral",
        )
        # humanize_scale = (1-0.0)*0.7 + 1.0*0.3 = 1.0
        assert controls.humanize_scale == pytest.approx(1.0)

    def test_accent_strength_formula(self):
        """accent = assist_gain * (0.6 + 0.4*(1-tightness))"""
        controls = derive_controls(
            tightness=0.5,
            assist_gain=0.8,
            expression_window=0.5,
            anticipation_bias="neutral",
        )
        # accent = 0.8 * (0.6 + 0.4*0.5) = 0.8 * 0.8 = 0.64
        assert controls.accent_strength == pytest.approx(0.64)

    def test_values_clamped(self):
        """Out-of-range inputs are clamped to 0..1."""
        controls = derive_controls(
            tightness=2.0,
            assist_gain=-0.5,
            expression_window=1.5,
            anticipation_bias="neutral",
        )
        assert controls.tightness == 1.0
        assert controls.assist_gain == 0.0
        assert controls.expression_window == 1.0

    def test_invalid_anticipation_bias_defaults_neutral(self):
        controls = derive_controls(
            tightness=0.5,
            assist_gain=0.5,
            expression_window=0.5,
            anticipation_bias="invalid",
        )
        assert controls.anticipation_bias == "neutral"

    def test_passthrough_values(self):
        """Original values are preserved (after clamping)."""
        controls = derive_controls(
            tightness=0.7,
            assist_gain=0.4,
            expression_window=0.6,
            anticipation_bias="ahead",
        )
        assert controls.tightness == 0.7
        assert controls.assist_gain == 0.4
        assert controls.expression_window == 0.6
        assert controls.anticipation_bias == "ahead"


# ============================================================================
# choose_pattern tests
# ============================================================================


class TestChoosePattern:
    def test_filters_by_family(self):
        req = PatternSelectionRequest(
            family="swing",
            density="normal",
            energy="mid",
            tightness=0.5,
            assist_gain=0.5,
            expression_window=0.5,
            anticipation_bias="neutral",
            seed="test",
        )
        result = choose_pattern(MOCK_PATTERNS, req)
        assert result.family == "swing"

    def test_filters_by_density(self):
        """sparse density → only patterns with max_density >= 0 (all), but prefer sparse-capable."""
        req = PatternSelectionRequest(
            family="straight",
            density="sparse",
            energy="mid",
            tightness=0.5,
            assist_gain=0.5,
            expression_window=0.5,
            anticipation_bias="neutral",
            seed="test",
        )
        result = choose_pattern(MOCK_PATTERNS, req)
        assert result.family == "straight"
        # Should get straight_sparse, straight_normal, or straight_dense (all >= 0)
        assert result.id in ["straight_sparse", "straight_normal", "straight_dense"]

    def test_deterministic_same_seed(self):
        """Same seed → same pattern selected."""
        req = PatternSelectionRequest(
            family="straight",
            density="normal",
            energy="mid",
            tightness=0.5,
            assist_gain=0.5,
            expression_window=0.5,
            anticipation_bias="neutral",
            seed="deterministic_test",
        )
        result1 = choose_pattern(MOCK_PATTERNS, req)
        result2 = choose_pattern(MOCK_PATTERNS, req)
        assert result1.id == result2.id

    def test_different_seeds_may_differ(self):
        """Different seeds may produce different results (not guaranteed but likely)."""
        req1 = PatternSelectionRequest(
            family="straight",
            density="dense",
            energy="mid",
            tightness=0.5,
            assist_gain=0.5,
            expression_window=0.5,
            anticipation_bias="neutral",
            seed="seed_a",
        )
        req2 = PatternSelectionRequest(
            family="straight",
            density="dense",
            energy="mid",
            tightness=0.5,
            assist_gain=0.5,
            expression_window=0.5,
            anticipation_bias="neutral",
            seed="seed_b",
        )
        # Just ensure both return valid patterns
        result1 = choose_pattern(MOCK_PATTERNS, req1)
        result2 = choose_pattern(MOCK_PATTERNS, req2)
        assert result1.family == "straight"
        assert result2.family == "straight"

    def test_fallback_to_any_when_no_family_match(self):
        """Unknown family falls back to any pattern."""
        patterns_no_exotic = [p for p in MOCK_PATTERNS if p.family != "exotic"]
        req = PatternSelectionRequest(
            family="exotic",  # type: ignore[arg-type]
            density="normal",
            energy="mid",
            tightness=0.5,
            assist_gain=0.5,
            expression_window=0.5,
            anticipation_bias="neutral",
            seed="test",
        )
        result = choose_pattern(MOCK_PATTERNS, req)
        assert result is not None  # Should fall back to any

    def test_raises_on_empty_patterns(self):
        req = PatternSelectionRequest(
            family="straight",
            density="normal",
            energy="mid",
            tightness=0.5,
            assist_gain=0.5,
            expression_window=0.5,
            anticipation_bias="neutral",
            seed="test",
        )
        with pytest.raises(ValueError, match="cannot be empty"):
            choose_pattern([], req)

    def test_energy_filter(self):
        """Patterns with energy constraints should filter appropriately."""
        req = PatternSelectionRequest(
            family="free",
            density="sparse",  # Use sparse to narrow to free_sparse only
            energy="low",
            tightness=0.5,
            assist_gain=0.5,
            expression_window=0.5,
            anticipation_bias="neutral",
            seed="test",
        )
        result = choose_pattern(MOCK_PATTERNS, req)
        # free_sparse: max_density=0 (allows sparse), min_energy=0, max_energy=2
        # free_expressive: max_density=2, min_energy=1 (rejects low)
        # With sparse density, only free_sparse qualifies (max_density=0)
        assert result.id == "free_sparse"


# ============================================================================
# End-to-end integration test
# ============================================================================


class TestEndToEndWiring:
    def test_intent_to_pattern_selection(self):
        """Full chain: ArrangerControlPlan → Request → Pattern → Controls."""
        plan = make_plan(
            mode="stabilize",
            density="normal",
            energy="mid",
            pattern_family="straight",
            tightness=0.7,
            expression_window=0.4,
            assist_gain=0.6,
            anticipation_bias="ahead",
        )

        # Step 1: Plan → Request
        req = to_selection_request(plan, seed="profile_123")
        assert req.family == "straight"
        assert req.seed == "profile_123"

        # Step 2: Request → Pattern
        pattern = choose_pattern(MOCK_PATTERNS, req)
        assert pattern.family == "straight"

        # Step 3: Request → Controls
        controls = derive_controls(
            tightness=req.tightness,
            assist_gain=req.assist_gain,
            expression_window=req.expression_window,
            anticipation_bias=req.anticipation_bias,
        )
        assert controls.tightness == 0.7
        assert controls.anticipation_bias == "ahead"
        # humanize_scale = (1-0.7)*0.7 + 0.4*0.3 = 0.21 + 0.12 = 0.33
        assert controls.humanize_scale == pytest.approx(0.33)
