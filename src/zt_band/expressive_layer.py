"""
Expressive layer for MIDI output: velocity shaping ONLY (no timing changes).

This module adds musical "feel" by adjusting velocity based on beat position,
following the stability-first principle: never modify timing, only dynamics.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Iterable, List, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class VelocityProfile:
    """
    Expressive velocity shaping for 4/4 time feel.
    
    Accents strong beats (1 and 3), lightens offbeats, clamps to MIDI range.
    All adjustments are deterministic based on beat position only.
    
    Attributes:
        downbeat_boost: Velocity increase for beat 1 (downbeat)
        midbeat_boost: Velocity increase for beat 3 (midpoint of bar)
        offbeat_cut: Velocity decrease for offbeats (e.g., 1.5, 2.5, 3.5, 4.5)
        min_vel: Minimum allowed velocity after shaping (MIDI 1-127 range)
        max_vel: Maximum allowed velocity after shaping (MIDI 1-127 range)
    
    Examples:
        >>> profile = VelocityProfile()  # defaults
        >>> profile.downbeat_boost
        12
        >>> custom = VelocityProfile(downbeat_boost=15, offbeat_cut=10)
    """
    downbeat_boost: int = 12
    midbeat_boost: int = 7
    offbeat_cut: int = 6
    min_vel: int = 20
    max_vel: int = 120


def _clamp(v: int, mn: int, mx: int) -> int:
    """Clamp value to range [mn, mx]."""
    return max(mn, min(mx, v))


def apply_velocity_profile(
    events: Iterable[T],
    *,
    profile: VelocityProfile = VelocityProfile(),
) -> List[T]:
    """
    Apply velocity shaping to events based on their beat position.
    
    Returns NEW event objects with adjusted velocity. Original events unchanged.
    
    Beat position logic (4/4 time):
    - Beat 1 (downbeat): +downbeat_boost
    - Beat 3 (midbar): +midbeat_boost
    - Offbeats (x.5): -offbeat_cut
    - All others: unchanged
    
    All velocities are clamped to [min_vel, max_vel] after adjustment.
    
    Parameters:
        events: Iterable of event objects with attributes:
            - start_beats: float (beat position)
            - velocity: int (original velocity)
            Plus any other attributes (preserved via dataclass replace)
        profile: VelocityProfile to apply (defaults to standard swing feel)
    
    Returns:
        List of new event objects with adjusted velocities.
    
    Requires:
        Events must be dataclass instances (for replace() to work).
    
    Examples:
        >>> from midi_out import NoteEvent
        >>> events = [
        ...     NoteEvent(0.0, 1.0, 60, 80, 0),   # downbeat: +12 → 92
        ...     NoteEvent(0.5, 0.5, 62, 80, 0),   # offbeat: -6 → 74
        ...     NoteEvent(2.0, 1.0, 64, 80, 0),   # beat 3: +7 → 87
        ... ]
        >>> shaped = apply_velocity_profile(events)
        >>> [e.velocity for e in shaped]
        [92, 74, 87]
    """
    out: List[T] = []
    for e in events:
        start = float(getattr(e, "start_beats"))
        vel = int(getattr(e, "velocity"))

        # Determine beat position within 4/4 bar
        beat_in_bar = start % 4.0
        is_offbeat = abs(beat_in_bar - (int(beat_in_bar) + 0.5)) < 1e-9

        # Apply position-based velocity adjustment
        v = vel
        if abs(beat_in_bar - 0.0) < 1e-9:  # Beat 1 (downbeat)
            v = vel + profile.downbeat_boost
        elif abs(beat_in_bar - 2.0) < 1e-9:  # Beat 3 (midbar)
            v = vel + profile.midbeat_boost
        elif is_offbeat:  # Offbeats (0.5, 1.5, 2.5, 3.5)
            v = vel - profile.offbeat_cut

        # Clamp to MIDI range
        v = _clamp(v, profile.min_vel, profile.max_vel)

        # Create new event with adjusted velocity (dataclass replace)
        e2 = replace(e, velocity=v)  # type: ignore[call-overload]
        out.append(e2)

    return out
