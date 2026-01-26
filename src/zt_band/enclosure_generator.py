"""
Enclosure Practice Generator

Generates MIDI examples demonstrating Barry Harris-style enclosure patterns.
Enclosures approach target chord tones from above and below by half-step,
creating chromatic voice-leading tension that resolves to stability.

Usage:
    from zt_band.enclosure_generator import generate_enclosure_midi, ENCLOSURE_EXAMPLES
    generate_enclosure_midi(output_path="enclosures.mid", tempo_bpm=80)
"""

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

try:
    from mido import Message, MidiFile, MidiTrack, MetaMessage, bpm2tempo
    MIDO_AVAILABLE = True
except ImportError:
    MIDO_AVAILABLE = False


# Scale degree to MIDI note mapping (C=60 as reference)
DEGREE_TO_MIDI = {
    "1": 60,   # C
    "b2": 61,  # Db
    "2": 62,   # D
    "b3": 63,  # Eb
    "#2": 63,  # D# (enharmonic)
    "3": 64,   # E
    "#3": 65,  # E# (enharmonic F)
    "4": 65,   # F
    "#4": 66,  # F#
    "b5": 66,  # Gb (enharmonic)
    "5": 67,   # G
    "#5": 68,  # G# (enharmonic)
    "b6": 68,  # Ab
    "6": 69,   # A
    "b7": 70,  # Bb
    "7": 71,   # B
    "8": 72,   # C (octave up)
}


@dataclass
class EnclosureExample:
    """Represents a single enclosure pattern example."""
    id: str
    degrees: list[str]
    chord: str
    description: str = ""
    target_degree: str = ""  # The chord tone being enclosed


# Barry Harris-style enclosure examples
# Pattern: approach target from above AND below by half-step
ENCLOSURE_EXAMPLES = [
    # Major 6th chord enclosures (targeting 3rd)
    EnclosureExample(
        id="enclosure_major_C6_target_3",
        degrees=["4", "#3", "2", "#2", "3"],  # F-E#-D-D#-E (approach 3rd from above/below)
        chord="C6",
        description="Enclosure to 3rd of C6 from above (4) and below (#2)",
        target_degree="3"
    ),

    # Minor 7th chord enclosures (targeting 5th)
    EnclosureExample(
        id="enclosure_minor_Dm7_target_5",
        degrees=["b6", "5", "#4", "5"],  # Ab-G-F#-G (encircle the 5th)
        chord="Dm7",
        description="Enclosure to 5th of Dm7",
        target_degree="5"
    ),

    # Dominant 7th enclosures (targeting 3rd - the guide tone)
    EnclosureExample(
        id="enclosure_dom7_G7_target_3",
        degrees=["4", "3", "#2", "3"],  # F-E-D#-E (approach guide tone)
        chord="G7",
        description="Enclosure to 3rd (guide tone) of G7",
        target_degree="3"
    ),

    # Dominant 7th enclosures (targeting b7 - the other guide tone)
    EnclosureExample(
        id="enclosure_dom7_G7_target_b7",
        degrees=["7", "b7", "6", "b7"],  # B-Bb-A-Bb (approach the b7)
        chord="G7",
        description="Enclosure to b7 (guide tone) of G7",
        target_degree="b7"
    ),

    # ii-V-I resolution chain
    EnclosureExample(
        id="enclosure_ii_v_i_chain",
        degrees=["4", "3", "#2", "3", "2", "b2", "1"],
        chord="ii-V-I",
        description="Enclosure chain: enclose 3rd then resolve to root",
        target_degree="1"
    ),

    # Upper enclosure only (from above)
    EnclosureExample(
        id="enclosure_upper_to_5",
        degrees=["b6", "5"],
        chord="Cmaj7",
        description="Upper chromatic approach to 5th",
        target_degree="5"
    ),

    # Lower enclosure only (from below)
    EnclosureExample(
        id="enclosure_lower_to_3",
        degrees=["#2", "3"],
        chord="Cmaj7",
        description="Lower chromatic approach to 3rd",
        target_degree="3"
    ),

    # Double enclosure (Barry Harris classic)
    EnclosureExample(
        id="enclosure_double_to_1",
        degrees=["2", "b2", "7", "1"],  # D-Db-B-C (above-below-below-target)
        chord="Cmaj7",
        description="Double enclosure to root: above, below, below, target",
        target_degree="1"
    ),

    # Bebop scale fragment with enclosure
    EnclosureExample(
        id="bebop_enclosure_descending",
        degrees=["8", "7", "b7", "6", "#5", "5"],  # C-B-Bb-A-G#-G
        chord="C7",
        description="Descending bebop scale with chromatic enclosure of 5th",
        target_degree="5"
    ),

    # Approach pattern for altered dominant
    EnclosureExample(
        id="enclosure_alt_dom_target_b9",
        degrees=["3", "b3", "b2", "2", "b2"],  # approach b9 with chromaticism
        chord="G7alt",
        description="Chromatic approach in altered dominant context",
        target_degree="b2"
    ),
]


