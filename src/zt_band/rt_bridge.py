"""
RT Bridge: Convert NoteEvents (start_beats/duration_beats) into step-indexed
(step_i, mido.Message) pairs for the real-time scheduler.

This module bridges the locked file-generation engine to the live RT scheduler
without touching the core MIDI writer.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

try:
    import mido
    MIDO_AVAILABLE = True
except ImportError:
    MIDO_AVAILABLE = False
    mido = None  # type: ignore

from .midi_out import NoteEvent

Grid = Literal[8, 16]


@dataclass(frozen=True)
class RtRenderSpec:
    """
    Convert NoteEvents (start_beats/duration_beats) into a step-indexed 2-bar cycle.
    """
    bpm: float
    grid: Grid = 16          # steps per bar (16 = 16th grid, 8 = 8th grid)
    bars_per_cycle: int = 2  # keep RT scheduler cycle aligned to clave module

    # Deterministic rounding for mapping beats->steps
    quantize: Literal["nearest", "down"] = "nearest"


def _beats_per_step(spec: RtRenderSpec) -> float:
    # 4/4: 4 beats per bar
    return 4.0 / float(spec.grid)


def _beats_per_cycle(spec: RtRenderSpec) -> float:
    return 4.0 * float(spec.bars_per_cycle)


def _step_index(start_beats: float, spec: RtRenderSpec, steps_per_cycle: int) -> int:
    bpc = _beats_per_cycle(spec)
    bps = _beats_per_step(spec)
    x = (start_beats % bpc) / bps
    if spec.quantize == "down":
        return int(x // 1) % steps_per_cycle
    return int(round(x)) % steps_per_cycle


def note_events_to_step_messages(
    note_events: list[NoteEvent],
    *,
    spec: RtRenderSpec,
    steps_per_cycle: int,
) -> list[tuple[int, mido.Message]]:
    """
    Convert NoteEvents -> step-indexed (step_i, mido.Message) pairs.
    Produces NOTE_ON at start, NOTE_OFF at end.

    This is the core bridge function that enables live playback of
    engine-generated accompaniment through the RT scheduler.
    """
    if not MIDO_AVAILABLE:
        raise RuntimeError("mido is not installed; cannot use RT bridge")

    out: list[tuple[int, mido.Message]] = []
    bps = _beats_per_step(spec)
    bpc = _beats_per_cycle(spec)

    for ev in note_events:
        # Map start beat to step (mod cycle)
        start_step = _step_index(ev.start_beats, spec, steps_per_cycle)

        # Map end beat to step
        end_beats = ev.start_beats + ev.duration_beats
        end_step_f = ((end_beats % bpc) / bps)
        if spec.quantize == "down":
            end_step = int(end_step_f // 1) % steps_per_cycle
        else:
            end_step = int(round(end_step_f)) % steps_per_cycle

        # Ensure note_off is not the same step as note_on (prevents stuck notes in RT)
        if end_step == start_step:
            end_step = (end_step + 1) % steps_per_cycle

        out.append(
            (start_step, mido.Message("note_on", note=ev.midi_note, velocity=ev.velocity, channel=ev.channel))
        )
        out.append(
            (end_step, mido.Message("note_off", note=ev.midi_note, velocity=0, channel=ev.channel))
        )

    # Deterministic ordering: step, then note_off before note_on at same step
    def _prio(msg: mido.Message) -> int:
        # note_off (or note_on vel=0) comes first at same step
        return 0 if msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0) else 1

    out.sort(key=lambda x: (x[0], _prio(x[1]), x[1].channel, getattr(x[1], "note", 0)))
    return out


def gm_program_changes_at_start() -> list[tuple[int, mido.Message]]:
    """
    Minimal GM setup for live RT: comp=Acoustic Grand (0), bass=Acoustic Bass (32).
    Sent at step 0 of each cycle.
    """
    if not MIDO_AVAILABLE:
        return []
    return [
        (0, mido.Message("program_change", program=0, channel=0)),
        (0, mido.Message("program_change", program=32, channel=1)),
    ]


def truncate_events_to_cycle(
    note_events: list[NoteEvent],
    bars_per_cycle: int,
) -> list[NoteEvent]:
    """
    Keep only events that start within the first N bars (for looping).
    Events outside the cycle boundary are dropped.
    """
    beats_per_cycle = 4.0 * bars_per_cycle
    return [ev for ev in note_events if ev.start_beats < beats_per_cycle]
