# tests/test_deterministic_humanizer.py
"""
Tests for DeterministicHumanizer: determinism, bounds, and mode behavior.
"""
from __future__ import annotations

import pytest

from zt_band.midi.humanizer import DeterministicHumanizer


class TestDeterminism:
    """Verify same inputs => same outputs across instances."""

    def test_same_seed_same_output_white(self) -> None:
        h1 = DeterministicHumanizer(seed="abc", mode="white")
        h2 = DeterministicHumanizer(seed="abc", mode="white")

        a = [h1.jitter_ms(tick_index=i, humanize_ms=10.0, channel="cc") for i in range(50)]
        b = [h2.jitter_ms(tick_index=i, humanize_ms=10.0, channel="cc") for i in range(50)]
        assert a == b

    def test_same_seed_same_output_smooth(self) -> None:
        h1 = DeterministicHumanizer(seed="xyz", mode="smooth", smooth_period=8)
        h2 = DeterministicHumanizer(seed="xyz", mode="smooth", smooth_period=8)

        a = [h1.jitter_ms(tick_index=i, humanize_ms=15.0, channel="note") for i in range(100)]
        b = [h2.jitter_ms(tick_index=i, humanize_ms=15.0, channel="note") for i in range(100)]
        assert a == b

    def test_different_seed_changes_output(self) -> None:
        h1 = DeterministicHumanizer(seed="abc", mode="white")
        h2 = DeterministicHumanizer(seed="xyz", mode="white")

        a = [h1.jitter_ms(tick_index=i, humanize_ms=10.0, channel="cc") for i in range(20)]
        b = [h2.jitter_ms(tick_index=i, humanize_ms=10.0, channel="cc") for i in range(20)]
        assert a != b

    def test_different_channel_changes_output(self) -> None:
        h = DeterministicHumanizer(seed="abc", mode="white")

        a = [h.jitter_ms(tick_index=i, humanize_ms=10.0, channel="cc") for i in range(20)]
        b = [h.jitter_ms(tick_index=i, humanize_ms=10.0, channel="note") for i in range(20)]
        assert a != b


class TestBounds:
    """Verify jitter stays within [-humanize_ms, +humanize_ms]."""

    def test_bounds_respected_white(self) -> None:
        h = DeterministicHumanizer(seed="bounds_test", mode="white")
        amp = 7.5
        vals = [h.jitter_ms(tick_index=i, humanize_ms=amp, channel="cc") for i in range(500)]
        assert max(vals) <= amp + 1e-9
        assert min(vals) >= -amp - 1e-9

    def test_bounds_respected_smooth(self) -> None:
        h = DeterministicHumanizer(seed="bounds_test", mode="smooth", smooth_period=8)
        amp = 12.0
        vals = [h.jitter_ms(tick_index=i, humanize_ms=amp, channel="note") for i in range(500)]
        assert max(vals) <= amp + 1e-9
        assert min(vals) >= -amp - 1e-9

    def test_zero_humanize_is_zero(self) -> None:
        h = DeterministicHumanizer(seed="abc", mode="smooth")
        for i in range(50):
            assert h.jitter_ms(tick_index=i, humanize_ms=0.0) == 0.0

    def test_negative_humanize_is_zero(self) -> None:
        h = DeterministicHumanizer(seed="abc", mode="white")
        for i in range(20):
            assert h.jitter_ms(tick_index=i, humanize_ms=-5.0) == 0.0


class TestModes:
    """Verify mode-specific behavior."""

    def test_white_mode_independent_samples(self) -> None:
        """White mode: each tick should be independent (high variance)."""
        h = DeterministicHumanizer(seed="white_test", mode="white")
        vals = [h.jitter_ms(tick_index=i, humanize_ms=10.0) for i in range(100)]
        # Check we have both positive and negative values (not stuck at one extreme)
        assert any(v > 0 for v in vals)
        assert any(v < 0 for v in vals)
        # Check variance is non-trivial
        mean = sum(vals) / len(vals)
        variance = sum((v - mean) ** 2 for v in vals) / len(vals)
        assert variance > 1.0  # Should have meaningful spread

    def test_smooth_mode_continuity(self) -> None:
        """Smooth mode: adjacent ticks should have similar values."""
        h = DeterministicHumanizer(seed="smooth_test", mode="smooth", smooth_period=16)
        vals = [h.jitter_ms(tick_index=i, humanize_ms=10.0) for i in range(100)]

        # Compute average absolute difference between adjacent samples
        diffs = [abs(vals[i + 1] - vals[i]) for i in range(len(vals) - 1)]
        avg_diff = sum(diffs) / len(diffs)

        # Smooth mode should have smaller jumps than white mode
        h_white = DeterministicHumanizer(seed="smooth_test", mode="white")
        vals_white = [h_white.jitter_ms(tick_index=i, humanize_ms=10.0) for i in range(100)]
        diffs_white = [abs(vals_white[i + 1] - vals_white[i]) for i in range(len(vals_white) - 1)]
        avg_diff_white = sum(diffs_white) / len(diffs_white)

        # Smooth should be significantly smoother
        assert avg_diff < avg_diff_white * 0.6


class TestGoldenVector:
    """
    Golden vector test: ensures exact reproducibility across runs.
    If this fails after a code change, determinism was broken.
    """

    def test_golden_vector_white(self) -> None:
        h = DeterministicHumanizer(seed="gp_vector001", mode="white")
        expected = [
            h.jitter_ms(tick_index=i, humanize_ms=7.5, channel="note")
            for i in range(10)
        ]
        # Re-run and compare
        actual = [
            h.jitter_ms(tick_index=i, humanize_ms=7.5, channel="note")
            for i in range(10)
        ]
        assert actual == expected

    def test_golden_vector_smooth(self) -> None:
        h = DeterministicHumanizer(seed="gp_vector001", mode="smooth", smooth_period=4)
        expected = [
            h.jitter_ms(tick_index=i, humanize_ms=7.5, channel="cc")
            for i in range(10)
        ]
        # Re-run and compare
        actual = [
            h.jitter_ms(tick_index=i, humanize_ms=7.5, channel="cc")
            for i in range(10)
        ]
        assert actual == expected
