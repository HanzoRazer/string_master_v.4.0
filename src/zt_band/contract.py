"""
Musical contract and invariants for MIDI generation.

This module defines the canonical stability interface between:
- Input formats (.ztprog, .ztplay, .ztex)
- Generator logic
- MIDI writer

Mirrors the published invariants in CLI_DOCUMENTATION.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional, Sequence


class ContractViolation(ValueError):
    """Raised when a musical/engine invariant is violated."""


@dataclass(frozen=True)
class MidiContract:
    """
    Canonical invariants for generated MIDI.

    Mirrors the repo's published invariants:
    - Tempo + time signature at time 0
    - No stuck notes (every note_on has a corresponding note_off)
    - Deterministic output when seed/inputs identical (when randomness is used)
    - Stable track names when possible
    - DAW-clean import
    """
    require_type_1: bool = True
    require_tempo_at_zero: bool = True
    require_timesig_at_zero: bool = True
    require_track_names: bool = True
    forbid_stuck_notes: bool = True


@dataclass(frozen=True)
class ProgramSpec:
    """
    Minimal "program contract" for zt-band generation.
    This is not a feature spec. It's the stability interface between:
      - ztprog/.ztplay/.ztex inputs
      - generator
      - MIDI writer
    """
    tempo_bpm: int
    time_sig_num: int = 4
    time_sig_den: int = 4
    ticks_per_beat: int = 480
    seed: Optional[int] = None  # If set, any randomness MUST derive from this.

    def validate(self) -> None:
        if not (20 <= self.tempo_bpm <= 300):
            raise ContractViolation(f"tempo_bpm out of bounds: {self.tempo_bpm}")
        if self.time_sig_num <= 0:
            raise ContractViolation(f"time_sig_num must be > 0: {self.time_sig_num}")
        if self.time_sig_den not in (1, 2, 4, 8, 16):
            raise ContractViolation(f"time_sig_den invalid: {self.time_sig_den}")
        if not (96 <= self.ticks_per_beat <= 1920):
            raise ContractViolation(f"ticks_per_beat out of bounds: {self.ticks_per_beat}")


@dataclass(frozen=True)
class NoteEvent:
    """
    Engine-internal representation: "what we intended to play"
    (This keeps generation logic separate from mido timing details.)
    """
    track: str
    start_tick: int
    dur_tick: int
    channel: int
    note: int
    velocity: int

    def validate(self) -> None:
        if self.start_tick < 0:
            raise ContractViolation("start_tick must be >= 0")
        if self.dur_tick <= 0:
            raise ContractViolation("dur_tick must be > 0")
        if not (0 <= self.channel <= 15):
            raise ContractViolation("channel must be 0..15")
        if not (0 <= self.note <= 127):
            raise ContractViolation("note must be 0..127")
        if not (1 <= self.velocity <= 127):
            raise ContractViolation("velocity must be 1..127")
        if not self.track:
            raise ContractViolation("track name must be non-empty")


def validate_events(events: Iterable[NoteEvent]) -> None:
    for e in events:
        e.validate()


def assert_determinism_inputs(program: ProgramSpec, randomness_used: bool) -> None:
    """
    If you introduce ANY randomness in generation, it must be seed-driven.
    This locks determinism without banning expressiveness.
    """
    if randomness_used and program.seed is None:
        raise ContractViolation(
            "randomness_used=True but ProgramSpec.seed is None. "
            "Set a seed to keep outputs deterministic."
        )
