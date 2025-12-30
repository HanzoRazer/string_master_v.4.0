"""
Tests for MIDI contract enforcement and timing engine.

Locks in stability by verifying:
- Meta events at time 0
- No stuck notes
- Contract violations are caught
"""

from __future__ import annotations

import pytest

from zt_band.contract import ProgramSpec, NoteEvent, ContractViolation
from zt_band.timing import build_midi_type1


def test_meta_events_at_time_zero():
    program = ProgramSpec(tempo_bpm=120, ticks_per_beat=480)
    events = [
        NoteEvent(track="Comp", start_tick=0, dur_tick=240, channel=0, note=60, velocity=90),
        NoteEvent(track="Comp", start_tick=240, dur_tick=240, channel=0, note=64, velocity=90),
    ]
    mid = build_midi_type1(program=program, events=events, track_order=["Comp"])
    # Track 0 should have tempo + timesig at t=0
    t0 = mid.tracks[0]
    assert any(getattr(m, "type", None) == "set_tempo" and m.time == 0 for m in t0)
    assert any(getattr(m, "type", None) == "time_signature" and m.time == 0 for m in t0)


def test_no_stuck_notes_enforced():
    program = ProgramSpec(tempo_bpm=120, ticks_per_beat=480)
    bad = [
        NoteEvent(track="Comp", start_tick=0, dur_tick=240, channel=0, note=60, velocity=90),
        # invalid: dur_tick <= 0 (would lead to broken timing)
        NoteEvent(track="Comp", start_tick=240, dur_tick=0, channel=0, note=64, velocity=90),
    ]
    with pytest.raises(ContractViolation):
        build_midi_type1(program=program, events=bad, track_order=["Comp"])


def test_program_spec_validation():
    # Valid
    ProgramSpec(tempo_bpm=120).validate()
    
    # Invalid tempo
    with pytest.raises(ContractViolation):
        ProgramSpec(tempo_bpm=500).validate()
    
    # Invalid time signature denominator
    with pytest.raises(ContractViolation):
        ProgramSpec(tempo_bpm=120, time_sig_den=3).validate()


def test_note_event_validation():
    # Valid
    NoteEvent(track="Test", start_tick=0, dur_tick=240, channel=0, note=60, velocity=90).validate()
    
    # Invalid: negative start_tick
    with pytest.raises(ContractViolation):
        NoteEvent(track="Test", start_tick=-1, dur_tick=240, channel=0, note=60, velocity=90).validate()
    
    # Invalid: zero duration
    with pytest.raises(ContractViolation):
        NoteEvent(track="Test", start_tick=0, dur_tick=0, channel=0, note=60, velocity=90).validate()
    
    # Invalid: note out of range
    with pytest.raises(ContractViolation):
        NoteEvent(track="Test", start_tick=0, dur_tick=240, channel=0, note=128, velocity=90).validate()
    
    # Invalid: empty track name
    with pytest.raises(ContractViolation):
        NoteEvent(track="", start_tick=0, dur_tick=240, channel=0, note=60, velocity=90).validate()
