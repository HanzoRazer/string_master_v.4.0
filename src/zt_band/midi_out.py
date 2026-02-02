"""
MIDI file generation and output utilities.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

try:
    import mido
    MIDO_AVAILABLE = True
except ImportError:
    MIDO_AVAILABLE = False


@dataclass
class NoteEvent:
    """
    Represents a single MIDI note event.

    Attributes:
        start_beats: Start time in beats (quarter notes)
        duration_beats: Duration in beats
        midi_note: MIDI note number (0-127)
        velocity: Note velocity (0-127)
        channel: MIDI channel (0-15)
    """
    start_beats: float
    duration_beats: float
    midi_note: int
    velocity: int
    channel: int = 0


def write_midi_file(
    comp_events: list[NoteEvent],
    bass_events: list[NoteEvent],
    tempo_bpm: int = 120,
    outfile: str = "backing.mid",
    meter: Tuple[int, int] = (4, 4),
) -> None:
    """
    Write MIDI note events to a .mid file with enforced stability invariants.

    Invariants enforced:
    - SMF Type 1 (multiple tracks)
    - Tempo meta-event at time 0
    - Time signature meta-event at time 0
    - Stable track names ("Comping", "Bass")
    - No stuck notes (verified after rendering)

    Parameters:
        comp_events: List of comping track events
        bass_events: List of bass track events
        tempo_bpm: Tempo in beats per minute
        outfile: Output filename
        meter: Time signature as (numerator, denominator), e.g. (4, 4) or (3, 4).
               Phase 6.0+: Used for MIDI time signature meta event.

    Raises:
        ImportError: If mido library is not installed
        ValueError: If stuck notes detected (unbalanced note on/off)
    """
    if not MIDO_AVAILABLE:
        raise ImportError(
            "mido library required for MIDI output. Install with: pip install mido"
        )

    # Validate tempo range (1-999 BPM reasonable for MIDI)
    if not (1 <= tempo_bpm <= 999):
        raise ValueError(f"tempo_bpm out of reasonable range 1-999: {tempo_bpm}")

    # Create MIDI file with multiple tracks (Type 1)
    ticks_per_beat = 480  # canonical resolution for this repo
    mid = mido.MidiFile(type=1, ticks_per_beat=ticks_per_beat)

    # Track 0: Tempo + time signature at time 0 (INVARIANT)
    tempo_track = mido.MidiTrack()
    mid.tracks.append(tempo_track)
    tempo_track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(tempo_bpm), time=0))
    # Phase 6.0: Use meter parameter for time signature
    meter_num, meter_denom = meter
    tempo_track.append(mido.MetaMessage('time_signature', numerator=meter_num, denominator=meter_denom, time=0))

    # Track 1: Comping (piano/guitar)
    comp_track = mido.MidiTrack()
    mid.tracks.append(comp_track)
    comp_track.append(mido.MetaMessage('track_name', name='Comping', time=0))
    comp_track.append(mido.Message('program_change', program=0, time=0))  # Acoustic Grand Piano

    _add_events_to_track(comp_track, comp_events, ticks_per_beat=ticks_per_beat)

    # Track 2: Bass
    bass_track = mido.MidiTrack()
    mid.tracks.append(bass_track)
    bass_track.append(mido.MetaMessage('track_name', name='Bass', time=0))
    bass_track.append(mido.Message('program_change', program=32, time=0))  # Acoustic Bass

    _add_events_to_track(bass_track, bass_events, ticks_per_beat=ticks_per_beat)

    # Verify no stuck notes before saving (INVARIANT)
    _verify_no_stuck_notes(mid)

    # Save file
    mid.save(outfile)


def _add_events_to_track(
    track: mido.MidiTrack,
    events: list[NoteEvent],
    *,
    ticks_per_beat: int,
) -> None:
    """
    Convert NoteEvent objects to MIDI messages and add to track.

    Uses priority-based ordering: note_off before note_on at same tick
    to prevent stuck notes on re-articulation.
    """
    if not events:
        return

    # Create list of (absolute_tick, priority, message) tuples
    # priority: note_off before note_on at same tick to avoid stuck notes on re-articulation
    messages_with_time: list[tuple[int, int, mido.Message]] = []

    for event in events:
        if event.duration_beats <= 0:
            # zero/negative duration should never happen; make it non-fatal but deterministic
            continue

        start_tick = int(round(event.start_beats * ticks_per_beat))
        end_tick = int(round((event.start_beats + event.duration_beats) * ticks_per_beat))
        if end_tick <= start_tick:
            end_tick = start_tick + 1  # minimum 1 tick duration

        # Note on (priority 1)
        messages_with_time.append(
            (start_tick, 1,
             mido.Message('note_on', note=event.midi_note, velocity=event.velocity, channel=event.channel))
        )

        # Note off (priority 0 - comes before note_on at same tick)
        messages_with_time.append(
            (end_tick, 0,
             mido.Message('note_off', note=event.midi_note, velocity=0, channel=event.channel))
        )

    # Sort by time, then priority (off before on)
    messages_with_time.sort(key=lambda x: (x[0], x[1]))

    # Convert to delta times and add to track
    last_tick = 0
    for abs_tick, _prio, msg in messages_with_time:
        delta = abs_tick - last_tick
        msg.time = delta
        track.append(msg)
        last_tick = abs_tick

    # End of track
    track.append(mido.MetaMessage('end_of_track', time=0))


def list_midi_ports() -> list[str]:
    """
    List available MIDI output ports.

    Returns:
        List of port names

    Raises:
        ImportError: If mido library is not installed
    """
    if not MIDO_AVAILABLE:
        raise ImportError(
            "mido library required. Install with: pip install mido python-rtmidi"
        )

    return mido.get_output_names()


def _verify_no_stuck_notes(mid: mido.MidiFile) -> None:
    """
    Verify that all note_on events have corresponding note_off events.

    Scans all tracks and ensures balanced note on/off per (channel, note) tuple.

    Raises:
        ValueError: If any notes are stuck (unbalanced on/off).
    """
    from collections import defaultdict

    # Track note balance per (channel, note)
    note_balance: dict[tuple[int, int], int] = defaultdict(int)

    for track in mid.tracks:
        for msg in track:
            if msg.type == 'note_on' and msg.velocity > 0:
                note_balance[(msg.channel, msg.note)] += 1
            elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                note_balance[(msg.channel, msg.note)] -= 1

    # Check for imbalances
    stuck_notes = [(ch, note) for (ch, note), bal in note_balance.items() if bal != 0]

    if stuck_notes:
        raise ValueError(
            f"Stuck notes detected (unbalanced note on/off): {stuck_notes}. "
            "This indicates a bug in event generation."
        )
