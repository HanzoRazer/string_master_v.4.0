"""
Expressive layer for MIDI output: velocity shaping ONLY (no timing changes).

This module adds musical "feel" by adjusting velocity based on beat position,
following the stability-first principle: never modify timing, only dynamics.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List


@dataclass(frozen=True)
class VelocityProfile:
    # "Feel" without timing edits
    downbeat_boost: int = 12   # beat 1
    midbeat_boost: int = 7     # beat 3 in 4/4
    offbeat_cut: int = 6       # & of beat
    min_vel: int = 20
    max_vel: int = 120


def _clamp(v: int, mn: int, mx: int) -> int:
    """Clamp value to range [mn, mx]."""
    return max(mn, min(mx, v))


def apply_velocity_profile(events: Iterable[object], profile: VelocityProfile = VelocityProfile()) -> List[object]:
    out: List[object] = []
    for e in events:
        start = float(getattr(e, "start_beats"))
        vel = int(getattr(e, "velocity"))

        beat_in_bar = start % 4.0
        tick = beat_in_bar - int(beat_in_bar)
        is_offbeat = abs(tick - 0.5) < 1e-9

        v = vel
        if abs(beat_in_bar - 0.0) < 1e-9:
            v = vel + profile.downbeat_boost
        elif abs(beat_in_bar - 2.0) < 1e-9:
            v = vel + profile.midbeat_boost
        elif is_offbeat:
            v = vel - profile.offbeat_cut

        v = _clamp(v, profile.min_vel, profile.max_vel)

        # Works with your dataclass NoteEvent (has __dict__)
        e2 = type(e)(**{**e.__dict__, "velocity": v})
        out.append(e2)

    return out