def degrees_to_midi(degrees: list[str], base_midi: int = 60) -> list[int]:
    """Convert scale degree names to MIDI note numbers.

    Args:
        degrees: List of scale degree strings (e.g., ["1", "#2", "3"])
        base_midi: MIDI note number for degree "1" (default 60 = middle C)

    Returns:
        List of MIDI note numbers
    """
    offset = base_midi - 60  # Adjust from C4 reference
    midi_notes = []
    for deg in degrees:
        if deg in DEGREE_TO_MIDI:
            midi_notes.append(DEGREE_TO_MIDI[deg] + offset)
        else:
            raise ValueError(f"Unknown scale degree: {deg}")
    return midi_notes


def generate_enclosure_midi(
    output_path: str | Path = "barry_harris_enclosure_examples.mid",
    tempo_bpm: int = 80,
    note_duration_ticks: int = 240,  # eighth note at 480 ticks/beat
    examples: Optional[list[EnclosureExample]] = None,
    base_midi: int = 60,  # C4
    velocity: int = 80,
) -> Path:
    """Generate a MIDI file containing enclosure examples.

    Args:
        output_path: Path to save the MIDI file
        tempo_bpm: Tempo in beats per minute
        note_duration_ticks: Duration of each note in ticks
        examples: List of enclosure examples (defaults to ENCLOSURE_EXAMPLES)
        base_midi: Base MIDI note for degree "1" (default 60 = C4)
        velocity: Note velocity (0-127)

    Returns:
        Path to the generated MIDI file

    Raises:
        ImportError: If mido is not installed
    """
    if not MIDO_AVAILABLE:
        raise ImportError("mido is required for MIDI generation. Install with: pip install mido")

    if examples is None:
        examples = ENCLOSURE_EXAMPLES

    output_path = Path(output_path)
    mid = MidiFile(ticks_per_beat=480)

    # Create track for each example
    for example in examples:
        track = MidiTrack()
        mid.tracks.append(track)

        # Track name
        track.append(MetaMessage('track_name', name=example.id, time=0))

        # Set tempo (only on first track, but mido handles this)
        if mid.tracks.index(track) == 0:
            track.append(MetaMessage('set_tempo', tempo=bpm2tempo(tempo_bpm), time=0))

        # Add text annotation with description
        if example.description:
            track.append(MetaMessage('text', text=example.description, time=0))

        # Convert degrees to MIDI and add notes
        midi_notes = degrees_to_midi(example.degrees, base_midi)

        for i, note in enumerate(midi_notes):
            # Note on
            track.append(Message('note_on', note=note, velocity=velocity, time=0 if i == 0 else note_duration_ticks))
            # Note off
            track.append(Message('note_off', note=note, velocity=0, time=note_duration_ticks))

        # Add a rest at end of each example (one beat)
        track.append(MetaMessage('end_of_track', time=480))

    # Save the file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    mid.save(str(output_path))

    return output_path


def list_examples() -> list[dict]:
    """Return enclosure examples as dictionaries for inspection."""
    return [
        {
            "id": ex.id,
            "degrees": ex.degrees,
            "chord": ex.chord,
            "description": ex.description,
            "target_degree": ex.target_degree,
        }
        for ex in ENCLOSURE_EXAMPLES
    ]


def generate_exercise_file(
    example: EnclosureExample,
    output_dir: str | Path = "exercises/enclosures",
    tempo_bpm: int = 80,
) -> Path:
    """Generate a single exercise file for an enclosure example.

    Args:
        example: The enclosure example to generate
        output_dir: Directory to save exercise files
        tempo_bpm: Tempo in beats per minute

    Returns:
        Path to the generated MIDI file
    """
    output_dir = Path(output_dir)
    output_path = output_dir / f"{example.id}.mid"
    return generate_enclosure_midi(
        output_path=output_path,
        tempo_bpm=tempo_bpm,
        examples=[example],
    )


def generate_all_exercises(
    output_dir: str | Path = "exercises/enclosures",
    tempo_bpm: int = 80,
) -> list[Path]:
    """Generate individual exercise files for all enclosure examples.

    Args:
        output_dir: Directory to save exercise files
        tempo_bpm: Tempo in beats per minute

    Returns:
        List of paths to generated MIDI files
    """
    paths = []
    for example in ENCLOSURE_EXAMPLES:
        path = generate_exercise_file(example, output_dir, tempo_bpm)
        paths.append(path)
    return paths


if __name__ == "__main__":
    # Quick test
    import sys

    if not MIDO_AVAILABLE:
        print("ERROR: mido not installed. Run: pip install mido")
        sys.exit(1)

    # Generate combined file
    combined_path = generate_enclosure_midi()
    print(f"Generated combined file: {combined_path}")

    # List examples
    print("\nEnclosure examples:")
    for ex in list_examples():
        print(f"  {ex['id']}: {ex['degrees']} ({ex['chord']})")
