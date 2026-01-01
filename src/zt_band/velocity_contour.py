"""
Velocity contour: per-bar velocity shaping for Brazilian "breathing" feel.

This is a style-only additive that scales existing note velocities
without changing timing grid, swing, note ordering, or chord selection.

The contour applies:
- Beat 1 = soft
- &2 = strong
- Beat 3 = soft
- &4 = strong
- Pickup = very soft
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Set, Tuple, Optional

from .midi_out import NoteEvent


@dataclass(frozen=True)
class VelContour:
    """
    Velocity contour configuration (default OFF).

    enabled:     whether to apply contour (False = pass-through)
    base:        reference velocity (unused if we scale existing velocities)
    soft_mul:    multiplier for beats 1, 3 (soft)
    strong_mul:  multiplier for &2, &4 (strong)
    pickup_mul:  multiplier for pickup anticipation hits
    ghost_mul:   optional multiplier for ghost hits (1.0 = no change)
    """
    enabled: bool = False
    base: int = 72
    soft_mul: float = 0.80
    strong_mul: float = 1.08
    pickup_mul: float = 0.65
    ghost_mul: float = 1.0


def _clamp_vel(v: int) -> int:
    """Clamp velocity to MIDI range [1, 127]."""
    if v < 1:
        return 1
    if v > 127:
        return 127
    return v


def apply_velocity_contour_4_4(
    events: List[NoteEvent],
    *,
    bar_steps: int,
    contour: VelContour,
    pickup_steps: Optional[Set[int]] = None,
    ghost_steps: Optional[Set[int]] = None,
) -> List[NoteEvent]:
    """
    Apply per-bar velocity contour for 4/4 with 16-step grid.

    Only modifies note velocity. Deterministic.

    Parameters
    ----------
    events:
        List of NoteEvent (start_beats, duration_beats, midi_note, velocity, channel).
    bar_steps:
        Steps per bar (16 for 4/4).
    contour:
        VelContour configuration.
    pickup_steps:
        Set of step indices that are pickup anticipations (apply pickup_mul).
    ghost_steps:
        Set of step indices that are ghost hits (optionally apply ghost_mul).

    Returns
    -------
    New list of NoteEvent with scaled velocities.
    """
    if not contour.enabled:
        return events

    if bar_steps != 16:
        # Only support 16-step 4/4 grid in this micro
        return events

    pickup_steps = pickup_steps or set()
    ghost_steps = ghost_steps or set()

    # Step groups for 16-step 4/4:
    # Beat 1 = step 0, Beat 2 = step 4, Beat 3 = step 8, Beat 4 = step 12
    # &1 = step 2, &2 = step 6, &3 = step 10, &4 = step 14
    soft_steps = {0, 8}      # beat 1, beat 3
    strong_steps = {6, 14}   # &2, &4

    out: List[NoteEvent] = []

    for e in events:
        # Calculate step within bar
        bar_beat = e.start_beats % 4  # position within 4/4 bar
        step = int(bar_beat * 4) % bar_steps  # convert to 16th-note step

        v0 = e.velocity

        # Determine multiplier
        if step in pickup_steps:
            mul = contour.pickup_mul
        elif step in strong_steps:
            mul = contour.strong_mul
        elif step in soft_steps:
            mul = contour.soft_mul
        else:
            mul = 1.0

        # Apply ghost multiplier on top if applicable
        if step in ghost_steps and contour.ghost_mul != 1.0:
            mul *= contour.ghost_mul

        v = _clamp_vel(int(round(v0 * mul)))

        # Create new NoteEvent with adjusted velocity
        out.append(NoteEvent(
            start_beats=e.start_beats,
            duration_beats=e.duration_beats,
            midi_note=e.midi_note,
            velocity=v,
            channel=e.channel,
        ))

    return out


def apply_velocity_contour_2_4(
    events: List[NoteEvent],
    *,
    bar_steps: int,
    contour: VelContour,
    pickup_steps: Optional[Set[int]] = None,
    ghost_steps: Optional[Set[int]] = None,
) -> List[NoteEvent]:
    """
    Apply per-bar velocity contour for 2/4 with 8-step grid.

    For 2/4 samba:
    - Beat 1 = soft
    - &2 = strong

    Parameters
    ----------
    events:
        List of NoteEvent.
    bar_steps:
        Steps per bar (8 for 2/4).
    contour:
        VelContour configuration.
    pickup_steps:
        Set of step indices for pickup hits.
    ghost_steps:
        Set of step indices for ghost hits.

    Returns
    -------
    New list of NoteEvent with scaled velocities.
    """
    if not contour.enabled:
        return events

    if bar_steps != 8:
        return events

    pickup_steps = pickup_steps or set()
    ghost_steps = ghost_steps or set()

    # Step groups for 8-step 2/4:
    # Beat 1 = step 0, Beat 2 = step 4
    # &1 = step 2, &2 = step 6
    soft_steps = {0}         # beat 1
    strong_steps = {6}       # &2

    out: List[NoteEvent] = []

    for e in events:
        bar_beat = e.start_beats % 2  # position within 2/4 bar
        step = int(bar_beat * 4) % bar_steps

        v0 = e.velocity

        if step in pickup_steps:
            mul = contour.pickup_mul
        elif step in strong_steps:
            mul = contour.strong_mul
        elif step in soft_steps:
            mul = contour.soft_mul
        else:
            mul = 1.0

        if step in ghost_steps and contour.ghost_mul != 1.0:
            mul *= contour.ghost_mul

        v = _clamp_vel(int(round(v0 * mul)))

        out.append(NoteEvent(
            start_beats=e.start_beats,
            duration_beats=e.duration_beats,
            midi_note=e.midi_note,
            velocity=v,
            channel=e.channel,
        ))

    return out


def apply_velocity_contour(
    events: List[NoteEvent],
    *,
    meter: str,
    bar_steps: int,
    contour: VelContour,
    pickup_steps: Optional[Set[int]] = None,
    ghost_steps: Optional[Set[int]] = None,
) -> List[NoteEvent]:
    """
    Unified dispatcher for velocity contour. Strict:
      - meter "4/4" requires bar_steps == 16
      - meter "2/4" requires bar_steps == 8

    If meter/steps mismatch or contour disabled, returns events unchanged (safe).

    Parameters
    ----------
    events:
        List of NoteEvent to process.
    meter:
        Time signature string ("4/4" or "2/4").
    bar_steps:
        Steps per bar (16 for 4/4, 8 for 2/4).
    contour:
        VelContour configuration.
    pickup_steps:
        Set of step indices for pickup hits.
    ghost_steps:
        Set of step indices for ghost hits.

    Returns
    -------
    List of NoteEvent with scaled velocities (or unchanged if meter/steps mismatch).
    """
    if not contour.enabled:
        return events

    m = str(meter).strip()

    if m == "4/4":
        if bar_steps != 16:
            return events
        return apply_velocity_contour_4_4(
            events,
            bar_steps=bar_steps,
            contour=contour,
            pickup_steps=pickup_steps,
            ghost_steps=ghost_steps,
        )

    if m == "2/4":
        if bar_steps != 8:
            return events
        return apply_velocity_contour_2_4(
            events,
            bar_steps=bar_steps,
            contour=contour,
            pickup_steps=pickup_steps,
            ghost_steps=ghost_steps,
        )

    # Unknown meter: do nothing (strict & safe)
    return events