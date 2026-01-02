"""
Tests for expressive_swing.py — swing and humanization post-processing.
"""
import pytest

from zt_band.expressive_swing import ExpressiveSpec, apply_expressive
from zt_band.midi_out import NoteEvent


class TestExpressiveSpec:
    def test_default_spec_is_bypass(self):
        spec = ExpressiveSpec()
        assert spec.swing == 0.0
        assert spec.humanize_ms == 0.0
        assert spec.humanize_vel == 0
        assert spec.seed is None

    def test_frozen_dataclass(self):
        spec = ExpressiveSpec(swing=0.5)
        with pytest.raises(AttributeError):
            spec.swing = 0.3  # type: ignore


class TestApplyExpressive:
    def test_bypass_when_all_zero(self):
        events = [
            NoteEvent(start_beats=0.0, duration_beats=1.0, midi_note=60, velocity=80),
            NoteEvent(start_beats=1.0, duration_beats=1.0, midi_note=62, velocity=80),
        ]
        spec = ExpressiveSpec()  # all zeros = bypass
        result = apply_expressive(events, spec=spec, tempo_bpm=120)
        assert len(result) == 2
        assert result[0].start_beats == 0.0
        assert result[1].start_beats == 1.0

    def test_swing_delays_offbeats(self):
        events = [
            NoteEvent(start_beats=0.0, duration_beats=0.5, midi_note=60, velocity=80),  # on beat
            NoteEvent(start_beats=0.5, duration_beats=0.5, midi_note=62, velocity=80),  # offbeat
            NoteEvent(start_beats=1.0, duration_beats=0.5, midi_note=64, velocity=80),  # on beat
            NoteEvent(start_beats=1.5, duration_beats=0.5, midi_note=65, velocity=80),  # offbeat
        ]
        spec = ExpressiveSpec(swing=0.5)  # 50% swing
        result = apply_expressive(events, spec=spec, tempo_bpm=120)

        # On-beat notes should not move
        assert result[0].start_beats == 0.0
        assert result[2].start_beats == 1.0

        # Off-beat notes should be delayed by swing * 0.5 = 0.25 beats
        assert result[1].start_beats == pytest.approx(0.75, abs=1e-6)
        assert result[3].start_beats == pytest.approx(1.75, abs=1e-6)

    def test_max_swing_adds_sixteenth(self):
        events = [
            NoteEvent(start_beats=0.5, duration_beats=0.5, midi_note=60, velocity=80),  # offbeat
        ]
        spec = ExpressiveSpec(swing=1.0)  # max swing
        result = apply_expressive(events, spec=spec, tempo_bpm=120)

        # Max swing adds 0.5 * 1.0 = 0.5 beats (a full 8th note delay)
        assert result[0].start_beats == pytest.approx(1.0, abs=1e-6)

    def test_humanize_timing_with_seed(self):
        events = [
            NoteEvent(start_beats=0.0, duration_beats=1.0, midi_note=60, velocity=80),
            NoteEvent(start_beats=1.0, duration_beats=1.0, midi_note=62, velocity=80),
        ]
        spec = ExpressiveSpec(humanize_ms=10.0, seed=42)
        result1 = apply_expressive(events, spec=spec, tempo_bpm=120)

        # Same seed should give same result
        result2 = apply_expressive(events, spec=spec, tempo_bpm=120)
        assert result1[0].start_beats == result2[0].start_beats
        assert result1[1].start_beats == result2[1].start_beats

    def test_humanize_timing_different_seeds(self):
        events = [
            NoteEvent(start_beats=0.5, duration_beats=1.0, midi_note=60, velocity=80),
        ]
        spec1 = ExpressiveSpec(humanize_ms=50.0, seed=42)
        spec2 = ExpressiveSpec(humanize_ms=50.0, seed=123)

        result1 = apply_expressive(events, spec=spec1, tempo_bpm=120)
        result2 = apply_expressive(events, spec=spec2, tempo_bpm=120)

        # Different seeds should give different results (almost always)
        assert result1[0].start_beats != result2[0].start_beats

    def test_humanize_velocity(self):
        events = [
            NoteEvent(start_beats=0.0, duration_beats=1.0, midi_note=60, velocity=80),
        ]
        spec = ExpressiveSpec(humanize_vel=10, seed=42)
        result = apply_expressive(events, spec=spec, tempo_bpm=120)

        # Velocity should be within +/- 10 of original
        assert 70 <= result[0].velocity <= 90

    def test_velocity_clamped_to_valid_range(self):
        events = [
            NoteEvent(start_beats=0.0, duration_beats=1.0, midi_note=60, velocity=5),   # near min
            NoteEvent(start_beats=1.0, duration_beats=1.0, midi_note=62, velocity=125), # near max
        ]
        spec = ExpressiveSpec(humanize_vel=20, seed=1)
        result = apply_expressive(events, spec=spec, tempo_bpm=120)

        # Both should be clamped to [1, 127]
        assert 1 <= result[0].velocity <= 127
        assert 1 <= result[1].velocity <= 127

    def test_timing_never_negative(self):
        events = [
            NoteEvent(start_beats=0.0, duration_beats=1.0, midi_note=60, velocity=80),
        ]
        # Large jitter that could push time negative
        spec = ExpressiveSpec(humanize_ms=500.0, seed=42)
        result = apply_expressive(events, spec=spec, tempo_bpm=120)

        # Time should never go negative
        assert result[0].start_beats >= 0.0

    def test_preserves_note_duration(self):
        events = [
            NoteEvent(start_beats=0.0, duration_beats=0.75, midi_note=60, velocity=80),
        ]
        spec = ExpressiveSpec(swing=0.3, humanize_ms=5.0, humanize_vel=5, seed=42)
        result = apply_expressive(events, spec=spec, tempo_bpm=120)

        # Duration should be unchanged
        assert result[0].duration_beats == 0.75

    def test_preserves_midi_note(self):
        events = [
            NoteEvent(start_beats=0.5, duration_beats=1.0, midi_note=72, velocity=80),
        ]
        spec = ExpressiveSpec(swing=0.5, humanize_vel=10, seed=42)
        result = apply_expressive(events, spec=spec, tempo_bpm=120)

        # MIDI note should be unchanged
        assert result[0].midi_note == 72

    def test_preserves_channel(self):
        events = [
            NoteEvent(start_beats=0.0, duration_beats=1.0, midi_note=60, velocity=80, channel=5),
        ]
        spec = ExpressiveSpec(swing=0.3)
        result = apply_expressive(events, spec=spec, tempo_bpm=120)

        # Channel should be unchanged
        assert result[0].channel == 5

    def test_combined_swing_and_humanize(self):
        events = [
            NoteEvent(start_beats=0.5, duration_beats=0.5, midi_note=60, velocity=80),  # offbeat
        ]
        spec = ExpressiveSpec(swing=0.4, humanize_ms=10.0, humanize_vel=5, seed=42)
        result = apply_expressive(events, spec=spec, tempo_bpm=120)

        # Should apply swing (0.2 beat delay) plus some humanization jitter
        # 0.5 + 0.2 = 0.7 base, plus jitter
        assert result[0].start_beats > 0.5  # at least swing applied
