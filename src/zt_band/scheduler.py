"""
Scheduler abstraction for unified MIDI event dispatch.

This module provides a canonical event representation (TickEvent) and
scheduling protocols that unify file-based MIDI writing with realtime output.

The key abstraction:
    TickEvent = (abs_tick: int, mido.Message)

Both file writers and realtime schedulers consume the same stream.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, Iterable, Protocol

if TYPE_CHECKING:
    from zt_band.midi.humanizer import DeterministicHumanizer

try:
    import mido
    MIDO_AVAILABLE = True
except ImportError:
    MIDO_AVAILABLE = False
    mido = None  # type: ignore


# Canonical event type: (absolute_tick, mido.Message)
TickEvent = tuple[int, "mido.Message"]


def ticks_per_second(bpm: float, ticks_per_beat: int) -> float:
    """
    Convert BPM and ticks_per_beat to ticks per second.

    bpm beats/min => bpm/60 beats/sec => * ticks_per_beat => ticks/sec
    """
    return (bpm / 60.0) * float(ticks_per_beat)


def ticks_to_seconds(ticks: int, bpm: float, ticks_per_beat: int) -> float:
    """
    Convert absolute tick count to wall-clock seconds.

    Parameters:
        ticks: Absolute tick position
        bpm: Tempo in beats per minute
        ticks_per_beat: MIDI resolution (typically 480)

    Returns:
        Time in seconds from tick 0
    """
    tps = ticks_per_second(bpm, ticks_per_beat)
    return float(ticks) / tps if tps > 0 else 0.0


def normalize_tick_events(events: Iterable[TickEvent]) -> list[TickEvent]:
    """
    Sort events by absolute tick (stable sort preserves same-tick order).

    We do not mutate messages; we only enforce deterministic ordering.
    This is the single place where event ordering is canonicalized.
    """
    ev = list(events)
    ev.sort(key=lambda x: int(x[0]))
    return ev


class MidiSender(Protocol):
    """Protocol for anything that can send a MIDI message."""

    def send(self, msg: "mido.Message") -> None:
        """Send a MIDI message."""
        ...


class Scheduler(Protocol):
    """
    Scheduler protocol: consumes TickEvents and emits them via some sink.

    Implementations:
        - RealtimeScheduler: wall-clock dispatch to MIDI port
        - CollectingScheduler: test helper that collects messages
        - (future) FileScheduler: delta-encode to MidiFile
    """

    def run(
        self,
        events: Iterable[TickEvent],
        *,
        bpm: float,
        ticks_per_beat: int,
    ) -> None:
        """
        Execute the event stream.

        Parameters:
            events: Iterable of (abs_tick, mido.Message)
            bpm: Tempo for tick-to-time conversion
            ticks_per_beat: MIDI resolution
        """
        ...


@dataclass(frozen=True)
class RealtimeScheduler:
    """
    Minimal realtime scheduler for MIDI output.

    Converts absolute ticks to monotonic wall-clock times and dispatches
    messages via sleep-until-target timing.

    Contract compliance (see docs/contracts/REALTIME_MIDI_CONTRACT.md):
        - Uses monotonic clock (no wall-clock drift)
        - Sleeps in small chunks (≤2ms) to reduce jitter
        - Late messages are sent immediately (no time-warp compression)

    NOTE: This scheduler does NOT implement catch-up time warping.
    If the system falls behind, messages are sent ASAP without compression.
    A fuller contract layer can add drop-priority later.
    """

    sender: MidiSender
    sleep_fn: Callable[[float], None] = time.sleep
    now_fn: Callable[[], float] = time.monotonic
    # If we're late by more than this (seconds), we still send immediately
    max_late_s: float = 0.020  # 20ms hard max per REALTIME_MIDI_CONTRACT
    # Humanizer for deterministic jitter (optional)
    humanizer: "DeterministicHumanizer | None" = None
    humanize_ms: float = 0.0

    def run(
        self,
        events: Iterable[TickEvent],
        *,
        bpm: float,
        ticks_per_beat: int,
    ) -> None:
        """
        Execute events in realtime.

        Parameters:
            events: Iterable of (abs_tick, mido.Message)
            bpm: Tempo in BPM
            ticks_per_beat: MIDI resolution

        Raises:
            RuntimeError: If mido is not available
        """
        if not MIDO_AVAILABLE:
            raise RuntimeError("mido is required for realtime scheduling")

        ev = normalize_tick_events(events)
        start = self.now_fn()

        for tick_index, (abs_tick, msg) in enumerate(ev):
            target = start + ticks_to_seconds(int(abs_tick), bpm, ticks_per_beat)

            # Apply humanize jitter BEFORE sleep-until-target loop
            if self.humanizer and self.humanize_ms > 0.0:
                mtype = getattr(msg, "type", None)
                channel = "note" if mtype in ("note_on", "note_off") else "cc"
                target += self.humanizer.jitter_ms(
                    tick_index=tick_index,
                    humanize_ms=self.humanize_ms,
                    channel=channel,
                ) / 1000.0
                # Prevent jitter into the past from creating unnecessary late flags
                now = self.now_fn()
                if target < now:
                    target = now

            # Sleep-until-target loop
            while True:
                now = self.now_fn()
                dt = target - now
                if dt <= 0:
                    break
                # Sleep in small chunks (≤2ms) to reduce jitter
                self.sleep_fn(min(dt, 0.002))

            # Late handling: send immediately; do not time-warp
            self.sender.send(msg)


@dataclass(frozen=True)
class CollectingScheduler:
    """
    Test helper: collects messages in the order they would be sent.

    Useful for unit tests without realtime or MIDI devices.
    Messages are appended to the `out` list in normalized tick order.
    """

    out: list["mido.Message"]

    def run(
        self,
        events: Iterable[TickEvent],
        *,
        bpm: float,
        ticks_per_beat: int,
    ) -> None:
        """
        Collect events without realtime dispatch.

        Parameters:
            events: Iterable of (abs_tick, mido.Message)
            bpm: Ignored (no timing needed)
            ticks_per_beat: Ignored (no timing needed)
        """
        if not MIDO_AVAILABLE:
            raise RuntimeError("mido is required")

        ev = normalize_tick_events(events)
        for _, msg in ev:
            self.out.append(msg)


# -----------------------------------------------------------------------------
# Bridge utilities: Convert NoteEvent -> TickEvent
# -----------------------------------------------------------------------------

def note_events_to_tick_events(
    events: Iterable,
    *,
    ticks_per_beat: int = 480,
) -> list[TickEvent]:
    """
    Convert NoteEvent objects to TickEvents.

    This is the bridge function that unifies the existing engine output
    with the scheduler abstraction. Both file writers and realtime
    schedulers can consume the same TickEvent stream.

    Parameters:
        events: Iterable of NoteEvent (must have start_beats, duration_beats,
                midi_note, velocity, channel attributes)
        ticks_per_beat: MIDI resolution (default 480)

    Returns:
        List of (abs_tick, mido.Message) tuples, sorted by tick.

    Note:
        This function generates note_on/note_off pairs. For priority ordering
        (note_off before note_on at same tick), use the priority-aware
        version in midi_out.py.
    """
    if not MIDO_AVAILABLE:
        raise RuntimeError("mido is required for TickEvent conversion")

    tick_events: list[TickEvent] = []

    for ne in events:
        start_tick = int(round(ne.start_beats * ticks_per_beat))
        end_tick = int(round((ne.start_beats + ne.duration_beats) * ticks_per_beat))

        # Clamp: ensure note_off occurs after note_on by at least 1 tick
        if end_tick <= start_tick:
            end_tick = start_tick + 1

        # Create note_on and note_off messages
        on = mido.Message(
            "note_on",
            note=int(ne.midi_note),
            velocity=int(ne.velocity),
            channel=int(ne.channel),
        )
        off = mido.Message(
            "note_off",
            note=int(ne.midi_note),
            velocity=0,
            channel=int(ne.channel),
        )

        tick_events.append((start_tick, on))
        tick_events.append((end_tick, off))

    # Sort by tick (stable)
    tick_events.sort(key=lambda x: x[0])
    return tick_events
