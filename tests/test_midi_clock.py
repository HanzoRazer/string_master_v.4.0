# tests/test_midi_clock.py
"""
Tests for MIDI Clock master scheduler.
"""
import time
from typing import List

from zt_band.midi.midi_clock import (
    MidiClockMaster,
    TempoSmoother,
    bpm_to_tick_period_s,
    MIDI_CLOCK,
    MIDI_START,
    MIDI_STOP,
)


class MockSender:
    """Captures sent MIDI bytes for testing."""

    def __init__(self):
        self.messages: List[bytes] = []

    def __call__(self, data: bytes) -> None:
        self.messages.append(data)

    def clear(self) -> None:
        self.messages.clear()

    @property
    def clock_count(self) -> int:
        return sum(1 for m in self.messages if m == bytes([MIDI_CLOCK]))

    @property
    def start_count(self) -> int:
        return sum(1 for m in self.messages if m == bytes([MIDI_START]))

    @property
    def stop_count(self) -> int:
        return sum(1 for m in self.messages if m == bytes([MIDI_STOP]))


def test_bpm_to_tick_period():
    """24 PPQN at 120 BPM = 20.833ms per tick."""
    period = bpm_to_tick_period_s(120.0)
    expected = (60.0 / 120.0) / 24.0  # 0.020833...
    assert abs(period - expected) < 1e-9


def test_bpm_to_tick_period_invalid():
    """Zero or negative BPM should raise."""
    try:
        bpm_to_tick_period_s(0)
        assert False, "Should raise"
    except ValueError:
        pass

    try:
        bpm_to_tick_period_s(-100)
        assert False, "Should raise"
    except ValueError:
        pass


def test_tempo_smoother_instant_when_tau_zero():
    """With tau=0, smoother should snap immediately to target."""
    smoother = TempoSmoother(tau_s=0.0, max_slew_bpm_per_s=1000.0)
    smoother.reset(100.0, 0.0)
    smoother.set_target(150.0)
    bpm = smoother.step(0.1)
    assert bpm == 150.0


def test_tempo_smoother_slew_limit():
    """Slew rate should clamp large jumps."""
    smoother = TempoSmoother(tau_s=0.0, max_slew_bpm_per_s=10.0)
    smoother.reset(100.0, 0.0)
    smoother.set_target(200.0)
    # After 1 second, max delta = 10 BPM
    bpm = smoother.step(1.0)
    assert bpm == 110.0


def test_tempo_smoother_is_settled():
    """is_settled should be True when near target."""
    smoother = TempoSmoother()
    smoother.reset(120.0, 0.0)
    assert smoother.is_settled  # same as target

    smoother.set_target(130.0)
    assert not smoother.is_settled


def test_clock_master_emits_start_stop():
    """Clock should emit MIDI Start on start() and Stop on stop()."""
    sender = MockSender()
    clock = MidiClockMaster(sender, emit_start_stop=True)

    clock.start(120.0)
    assert sender.start_count == 1
    assert sender.stop_count == 0

    clock.stop()
    assert sender.stop_count == 1


def test_clock_master_no_start_stop_when_disabled():
    """With emit_start_stop=False, no Start/Stop messages."""
    sender = MockSender()
    clock = MidiClockMaster(sender, emit_start_stop=False)

    clock.start(120.0)
    clock.stop()

    assert sender.start_count == 0
    assert sender.stop_count == 0


def test_clock_master_tick_emits_clocks():
    """tick() should emit clock messages when due."""
    sender = MockSender()
    clock = MidiClockMaster(sender, emit_start_stop=False, max_catchup_ticks=100)

    clock.start(120.0)

    # Force time to advance past several tick periods
    # At 120 BPM: tick period = 20.833ms, so 50ms = ~2.4 ticks
    # We'll simulate by directly manipulating _next_tick_t
    clock._next_tick_t = time.monotonic() - 0.1  # 100ms behind

    ticks = clock.tick()
    assert ticks > 0
    assert sender.clock_count == ticks


def test_clock_master_bounded_catchup():
    """tick() should not emit more than max_catchup_ticks."""
    sender = MockSender()
    clock = MidiClockMaster(sender, emit_start_stop=False, max_catchup_ticks=3)

    clock.start(120.0)
    clock._next_tick_t = time.monotonic() - 1.0  # Way behind

    ticks = clock.tick()
    assert ticks == 3  # Capped at max


def test_clock_master_set_bpm_target():
    """set_bpm_target should update smoother target."""
    sender = MockSender()
    clock = MidiClockMaster(sender)

    clock.start(100.0)
    assert clock.bpm_target == 100.0

    clock.set_bpm_target(140.0)
    assert clock.bpm_target == 140.0


def test_clock_master_quarter_note_count():
    """quarter_note_count should be tick_count / 24."""
    sender = MockSender()
    clock = MidiClockMaster(sender, emit_start_stop=False, max_catchup_ticks=48)

    clock.start(120.0)
    clock._next_tick_t = time.monotonic() - 1.0  # Force 48 ticks

    clock.tick()
    assert clock.tick_count == 48
    assert clock.quarter_note_count() == 2.0


def test_clock_master_not_running_before_start():
    """Clock should not be running before start()."""
    sender = MockSender()
    clock = MidiClockMaster(sender)

    assert not clock.running
    assert clock.tick() == 0

    clock.start(120.0)
    assert clock.running


def test_clock_master_time_until_next_tick():
    """time_until_next_tick should return positive value when not due."""
    sender = MockSender()
    clock = MidiClockMaster(sender, emit_start_stop=False)

    clock.start(60.0)  # 60 BPM = 41.67ms per tick
    clock.tick()  # Emit first tick, advance next_tick_t

    wait = clock.time_until_next_tick()
    assert wait >= 0.0
