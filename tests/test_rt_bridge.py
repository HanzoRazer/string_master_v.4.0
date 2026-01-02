"""
Tests for RT bridge: NoteEvents -> step-indexed MIDI messages.
"""
from zt_band.midi_out import NoteEvent
from zt_band.rt_bridge import (
    RtRenderSpec,
    _beats_per_cycle,
    _beats_per_step,
    _step_index,
    gm_program_changes_at_start,
    note_events_to_step_messages,
    truncate_events_to_cycle,
)


class TestRtRenderSpec:
    def test_beats_per_step_16th_grid(self):
        spec = RtRenderSpec(bpm=120.0, grid=16)
        # 4 beats / 16 steps = 0.25 beats per step
        assert _beats_per_step(spec) == 0.25

    def test_beats_per_step_8th_grid(self):
        spec = RtRenderSpec(bpm=120.0, grid=8)
        # 4 beats / 8 steps = 0.5 beats per step
        assert _beats_per_step(spec) == 0.5

    def test_beats_per_cycle_2_bars(self):
        spec = RtRenderSpec(bpm=120.0, bars_per_cycle=2)
        # 4 beats per bar * 2 bars = 8 beats
        assert _beats_per_cycle(spec) == 8.0


class TestStepIndex:
    def test_beat_0_is_step_0(self):
        spec = RtRenderSpec(bpm=120.0, grid=16, bars_per_cycle=2)
        steps_per_cycle = 32
        assert _step_index(0.0, spec, steps_per_cycle) == 0

    def test_beat_1_is_step_4(self):
        # With 16th grid: 4 steps per beat
        spec = RtRenderSpec(bpm=120.0, grid=16, bars_per_cycle=2)
        steps_per_cycle = 32
        assert _step_index(1.0, spec, steps_per_cycle) == 4

    def test_wraps_at_cycle_boundary(self):
        spec = RtRenderSpec(bpm=120.0, grid=16, bars_per_cycle=2)
        steps_per_cycle = 32
        # 8 beats = full cycle, should wrap to step 0
        assert _step_index(8.0, spec, steps_per_cycle) == 0


class TestNoteEventsToStepMessages:
    def test_single_note_produces_on_and_off(self):
        spec = RtRenderSpec(bpm=120.0, grid=16, bars_per_cycle=2)
        steps_per_cycle = 32

        events = [
            NoteEvent(start_beats=0.0, duration_beats=0.5, midi_note=60, velocity=100, channel=0)
        ]

        msgs = note_events_to_step_messages(events, spec=spec, steps_per_cycle=steps_per_cycle)

        # Should have note_on and note_off
        assert len(msgs) == 2

        # First should be note_on at step 0
        step, msg = msgs[0] if msgs[0][1].type == "note_on" and msgs[0][1].velocity > 0 else msgs[1]
        assert msg.note == 60
        assert msg.velocity == 100

    def test_note_off_not_same_step_as_note_on(self):
        spec = RtRenderSpec(bpm=120.0, grid=16, bars_per_cycle=2)
        steps_per_cycle = 32

        # Very short note that might land on same step
        events = [
            NoteEvent(start_beats=0.0, duration_beats=0.1, midi_note=60, velocity=100, channel=0)
        ]

        msgs = note_events_to_step_messages(events, spec=spec, steps_per_cycle=steps_per_cycle)

        # Get the steps
        on_step = None
        off_step = None
        for step, msg in msgs:
            if msg.type == "note_on" and msg.velocity > 0:
                on_step = step
            elif msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
                off_step = step

        # They should be different (off is at least 1 step after on)
        assert on_step != off_step

    def test_ordering_note_off_before_note_on_at_same_step(self):
        spec = RtRenderSpec(bpm=120.0, grid=16, bars_per_cycle=2)
        steps_per_cycle = 32

        # Two notes: one ends at step 4, another starts at step 4
        events = [
            NoteEvent(start_beats=0.0, duration_beats=1.0, midi_note=60, velocity=100, channel=0),  # ends step 4
            NoteEvent(start_beats=1.0, duration_beats=1.0, midi_note=64, velocity=100, channel=0),  # starts step 4
        ]

        msgs = note_events_to_step_messages(events, spec=spec, steps_per_cycle=steps_per_cycle)

        # At step 4, note_off should come before note_on
        step_4_msgs = [(s, m) for s, m in msgs if s == 4]
        if len(step_4_msgs) >= 2:
            # First message at step 4 should be note_off
            first_type = step_4_msgs[0][1].type
            assert first_type == "note_off" or (step_4_msgs[0][1].type == "note_on" and step_4_msgs[0][1].velocity == 0)


class TestGmProgramChanges:
    def test_returns_two_program_changes(self):
        msgs = gm_program_changes_at_start()
        assert len(msgs) == 2

        # Both at step 0
        for step, msg in msgs:
            assert step == 0
            assert msg.type == "program_change"


class TestTruncateEventsToCycle:
    def test_keeps_events_within_cycle(self):
        events = [
            NoteEvent(start_beats=0.0, duration_beats=1.0, midi_note=60, velocity=100, channel=0),
            NoteEvent(start_beats=4.0, duration_beats=1.0, midi_note=64, velocity=100, channel=0),
        ]

        # 2 bars = 8 beats, both events should be kept
        result = truncate_events_to_cycle(events, bars_per_cycle=2)
        assert len(result) == 2

    def test_drops_events_outside_cycle(self):
        events = [
            NoteEvent(start_beats=0.0, duration_beats=1.0, midi_note=60, velocity=100, channel=0),
            NoteEvent(start_beats=10.0, duration_beats=1.0, midi_note=64, velocity=100, channel=0),  # outside 2-bar cycle
        ]

        # 2 bars = 8 beats, second event at beat 10 should be dropped
        result = truncate_events_to_cycle(events, bars_per_cycle=2)
        assert len(result) == 1
        assert result[0].start_beats == 0.0
