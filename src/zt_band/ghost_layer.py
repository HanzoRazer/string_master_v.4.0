"""
Ghost hits layer: low-velocity staccato taps for Brazilian feel.

Ghost hits are deterministic, style-driven, and never override real hits.
They add "air" to samba/bossa grooves without changing harmonic rhythm.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Set, Tuple

from .midi_out import NoteEvent


@dataclass
class GhostSpec:
    """
    Ghost hit configuration (all default OFF).

    ghost_vel:       velocity for ghost taps (0 = disabled, typically 10-25)
    ghost_steps:     list of 16th-note grid steps within the bar to ghost
                     (4/4 bar = steps 0..15; beat 1=0, &1=2, e1=1, a1=3, etc.)
    ghost_len_beats: duration of ghost notes in beats (tiny, e.g. 0.0625 = 1/16)
    ghost_channel:   MIDI channel for ghosts (None = use comp channel)
    """
    ghost_vel: int = 0
    ghost_steps: Tuple[int, ...] = ()
    ghost_len_beats: float = 0.0625  # 1/16 note default
    ghost_channel: Optional[int] = None


def add_ghost_hits(
    events: List[NoteEvent],
    chord_pitches: List[int],
    *,
    bar_start_beats: float,
    beats_per_bar: int,
    ghost_spec: GhostSpec,
    comp_channel: int = 0,
) -> List[NoteEvent]:
    """
    Add low-velocity staccato ghost chord taps at selected grid steps.

    - Deterministic (no randomness)
    - Never overwrites real hits
    - Returns new list with ghost events appended

    Parameters
    ----------
    events:
        Existing comp events for this bar.
    chord_pitches:
        List of MIDI pitches for the current chord voicing.
    bar_start_beats:
        Start time of this bar in beats.
    beats_per_bar:
        Number of beats per bar (4 for 4/4, 2 for 2/4).
    ghost_spec:
        Ghost hit configuration.
    comp_channel:
        Default MIDI channel if ghost_channel not specified.

    Returns
    -------
    New list with ghost events appended (original events unchanged).
    """
    if ghost_spec.ghost_vel <= 0:
        return events
    if not ghost_spec.ghost_steps:
        return events
    if not chord_pitches:
        return events

    # Calculate step duration in beats (16 steps per 4/4 bar)
    steps_per_bar = beats_per_bar * 4  # 16 for 4/4, 8 for 2/4
    step_duration_beats = beats_per_bar / steps_per_bar

    # Find occupied steps (where real hits already exist)
    occupied_steps: Set[int] = set()
    for e in events:
        if e.channel == comp_channel:
            # Convert beat position to step
            relative_beat = e.start_beats - bar_start_beats
            if 0 <= relative_beat < beats_per_bar:
                step = int(relative_beat / step_duration_beats)
                occupied_steps.add(step)

    vel = max(1, min(int(ghost_spec.ghost_vel), 127))
    channel = ghost_spec.ghost_channel if ghost_spec.ghost_channel is not None else comp_channel
    length = ghost_spec.ghost_len_beats

    # Pick 3 chord tones for muted tap feel
    ghost_pitches = chord_pitches[:3] if len(chord_pitches) >= 3 else chord_pitches

    out = list(events)

    for step in ghost_spec.ghost_steps:
        step_idx = int(step) % steps_per_bar
        if step_idx in occupied_steps:
            continue  # don't collide with real hit

        ghost_start_beats = bar_start_beats + (step_idx * step_duration_beats)

        for pitch in ghost_pitches:
            out.append(
                NoteEvent(
                    start_beats=ghost_start_beats,
                    duration_beats=length,
                    midi_note=pitch,
                    velocity=vel,
                    channel=channel,
                )
            )

    return out


# Common ghost step presets (4/4 bar, 16 steps)
# Beat positions: 1=0, &1=2, 2=4, &2=6, 3=8, &3=10, 4=12, &4=14
# "e" positions (between beat and &): 1e=1, 2e=5, 3e=9, 4e=13
# "a" positions (between & and next beat): 1a=3, 2a=7, 3a=11, 4a=15

GHOST_STEPS_E_ALL = (1, 5, 9, 13)       # "e" of each beat — subtle Brazilian feel
GHOST_STEPS_A_ALL = (3, 7, 11, 15)      # "a" of each beat — more aggressive
GHOST_STEPS_E_OFFBEAT = (5, 13)         # "e" of 2 and 4 only — minimal
GHOST_STEPS_TAMBORIM = (1, 3, 5, 7, 9, 11, 13, 15)  # all 16ths except main hits


# Default ghost spec for Brazilian samba feel
GHOST_SPEC_BRAZIL = GhostSpec(
    ghost_vel=14,
    ghost_steps=GHOST_STEPS_E_ALL,
    ghost_len_beats=0.0625,
)

GHOST_SPEC_OFF = GhostSpec()  # disabled
