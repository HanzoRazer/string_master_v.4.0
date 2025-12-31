"""
Tests for velocity contour (Brazilian "breathing" feel).
"""
import pytest

from zt_band.velocity_contour import VelContour, apply_velocity_contour_4_4, apply_velocity_contour_2_4
from zt_band.midi_out import NoteEvent


def make_note(start: float, velocity: int, channel: int = 0) -> NoteEvent:
    """Helper to create a NoteEvent for testing."""
    return NoteEvent(
        start_beats=start,
        duration_beats=0.25,
        midi_note=60,
        velocity=velocity,
        channel=channel,
    )


class TestVelContour4_4:
    """Tests for 4/4 velocity contour."""

    def test_disabled_returns_unchanged(self):
        """When disabled, events pass through unchanged."""
        contour = VelContour(enabled=False)
        events = [make_note(0.0, 80), make_note(1.5, 80)]

        result = apply_velocity_contour_4_4(
            events, bar_steps=16, contour=contour, pickup_steps=set(), ghost_steps=set()
        )

        assert len(result) == 2
        assert result[0].velocity == 80
        assert result[1].velocity == 80

    def test_soft_beats_scaled_down(self):
        """Beat 1 and 3 (steps 0, 8) should be scaled down by soft_mul."""
        contour = VelContour(enabled=True, soft_mul=0.5, strong_mul=1.0)
        events = [
            make_note(0.0, 100),  # beat 1 -> step 0 -> soft
            make_note(2.0, 100),  # beat 3 -> step 8 -> soft
        ]

        result = apply_velocity_contour_4_4(
            events, bar_steps=16, contour=contour, pickup_steps=set(), ghost_steps=set()
        )

        assert result[0].velocity == 50  # 100 * 0.5
        assert result[1].velocity == 50  # 100 * 0.5

    def test_strong_beats_scaled_up(self):
        """&2 and &4 (steps 6, 14) should be scaled up by strong_mul."""
        contour = VelContour(enabled=True, soft_mul=1.0, strong_mul=2.0)
        events = [
            make_note(1.5, 60),  # &2 -> step 6 -> strong
            make_note(3.5, 60),  # &4 -> step 14 -> strong
        ]

        result = apply_velocity_contour_4_4(
            events, bar_steps=16, contour=contour, pickup_steps=set(), ghost_steps=set()
        )

        # Both should be scaled up, clamped to 127
        assert result[0].velocity == 120  # 60 * 2.0
        assert result[1].velocity == 120  # 60 * 2.0

    def test_velocity_clamped_to_127(self):
        """Velocity should not exceed 127."""
        contour = VelContour(enabled=True, soft_mul=1.0, strong_mul=2.0)
        events = [make_note(1.5, 80)]  # &2 -> 80 * 2.0 = 160 -> clamp to 127

        result = apply_velocity_contour_4_4(
            events, bar_steps=16, contour=contour, pickup_steps=set(), ghost_steps=set()
        )

        assert result[0].velocity == 127

    def test_velocity_clamped_to_1(self):
        """Velocity should not go below 1."""
        contour = VelContour(enabled=True, soft_mul=0.01)
        events = [make_note(0.0, 10)]  # beat 1 -> 10 * 0.01 = 0.1 -> clamp to 1

        result = apply_velocity_contour_4_4(
            events, bar_steps=16, contour=contour, pickup_steps=set(), ghost_steps=set()
        )

        assert result[0].velocity == 1

    def test_pickup_steps_use_pickup_mul(self):
        """Steps marked as pickup use pickup_mul instead of position-based scaling."""
        contour = VelContour(enabled=True, soft_mul=1.0, strong_mul=1.0, pickup_mul=0.5)
        events = [make_note(3.5, 100)]  # &4 -> step 14

        # Without pickup flag: would be strong (1.0)
        result1 = apply_velocity_contour_4_4(
            events, bar_steps=16, contour=contour, pickup_steps=set(), ghost_steps=set()
        )
        assert result1[0].velocity == 100  # strong_mul = 1.0

        # With pickup flag: uses pickup_mul
        result2 = apply_velocity_contour_4_4(
            events, bar_steps=16, contour=contour, pickup_steps={14}, ghost_steps=set()
        )
        assert result2[0].velocity == 50  # 100 * 0.5

    def test_ghost_steps_apply_ghost_mul(self):
        """Ghost steps get additional ghost_mul applied on top."""
        contour = VelContour(enabled=True, soft_mul=1.0, strong_mul=1.0, ghost_mul=0.5)
        events = [make_note(0.25, 80)]  # step 1 (e of beat 1)

        result = apply_velocity_contour_4_4(
            events, bar_steps=16, contour=contour, pickup_steps=set(), ghost_steps={1}
        )

        # Step 1 is neither soft nor strong, so base mul=1.0, then ghost_mul=0.5
        assert result[0].velocity == 40  # 80 * 1.0 * 0.5

    def test_non_16_step_bar_returns_unchanged(self):
        """Non-16-step grids pass through unchanged (guard clause)."""
        contour = VelContour(enabled=True, soft_mul=0.5)
        events = [make_note(0.0, 100)]

        result = apply_velocity_contour_4_4(
            events, bar_steps=8, contour=contour, pickup_steps=set(), ghost_steps=set()
        )

        assert result[0].velocity == 100  # unchanged

    def test_full_bar_contour(self):
        """Integration test: full bar with soft/strong positions."""
        contour = VelContour(enabled=True, soft_mul=0.80, strong_mul=1.08, pickup_mul=0.65)
        events = [
            make_note(0.0, 75),   # beat 1 -> soft -> 60
            make_note(1.5, 90),   # &2 -> strong -> 97
            make_note(2.0, 75),   # beat 3 -> soft -> 60
            make_note(3.5, 90),   # &4 -> strong -> 97
        ]

        result = apply_velocity_contour_4_4(
            events, bar_steps=16, contour=contour, pickup_steps=set(), ghost_steps=set()
        )

        assert result[0].velocity == 60   # 75 * 0.80
        assert result[1].velocity == 97   # 90 * 1.08
        assert result[2].velocity == 60   # 75 * 0.80
        assert result[3].velocity == 97   # 90 * 1.08


