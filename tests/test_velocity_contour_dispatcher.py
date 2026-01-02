"""
Tests for velocity contour dispatcher (unified entry point).
"""

from zt_band.midi_out import NoteEvent
from zt_band.velocity_contour import VelContour, apply_velocity_contour


def make_note(start: float, velocity: int, channel: int = 0) -> NoteEvent:
    """Helper to create a NoteEvent for testing."""
    return NoteEvent(
        start_beats=start,
        duration_beats=0.25,
        midi_note=60,
        velocity=velocity,
        channel=channel,
    )


class TestDispatcherStrictGates:
    """Tests for dispatcher meter/steps strictness."""

    def test_disabled_contour_returns_unchanged(self):
        """Disabled contour passes through unchanged regardless of meter."""
        contour = VelContour(enabled=False)
        events = [make_note(0.0, 80)]

        result = apply_velocity_contour(
            events, meter="4/4", bar_steps=16, contour=contour
        )

        assert result[0].velocity == 80

    def test_4_4_wrong_bar_steps_returns_unchanged(self):
        """4/4 with bar_steps != 16 returns unchanged."""
        contour = VelContour(enabled=True, soft_mul=0.5)
        events = [make_note(0.0, 80)]  # beat 1 would be soft

        # Wrong bar_steps for 4/4
        result = apply_velocity_contour(
            events, meter="4/4", bar_steps=8, contour=contour
        )

        assert result[0].velocity == 80  # unchanged

    def test_4_4_correct_bar_steps_applies_contour(self):
        """4/4 with bar_steps == 16 applies contour."""
        contour = VelContour(enabled=True, soft_mul=0.5)
        events = [make_note(0.0, 80)]  # beat 1 -> soft

        result = apply_velocity_contour(
            events, meter="4/4", bar_steps=16, contour=contour
        )

        assert result[0].velocity == 40  # 80 * 0.5

    def test_2_4_wrong_bar_steps_returns_unchanged(self):
        """2/4 with bar_steps != 8 returns unchanged."""
        contour = VelContour(enabled=True, soft_mul=0.5)
        events = [make_note(0.0, 80)]

        # Wrong bar_steps for 2/4
        result = apply_velocity_contour(
            events, meter="2/4", bar_steps=16, contour=contour
        )

        assert result[0].velocity == 80  # unchanged

    def test_2_4_correct_bar_steps_applies_contour(self):
        """2/4 with bar_steps == 8 applies contour."""
        contour = VelContour(enabled=True, soft_mul=0.5)
        events = [make_note(0.0, 80)]  # beat 1 -> soft in 2/4

        result = apply_velocity_contour(
            events, meter="2/4", bar_steps=8, contour=contour
        )

        assert result[0].velocity == 40  # 80 * 0.5

    def test_unknown_meter_returns_unchanged(self):
        """Unknown meter returns unchanged (safe fallback)."""
        contour = VelContour(enabled=True, soft_mul=0.5)
        events = [make_note(0.0, 80)]

        result = apply_velocity_contour(
            events, meter="3/4", bar_steps=12, contour=contour
        )

        assert result[0].velocity == 80  # unchanged

    def test_meter_whitespace_stripped(self):
        """Meter string with whitespace is handled."""
        contour = VelContour(enabled=True, soft_mul=0.5)
        events = [make_note(0.0, 80)]

        result = apply_velocity_contour(
            events, meter=" 4/4 ", bar_steps=16, contour=contour
        )

        assert result[0].velocity == 40  # contour applied
