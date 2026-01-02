"""
Tests for expressive_layer.py — velocity shaping (no timing changes).
"""
from zt_band.expressive_layer import VelocityProfile, _clamp, apply_velocity_profile
from zt_band.midi_out import NoteEvent


class TestClamp:
    def test_clamp_within_range(self):
        assert _clamp(50, 0, 100) == 50

    def test_clamp_below_min(self):
        assert _clamp(-10, 0, 100) == 0

    def test_clamp_above_max(self):
        assert _clamp(150, 0, 100) == 100

    def test_clamp_at_boundaries(self):
        assert _clamp(0, 0, 100) == 0
        assert _clamp(100, 0, 100) == 100


class TestVelocityProfile:
    def test_default_values(self):
        p = VelocityProfile()
        assert p.downbeat_boost == 12
        assert p.midbeat_boost == 7
        assert p.offbeat_cut == 6
        assert p.min_vel == 20
        assert p.max_vel == 120

    def test_custom_values(self):
        p = VelocityProfile(downbeat_boost=20, offbeat_cut=10)
        assert p.downbeat_boost == 20
        assert p.offbeat_cut == 10


class TestApplyVelocityProfile:
    def test_downbeat_boosted(self):
        events = [
            NoteEvent(start_beats=0.0, duration_beats=1.0, midi_note=60, velocity=80),  # beat 1
        ]
        profile = VelocityProfile(downbeat_boost=12)
        result = apply_velocity_profile(events, profile)

        assert len(result) == 1
        # Beat 1 (0.0 in 4/4) should get downbeat boost
        assert result[0].velocity == 92  # 80 + 12

    def test_midbeat_boosted(self):
        events = [
            NoteEvent(start_beats=2.0, duration_beats=1.0, midi_note=60, velocity=80),  # beat 3
        ]
        profile = VelocityProfile(midbeat_boost=7)
        result = apply_velocity_profile(events, profile)

        assert len(result) == 1
        # Beat 3 (2.0 in 4/4) should get midbeat boost
        assert result[0].velocity == 87  # 80 + 7

    def test_offbeat_cut(self):
        events = [
            NoteEvent(start_beats=0.5, duration_beats=0.5, midi_note=60, velocity=80),  # & of 1
            NoteEvent(start_beats=1.5, duration_beats=0.5, midi_note=62, velocity=80),  # & of 2
        ]
        profile = VelocityProfile(offbeat_cut=6)
        result = apply_velocity_profile(events, profile)

        assert len(result) == 2
        # Offbeats should be cut
        assert result[0].velocity == 74  # 80 - 6
        assert result[1].velocity == 74  # 80 - 6

    def test_velocity_clamped_to_max(self):
        events = [
            NoteEvent(start_beats=0.0, duration_beats=1.0, midi_note=60, velocity=115),  # near max
        ]
        profile = VelocityProfile(downbeat_boost=12, max_vel=120)
        result = apply_velocity_profile(events, profile)

        # 115 + 12 = 127, but max is 120
        assert result[0].velocity == 120

    def test_velocity_clamped_to_min(self):
        events = [
            NoteEvent(start_beats=0.5, duration_beats=0.5, midi_note=60, velocity=22),  # near min
        ]
        profile = VelocityProfile(offbeat_cut=6, min_vel=20)
        result = apply_velocity_profile(events, profile)

        # 22 - 6 = 16, but min is 20
        assert result[0].velocity == 20

    def test_no_change_for_unaffected_beats(self):
        events = [
            NoteEvent(start_beats=1.0, duration_beats=1.0, midi_note=60, velocity=80),  # beat 2
            NoteEvent(start_beats=3.0, duration_beats=1.0, midi_note=62, velocity=80),  # beat 4
        ]
        profile = VelocityProfile()
        result = apply_velocity_profile(events, profile)

        # Beats 2 and 4 (not downbeat, midbeat, or offbeat) should be unchanged
        assert result[0].velocity == 80
        assert result[1].velocity == 80

    def test_preserves_other_attributes(self):
        events = [
            NoteEvent(start_beats=0.0, duration_beats=0.75, midi_note=72, velocity=80, channel=5),
        ]
        profile = VelocityProfile()
        result = apply_velocity_profile(events, profile)

        assert result[0].start_beats == 0.0
        assert result[0].duration_beats == 0.75
        assert result[0].midi_note == 72
        assert result[0].channel == 5

    def test_empty_events_returns_empty(self):
        result = apply_velocity_profile([], VelocityProfile())
        assert result == []

    def test_bar_wrapping(self):
        events = [
            NoteEvent(start_beats=4.0, duration_beats=1.0, midi_note=60, velocity=80),  # beat 1 of bar 2
            NoteEvent(start_beats=6.0, duration_beats=1.0, midi_note=62, velocity=80),  # beat 3 of bar 2
        ]
        profile = VelocityProfile(downbeat_boost=12, midbeat_boost=7)
        result = apply_velocity_profile(events, profile)

        # beat_in_bar = 4.0 % 4.0 = 0.0 (downbeat)
        assert result[0].velocity == 92  # 80 + 12
        # beat_in_bar = 6.0 % 4.0 = 2.0 (midbeat)
        assert result[1].velocity == 87  # 80 + 7