class TestVelContour2_4:
    """Tests for 2/4 velocity contour."""

    def test_disabled_returns_unchanged(self):
        """When disabled, events pass through unchanged."""
        contour = VelContour(enabled=False)
        events = [make_note(0.0, 80)]

        result = apply_velocity_contour_2_4(
            events, bar_steps=8, contour=contour, pickup_steps=set(), ghost_steps=set()
        )

        assert result[0].velocity == 80

    def test_soft_beat_1(self):
        """Beat 1 in 2/4 (step 0) should use soft_mul."""
        contour = VelContour(enabled=True, soft_mul=0.5)
        events = [make_note(0.0, 100)]  # beat 1 -> step 0 -> soft

        result = apply_velocity_contour_2_4(
            events, bar_steps=8, contour=contour, pickup_steps=set(), ghost_steps=set()
        )

        assert result[0].velocity == 50

    def test_strong_and_of_2(self):
        """&2 in 2/4 (step 6) should use strong_mul."""
        contour = VelContour(enabled=True, soft_mul=1.0, strong_mul=2.0)
        events = [make_note(1.5, 50)]  # &2 -> step 6 -> strong

        result = apply_velocity_contour_2_4(
            events, bar_steps=8, contour=contour, pickup_steps=set(), ghost_steps=set()
        )

        assert result[0].velocity == 100  # 50 * 2.0

    def test_non_8_step_bar_returns_unchanged(self):
        """Non-8-step grids pass through unchanged."""
        contour = VelContour(enabled=True, soft_mul=0.5)
        events = [make_note(0.0, 100)]

        result = apply_velocity_contour_2_4(
            events, bar_steps=16, contour=contour, pickup_steps=set(), ghost_steps=set()
        )

        assert result[0].velocity == 100  # unchanged
