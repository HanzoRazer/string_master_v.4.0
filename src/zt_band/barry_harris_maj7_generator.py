"""
Barry Harris Maj7 Scale Exercise Generator.

Generates MIDI exercises from the source-grounded maj7 ruleset.

Rules enforced:
- Degree groups: chord tones (1,3,5,7) vs non-chord tones (2,4,6)
- EXPLICIT: Half-step 7↔1
- EXPLICIT: No half-steps among 2,4,6
- IMPLIED: Stepwise motion

Usage:
    python -m zt_band.barry_harris_maj7_generator
    python -m zt_band.barry_harris_maj7_generator --key G --loops 4
    python -m zt_band.barry_harris_maj7_generator --all-keys --tempo 100
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from mido import Message, MidiFile, MidiTrack, MetaMessage


# =============================================================================
# Constants
# =============================================================================

TICKS_PER_BEAT = 480
MICROSECONDS_PER_MINUTE = 60_000_000
DEFAULT_TEMPO_BPM = 80

# GM Patches
PATCH_ACOUSTIC_PIANO = 0
PATCH_ELECTRIC_PIANO = 4
PATCH_VIBRAPHONE = 11

# Channels
CH_MELODY = 0
CH_CHORD = 1

# Note names
NOTE_NAMES = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']

# Circle of fourths for all-keys mode
CIRCLE_OF_FOURTHS = [0, 5, 10, 3, 8, 1, 6, 11, 4, 9, 2, 7]

# Major scale intervals from root (in semitones)
# 1=0, 2=2, 3=4, 4=5, 5=7, 6=9, 7=11
MAJOR_SCALE_INTERVALS = [0, 2, 4, 5, 7, 9, 11]

# Degree labels for markers
DEGREE_NAMES = ['1', '2', '3', '4', '5', '6', '7']


# =============================================================================
# Ruleset Loader
# =============================================================================

def load_ruleset(path: Optional[Path] = None) -> dict:
    """Load the maj7 ruleset JSON."""
    if path is None:
        # Find relative to this file
        here = Path(__file__).parent
        candidates = [
            here.parent.parent / "schemas" / "barry_harris_7th_scale_maj7_v1.json",
            here / "schemas" / "barry_harris_7th_scale_maj7_v1.json",
            Path("schemas/barry_harris_7th_scale_maj7_v1.json"),
        ]
        for p in candidates:
            if p.exists():
                path = p
                break

    if path and path.exists():
        with open(path) as f:
            return json.load(f)

    # Fallback: hardcoded minimal ruleset
    return {
        "degree_groups": {
            "chord_tones": ["1", "3", "5", "7"],
            "non_chord_tones": ["2", "4", "6"]
        }
    }


# =============================================================================
# Scale Builder
# =============================================================================

@dataclass
class MajorScaleExercise:
    """A scale exercise in a specific key."""
    root_name: str
    root_midi: int  # MIDI note number of root (e.g., 60 for C4)
    scale_notes: List[int]  # Full octave of MIDI notes
    chord_tones: List[int]  # Indices into scale (0-indexed): 0, 2, 4, 6
    non_chord_tones: List[int]  # Indices: 1, 3, 5


def build_scale(root_midi: int) -> List[int]:
    """Build major scale from root MIDI note."""
    return [root_midi + interval for interval in MAJOR_SCALE_INTERVALS]


def get_exercise(root_name: str, root_midi: int) -> MajorScaleExercise:
    """Create exercise data for a key."""
    scale = build_scale(root_midi)
    return MajorScaleExercise(
        root_name=root_name,
        root_midi=root_midi,
        scale_notes=scale,
        chord_tones=[0, 2, 4, 6],      # 1, 3, 5, 7
        non_chord_tones=[1, 3, 5],     # 2, 4, 6
    )


# =============================================================================
# Exercise Patterns
# =============================================================================

def pattern_ascending_scale(exercise: MajorScaleExercise, octaves: int = 2) -> List[int]:
    """Ascending scale over N octaves, ending on root."""
    notes = []
    for octave in range(octaves):
        for note in exercise.scale_notes:
            notes.append(note + (octave * 12))
    # Add final root
    notes.append(exercise.root_midi + (octaves * 12))
    return notes


def pattern_descending_scale(exercise: MajorScaleExercise, octaves: int = 2) -> List[int]:
    """Descending scale over N octaves, ending on root."""
    notes = []
    start_octave = octaves
    for octave in range(start_octave, 0, -1):
        for note in reversed(exercise.scale_notes):
            notes.append(note + (octave * 12))
    # Add final root
    notes.append(exercise.root_midi)
    return notes


def pattern_up_down(exercise: MajorScaleExercise, octaves: int = 1) -> List[int]:
    """Up one octave, down one octave, land on root."""
    up = pattern_ascending_scale(exercise, octaves)[:-1]  # Remove final root
    down = pattern_descending_scale(exercise, octaves)
    return up + down


def pattern_chord_tones_only(exercise: MajorScaleExercise, octaves: int = 2) -> List[int]:
    """Arpeggiate chord tones (1-3-5-7) over octaves."""
    notes = []
    chord_degrees = [0, 2, 4, 6]  # 1, 3, 5, 7 in 0-indexed
    for octave in range(octaves):
        for deg in chord_degrees:
            notes.append(exercise.scale_notes[deg] + (octave * 12))
    # Final root
    notes.append(exercise.root_midi + (octaves * 12))
    return notes


def pattern_stepwise_chord_tone_targets(exercise: MajorScaleExercise) -> List[int]:
    """
    Stepwise motion targeting chord tones.
    Pattern: approach each chord tone from below by step.
    1 -> 2-3 -> 4-5 -> 6-7 -> 1(8ve)
    """
    notes = []
    scale = exercise.scale_notes

    # 1
    notes.append(scale[0])
    # 2 -> 3
    notes.extend([scale[1], scale[2]])
    # 4 -> 5
    notes.extend([scale[3], scale[4]])
    # 6 -> 7
    notes.extend([scale[5], scale[6]])
    # 1 (octave)
    notes.append(scale[0] + 12)

    return notes


def pattern_7_to_1_approach(exercise: MajorScaleExercise, octaves: int = 2) -> List[int]:
    """
    7→1 approach drill (EXPLICIT from audio).

    Emphasizes the half-step resolution from leading tone to tonic.
    Pattern per octave: 5-6-7-1 | 5-6-7-1 (repeated approach)

    Rule enforced: "7 resolves to 1 by half step"
    """
    notes = []
    scale = exercise.scale_notes

    for octave in range(octaves):
        offset = octave * 12
        # Approach sequence: 5 -> 6 -> 7 -> 1
        notes.append(scale[4] + offset)  # 5
        notes.append(scale[5] + offset)  # 6
        notes.append(scale[6] + offset)  # 7
        notes.append(scale[0] + offset + 12)  # 1 (resolution)

        # Repeat with slight variation: 3 -> 4 -> 5 -> 6 -> 7 -> 1
        notes.append(scale[2] + offset)  # 3
        notes.append(scale[3] + offset)  # 4
        notes.append(scale[4] + offset)  # 5
        notes.append(scale[5] + offset)  # 6
        notes.append(scale[6] + offset)  # 7
        notes.append(scale[0] + offset + 12)  # 1 (resolution)

    return notes


def pattern_resolution_drill(exercise: MajorScaleExercise) -> List[int]:
    """
    Resolution drill: approach each chord tone by step.

    Enforces stepwise motion + chord tone targeting.
    Pattern: 2→1, 4→3, 6→5, 7→1(8ve)
    """
    notes = []
    scale = exercise.scale_notes

    # 2 -> 1 (step down to root)
    notes.extend([scale[1], scale[0]])
    # 4 -> 3 (step down to 3rd)
    notes.extend([scale[3], scale[2]])
    # 6 -> 5 (step down to 5th)
    notes.extend([scale[5], scale[4]])
    # 7 -> 1 (EXPLICIT: half-step up to root)
    notes.extend([scale[6], scale[0] + 12])

    # Reverse: approach from below
    # 7 -> 1 (leading tone resolution)
    notes.extend([scale[6], scale[0] + 12])
    # 2 -> 3 (step up to 3rd)
    notes.extend([scale[1], scale[2]])
    # 4 -> 5 (step up to 5th)
    notes.extend([scale[3], scale[4]])
    # 6 -> 7 (step up to 7th)
    notes.extend([scale[5], scale[6]])
    # 7 -> 1 (final resolution)
    notes.extend([scale[6], scale[0] + 12])

    return notes


# =============================================================================
# MIDI Builders
# =============================================================================

def tempo_to_microseconds(bpm: int) -> int:
    return MICROSECONDS_PER_MINUTE // bpm


def ticks_8th() -> int:
    return TICKS_PER_BEAT // 2


def ticks_quarter() -> int:
    return TICKS_PER_BEAT


def build_melody_track(
    notes: List[int],
    velocity: int = 80,
    note_duration: int = None,
) -> MidiTrack:
    """Build melody track with proper delta timing."""
    track = MidiTrack()
    track.append(Message('program_change', channel=CH_MELODY, program=PATCH_ACOUSTIC_PIANO, time=0))

    if note_duration is None:
        note_duration = ticks_8th()

    first_note = True
    for pitch in notes:
        delta = 0 if first_note else 0  # note_on immediately after previous note_off
        first_note = False

        track.append(Message('note_on', channel=CH_MELODY, note=pitch, velocity=velocity, time=delta))
        track.append(Message('note_off', channel=CH_MELODY, note=pitch, velocity=0, time=note_duration))

    return track


def build_chord_pad(
    exercise: MajorScaleExercise,
    duration_bars: int = 4,
) -> MidiTrack:
    """Build sustained maj7 chord pad."""
    track = MidiTrack()
    track.append(Message('program_change', channel=CH_CHORD, program=PATCH_ELECTRIC_PIANO, time=0))

    # Maj7 voicing: root, 3rd, 5th, 7th
    chord = [
        exercise.root_midi,
        exercise.scale_notes[2],  # 3rd
        exercise.scale_notes[4],  # 5th
        exercise.scale_notes[6],  # 7th
    ]

    chord_duration = ticks_quarter() * 4 * duration_bars

    # All notes on
    for i, pitch in enumerate(chord):
        track.append(Message('note_on', channel=CH_CHORD, note=pitch, velocity=50, time=0))

    # All notes off after duration
    for i, pitch in enumerate(chord):
        delta = chord_duration if i == 0 else 0
        track.append(Message('note_off', channel=CH_CHORD, note=pitch, velocity=0, time=delta))

    return track


# =============================================================================
# Exercise Generator
# =============================================================================

def generate_exercise_midi(
    output_path: Path,
    root_name: str = "C",
    root_midi: int = 60,
    tempo_bpm: int = DEFAULT_TEMPO_BPM,
    loops: int = 2,
    pattern: str = "up_down",
    include_chord: bool = True,
) -> Path:
    """Generate a single exercise MIDI file."""
    exercise = get_exercise(root_name, root_midi)

    # Select pattern
    if pattern == "ascending":
        notes = pattern_ascending_scale(exercise)
    elif pattern == "descending":
        notes = pattern_descending_scale(exercise)
    elif pattern == "up_down":
        notes = pattern_up_down(exercise)
    elif pattern == "chord_tones":
        notes = pattern_chord_tones_only(exercise)
    elif pattern == "targets":
        notes = pattern_stepwise_chord_tone_targets(exercise)
    elif pattern == "7_to_1":
        notes = pattern_7_to_1_approach(exercise)
    elif pattern == "resolution":
        notes = pattern_resolution_drill(exercise)
    else:
        notes = pattern_up_down(exercise)

    # Repeat for loops
    full_notes = notes * loops

    # Create MIDI file
    mid = MidiFile(ticks_per_beat=TICKS_PER_BEAT)

    # Conductor track
    conductor = MidiTrack()
    conductor.append(MetaMessage('set_tempo', tempo=tempo_to_microseconds(tempo_bpm), time=0))
    conductor.append(MetaMessage('track_name', name='Conductor', time=0))
    conductor.append(MetaMessage('marker', text=f'Barry Harris Maj7: {root_name}', time=0))
    mid.tracks.append(conductor)

    # Melody track
    melody = build_melody_track(full_notes)
    melody.insert(0, MetaMessage('track_name', name='Scale', time=0))
    mid.tracks.append(melody)

    # Optional chord pad
    if include_chord:
        # Calculate how many bars the melody takes
        notes_per_bar = 8  # 8th notes in 4/4
        total_notes = len(full_notes)
        bars = (total_notes // notes_per_bar) + 1

        chord = build_chord_pad(exercise, duration_bars=bars)
        chord.insert(0, MetaMessage('track_name', name='Chord', time=0))
        mid.tracks.append(chord)

    mid.save(str(output_path))
    return output_path


def generate_all_keys(
    output_dir: Path,
    tempo_bpm: int = DEFAULT_TEMPO_BPM,
    loops: int = 2,
    pattern: str = "up_down",
) -> List[Path]:
    """Generate exercises in all 12 keys (circle of fourths)."""
    output_dir.mkdir(parents=True, exist_ok=True)

    generated = []
    base_midi = 60  # C4

    for semitones in CIRCLE_OF_FOURTHS:
        key_name = NOTE_NAMES[semitones]
        root_midi = base_midi + semitones

        filename = f"barry_harris_maj7_{key_name}_{pattern}.mid"
        output_path = output_dir / filename

        generate_exercise_midi(
            output_path=output_path,
            root_name=key_name,
            root_midi=root_midi,
            tempo_bpm=tempo_bpm,
            loops=loops,
            pattern=pattern,
        )
        generated.append(output_path)
        print(f"  Generated: {filename}")

    return generated


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Generate Barry Harris Maj7 scale exercises from source-grounded ruleset"
    )
    parser.add_argument(
        "--output", "-o",
        default="barry_harris_maj7_exercise.mid",
        help="Output MIDI file path"
    )
    parser.add_argument(
        "--key",
        default="C",
        choices=NOTE_NAMES,
        help="Root key (default: C)"
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
        default=2,
        help="Number of repetitions (default: 2)"
    )
    parser.add_argument(
        "--pattern",
        choices=["ascending", "descending", "up_down", "chord_tones", "targets", "7_to_1", "resolution"],
        default="up_down",
        help="Exercise pattern: up_down, 7_to_1 (approach drill), resolution (default: up_down)"
    )
    parser.add_argument(
        "--all-keys",
        action="store_true",
        help="Generate exercises for all 12 keys"
    )
    parser.add_argument(
        "--no-chord",
        action="store_true",
        help="Exclude chord pad track"
    )

    args = parser.parse_args()

    if args.all_keys:
        print(f"Generating Barry Harris Maj7 exercises in all 12 keys...")
        output_dir = Path(args.output).parent if args.output != "barry_harris_maj7_exercise.mid" else Path(".")
        files = generate_all_keys(
            output_dir=output_dir,
            tempo_bpm=args.tempo,
            loops=args.loops,
            pattern=args.pattern,
        )
        print(f"\nGenerated {len(files)} files.")
    else:
        # Find root MIDI note
        key_idx = NOTE_NAMES.index(args.key)
        root_midi = 60 + key_idx  # C4 = 60

        output = generate_exercise_midi(
            output_path=Path(args.output),
            root_name=args.key,
            root_midi=root_midi,
            tempo_bpm=args.tempo,
            loops=args.loops,
            pattern=args.pattern,
            include_chord=not args.no_chord,
        )

        print(f"Generated: {output}")
        print(f"  Key: {args.key} maj7")
        print(f"  Pattern: {args.pattern}")
        print(f"  Tempo: {args.tempo} BPM")
        print(f"  Loops: {args.loops}")


if __name__ == "__main__":
    main()
