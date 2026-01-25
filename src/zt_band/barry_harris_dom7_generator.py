"""
Barry Harris Dom7 (6th Diminished) Scale Exercise Generator.

Generates MIDI exercises from the EXPANDED INFERENCE dom7 ruleset.

The 8-note scale: 1-2-3-4-5-b6-6-b7
- Chord tones (1-3-5-b7) land on downbeats in continuous 8ths
- b6 is the "extra note" (diminished passing tone between 5 and 6)

NOTE: This is common Barry Harris pedagogy but NOT explicitly stated
in the source transcript. Use maj7_generator for source-grounded rules.

Usage:
    python -m zt_band.barry_harris_dom7_generator
    python -m zt_band.barry_harris_dom7_generator --key G --loops 4
    python -m zt_band.barry_harris_dom7_generator --all-keys --pattern bebop_down
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
DEFAULT_TEMPO_BPM = 120  # Bebop tempo

# GM Patches
PATCH_ACOUSTIC_PIANO = 0
PATCH_ELECTRIC_PIANO = 4
PATCH_JAZZ_GUITAR = 26

# Channels
CH_MELODY = 0
CH_CHORD = 1

# Note names
NOTE_NAMES = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']

# Circle of fourths
CIRCLE_OF_FOURTHS = [0, 5, 10, 3, 8, 1, 6, 11, 4, 9, 2, 7]

# Dom7 bebop scale intervals from root (in semitones)
# 1=0, 2=2, 3=4, 4=5, 5=7, b6=8, 6=9, b7=10
# This is the 8-note "6th diminished" scale
DOM7_BEBOP_SCALE_INTERVALS = [0, 2, 4, 5, 7, 8, 9, 10]

# Standard dom7 scale (mixolydian) for comparison
MIXOLYDIAN_INTERVALS = [0, 2, 4, 5, 7, 9, 10]

# Degree labels
DEGREE_NAMES_8 = ['1', '2', '3', '4', '5', 'b6', '6', 'b7']


# =============================================================================
# Scale Builder
# =============================================================================

@dataclass
class Dom7BebopExercise:
    """A bebop scale exercise in a specific key."""
    root_name: str
    root_midi: int
    bebop_scale: List[int]      # 8-note scale
    mixolydian_scale: List[int]  # 7-note scale for comparison
    chord_tones_idx: List[int]   # Indices of chord tones in bebop scale: 0, 2, 4, 7
    passing_tones_idx: List[int] # Indices of passing tones: 1, 3, 5, 6


def build_bebop_scale(root_midi: int) -> List[int]:
    """Build 8-note dom7 bebop scale from root."""
    return [root_midi + interval for interval in DOM7_BEBOP_SCALE_INTERVALS]


def build_mixolydian(root_midi: int) -> List[int]:
    """Build standard mixolydian scale."""
    return [root_midi + interval for interval in MIXOLYDIAN_INTERVALS]


def get_exercise(root_name: str, root_midi: int) -> Dom7BebopExercise:
    """Create exercise data for a key."""
    bebop = build_bebop_scale(root_midi)
    mixo = build_mixolydian(root_midi)
    return Dom7BebopExercise(
        root_name=root_name,
        root_midi=root_midi,
        bebop_scale=bebop,
        mixolydian_scale=mixo,
        chord_tones_idx=[0, 2, 4, 7],    # 1, 3, 5, b7
        passing_tones_idx=[1, 3, 5, 6],  # 2, 4, b6, 6
    )


# =============================================================================
# Exercise Patterns
# =============================================================================

def pattern_bebop_ascending(exercise: Dom7BebopExercise, octaves: int = 2) -> List[int]:
    """
    Ascending bebop scale.

    Key insight: Starting on root (beat 1), all chord tones land on downbeats.
    1(down)-2(up)-3(down)-4(up)-5(down)-b6(up)-6(down)-b7(up)-1(down)
    """
    notes = []
    for octave in range(octaves):
        for note in exercise.bebop_scale:
            notes.append(note + (octave * 12))
    # Final root
    notes.append(exercise.root_midi + (octaves * 12))
    return notes


def pattern_bebop_descending(exercise: Dom7BebopExercise, octaves: int = 2) -> List[int]:
    """
    Descending bebop scale.

    Starting from root an octave up, descending keeps chord tones on downbeats.
    """
    notes = []
    for octave in range(octaves, 0, -1):
        for note in reversed(exercise.bebop_scale):
            notes.append(note + (octave * 12))
    # Final root
    notes.append(exercise.root_midi)
    return notes


def pattern_bebop_up_down(exercise: Dom7BebopExercise, octaves: int = 1) -> List[int]:
    """Up and down the bebop scale."""
    up = pattern_bebop_ascending(exercise, octaves)[:-1]
    down = pattern_bebop_descending(exercise, octaves)
    return up + down


def pattern_chord_tones_only(exercise: Dom7BebopExercise, octaves: int = 2) -> List[int]:
    """
    Arpeggiate chord tones only (1-3-5-b7).

    These are the notes that MUST land on downbeats.
    """
    notes = []
    chord_indices = [0, 2, 4, 7]  # 1, 3, 5, b7 in bebop scale
    for octave in range(octaves):
        for idx in chord_indices:
            notes.append(exercise.bebop_scale[idx] + (octave * 12))
    # Final root
    notes.append(exercise.root_midi + (octaves * 12))
    return notes


def pattern_downbeat_drill(exercise: Dom7BebopExercise, octaves: int = 1) -> List[int]:
    """
    Downbeat targeting drill.

    Emphasizes landing on chord tones by approaching from scale tone above.
    Pattern: 2-1, 4-3, b6-5, 6-b7, 1(8ve)
    """
    notes = []
    scale = exercise.bebop_scale

    for octave in range(octaves):
        offset = octave * 12
        # 2 -> 1 (approach root from above)
        notes.extend([scale[1] + offset, scale[0] + offset])
        # 4 -> 3 (approach 3rd from above)
        notes.extend([scale[3] + offset, scale[2] + offset])
        # b6 -> 5 (approach 5th from above)
        notes.extend([scale[5] + offset, scale[4] + offset])
        # 6 -> b7 (approach b7 from below — the exception)
        notes.extend([scale[6] + offset, scale[7] + offset])

    # Final root
    notes.append(exercise.root_midi + (octaves * 12))
    return notes


def pattern_enclosure(exercise: Dom7BebopExercise) -> List[int]:
    """
    Enclosure pattern (EXPANDED INFERENCE).

    Surround each chord tone with upper and lower neighbor.
    Pattern for each chord tone: above-below-target
    """
    notes = []
    scale = exercise.bebop_scale

    # Enclosure to 1: 2-b7(below)-1
    notes.extend([scale[1], scale[7] - 12, scale[0]])
    # Enclosure to 3: 4-2-3
    notes.extend([scale[3], scale[1], scale[2]])
    # Enclosure to 5: b6-4-5
    notes.extend([scale[5], scale[3], scale[4]])
    # Enclosure to b7: 1(8ve)-6-b7
    notes.extend([scale[0] + 12, scale[6], scale[7]])
    # Resolve to 1
    notes.append(scale[0] + 12)

    return notes


def pattern_guide_tone_line(exercise: Dom7BebopExercise) -> List[int]:
    """
    Guide tone targeting (3rd and b7).

    Pattern: approach 3rd, land on 3rd, approach b7, land on b7, resolve.
    """
    notes = []
    scale = exercise.bebop_scale

    # Approach and land on 3rd: 1-2-3
    notes.extend([scale[0], scale[1], scale[2]])
    # Move to 5
    notes.extend([scale[3], scale[4]])
    # Approach and land on b7: 5-6-b7
    notes.extend([scale[4], scale[6], scale[7]])
    # Resolve to root
    notes.append(scale[0] + 12)

    # Second phrase: descending
    # From 1, approach b7 from above: 1-b7
    notes.extend([scale[0] + 12, scale[7]])
    # Descend through 6-b6-5
    notes.extend([scale[6], scale[5], scale[4]])
    # Approach 3rd from above: 4-3
    notes.extend([scale[3], scale[2]])
    # Descend to root: 2-1
    notes.extend([scale[1], scale[0]])

    return notes


def pattern_chromatic_approach(exercise: Dom7BebopExercise) -> List[int]:
    """
    Chromatic approach to chord tones.

    Approach each chord tone by half-step from below.
    """
    notes = []
    scale = exercise.bebop_scale

    # Chromatic approach to 1: b1(below)-1
    notes.extend([scale[0] - 1, scale[0]])
    # Chromatic approach to 3: b3-3
    notes.extend([scale[2] - 1, scale[2]])
    # Chromatic approach to 5: b5-5
    notes.extend([scale[4] - 1, scale[4]])
    # Chromatic approach to b7: 6-b7 (already half-step in scale)
    notes.extend([scale[6], scale[7]])
    # Resolve to 1
    notes.append(scale[0] + 12)

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
    velocity: int = 85,
    note_duration: int = None,
    swing: bool = False,
) -> MidiTrack:
    """Build melody track with proper delta timing."""
    track = MidiTrack()
    track.append(Message('program_change', channel=CH_MELODY, program=PATCH_ACOUSTIC_PIANO, time=0))

    if note_duration is None:
        note_duration = ticks_8th()

    first_note = True
    for i, pitch in enumerate(notes):
        delta = 0 if first_note else 0
        first_note = False

        # Optional swing feel (long-short pattern)
        if swing:
            duration = int(note_duration * 1.33) if i % 2 == 0 else int(note_duration * 0.67)
        else:
            duration = note_duration

        track.append(Message('note_on', channel=CH_MELODY, note=pitch, velocity=velocity, time=delta))
        track.append(Message('note_off', channel=CH_MELODY, note=pitch, velocity=0, time=duration))

    return track


def build_dom7_chord(
    exercise: Dom7BebopExercise,
    duration_bars: int = 4,
) -> MidiTrack:
    """Build sustained dom7 chord."""
    track = MidiTrack()
    track.append(Message('program_change', channel=CH_CHORD, program=PATCH_ELECTRIC_PIANO, time=0))

    # Dom7 voicing: root, 3rd, 5th, b7
    scale = exercise.bebop_scale
    chord = [
        exercise.root_midi,
        scale[2],  # 3rd
        scale[4],  # 5th
        scale[7],  # b7
    ]

    chord_duration = ticks_quarter() * 4 * duration_bars

    for i, pitch in enumerate(chord):
        track.append(Message('note_on', channel=CH_CHORD, note=pitch, velocity=50, time=0))

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
    pattern: str = "bebop_up_down",
    include_chord: bool = True,
    swing: bool = False,
) -> Path:
    """Generate a single exercise MIDI file."""
    exercise = get_exercise(root_name, root_midi)

    # Select pattern
    if pattern == "bebop_up":
        notes = pattern_bebop_ascending(exercise)
    elif pattern == "bebop_down":
        notes = pattern_bebop_descending(exercise)
    elif pattern == "bebop_up_down":
        notes = pattern_bebop_up_down(exercise)
    elif pattern == "chord_tones":
        notes = pattern_chord_tones_only(exercise)
    elif pattern == "downbeat":
        notes = pattern_downbeat_drill(exercise)
    elif pattern == "enclosure":
        notes = pattern_enclosure(exercise)
    elif pattern == "guide_tones":
        notes = pattern_guide_tone_line(exercise)
    elif pattern == "chromatic":
        notes = pattern_chromatic_approach(exercise)
    else:
        notes = pattern_bebop_up_down(exercise)

    # Repeat for loops
    full_notes = notes * loops

    # Create MIDI file
    mid = MidiFile(ticks_per_beat=TICKS_PER_BEAT)

    # Conductor track
    conductor = MidiTrack()
    conductor.append(MetaMessage('set_tempo', tempo=tempo_to_microseconds(tempo_bpm), time=0))
    conductor.append(MetaMessage('track_name', name='Conductor', time=0))
    conductor.append(MetaMessage('marker', text=f'Barry Harris Dom7 Bebop: {root_name}7', time=0))
    mid.tracks.append(conductor)

    # Melody track
    melody = build_melody_track(full_notes, swing=swing)
    melody.insert(0, MetaMessage('track_name', name='Bebop Line', time=0))
    mid.tracks.append(melody)

    # Optional chord pad
    if include_chord:
        notes_per_bar = 8
        total_notes = len(full_notes)
        bars = (total_notes // notes_per_bar) + 1

        chord = build_dom7_chord(exercise, duration_bars=bars)
        chord.insert(0, MetaMessage('track_name', name='Dom7 Chord', time=0))
        mid.tracks.append(chord)

    mid.save(str(output_path))
    return output_path


def generate_all_keys(
    output_dir: Path,
    tempo_bpm: int = DEFAULT_TEMPO_BPM,
    loops: int = 2,
    pattern: str = "bebop_up_down",
    swing: bool = False,
) -> List[Path]:
    """Generate exercises in all 12 keys."""
    output_dir.mkdir(parents=True, exist_ok=True)

    generated = []
    base_midi = 60

    for semitones in CIRCLE_OF_FOURTHS:
        key_name = NOTE_NAMES[semitones]
        root_midi = base_midi + semitones

        filename = f"barry_harris_dom7_{key_name}_{pattern}.mid"
        output_path = output_dir / filename

        generate_exercise_midi(
            output_path=output_path,
            root_name=key_name,
            root_midi=root_midi,
            tempo_bpm=tempo_bpm,
            loops=loops,
            pattern=pattern,
            swing=swing,
        )
        generated.append(output_path)
        print(f"  Generated: {filename}")

    return generated


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Generate Barry Harris Dom7 bebop scale exercises (EXPANDED INFERENCE)"
    )
    parser.add_argument(
        "--output", "-o",
        default="barry_harris_dom7_exercise.mid",
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
        choices=[
            "bebop_up", "bebop_down", "bebop_up_down",
            "chord_tones", "downbeat", "enclosure",
            "guide_tones", "chromatic"
        ],
        default="bebop_up_down",
        help="Exercise pattern (default: bebop_up_down)"
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
    parser.add_argument(
        "--swing",
        action="store_true",
        help="Apply swing feel (long-short 8ths)"
    )

    args = parser.parse_args()

    if args.all_keys:
        print(f"Generating Barry Harris Dom7 bebop exercises in all 12 keys...")
        output_dir = Path(args.output).parent if args.output != "barry_harris_dom7_exercise.mid" else Path(".")
        files = generate_all_keys(
            output_dir=output_dir,
            tempo_bpm=args.tempo,
            loops=args.loops,
            pattern=args.pattern,
            swing=args.swing,
        )
        print(f"\nGenerated {len(files)} files.")
    else:
        key_idx = NOTE_NAMES.index(args.key)
        root_midi = 60 + key_idx

        output = generate_exercise_midi(
            output_path=Path(args.output),
            root_name=args.key,
            root_midi=root_midi,
            tempo_bpm=args.tempo,
            loops=args.loops,
            pattern=args.pattern,
            include_chord=not args.no_chord,
            swing=args.swing,
        )

        print(f"Generated: {output}")
        print(f"  Key: {args.key}7")
        print(f"  Pattern: {args.pattern}")
        print(f"  Tempo: {args.tempo} BPM")
        print(f"  Loops: {args.loops}")
        print(f"  Swing: {'yes' if args.swing else 'no'}")


if __name__ == "__main__":
    main()
