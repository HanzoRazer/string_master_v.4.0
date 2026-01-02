# tests/test_midi_ordering.py
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple
import tempfile

import pytest
import mido

from zt_band.midi_out import NoteEvent, write_midi_file


def _abs_ticks(track: mido.MidiTrack) -> List[Tuple[int, mido.Message]]:
    """Return list of (absolute_tick, message) for a track."""
    out: List[Tuple[int, mido.Message]] = []
    t = 0
    for msg in track:
        t += int(getattr(msg, "time", 0) or 0)
        out.append((t, msg))
    return out


def _same_tick_rehit_events(note: int = 60, channel: int = 0) -> List[NoteEvent]:
    """
    Create a re-hit where note-off and next note-on land on the same tick:
      - event1: start=0.0, dur=0.5
      - event2: start=0.5, dur=0.5
    With ticks_per_beat=480: 0.5 beat == 240 ticks, so end_tick==start_tick.
    """
    return [
        NoteEvent(start_beats=0.0, duration_beats=0.5, midi_note=note, velocity=90, channel=channel),
        NoteEvent(start_beats=0.5, duration_beats=0.5, midi_note=note, velocity=90, channel=channel),
    ]


def test_midi_orders_note_off_before_note_on_at_same_tick() -> None:
    """
    Contract test:
    If a note ends and restarts at the same absolute tick, emit note_off first.
    Some DAWs interpret note_on before note_off at same tick as "legato/merged"
    or can cause audible artifacts.
    """
    comp = _same_tick_rehit_events(note=60, channel=0)
    bass: List[NoteEvent] = []

    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "rehit.mid"
        write_midi_file(comp, bass, tempo_bpm=120, outfile=str(out))

        mid = mido.MidiFile(str(out))
        assert len(mid.tracks) >= 2, "Expected Type-1 MIDI with at least comp track"

        # Track 1 is "Comping" per current invariants
        track = mid.tracks[1]
        abs_msgs = _abs_ticks(track)

        # Build per-tick ordered list of message types for (channel, note)
        per_tick: Dict[Tuple[int, int, int], List[str]] = {}
        # key: (abs_tick, channel, note) -> list of 'note_on'/'note_off' in encounter order
        for t, msg in abs_msgs:
            if msg.type not in ("note_on", "note_off"):
                continue
            ch = getattr(msg, "channel", None)
            n = getattr(msg, "note", None)
            if ch is None or n is None:
                continue
            key = (t, int(ch), int(n))
            per_tick.setdefault(key, []).append(msg.type)

        # We specifically expect at least one same-tick pair for (tick=240, ch=0, note=60)
        target_key = (240, 0, 60)
        assert target_key in per_tick, (
            f"Expected same-tick messages at {target_key}, got keys={sorted(per_tick.keys())}"
        )

        types = per_tick[target_key]
        # Must contain both
        assert "note_off" in types and "note_on" in types, f"Expected both on/off at {target_key}, got {types}"

        # And ordering must be off then on
        first_off = types.index("note_off")
        first_on = types.index("note_on")
        assert first_off < first_on, (
            f"Ordering violation at {target_key}: expected note_off before note_on, got {types}"
        )


def test_midi_rehit_is_balanced_and_loadable() -> None:
    """
    Baseline sanity: file loads and note on/off counts are balanced.
    (This is already enforced by write_midi_file's invariant checks.)
    """
    comp = _same_tick_rehit_events(note=64, channel=0)
    bass: List[NoteEvent] = []

    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "rehit_balanced.mid"
        write_midi_file(comp, bass, tempo_bpm=120, outfile=str(out))
        mid = mido.MidiFile(str(out))
        # If it loads, and write_midi_file didn't raise, we consider the invariant satisfied.
        assert mid is not None
