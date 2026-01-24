# zt_band/midi/midi_clock.py
"""
MIDI Clock master scheduler with tempo smoothing and drift resistance.

Design goals:
  - Monotonic scheduling (no drift accumulation)
  - Catch-up with bounded bursts if loop overruns
  - Smooth tempo changes via TempoSmoother

Usage:
    clock = MidiClockMaster(send_bytes=my_sender)
    clock.start(bpm=120.0)
    while running:
        clock.set_bpm_target(new_bpm)  # anytime
        clock.tick()                   # call frequently (e.g., every 1-5ms)
    clock.stop()
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Optional

# MIDI realtime bytes
MIDI_CLOCK = 0xF8
MIDI_START = 0xFA
MIDI_CONTINUE = 0xFB
MIDI_STOP = 0xFC

SendBytes = Callable[[bytes], None]


def now_s() -> float:
    """Monotonic time source (never wall clock)."""
    return time.monotonic()


def bpm_to_tick_period_s(bpm: float) -> float:
    """
    MIDI clock sends 24 PPQN ticks.
    1 quarter note = 60 / bpm seconds.
    tick_period = (60 / bpm) / 24
    """
    if bpm <= 0:
        raise ValueError("bpm must be > 0")
    return (60.0 / bpm) / 24.0


@dataclass
class TempoSmoother:
    """
    Smooths abrupt BPM changes to avoid clock jumps.

    This is a bounded slew limiter + exponential smoother.
    It is NOT expressive rubato — just safety + stability.

    Modes:
      - time constant (tau_s): exponential smoothing
      - max slew: clamp bpm delta per second
    """
    tau_s: float = 0.25                # smaller = faster response
    max_slew_bpm_per_s: float = 50.0   # clamp rate of change

    _bpm_current: float = field(default=120.0, repr=False)
    _bpm_target: float = field(default=120.0, repr=False)
    _last_t: float = field(default=-1.0, repr=False)  # -1 = uninitialized
    _initialized: bool = field(default=False, repr=False)

    def reset(self, bpm: float, t: float) -> None:
        """Reset smoother state to given BPM at time t."""
        self._bpm_current = float(bpm)
        self._bpm_target = float(bpm)
        self._last_t = float(t)
        self._initialized = True

    def set_target(self, bpm: float) -> None:
        """Set new target BPM (smoothing will interpolate toward it)."""
        self._bpm_target = float(bpm)

    def step(self, t: float) -> float:
        """
        Advance smoothing to time t and return current bpm.
        Call this each tick to get the smoothed tempo.
        """
        if not self._initialized:
            self._last_t = float(t)
            self._initialized = True

        dt = max(0.0, float(t) - self._last_t)
        self._last_t = float(t)

        # Exponential smoothing toward target with time constant tau
        if self.tau_s <= 0:
            bpm_next = self._bpm_target
        else:
            # alpha = 1 - e^(-dt/tau) for exponential decay
            alpha = 1.0 - pow(2.718281828, -dt / self.tau_s)
            bpm_next = self._bpm_current + alpha * (self._bpm_target - self._bpm_current)

        # Slew rate limit
        max_delta = self.max_slew_bpm_per_s * dt
        delta = bpm_next - self._bpm_current
        if delta > max_delta:
            bpm_next = self._bpm_current + max_delta
        elif delta < -max_delta:
            bpm_next = self._bpm_current - max_delta

        self._bpm_current = float(bpm_next)
        return self._bpm_current

    @property
    def bpm_current(self) -> float:
        """Current smoothed BPM."""
        return self._bpm_current

    @property
    def bpm_target(self) -> float:
        """Target BPM we're smoothing toward."""
        return self._bpm_target

    @property
    def is_settled(self) -> bool:
        """True if current is within 0.1 BPM of target."""
        return abs(self._bpm_current - self._bpm_target) < 0.1


