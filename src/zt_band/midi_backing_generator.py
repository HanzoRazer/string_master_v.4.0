"""
MIDI Backing Track Generator for Jazz Practice.

Generates multi-track MIDI files with:
- Guitar licks (bebop lines over tritone subs)
- Basslines (root-5-walk-up patterns)
- Shell chord voicings (1-3-7)
- Optional metronome
- DAW markers for navigation
- Transposition to any key or circle-of-fourths

Usage:
    python -m zt_band.midi_backing_generator [--output FILE] [--loops N] [--no-drums]
    python -m zt_band.midi_backing_generator --all-keys --loops 2
    python -m zt_band.midi_backing_generator --transpose 5  # Up a fourth
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

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

# Note names for markers
NOTE_NAMES = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']

# Circle of fourths (for --all-keys mode)
CIRCLE_OF_FOURTHS = [0, 5, 10, 3, 8, 1, 6, 11, 4, 9, 2, 7]  # C, F, Bb, Eb, Ab, Db, Gb, B, E, A, D, G


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
    root_note: int  # MIDI note number of the root (for transposition reference)
    lick_notes: List[int]
    bass_notes: List[int]
    chord_voicings: List[List[int]]  # List of chords, each chord is list of pitches
    resolution_note: int

    def transpose(self, semitones: int) -> "Phrase":
        """Return a new Phrase transposed by the given semitones."""
        return Phrase(
            name=self._transpose_name(semitones),
            root_note=self.root_note + semitones,
            lick_notes=[n + semitones for n in self.lick_notes],
            bass_notes=[n + semitones for n in self.bass_notes],
            chord_voicings=[[n + semitones for n in chord] for chord in self.chord_voicings],
            resolution_note=self.resolution_note + semitones,
        )

    def _transpose_name(self, semitones: int) -> str:
        """Generate transposed phrase name."""
        # Parse original name like "C7 → F"
        if "→" in self.name:
            parts = self.name.split("→")
            root_name = parts[0].strip().replace("7", "")
            target_name = parts[1].strip()

            # Find original root index
            root_idx = NOTE_NAMES.index(root_name) if root_name in NOTE_NAMES else 0
            target_idx = NOTE_NAMES.index(target_name) if target_name in NOTE_NAMES else 0

            new_root = NOTE_NAMES[(root_idx + semitones) % 12]
            new_target = NOTE_NAMES[(target_idx + semitones) % 12]

            return f"{new_root}7 → {new_target}"
        return self.name


# =============================================================================
# Phrase Definitions (Tritone Substitutions)
# =============================================================================

def get_base_phrases() -> List[Phrase]:
    """Return the base practice phrases in C (tritone sub resolutions)."""
    return [
        Phrase(
            name="C7 → F",
            root_note=48,  # C3
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
            root_note=42,  # Gb2
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


def get_phrases(transpose: int = 0) -> List[Phrase]:
    """Get phrases, optionally transposed."""
    base = get_base_phrases()
    if transpose == 0:
        return base
    return [p.transpose(transpose) for p in base]


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


def build_guitar_track(
    phrases: List[Phrase],
    loops: int = 1,
    add_markers: bool = True,
) -> MidiTrack:
    """Build guitar track with licks and optional DAW markers."""
    track = MidiTrack()
    track.append(Message('program_change', channel=CH_GUITAR, program=PATCH_NYLON_GUITAR, time=0))

    note_duration = ticks_8th()
    first_note_global = True

    for loop_num in range(loops):
        for phrase_idx, phrase in enumerate(phrases):
            # Add DAW marker at start of each phrase
            if add_markers:
                marker_time = 0 if (loop_num == 0 and phrase_idx == 0) else 0
                marker_text = f"Loop {loop_num + 1}: {phrase.name}"
                track.append(MetaMessage('marker', text=marker_text, time=0))

            # Play lick as 8th notes
            for i, pitch in enumerate(phrase.lick_notes):
                if first_note_global:
                    delta = 0
                    first_note_global = False
                elif i == 0:
                    # Gap between phrases (rest for remaining time in bar)
                    delta = ticks_quarter() * 2  # Half bar rest
                else:
                    delta = 0  # Note starts immediately after previous note_off

                track.append(Message('note_on', channel=CH_GUITAR, note=pitch, velocity=85, time=delta))
                track.append(Message('note_off', channel=CH_GUITAR, note=pitch, velocity=0, time=note_duration))

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
                    delta = 0 if first_chord else (chord_duration if j == 0 else 0)
                    if j == 0 and first_chord:
                        first_chord = False
                    track.append(Message('note_on', channel=CH_CHORD, note=pitch, velocity=60, time=delta))

                # All notes of chord end together
                for j, pitch in enumerate(chord_pitches):
                    delta = chord_duration if j == 0 else 0
                    track.append(Message('note_off', channel=CH_CHORD, note=pitch, velocity=0, time=delta))

    return track


def build_drum_track(phrases: List[Phrase], loops: int = 1) -> MidiTrack:
    """Build drum track with hi-hat + kick/snare pattern."""
    track = MidiTrack()

    # Count total beats: 4 beats per phrase
    beats_per_phrase = 4
    total_beats = len(phrases) * beats_per_phrase * loops

    for i in range(total_beats):
        delta = 0 if i == 0 else ticks_quarter()
        beat_in_bar = i % 4

        # Hi-hat on every beat
        track.append(Message('note_on', channel=CH_DRUM, note=HIHAT_CLOSED, velocity=60, time=delta))
        track.append(Message('note_off', channel=CH_DRUM, note=HIHAT_CLOSED, velocity=0, time=ticks_8th()))

        # Kick on 1 and 3
        if beat_in_bar in (0, 2):
            track.append(Message('note_on', channel=CH_DRUM, note=KICK, velocity=80, time=0))
            track.append(Message('note_off', channel=CH_DRUM, note=KICK, velocity=0, time=ticks_8th()))

        # Snare on 2 and 4
        if beat_in_bar in (1, 3):
            track.append(Message('note_on', channel=CH_DRUM, note=SNARE, velocity=70, time=0))
            track.append(Message('note_off', channel=CH_DRUM, note=SNARE, velocity=0, time=ticks_8th()))

    return track


# =============================================================================
# Main Generator
# =============================================================================

def generate_practice_midi(
    output_path: str | Path = "jazz_tritone_practice.mid",
    tempo_bpm: int = DEFAULT_TEMPO_BPM,
    loops: int = 1,
    include_drums: bool = True,
    transpose: int = 0,
    add_markers: bool = True,
) -> Path:
    """
    Generate a multi-track MIDI practice file.

    Args:
        output_path: Output file path
        tempo_bpm: Tempo in BPM
        loops: Number of times to repeat the phrases
        include_drums: Whether to include drum track
        transpose: Semitones to transpose (0-11)
        add_markers: Add DAW navigation markers

    Returns:
        Path to the generated MIDI file
    """
    output_path = Path(output_path)
    phrases = get_phrases(transpose)

    mid = MidiFile(ticks_per_beat=TICKS_PER_BEAT)

    # Create conductor track with tempo
    conductor = MidiTrack()
    conductor.append(MetaMessage('set_tempo', tempo=tempo_to_microseconds(tempo_bpm), time=0))
    conductor.append(MetaMessage('track_name', name='Conductor', time=0))

    # Add key signature marker
    if transpose != 0:
        key_name = NOTE_NAMES[transpose % 12]
        conductor.append(MetaMessage('marker', text=f'Key: {key_name}', time=0))

    mid.tracks.append(conductor)

    # Add instrument tracks
    guitar_track = build_guitar_track(phrases, loops, add_markers)
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


def generate_all_keys(
    output_dir: str | Path = ".",
    tempo_bpm: int = DEFAULT_TEMPO_BPM,
    loops: int = 1,
    include_drums: bool = True,
) -> List[Path]:
    """
    Generate practice files in all 12 keys (circle of fourths).

    Returns:
        List of paths to generated files
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    generated = []

    for semitones in CIRCLE_OF_FOURTHS:
        key_name = NOTE_NAMES[semitones]
        filename = f"tritone_practice_{key_name}.mid"
        output_path = output_dir / filename

        generate_practice_midi(
            output_path=output_path,
            tempo_bpm=tempo_bpm,
            loops=loops,
            include_drums=include_drums,
            transpose=semitones,
        )
        generated.append(output_path)
        print(f"  Generated: {filename}")

    return generated


