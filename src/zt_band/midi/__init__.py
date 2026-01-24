# zt_band/midi/__init__.py
"""
MIDI utilities for zt-band.

Primary components:
    MidiClockMaster: MIDI Clock master scheduler with tempo smoothing
    TempoSmoother: Bounded slew limiter for tempo changes
    DeterministicHumanizer: Seedable jitter generator for human feel
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

from .humanizer import DeterministicHumanizer

__all__ = [
    "MidiClockMaster",
    "TempoSmoother",
    "DeterministicHumanizer",
    "MIDI_CLOCK",
    "MIDI_START",
    "MIDI_CONTINUE",
    "MIDI_STOP",
    "bpm_to_tick_period_s",
    "SendBytes",
]
