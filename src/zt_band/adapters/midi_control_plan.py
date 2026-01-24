# zt_band/adapters/midi_control_plan.py
"""
MidiControlPlan: Output of the Groove Intent adapter.

This plan is the ONLY thing that should touch MIDI control messages,
clock policy, and humanization knobs.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Literal

MidiMessage = Tuple[int, int, int]  # (status, data1, data2) e.g. (0xB0|ch, cc, value)

ClockMode = Literal["none", "midi_clock_follow", "midi_clock_master"]


@dataclass(frozen=True)
class MidiControlPlan:
    """
    Output of the adapter: what zt-band should do to express the intent through MIDI.
    This plan is the ONLY thing that should touch MIDI control messages, clock policy,
    and humanization knobs.

    zt-band can apply this plan each tick / bar boundary.
    """
    # Tempo & sync
    clock_mode: ClockMode
    target_bpm: float
    # If clock_mode == midi_clock_master, caller emits MIDI clock at this BPM.
    # If follow, caller reads external clock and uses target_bpm only for guidance/UI.

    # Timing / feel
    humanize_ms: float
    # Signed: negative shifts "push" (ahead), positive shifts "pull" (behind)
    global_microshift_ms: float

    # Dynamics assist
    assist_gain: float
    expression_window: float

    # Recovery behavior
    recovery_enabled: bool
    grace_beats: float

    # --- Fields with defaults (must come after non-defaults) ---
    # Humanizer seed and enable flag
    humanize_seed: str = "default"
    humanize_enabled: bool = True

    # MIDI control messages to send (CC etc.)
    cc_messages: List[MidiMessage] = field(default_factory=list)

    # Debuggable reasons
    reason_codes: List[str] = field(default_factory=list)

    # Optional: instrument/track routing hints
    routing: Dict[str, str] = field(default_factory=dict)

    def as_dict(self) -> Dict:
        return {
            "clock_mode": self.clock_mode,
            "target_bpm": self.target_bpm,
            "humanize_ms": self.humanize_ms,
            "humanize_seed": self.humanize_seed,
            "humanize_enabled": self.humanize_enabled,
            "global_microshift_ms": self.global_microshift_ms,
            "assist_gain": self.assist_gain,
            "expression_window": self.expression_window,
            "recovery_enabled": self.recovery_enabled,
            "grace_beats": self.grace_beats,
            "cc_messages": self.cc_messages,
            "reason_codes": self.reason_codes,
            "routing": self.routing,
        }
