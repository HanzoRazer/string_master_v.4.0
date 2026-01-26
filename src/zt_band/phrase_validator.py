# phrase_validator.py – Validate MIDI phrases against Zone-Tritone and Barry Harris rules

from mido import MidiFile
from typing import List, Dict, Tuple

# Assume shared.pitch_class utilities
from shared.zone_tritone.pc import pc_from_name
from shared.zone_tritone.zones import is_zone_cross, zone
from shared.zone_tritone.tritones import tritone_partner

# Example validation rules

CHORD_TONES = {
    "Bb7": [pc_from_name(p) for p in ["Bb", "D", "F", "Ab"]],
    "Eb7": [pc_from_name(p) for p in ["Eb", "G", "Bb", "Db"]],
    "Cmaj7": [pc_from_name(p) for p in ["C", "E", "G", "B"]]
}

def extract_pitches_from_midi(mid: MidiFile) -> List[int]:
    """Flatten note-on messages into a pitch list"""
    notes = []
    for track in mid.tracks:
        for msg in track:
            if msg.type == 'note_on' and msg.velocity > 0:
                notes.append(msg.note % 12)  # Only pitch class
    return notes

def count_zone_crossings(pitches: List[int]) -> int:
    return sum(1 for a, b in zip(pitches, pitches[1:]) if is_zone_cross(a, b))

def count_chord_tone_hits(pitches: List[int], chord: str) -> int:
    chord_tones = CHORD_TONES.get(chord, [])
    return sum(1 for p in pitches if p in chord_tones)

def validate_phrase(mid: MidiFile, chord: str) -> Dict[str, float]:
    """Return rule-compliance metrics"""
    pcs = extract_pitches_from_midi(mid)
    total = len(pcs)
    return {
        "zone_cross_ratio": count_zone_crossings(pcs) / max(1, total - 1),
        "chord_tone_hit_ratio": count_chord_tone_hits(pcs, chord) / total
    }

# Example usage
if __name__ == "__main__":
    import sys
    mid = MidiFile(sys.argv[1])
    metrics = validate_phrase(mid, chord="Bb7")
    print("\nValidation Results:")
    for rule, score in metrics.items():
        print(f"{rule}: {score:.2f}")
