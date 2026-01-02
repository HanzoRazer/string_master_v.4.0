"""
Expressive layer for MIDI generation.

Stability-first: modifies velocity only, never timing.
Future layers (swing, humanize) can be added as separate opt-in modules.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from .contract import NoteEvent


@dataclass(frozen=True)
class VelocityShape:
    """
    Expressive layer that does NOT alter note timing.
    Stability-first: velocity only.
    """
    base: int = 78
    downbeat_boost: int = 14   # beat 1
    midbeat_boost: int = 8     # beat 3 (in 4/4)
    offbeat_cut: int = 6       # & of beats / lighter hits
    min_vel: int = 30
    max_vel: int = 115

    def clamp(self, v: int) -> int:
        return max(self.min_vel, min(self.max_vel, v))


def apply_velocity_shape(
    events: Iterable[NoteEvent],
    *,
    ticks_per_beat: int,
    shape: VelocityShape = VelocityShape(),
) -> list[NoteEvent]:
    """
    Simple groove: accents downbeats. No randomness. No timing edits.
    Works even if you later add swing/humanize in a separate (optional) layer.
    """
    out: list[NoteEvent] = []
    for e in events:
        beat_index = (e.start_tick // ticks_per_beat) % 4  # assumes 4/4 feel
        tick_in_beat = e.start_tick % ticks_per_beat
        is_offbeat = tick_in_beat >= (ticks_per_beat // 2)

        v = shape.base
        if beat_index == 0 and not is_offbeat:
            v += shape.downbeat_boost
        elif beat_index == 2 and not is_offbeat:
            v += shape.midbeat_boost
        elif is_offbeat:
            v -= shape.offbeat_cut

        out.append(
            NoteEvent(
                track=e.track,
                start_tick=e.start_tick,
                dur_tick=e.dur_tick,
                channel=e.channel,
                note=e.note,
                velocity=shape.clamp(v),
            )
        )
    return out
