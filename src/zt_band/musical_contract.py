"""
Musical contract enforcement for zt-band generator stability.

This module validates that generated events satisfy stability invariants
BEFORE MIDI writing, ensuring reproducible and DAW-compatible output.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass


class ContractViolation(ValueError):
    """Raised when the generator violates stability invariants."""


@dataclass(frozen=True)
class MusicalContract:
    """Stability contract (no feature creep)"""
    require_seed_when_probabilistic: bool = True
    forbid_negative_start: bool = True
    forbid_nonpositive_duration: bool = True
    forbid_velocity_zero: bool = True


def validate_note_events(
    events: Iterable[object],
    *,
    contract: MusicalContract = MusicalContract(),
) -> None:
    """
    Validates your existing NoteEvent shape:
      start_beats: float
      duration_beats: float
      midi_note: int 0..127
      velocity: int 1..127
      channel: int 0..15
    """
    for e in events:
        start = float(e.start_beats)
        dur = float(e.duration_beats)
        note = int(e.midi_note)
        vel = int(e.velocity)
        ch = int(e.channel)

        if contract.forbid_negative_start and start < 0:
            raise ContractViolation(f"start_beats < 0: {start}")

        if contract.forbid_nonpositive_duration and dur <= 0:
            raise ContractViolation(f"duration_beats <= 0: {dur}")

        if not (0 <= note <= 127):
            raise ContractViolation(f"midi_note out of range 0..127: {note}")

        if not (0 <= ch <= 15):
            raise ContractViolation(f"channel out of range 0..15: {ch}")

        if contract.forbid_velocity_zero and vel <= 0:
            raise ContractViolation(f"velocity must be > 0: {vel}")

        if vel > 127:
            raise ContractViolation(f"velocity out of range 0..127: {vel}")


def enforce_determinism_inputs(
    *,
    tritone_mode: str,
    tritone_seed: int | None,
    contract: MusicalContract = MusicalContract(),
) -> None:
    if (
        contract.require_seed_when_probabilistic
        and tritone_mode == "probabilistic"
        and tritone_seed is None
    ):
        raise ContractViolation(
            "tritone_mode=probabilistic requires tritone_seed for reproducible output."
        )
