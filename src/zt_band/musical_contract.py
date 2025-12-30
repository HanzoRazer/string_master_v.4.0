"""
Musical contract enforcement for zt-band generator stability.

This module validates that generated events satisfy stability invariants
BEFORE MIDI writing, ensuring reproducible and DAW-compatible output.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional


class ContractViolation(ValueError):
    """Raised when the generator violates stability invariants."""


@dataclass(frozen=True)
class MusicalContract:
    """
    Stability-first musical contract for zt-band output.

    Scope:
    - Valid MIDI ranges (notes 0-127, channels 0-15, velocities 1-127)
    - Non-negative time (start_beats >= 0)
    - Positive durations (duration_beats > 0)
    - Determinism enforcement for probabilistic behavior (requires seed)
    
    All checks default to enabled for maximum stability.
    """
    require_seed_when_probabilistic: bool = True
    forbid_nonpositive_durations: bool = True
    forbid_negative_start: bool = True
    forbid_velocity_zero_on_note_on: bool = True


def validate_note_events(
    events: Iterable[object],
    *,
    contract: MusicalContract = MusicalContract(),
) -> None:
    """
    Validate events produced by the generator BEFORE MIDI writing.

    Expects objects with attributes:
      start_beats: float     (>= 0 if forbid_negative_start)
      duration_beats: float  (> 0 if forbid_nonpositive_durations)
      midi_note: int         (0-127)
      velocity: int          (1-127 if forbid_velocity_zero_on_note_on, else 0-127)
      channel: int           (0-15)
    
    Raises:
        ContractViolation: If any event violates the contract.
    
    Examples:
        >>> from midi_out import NoteEvent
        >>> events = [NoteEvent(0.0, 1.0, 60, 80, 0)]
        >>> validate_note_events(events)  # passes
        >>> bad = [NoteEvent(-1.0, 1.0, 60, 80, 0)]
        >>> validate_note_events(bad)  # raises ContractViolation
    """
    for e in events:
        start = float(getattr(e, "start_beats"))
        dur = float(getattr(e, "duration_beats"))
        note = int(getattr(e, "midi_note"))
        vel = int(getattr(e, "velocity"))
        ch = int(getattr(e, "channel"))

        if contract.forbid_negative_start and start < 0:
            raise ContractViolation(f"start_beats < 0: {start}")

        if contract.forbid_nonpositive_durations and dur <= 0:
            raise ContractViolation(f"duration_beats <= 0: {dur}")

        if not (0 <= note <= 127):
            raise ContractViolation(f"midi_note out of range 0..127: {note}")

        if not (0 <= ch <= 15):
            raise ContractViolation(f"channel out of range 0..15: {ch}")

        if contract.forbid_velocity_zero_on_note_on and vel <= 0:
            raise ContractViolation(f"velocity must be > 0 for note_on semantics: {vel}")

        if vel > 127:
            raise ContractViolation(f"velocity out of range 0..127: {vel}")


def enforce_determinism_inputs(
    *,
    tritone_mode: str,
    tritone_seed: Optional[int],
    contract: MusicalContract = MusicalContract(),
) -> None:
    """
    Enforce that probabilistic operations provide a seed for reproducibility.
    
    If tritone_mode is "probabilistic", a seed MUST be provided unless
    contract.require_seed_when_probabilistic is relaxed (not recommended).
    
    Parameters:
        tritone_mode: One of "none", "all_doms", "probabilistic"
        tritone_seed: Optional random seed (required when mode="probabilistic")
        contract: Contract to enforce
    
    Raises:
        ContractViolation: If probabilistic mode used without seed.
    
    Examples:
        >>> enforce_determinism_inputs(tritone_mode="none", tritone_seed=None)  # OK
        >>> enforce_determinism_inputs(tritone_mode="all_doms", tritone_seed=None)  # OK
        >>> enforce_determinism_inputs(tritone_mode="probabilistic", tritone_seed=42)  # OK
        >>> enforce_determinism_inputs(tritone_mode="probabilistic", tritone_seed=None)  # raises
    """
    if (
        contract.require_seed_when_probabilistic
        and tritone_mode == "probabilistic"
        and tritone_seed is None
    ):
        raise ContractViolation(
            "tritone-mode=probabilistic requires --tritone-seed for reproducible output. "
            "Use: zt-band create --tritone-mode probabilistic --tritone-seed 42"
        )