class MidiClockMaster:
    """
    MIDI Clock master scheduler.

    Design goals:
      - Monotonic scheduling (no drift accumulation)
      - Catch-up with bounded bursts if loop overruns
      - Smooth tempo changes (TempoSmoother)

    Usage:
        clock = MidiClockMaster(send_bytes=my_sender)
        clock.start(bpm=120.0)
        while running:
            clock.set_bpm_target(new_bpm)  # anytime
            clock.tick()                   # call frequently (e.g., every 1-5ms)
        clock.stop()
    """

    def __init__(
        self,
        send_bytes: SendBytes,
        *,
        smoother: Optional[TempoSmoother] = None,
        max_catchup_ticks: int = 6,
        emit_start_stop: bool = True,
    ) -> None:
        """
        Args:
            send_bytes: Callback to send raw MIDI bytes
            smoother: Optional custom TempoSmoother (default creates one)
            max_catchup_ticks: Max ticks to emit in one tick() call if behind
            emit_start_stop: Whether to emit MIDI Start/Stop messages
        """
        self._send = send_bytes
        self._smoother = smoother or TempoSmoother()
        self._max_catchup_ticks = int(max_catchup_ticks)
        self._emit_start_stop = bool(emit_start_stop)

        self._running = False
        self._next_tick_t: float = 0.0
        self._tick_count: int = 0

    def start(self, bpm: float = 120.0) -> None:
        """
        Start the clock at given BPM.
        Emits MIDI Start if emit_start_stop is True.
        """
        t = now_s()
        self._smoother.reset(bpm, t)
        self._next_tick_t = t
        self._tick_count = 0
        self._running = True

        if self._emit_start_stop:
            self._send(bytes([MIDI_START]))

    def stop(self) -> None:
        """
        Stop the clock.
        Emits MIDI Stop if emit_start_stop is True.
        """
        self._running = False
        if self._emit_start_stop:
            self._send(bytes([MIDI_STOP]))

    def set_bpm_target(self, bpm: float) -> None:
        """
        Set new target BPM. Tempo will smooth toward it.
        Safe to call anytime, even while running.
        """
        self._smoother.set_target(bpm)

    def tick(self) -> int:
        """
        Call frequently (recommended: every 1-5ms).
        Emits any due clock ticks, bounded by max_catchup_ticks.

        Returns:
            Number of clock ticks emitted this call.
        """
        if not self._running:
            return 0

        t = now_s()
        ticks_emitted = 0

        # Emit all due ticks, up to max_catchup_ticks
        while self._next_tick_t <= t and ticks_emitted < self._max_catchup_ticks:
            self._send(bytes([MIDI_CLOCK]))
            self._tick_count += 1
            ticks_emitted += 1

            # Advance smoother and compute next tick period
            bpm = self._smoother.step(self._next_tick_t)
            period = bpm_to_tick_period_s(bpm)
            self._next_tick_t += period

        # If we hit max_catchup_ticks, we're behind. Reset to avoid spiraling.
        if ticks_emitted >= self._max_catchup_ticks and self._next_tick_t < t:
            # Skip ahead to now to avoid endless catch-up
            self._next_tick_t = t

        return ticks_emitted

    @property
    def running(self) -> bool:
        """True if clock is currently running."""
        return self._running

    @property
    def tick_count(self) -> int:
        """Total clock ticks emitted since start()."""
        return self._tick_count

    @property
    def bpm_current(self) -> float:
        """Current smoothed BPM."""
        return self._smoother.bpm_current

    @property
    def bpm_target(self) -> float:
        """Target BPM we're smoothing toward."""
        return self._smoother.bpm_target

    def quarter_note_count(self) -> float:
        """
        Approximate quarter notes elapsed since start.
        (tick_count / 24 PPQN)
        """
        return self._tick_count / 24.0

    def time_until_next_tick(self) -> float:
        """
        Seconds until next tick is due.
        Returns 0 if tick is overdue.
        """
        if not self._running:
            return 0.0
        return max(0.0, self._next_tick_t - now_s())
