# zt_band/adapters/__init__.py
"""
Adapters for translating Groove Control Intent to various output formats.

Primary adapter:
    groove_intent_adapter.build_midi_control_plan()
        -> Converts GrooveControlIntentV1 to MidiControlPlan
"""

from .midi_control_plan import MidiControlPlan, ClockMode, MidiMessage
from .default_map import MidiControlMap, DEFAULT_MAP
from .groove_intent_adapter import build_midi_control_plan

__all__ = [
    "MidiControlPlan",
    "ClockMode",
    "MidiMessage",
    "MidiControlMap",
    "DEFAULT_MAP",
    "build_midi_control_plan",
]
