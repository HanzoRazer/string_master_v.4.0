"""
Tests for scheduler abstraction.

Verifies:
- Tick-to-time conversion
- Event normalization (sorting)
- CollectingScheduler behavior
- NoteEvent -> TickEvent bridge
"""
from __future__ import annotations

import pytest

try:
    import mido
    MIDO_AVAILABLE = True
except ImportError:
    MIDO_AVAILABLE = False

pytestmark = pytest.mark.skipif(not MIDO_AVAILABLE, reason="mido not installed")


class TestTickConversion:
    """Test tick-to-time conversion functions."""

    def test_ticks_per_second_120bpm_480tpq(self):
        """At 120 BPM, 480 ticks/beat = 960 ticks/second."""
        from zt_band.scheduler import ticks_per_second

        tps = ticks_per_second(bpm=120.0, ticks_per_beat=480)
        assert abs(tps - 960.0) < 1e-9

    def test_ticks_to_seconds_basic(self):
        """At 120 BPM, 480 ticks/beat: 480 ticks = 0.5 seconds (1 beat)."""
        from zt_band.scheduler import ticks_to_seconds

        seconds = ticks_to_seconds(ticks=480, bpm=120.0, ticks_per_beat=480)
        assert abs(seconds - 0.5) < 1e-9

    def test_ticks_to_seconds_two_beats(self):
        """At 120 BPM, 960 ticks = 1 second (2 beats)."""
        from zt_band.scheduler import ticks_to_seconds

        seconds = ticks_to_seconds(ticks=960, bpm=120.0, ticks_per_beat=480)
        assert abs(seconds - 1.0) < 1e-9

    def test_ticks_to_seconds_zero_tps_safe(self):
        """Zero BPM returns 0 seconds (no division by zero)."""
        from zt_band.scheduler import ticks_to_seconds

        seconds = ticks_to_seconds(ticks=480, bpm=0.0, ticks_per_beat=480)
        assert seconds == 0.0


class TestNormalization:
    """Test event normalization (sorting)."""

    def test_normalize_sorts_by_tick(self):
        """Events are sorted by absolute tick."""
        from zt_band.scheduler import normalize_tick_events

        events = [
            (480, mido.Message("note_on", note=60, velocity=64)),
            (0, mido.Message("program_change", program=0)),
            (240, mido.Message("note_on", note=62, velocity=64)),
        ]

        normalized = normalize_tick_events(events)

        assert normalized[0][0] == 0  # program_change first
        assert normalized[1][0] == 240  # second note
        assert normalized[2][0] == 480  # first note (now third)

    def test_normalize_stable_sort_preserves_same_tick_order(self):
        """Same-tick events preserve insertion order (stable sort)."""
        from zt_band.scheduler import normalize_tick_events

        # Two events at tick 0
        events = [
            (0, mido.Message("program_change", program=0)),
            (0, mido.Message("control_change", control=7, value=100)),
        ]

        normalized = normalize_tick_events(events)

        assert normalized[0][1].type == "program_change"
        assert normalized[1][1].type == "control_change"


class TestCollectingScheduler:
    """Test the CollectingScheduler test helper."""

    def test_collecting_scheduler_captures_messages(self):
        """CollectingScheduler appends messages in tick order."""
        from zt_band.scheduler import CollectingScheduler

        out: list[mido.Message] = []
        sched = CollectingScheduler(out=out)

        events = [
            (240, mido.Message("note_on", note=60, velocity=64)),
            (0, mido.Message("program_change", program=0)),
            (240, mido.Message("note_off", note=60, velocity=0)),
        ]

        sched.run(events, bpm=120.0, ticks_per_beat=480)

        assert len(out) == 3
        assert out[0].type == "program_change"  # tick 0 first
        assert out[1].type == "note_on"  # tick 240
        assert out[2].type == "note_off"  # tick 240 (after note_on due to stable sort)

    def test_collecting_scheduler_empty_events(self):
        """Empty event list produces empty output."""
        from zt_band.scheduler import CollectingScheduler

        out: list[mido.Message] = []
        sched = CollectingScheduler(out=out)

        sched.run([], bpm=120.0, ticks_per_beat=480)

        assert out == []


class TestNoteEventBridge:
    """Test NoteEvent -> TickEvent conversion."""

    def test_note_events_to_tick_events_basic(self):
        """NoteEvent converts to note_on/note_off pair."""
        from zt_band.midi_out import NoteEvent
        from zt_band.scheduler import note_events_to_tick_events

        events = [
            NoteEvent(
                start_beats=0.0,
                duration_beats=1.0,
                midi_note=60,
                velocity=64,
                channel=0,
            )
        ]

        tick_events = note_events_to_tick_events(events, ticks_per_beat=480)

        assert len(tick_events) == 2

        # note_on at tick 0
        assert tick_events[0][0] == 0
        assert tick_events[0][1].type == "note_on"
        assert tick_events[0][1].note == 60
        assert tick_events[0][1].velocity == 64

        # note_off at tick 480
        assert tick_events[1][0] == 480
        assert tick_events[1][1].type == "note_off"
        assert tick_events[1][1].note == 60

    def test_note_events_to_tick_events_minimum_duration(self):
        """Zero-duration note gets minimum 1-tick duration."""
        from zt_band.midi_out import NoteEvent
        from zt_band.scheduler import note_events_to_tick_events

        events = [
            NoteEvent(
                start_beats=0.0,
                duration_beats=0.0,  # zero duration
                midi_note=60,
                velocity=64,
                channel=0,
            )
        ]

        tick_events = note_events_to_tick_events(events, ticks_per_beat=480)

        # note_on at tick 0, note_off at tick 1 (minimum)
        assert tick_events[0][0] == 0
        assert tick_events[1][0] == 1

    def test_note_events_to_tick_events_sorted_output(self):
        """Output is sorted by tick."""
        from zt_band.midi_out import NoteEvent
        from zt_band.scheduler import note_events_to_tick_events

        events = [
            NoteEvent(start_beats=1.0, duration_beats=0.5, midi_note=62, velocity=64, channel=0),
            NoteEvent(start_beats=0.0, duration_beats=0.5, midi_note=60, velocity=64, channel=0),
        ]

        tick_events = note_events_to_tick_events(events, ticks_per_beat=480)

        # Should be sorted: tick 0, 240, 480, 720
        ticks = [t for t, _ in tick_events]
        assert ticks == sorted(ticks)


class TestRealtimeScheduler:
    """Test RealtimeScheduler with mocked time functions."""

    def test_realtime_scheduler_sends_in_order(self):
        """RealtimeScheduler sends messages via sender."""
        from zt_band.scheduler import RealtimeScheduler

        sent: list[mido.Message] = []

        class MockSender:
            def send(self, msg: mido.Message) -> None:
                sent.append(msg)

        # Mock clock that advances each call
        # start=0, then each now() call returns 1000 (always past any target)
        call_count = [0]

        def mock_now() -> float:
            call_count[0] += 1
            if call_count[0] == 1:
                return 0.0  # start time
            return 1000.0  # always "past" any event target

        sched = RealtimeScheduler(
            sender=MockSender(),
            sleep_fn=lambda _: None,  # no-op
            now_fn=mock_now,
        )

        events = [
            (0, mido.Message("note_on", note=60, velocity=64)),
            (480, mido.Message("note_off", note=60, velocity=0)),
        ]

        sched.run(events, bpm=120.0, ticks_per_beat=480)

        assert len(sent) == 2
        assert sent[0].type == "note_on"
        assert sent[1].type == "note_off"
