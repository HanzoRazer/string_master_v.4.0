# zt_band/midi/__init__.py
"""
MIDI utilities for zt-band.

Primary components:
    MidiClockMaster: MIDI Clock master scheduler with tempo smoothing
    TempoSmoother: Bounded slew limiter for tempo changes
"""

from .midi_clock import (
    MidiClockMaster,
    TempoSmoother,
    MIDI_CLOCK,
    MIDI_START,
    MIDI_CONTINUE,
    MIDI_STOP,
    bpm_to_tick_period_s,
    SendBytes,
)

__all__ = [
    "MidiClockMaster",
    "TempoSmoother",
    "MIDI_CLOCK",
    "MIDI_START",
    "MIDI_CONTINUE",
    "MIDI_STOP",
    "bpm_to_tick_period_s",
    "SendBytes",
]
