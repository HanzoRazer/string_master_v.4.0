"""
Expressive layer: swing and humanize post-processing for main engine.

Safe-by-design: never changes chord logic, fully bypassable.
"""
from __future__ import annotations

import random
from collections.abc import Iterable
from dataclasses import dataclass

from .midi_out import NoteEvent


@dataclass(frozen=True)
class ExpressiveSpec:
    """
    Expressive layer specification.

    All parameters default to OFF (0.0 or 0) so the core remains unchanged
    unless explicitly requested.

    Attributes:
        swing: 0..1, applied to 8th offbeats (0 = straight, 1 = max swing)
        humanize_ms: +/- ms jitter for timing (0 = perfect timing)
        humanize_vel: +/- velocity jitter (0 = consistent velocity)
        seed: Random seed for reproducible humanization
    """
    swing: float = 0.0
    humanize_ms: float = 0.0
    humanize_vel: int = 0
    seed: int | None = None


def apply_expressive(
    events: Iterable[NoteEvent],
    *,
    spec: ExpressiveSpec,
    tempo_bpm: int,
) -> list[NoteEvent]:
    """
    Apply swing and humanize to note events.

    This is a pure post-processing layer that does NOT change:
    - Chord logic
    - Note counts
    - MIDI structure

    Can be bypassed by setting all spec values to 0.

    Parameters:
        events: Input note events (from generator)
        spec: Expressive specification
        tempo_bpm: Tempo for beats->seconds conversion

    Returns:
        New list of events with expressive adjustments applied.
    """
    if spec.swing <= 0 and spec.humanize_ms <= 0 and spec.humanize_vel <= 0:
        # Bypass: return unchanged
        return list(events)

    rng = random.Random(spec.seed)

    # beats -> seconds conversion
    sec_per_beat = 60.0 / max(1, tempo_bpm)
    jitter_beats = (spec.humanize_ms / 1000.0) / sec_per_beat if spec.humanize_ms > 0 else 0.0

    out: list[NoteEvent] = []
    for ev in events:
        t = ev.start_beats

        # Swing: delay the "and" of each beat (8th offbeat) by a fraction of an 8th
        if spec.swing > 0:
            frac = t - int(t)
            # treat ~0.5 as offbeat (8th note grid)
            if abs(frac - 0.5) < 1e-6:
                t += 0.5 * spec.swing  # max adds a 16th-note delay

        # Humanize timing
        if jitter_beats > 0:
            t += rng.uniform(-jitter_beats, jitter_beats)
            if t < 0:
                t = 0.0

        # Humanize velocity
        v = ev.velocity
        if spec.humanize_vel > 0:
            v = max(1, min(127, v + rng.randint(-spec.humanize_vel, spec.humanize_vel)))

        out.append(NoteEvent(
            start_beats=t,
            duration_beats=ev.duration_beats,
            midi_note=ev.midi_note,
            velocity=v,
            channel=ev.channel,
        ))

    return out
