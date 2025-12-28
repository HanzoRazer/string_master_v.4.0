"""
MIDI file generation and output utilities.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

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
    comp_events: List[NoteEvent],
    bass_events: List[NoteEvent],
    tempo_bpm: int = 120,
    outfile: str = "backing.mid",
) -> None:
    """
    Write MIDI note events to a .mid file.
    
    Parameters:
        comp_events: List of comping track events
        bass_events: List of bass track events
        tempo_bpm: Tempo in beats per minute
        outfile: Output filename
    
    Raises:
        ImportError: If mido library is not installed
    """
    if not MIDO_AVAILABLE:
        raise ImportError(
            "mido library required for MIDI output. Install with: pip install mido"
        )
    
    # Create MIDI file with two tracks
    mid = mido.MidiFile(type=1)
    
    # Track 0: Tempo track
    tempo_track = mido.MidiTrack()
    mid.tracks.append(tempo_track)
    tempo_track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(tempo_bpm), time=0))
    
    # Track 1: Comping (piano/guitar)
    comp_track = mido.MidiTrack()
    mid.tracks.append(comp_track)
    comp_track.append(mido.MetaMessage('track_name', name='Comping', time=0))
    comp_track.append(mido.Message('program_change', program=0, time=0))  # Acoustic Grand Piano
    
    _add_events_to_track(comp_track, comp_events, tempo_bpm)
    
    # Track 2: Bass
    bass_track = mido.MidiTrack()
    mid.tracks.append(bass_track)
    bass_track.append(mido.MetaMessage('track_name', name='Bass', time=0))
    bass_track.append(mido.Message('program_change', program=32, time=0))  # Acoustic Bass
    
    _add_events_to_track(bass_track, bass_events, tempo_bpm)
    
    # Save file
    mid.save(outfile)


def _add_events_to_track(track: 'mido.MidiTrack', events: List[NoteEvent], tempo_bpm: int) -> None:
    """
    Convert NoteEvent objects to MIDI messages and add to track.
    
    Uses absolute timing internally, then converts to delta times.
    """
    if not events:
        return
    
    # Convert beat times to MIDI ticks
    ticks_per_beat = 480  # Standard MIDI resolution
    
    # Create list of (absolute_tick, message) tuples
    messages_with_time: List[tuple[int, 'mido.Message']] = []
    
    for event in events:
        start_tick = int(event.start_beats * ticks_per_beat)
        end_tick = int((event.start_beats + event.duration_beats) * ticks_per_beat)
        
        # Note on
        messages_with_time.append((
            start_tick,
            mido.Message('note_on', note=event.midi_note, velocity=event.velocity, channel=event.channel)
        ))
        
        # Note off
        messages_with_time.append((
            end_tick,
            mido.Message('note_off', note=event.midi_note, velocity=0, channel=event.channel)
        ))
    
    # Sort by absolute time
    messages_with_time.sort(key=lambda x: x[0])
    
    # Convert to delta times and add to track
    last_tick = 0
    for abs_tick, msg in messages_with_time:
        delta = abs_tick - last_tick
        msg.time = delta
        track.append(msg)
        last_tick = abs_tick
    
    # End of track
    track.append(mido.MetaMessage('end_of_track', time=0))


def list_midi_ports() -> List[str]:
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
