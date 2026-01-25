"""
MIDI Backing Track Generator for Jazz Practice.

Generates multi-track MIDI files with:
- Guitar licks (bebop lines over tritone subs)
- Basslines (root-5-walk-up patterns)
- Shell chord voicings (1-3-7)
- Optional metronome

Usage:
    python -m zt_band.midi_backing_generator [--output FILE] [--loops N] [--no-drums]
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

from mido import Message, MidiFile, MidiTrack, MetaMessage


# =============================================================================
# Constants
# =============================================================================

DEFAULT_TEMPO_BPM = 120
MICROSECONDS_PER_MINUTE = 60_000_000
TICKS_PER_BEAT = 480

# GM Patches
PATCH_NYLON_GUITAR = 24
PATCH_ACOUSTIC_BASS = 33
PATCH_ACOUSTIC_PIANO = 1

# Channels
CH_GUITAR = 0
CH_BASS = 1
CH_CHORD = 2
CH_DRUM = 9  # GM standard drum channel

# Drum notes
HIHAT_CLOSED = 42
KICK = 36
SNARE = 38


# =============================================================================
# Data Structures
# =============================================================================

@dataclass
class NoteEvent:
    """A single note with pitch, duration, and velocity."""
    pitch: int
    duration_ticks: int
    velocity: int = 80


@dataclass
class Phrase:
    """A musical phrase with lick, bass, and chord data."""
    name: str
    lick_notes: List[int]
    bass_notes: List[int]
    chord_voicings: List[List[int]]  # List of chords, each chord is list of pitches
    resolution_note: int


# =============================================================================
# Phrase Definitions (Tritone Substitutions)
# =============================================================================

def get_phrases() -> List[Phrase]:
    """Return the practice phrases (tritone sub resolutions)."""
    return [
        Phrase(
            name="C7 → F",
            lick_notes=[48, 51, 53, 55, 56, 60, 61, 63, 69],  # bebop line → A resolution
            bass_notes=[36, 43, 45, 46],  # C, G, A, Bb (walk-up)
            chord_voicings=[
                [48, 52, 58],  # C7: C, E, Bb
                [48, 52, 58],  # C7 (repeat)
                [53, 57, 63],  # Fmaj7: F, A, E
                [53, 57, 63],  # Fmaj7 (repeat)
            ],
            resolution_note=69,  # A
        ),
        Phrase(
            name="Gb7 → B",
            lick_notes=[42, 46, 49, 51, 53, 54, 58, 63],  # bebop line → D# resolution
            bass_notes=[42, 49, 51, 52],  # Gb, Db, Eb, E (walk-up)
            chord_voicings=[
                [42, 46, 52],  # Gb7: Gb, Bb, E
                [42, 46, 52],  # Gb7 (repeat)
                [47, 51, 57],  # Bmaj7: B, D#, A#
                [47, 51, 57],  # Bmaj7 (repeat)
            ],
            resolution_note=63,  # D#/Eb
        ),
    ]


# =============================================================================
# Track Builders
# =============================================================================

def tempo_to_microseconds(bpm: int) -> int:
    """Convert BPM to microseconds per quarter note."""
    return MICROSECONDS_PER_MINUTE // bpm


def ticks_8th() -> int:
    return TICKS_PER_BEAT // 2


def ticks_quarter() -> int:
    return TICKS_PER_BEAT


def ticks_half() -> int:
    return TICKS_PER_BEAT * 2


def build_guitar_track(phrases: List[Phrase], loops: int = 1) -> MidiTrack:
    """Build guitar track with licks."""
    track = MidiTrack()
    track.append(Message('program_change', channel=CH_GUITAR, program=PATCH_NYLON_GUITAR, time=0))

    current_time = 0
    note_duration = ticks_8th()

    for _ in range(loops):
        for phrase in phrases:
            # Play lick as 8th notes
            for i, pitch in enumerate(phrase.lick_notes):
                # Delta time: 0 for first note, note_duration for subsequent
                delta = 0 if (i == 0 and current_time == 0) else (note_duration if i > 0 else ticks_quarter() * 4)
                track.append(Message('note_on', channel=CH_GUITAR, note=pitch, velocity=80, time=delta))
                track.append(Message('note_off', channel=CH_GUITAR, note=pitch, velocity=0, time=note_duration))

            # Rest between phrases (1 bar)
            current_time += ticks_quarter() * 4

    return track


def build_bass_track(phrases: List[Phrase], loops: int = 1) -> MidiTrack:
    """Build bass track with walking patterns."""
    track = MidiTrack()
    track.append(Message('program_change', channel=CH_BASS, program=PATCH_ACOUSTIC_BASS, time=0))

    note_duration = ticks_quarter()
    first_note = True

    for _ in range(loops):
        for phrase in phrases:
            for i, pitch in enumerate(phrase.bass_notes):
                delta = 0 if first_note else note_duration
                first_note = False
                track.append(Message('note_on', channel=CH_BASS, note=pitch, velocity=70, time=delta))
                track.append(Message('note_off', channel=CH_BASS, note=pitch, velocity=0, time=note_duration))

    return track


def build_chord_track(phrases: List[Phrase], loops: int = 1) -> MidiTrack:
    """Build chord track with shell voicings."""
    track = MidiTrack()
    track.append(Message('program_change', channel=CH_CHORD, program=PATCH_ACOUSTIC_PIANO, time=0))

    chord_duration = ticks_quarter()
    first_chord = True

    for _ in range(loops):
        for phrase in phrases:
            for chord_pitches in phrase.chord_voicings:
                # All notes of chord start together
                for j, pitch in enumerate(chord_pitches):
                    delta = 0 if (first_chord and j == 0) else (chord_duration if j == 0 else 0)
                    if j == 0:
                        first_chord = False
                    track.append(Message('note_on', channel=CH_CHORD, note=pitch, velocity=60, time=delta))

                # All notes of chord end together
                for j, pitch in enumerate(chord_pitches):
                    delta = chord_duration if j == 0 else 0
                    track.append(Message('note_off', channel=CH_CHORD, note=pitch, velocity=0, time=delta))

    return track


def build_drum_track(phrases: List[Phrase], loops: int = 1) -> MidiTrack:
    """Build simple drum track (hi-hat on quarters)."""
    track = MidiTrack()

    # Count total beats: 4 beats per phrase, 2 phrases
    beats_per_loop = len(phrases) * 4
    total_beats = beats_per_loop * loops

    for i in range(total_beats):
        delta = 0 if i == 0 else ticks_quarter()
        track.append(Message('note_on', channel=CH_DRUM, note=HIHAT_CLOSED, velocity=60, time=delta))
        track.append(Message('note_off', channel=CH_DRUM, note=HIHAT_CLOSED, velocity=0, time=ticks_8th()))

    return track


# =============================================================================
# Main Generator
# =============================================================================

def generate_practice_midi(
    output_path: str | Path = "jazz_tritone_practice.mid",
    tempo_bpm: int = DEFAULT_TEMPO_BPM,
    loops: int = 1,
    include_drums: bool = True,
) -> Path:
    """
    Generate a multi-track MIDI practice file.

    Args:
        output_path: Output file path
        tempo_bpm: Tempo in BPM
        loops: Number of times to repeat the phrases
        include_drums: Whether to include drum track

    Returns:
        Path to the generated MIDI file
    """
    output_path = Path(output_path)
    phrases = get_phrases()

    mid = MidiFile(ticks_per_beat=TICKS_PER_BEAT)

    # Create conductor track with tempo
    conductor = MidiTrack()
    conductor.append(MetaMessage('set_tempo', tempo=tempo_to_microseconds(tempo_bpm), time=0))
    conductor.append(MetaMessage('track_name', name='Conductor', time=0))
    mid.tracks.append(conductor)

    # Add instrument tracks
    guitar_track = build_guitar_track(phrases, loops)
    guitar_track.insert(0, MetaMessage('track_name', name='Guitar', time=0))
    mid.tracks.append(guitar_track)

    bass_track = build_bass_track(phrases, loops)
    bass_track.insert(0, MetaMessage('track_name', name='Bass', time=0))
    mid.tracks.append(bass_track)

    chord_track = build_chord_track(phrases, loops)
    chord_track.insert(0, MetaMessage('track_name', name='Chords', time=0))
    mid.tracks.append(chord_track)

    if include_drums:
        drum_track = build_drum_track(phrases, loops)
        drum_track.insert(0, MetaMessage('track_name', name='Drums', time=0))
        mid.tracks.append(drum_track)

    mid.save(str(output_path))
    return output_path


# =============================================================================
# CLI
# =============================================================================

def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate MIDI backing tracks for jazz practice"
    )
    parser.add_argument(
        "--output", "-o",
        default="jazz_tritone_practice.mid",
        help="Output MIDI file path"
    )
    parser.add_argument(
        "--tempo",
        type=int,
        default=DEFAULT_TEMPO_BPM,
        help=f"Tempo in BPM (default: {DEFAULT_TEMPO_BPM})"
    )
    parser.add_argument(
        "--loops",
        type=int,
        default=1,
        help="Number of times to loop the phrases (default: 1)"
    )
    parser.add_argument(
        "--no-drums",
        action="store_true",
        help="Exclude drum track"
    )

    args = parser.parse_args()

    output = generate_practice_midi(
        output_path=args.output,
        tempo_bpm=args.tempo,
        loops=args.loops,
        include_drums=not args.no_drums,
    )

    print(f"Generated: {output}")
    print(f"  Tempo: {args.tempo} BPM")
    print(f"  Loops: {args.loops}")
    print(f"  Drums: {'yes' if not args.no_drums else 'no'}")


if __name__ == "__main__":
    main()