# =============================================================================
# CLI
# =============================================================================

def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate MIDI backing tracks for jazz tritone substitution practice"
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
    parser.add_argument(
        "--transpose",
        type=int,
        default=0,
        help="Transpose by N semitones (0-11)"
    )
    parser.add_argument(
        "--all-keys",
        action="store_true",
        help="Generate files for all 12 keys (circle of fourths)"
    )
    parser.add_argument(
        "--no-markers",
        action="store_true",
        help="Exclude DAW navigation markers"
    )

    args = parser.parse_args()

    if args.all_keys:
        print(f"Generating practice files in all 12 keys...")
        output_dir = Path(args.output).parent if args.output != "jazz_tritone_practice.mid" else Path(".")
        files = generate_all_keys(
            output_dir=output_dir,
            tempo_bpm=args.tempo,
            loops=args.loops,
            include_drums=not args.no_drums,
        )
        print(f"\nGenerated {len(files)} files in circle-of-fourths order.")
    else:
        output = generate_practice_midi(
            output_path=args.output,
            tempo_bpm=args.tempo,
            loops=args.loops,
            include_drums=not args.no_drums,
            transpose=args.transpose,
            add_markers=not args.no_markers,
        )

        key_name = NOTE_NAMES[args.transpose % 12] if args.transpose else "C"
        print(f"Generated: {output}")
        print(f"  Key: {key_name}")
        print(f"  Tempo: {args.tempo} BPM")
        print(f"  Loops: {args.loops}")
        print(f"  Drums: {'yes' if not args.no_drums else 'no'}")
        print(f"  Markers: {'yes' if not args.no_markers else 'no'}")


if __name__ == "__main__":
    main()
