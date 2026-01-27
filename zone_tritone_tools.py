"""
zone_tritone_tools.py

A small, self-contained toolkit that:
1) Implements the Zone-Tritone "gravity" primitives (zones, tritone axes, dominant pairs)
2) Analyzes a blues (e.g., Red House in Bb) for tritone gravity events
3) Generates MIDI practice loops (including backdoor cadence) with mido

Requires: pip install mido
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Iterable

# -----------------------------
# 1) Pitch-class utilities
# -----------------------------

NOTE_TO_PC: Dict[str, int] = {
    "C": 0, "B#": 0,
    "C#": 1, "Db": 1,
    "D": 2,
    "D#": 3, "Eb": 3,
    "E": 4, "Fb": 4,
    "E#": 5, "F": 5,
    "F#": 6, "Gb": 6,
    "G": 7,
    "G#": 8, "Ab": 8,
    "A": 9,
    "A#": 10, "Bb": 10,
    "B": 11, "Cb": 11,
}

PC_TO_NAME_SHARP: Dict[int, str] = {
    0: "C", 1: "C#", 2: "D", 3: "D#", 4: "E", 5: "F",
    6: "F#", 7: "G", 8: "G#", 9: "A", 10: "A#", 11: "B"
}
PC_TO_NAME_FLAT: Dict[int, str] = {
    0: "C", 1: "Db", 2: "D", 3: "Eb", 4: "E", 5: "F",
    6: "Gb", 7: "G", 8: "Ab", 9: "A", 10: "Bb", 11: "B"
}

def pc(name: str) -> int:
    """Convert note name to pitch class [0..11]."""
    name = name.strip()
    if name not in NOTE_TO_PC:
        raise ValueError(f"Unknown note name: {name}")
    return NOTE_TO_PC[name]

def name_from_pc(p: int, prefer_flats: bool = True) -> str:
    p %= 12
    return (PC_TO_NAME_FLAT if prefer_flats else PC_TO_NAME_SHARP)[p]

def zone(p: int) -> int:
    """Zone is parity of pitch class: 0=even-zone, 1=odd-zone."""
    return (p % 12) % 2

def is_half_step(a: int, b: int) -> bool:
    """True if a->b is a semitone move in either direction."""
    d = (b - a) % 12
    return d in (1, 11)

def is_zone_cross(a: int, b: int) -> bool:
    """Half-steps cross zones (parity changes)."""
    return zone(a) != zone(b)

# -----------------------------
# 2) Tritone axes + dominants
# -----------------------------

TritoneAxis = Tuple[int, int]

def canonical_axis(a: int, b: int) -> TritoneAxis:
    """Sort for stable representation."""
    a %= 12; b %= 12
    return (a, b) if a < b else (b, a)

def tritone_partner(p: int) -> int:
    return (p + 6) % 12

def all_tritone_axes() -> List[TritoneAxis]:
    """Return the 6 unique tritone axes in 12-TET."""
    axes = set()
    for p in range(12):
        axes.add(canonical_axis(p, tritone_partner(p)))
    return sorted(axes)

def dominant_roots_from_axis(axis: TritoneAxis) -> Tuple[int, int]:
    """
    Given a tritone axis (the 3rd & 7th of a dominant), return the two dominant roots
    that share that tritone (tritone-sub pair).

    If a dominant root is R, its 3rd is R+4 and its 7th is R+10.
    So axis should match {R+4, R+10} (unordered).
    Solve: R+4 = x and R+10 = y => y-x = 6 (a tritone), consistent.
    Then R = x-4 (mod12) (also = y-10).
    The tritone-sub root is R+6.
    """
    x, y = axis
    # pick one member as "3rd" candidate
    r1 = (x - 4) % 12
    r1_axis = canonical_axis((r1 + 4) % 12, (r1 + 10) % 12)
    if r1_axis != canonical_axis(x, y):
        # try using the other member
        r1 = (y - 4) % 12
        r1_axis = canonical_axis((r1 + 4) % 12, (r1 + 10) % 12)
        if r1_axis != canonical_axis(x, y):
            raise ValueError(f"Axis {axis} does not match any dominant's (3rd,7th).")
    r2 = (r1 + 6) % 12
    return r1, r2

def dominant_tritone_axis(root: int) -> TritoneAxis:
    """Axis (3rd,7th) for a dominant 7th chord built on root."""
    return canonical_axis((root + 4) % 12, (root + 10) % 12)

# -----------------------------
# 3) "Red House" style blues analysis
# -----------------------------

@dataclass(frozen=True)
class DominantEvent:
    chord_root: int
    axis: TritoneAxis
    resolve_to: int  # target tonic pitch class (or chord root)
    gravity_role: str  # "tonic_dom", "front_door", "backdoor", "sub"

def blues_12bar_roots(key_root: int) -> List[int]:
    """
    12-bar blues in dominant sevenths, expressed as chord roots (pitch classes).
    I7 (4 bars), IV7 (2), I7 (2), V7 (1), IV7 (1), I7 (2)

    This is a neutral template; Hendrix often stretches/varies bars,
    but this is a good analysis baseline.
    """
    I = key_root % 12
    IV = (I + 5) % 12
    V = (I + 7) % 12
    return [I, I, I, I, IV, IV, I, I, V, IV, I, I]

def analyze_blues_gravity(key_name: str, prefer_flats: bool = True) -> List[DominantEvent]:
    """
    Produce a list of DominantEvents for a 12-bar blues in the given key center.
    Each bar's dominant has a tritone axis.
    """
    key_root = pc(key_name)
    bars = blues_12bar_roots(key_root)
    events: List[DominantEvent] = []
    for r in bars:
        ax = dominant_tritone_axis(r)
        role = "tonic_dom" if r == key_root else ("subdominant_dom" if r == (key_root + 5) % 12 else "dominant_dom")
        events.append(DominantEvent(chord_root=r, axis=ax, resolve_to=key_root, gravity_role=role))
    return events

def backdoor_cadence_roots(key_root: int) -> Tuple[int, int, int]:
    """IV -> bVII7 -> I in major key center."""
    I = key_root % 12
    IV = (I + 5) % 12
    bVII = (I + 10) % 12
    return IV, bVII, I

# -----------------------------
# 4) MIDI generation (mido)
# -----------------------------

def make_backdoor_midi(
    out_path: str,
    key: str = "C",
    bpm: int = 84,
    bars: int = 16,
    tpb: int = 480,
) -> str:
    """
    Generate a non-truncated practice loop:
    - IVmaj7 (1 bar) -> bVII7 (1 bar) -> Imaj7 (2 bars) repeated
    - final 2-bar tonic hold

    Uses simple piano voicings; you can replace with guitar-friendly voicings later.
    """
    import mido
    from mido import MidiFile, MidiTrack, Message, MetaMessage

    key_root = pc(key)
    IV, bVII, I = backdoor_cadence_roots(key_root)

    def midi_note(pitch_class: int, octave: int) -> int:
        return 12 * (octave + 1) + (pitch_class % 12)

    # Simple, clear voicings (root position-ish in a mid register)
    # maj7: R 3 5 7 ; dom7: R 3 5 b7
    def maj7_voicing(root_pc: int) -> List[int]:
        return [
            midi_note(root_pc, 3),
            midi_note((root_pc + 4) % 12, 3),
            midi_note((root_pc + 7) % 12, 4),
            midi_note((root_pc + 11) % 12, 4),
        ]

    def dom7_voicing(root_pc: int) -> List[int]:
        return [
            midi_note(root_pc, 3),
            midi_note((root_pc + 4) % 12, 3),
            midi_note((root_pc + 7) % 12, 4),
            midi_note((root_pc + 10) % 12, 4),
        ]

    BAR = tpb * 4

    def chord(track: MidiTrack, notes: List[int], dur: int, vel: int = 76):
        for i, n in enumerate(notes):
            track.append(Message("note_on", note=n, velocity=vel, time=0 if i else 0, channel=0))
        for i, n in enumerate(notes):
            track.append(Message("note_off", note=n, velocity=0, time=dur if i == 0 else 0, channel=0))

    mid = MidiFile(ticks_per_beat=tpb)
    tr = MidiTrack()
    mid.tracks.append(tr)

    tr.append(MetaMessage("set_tempo", tempo=mido.bpm2tempo(bpm), time=0))
    tr.append(MetaMessage("time_signature", numerator=4, denominator=4, time=0))
    tr.append(MetaMessage("key_signature", key=key, time=0))
    tr.append(Message("program_change", program=0, time=0, channel=0))

    # Build bars in blocks of 4: IV (1), bVII7 (1), I (2)
    block = [("IV", maj7_voicing(IV)), ("bVII7", dom7_voicing(bVII)), ("I", maj7_voicing(I)), ("I", maj7_voicing(I))]
    blocks = bars // 4

    for _ in range(blocks):
        chord(tr, block[0][1], BAR)
        chord(tr, block[1][1], BAR)
        chord(tr, block[2][1], BAR)
        chord(tr, block[3][1], BAR)

    # strong ending
    chord(tr, maj7_voicing(I), BAR * 2, vel=84)

    tr.append(MetaMessage("end_of_track", time=0))
    mid.save(out_path)
    return out_path

# -----------------------------
# 5) Demo runner
# -----------------------------

if __name__ == "__main__":
    # Example: Red House (Bb blues) gravity printout
    events = analyze_blues_gravity("Bb")
    print("12-bar Bb blues dominant events:")
    for i, ev in enumerate(events, start=1):
        r = name_from_pc(ev.chord_root, prefer_flats=True)
        ax = (name_from_pc(ev.axis[0], True), name_from_pc(ev.axis[1], True))
        print(f"Bar {i:02d}: {r}7  axis={ax}  role={ev.gravity_role}")

    # Example: make a backdoor MIDI loop in C
    out = make_backdoor_midi("backdoor_IV_bVII_I_C.mid", key="C", bpm=84, bars=16)
    print("Wrote:", out)
