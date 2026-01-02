"""
Tests for ghost_layer.py — ghost hit generation for Brazilian feel.
"""
from zt_band.ghost_layer import (
    GHOST_SPEC_BRAZIL,
    GHOST_SPEC_OFF,
    GHOST_STEPS_A_ALL,
    GHOST_STEPS_E_ALL,
    GHOST_STEPS_E_OFFBEAT,
    GHOST_STEPS_TAMBORIM,
    GhostSpec,
    add_ghost_hits,
)
from zt_band.midi_out import NoteEvent


class TestGhostSpec:
    def test_default_spec_is_disabled(self):
        spec = GhostSpec()
        assert spec.ghost_vel == 0
        assert spec.ghost_steps == ()
        assert spec.ghost_len_beats == 0.0625
        assert spec.ghost_channel is None

    def test_brazil_preset(self):
        assert GHOST_SPEC_BRAZIL.ghost_vel == 14
        assert GHOST_SPEC_BRAZIL.ghost_steps == GHOST_STEPS_E_ALL
        assert GHOST_SPEC_BRAZIL.ghost_len_beats == 0.0625

    def test_off_preset(self):
        assert GHOST_SPEC_OFF.ghost_vel == 0
        assert GHOST_SPEC_OFF.ghost_steps == ()


class TestGhostStepsPresets:
    def test_e_all_positions(self):
        # "e" of each beat: 1e=1, 2e=5, 3e=9, 4e=13
        assert GHOST_STEPS_E_ALL == (1, 5, 9, 13)

    def test_a_all_positions(self):
        # "a" of each beat: 1a=3, 2a=7, 3a=11, 4a=15
        assert GHOST_STEPS_A_ALL == (3, 7, 11, 15)

    def test_e_offbeat_positions(self):
        # "e" of beats 2 and 4 only
        assert GHOST_STEPS_E_OFFBEAT == (5, 13)

    def test_tamborim_positions(self):
        # All 16ths except main beat positions
        assert GHOST_STEPS_TAMBORIM == (1, 3, 5, 7, 9, 11, 13, 15)


class TestAddGhostHits:
    def test_disabled_returns_unchanged(self):
        events = [NoteEvent(start_beats=0.0, duration_beats=1.0, midi_note=60, velocity=80)]
        spec = GhostSpec(ghost_vel=0)  # disabled
        result = add_ghost_hits(
            events,
            chord_pitches=[60, 64, 67],
            bar_start_beats=0.0,
            beats_per_bar=4,
            ghost_spec=spec,
        )
        assert result == events

    def test_empty_steps_returns_unchanged(self):
        events = [NoteEvent(start_beats=0.0, duration_beats=1.0, midi_note=60, velocity=80)]
        spec = GhostSpec(ghost_vel=20, ghost_steps=())  # no steps
        result = add_ghost_hits(
            events,
            chord_pitches=[60, 64, 67],
            bar_start_beats=0.0,
            beats_per_bar=4,
            ghost_spec=spec,
        )
        assert result == events

    def test_empty_chord_returns_unchanged(self):
        events = [NoteEvent(start_beats=0.0, duration_beats=1.0, midi_note=60, velocity=80)]
        spec = GhostSpec(ghost_vel=20, ghost_steps=(1, 5))
        result = add_ghost_hits(
            events,
            chord_pitches=[],  # no pitches
            bar_start_beats=0.0,
            beats_per_bar=4,
            ghost_spec=spec,
        )
        assert result == events

    def test_adds_ghost_notes_at_correct_steps(self):
        events = []  # no existing events
        spec = GhostSpec(ghost_vel=15, ghost_steps=(1,), ghost_len_beats=0.0625)
        result = add_ghost_hits(
            events,
            chord_pitches=[60, 64, 67],
            bar_start_beats=0.0,
            beats_per_bar=4,
            ghost_spec=spec,
        )
        # Step 1 in 4/4 bar (16 steps) = 0.25 beats
        # Should add 3 ghost notes (one per chord pitch, limited to 3)
        assert len(result) == 3
        for ev in result:
            assert ev.start_beats == 0.25  # step 1 = 0.25 beats
            assert ev.velocity == 15
            assert ev.duration_beats == 0.0625

    def test_does_not_collide_with_existing_events(self):
        # Place a real event at step 1 (0.25 beats)
        events = [NoteEvent(start_beats=0.25, duration_beats=0.5, midi_note=60, velocity=80, channel=0)]
        spec = GhostSpec(ghost_vel=15, ghost_steps=(1, 5))  # try steps 1 and 5
        result = add_ghost_hits(
            events,
            chord_pitches=[60, 64, 67],
            bar_start_beats=0.0,
            beats_per_bar=4,
            ghost_spec=spec,
            comp_channel=0,
        )
        # Step 1 is occupied, step 5 is free
        # Should have original event + 3 ghost notes at step 5
        assert len(result) == 4
        # Check ghost notes are at step 5 (1.25 beats)
        ghost_events = [e for e in result if e.velocity == 15]
        assert len(ghost_events) == 3
        for ev in ghost_events:
            assert ev.start_beats == 1.25

    def test_uses_custom_channel(self):
        events = []
        spec = GhostSpec(ghost_vel=15, ghost_steps=(1,), ghost_channel=5)
        result = add_ghost_hits(
            events,
            chord_pitches=[60],
            bar_start_beats=0.0,
            beats_per_bar=4,
            ghost_spec=spec,
            comp_channel=0,
        )
        assert len(result) == 1
        assert result[0].channel == 5

    def test_uses_comp_channel_when_none(self):
        events = []
        spec = GhostSpec(ghost_vel=15, ghost_steps=(1,), ghost_channel=None)
        result = add_ghost_hits(
            events,
            chord_pitches=[60],
            bar_start_beats=0.0,
            beats_per_bar=4,
            ghost_spec=spec,
            comp_channel=3,
        )
        assert len(result) == 1
        assert result[0].channel == 3

    def test_velocity_clamped_to_valid_range(self):
        events = []
        spec = GhostSpec(ghost_vel=200, ghost_steps=(1,))  # over 127
        result = add_ghost_hits(
            events,
            chord_pitches=[60],
            bar_start_beats=0.0,
            beats_per_bar=4,
            ghost_spec=spec,
        )
        assert len(result) == 1
        assert result[0].velocity == 127  # clamped

    def test_limits_ghost_pitches_to_three(self):
        events = []
        spec = GhostSpec(ghost_vel=15, ghost_steps=(1,))
        result = add_ghost_hits(
            events,
            chord_pitches=[60, 64, 67, 72, 76],  # 5 pitches
            bar_start_beats=0.0,
            beats_per_bar=4,
            ghost_spec=spec,
        )
        # Should only use first 3 pitches
        assert len(result) == 3
        pitches = {e.midi_note for e in result}
        assert pitches == {60, 64, 67}

    def test_works_with_2_4_time(self):
        events = []
        spec = GhostSpec(ghost_vel=15, ghost_steps=(1, 3))
        result = add_ghost_hits(
            events,
            chord_pitches=[60],
            bar_start_beats=0.0,
            beats_per_bar=2,  # 2/4 time
            ghost_spec=spec,
        )
        # 2/4 bar has 8 steps, step duration = 0.25 beats
        # Step 1 = 0.25, Step 3 = 0.75
        assert len(result) == 2
        starts = sorted(e.start_beats for e in result)
        assert starts == [0.25, 0.75]
