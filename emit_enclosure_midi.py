#!/usr/bin/env python3
"""
emit_enclosure_midi.py

Reads enclosures_canonical.json and generates MIDI backing tracks for all
14 enclosure exercises at 3 difficulty levels (beginner/intermediate/advanced).

Output: exercises/enclosures/midi/{id}_{level}.mid  (14 x 3 = 42 files)

Each backing track provides:
  - Shell voicing comping (channel 0) - jazz guitar / piano
  - Walking bass (channel 1)
  - Swing drums (channel 9) - ride, kick, snare, hi-hat

All exercises are 4/4 swing feel with bebop jazz accompaniment.
"""
import json
import os
import sys

try:
    import mido
except ImportError:
    print("ERROR: mido not installed. Run: pip install mido")
    sys.exit(1)

# Fix Windows console encoding
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.abspath(__file__))

# ── Load canonical data ──
with open(os.path.join(ROOT, "enclosures_canonical.json"), encoding="utf-8") as f:
    canon = json.load(f)

exercises = canon["exercises"]

# ── MIDI Constants ──
TPB = 480               # ticks per beat
BAR = TPB * 4           # ticks per bar (4/4)
LOOPS = 4               # number of loops per file

# Programs
PROG_JAZZ_GUITAR = 26   # Electric Guitar (Jazz)
PROG_ACOUSTIC_BASS = 32 # Acoustic Bass

# Percussion (channel 9)
RIDE_CYMBAL = 51
RIDE_BELL = 53
KICK = 36
SNARE = 38
HI_HAT_CLOSED = 42
HI_HAT_PEDAL = 44

# Velocity levels
VEL_COMP = 70
VEL_COMP_ACCENT = 85
VEL_BASS = 80
VEL_RIDE = 75
VEL_RIDE_ACCENT = 90
VEL_KICK = 70
VEL_SNARE = 55       # ghost snare (brushes feel)
VEL_HH_PEDAL = 40

# ── Pitch Class Map ──
PC_MAP = {
    "C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3,
    "E": 4, "Fb": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7,
    "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11, "Cb": 11,
}

# ── Chord Quality Voicings ──
# Intervals from root (in semitones) for shell voicings
CHORD_VOICINGS = {
    "maj7":  [0, 4, 7, 11],      # R 3 5 7
    "6":     [0, 4, 7, 9],       # R 3 5 6
    "7":     [0, 4, 7, 10],      # R 3 5 b7
    "7alt":  [0, 4, 8, 10],      # R 3 #5 b7 (altered voicing)
    "m7":    [0, 3, 7, 10],      # R b3 5 b7
}

# Roman numeral -> (interval_from_key, quality)
RN_MAP = {
    "Imaj7": (0, "maj7"),
    "I6":    (0, "6"),
    "ii7":   (2, "m7"),
    "V7":    (7, "7"),
    "V7alt": (7, "7alt"),
    "vi7":   (9, "m7"),
    "i7":    (0, "m7"),
}

# Concrete chord symbol parsing
CONCRETE_QUALITIES = {
    "maj7": "maj7", "6": "6", "7": "7", "m7": "m7", "7alt": "7alt",
}


def parse_chord_symbol(sym):
    """Parse a chord symbol like 'Imaj7' or 'V7alt' into (root_offset, quality)."""
    sym = sym.strip()
    if sym in RN_MAP:
        return RN_MAP[sym]
    # Unknown - treat as tonic major
    return (0, "maj7")


def chord_notes(key_pc, root_offset, quality, octave=3):
    """Return MIDI note numbers for a chord voicing."""
    root = key_pc + root_offset
    intervals = CHORD_VOICINGS.get(quality, CHORD_VOICINGS["maj7"])
    base = 12 * octave + root
    return [base + iv for iv in intervals]


def bass_note(key_pc, root_offset, octave=2):
    """Return MIDI bass note."""
    return 12 * octave + key_pc + root_offset


# ── Walking Bass Helpers ──

def walking_bass_bar(root_midi, quality, bar_ticks=BAR):
    """Generate a simple walking bass line for one bar (4 beats).

    Returns list of (tick_offset, note, duration, velocity).
    """
    beat = bar_ticks // 4
    notes = []

    # Simple walk: root, 3rd/5th, chromatic approach, root
    intervals = CHORD_VOICINGS.get(quality, [0, 4, 7, 11])

    # Beat 1: root
    notes.append((0, root_midi, beat - 10, VEL_BASS))
    # Beat 2: 3rd or 5th
    step2 = intervals[1] if len(intervals) > 1 else 4
    notes.append((beat, root_midi + step2, beat - 10, VEL_BASS - 5))
    # Beat 3: 5th
    step3 = intervals[2] if len(intervals) > 2 else 7
    notes.append((beat * 2, root_midi + step3, beat - 10, VEL_BASS - 5))
    # Beat 4: chromatic approach to next root (half step below)
    notes.append((beat * 3, root_midi - 1, beat - 10, VEL_BASS - 10))

    return notes


def walking_bass_bar_last(root_midi, quality, bar_ticks=BAR):
    """Walking bass for last bar of a chord - resolve to root."""
    beat = bar_ticks // 4
    intervals = CHORD_VOICINGS.get(quality, [0, 4, 7, 11])
    notes = []

    notes.append((0, root_midi, beat - 10, VEL_BASS))
    step2 = intervals[2] if len(intervals) > 2 else 7
    notes.append((beat, root_midi + step2, beat - 10, VEL_BASS - 5))
    step3 = intervals[1] if len(intervals) > 1 else 4
    notes.append((beat * 2, root_midi + step3, beat - 10, VEL_BASS - 5))
    # Beat 4: root octave
    notes.append((beat * 3, root_midi, beat - 10, VEL_BASS))

    return notes


# ── Drum Pattern Helpers ──

def swing_drums_bar(level, bar_ticks=BAR):
    """Generate swing drum pattern for one bar.

    Returns list of (tick_offset, note, velocity, duration).
    """
    beat = bar_ticks // 4
    triplet = beat // 3  # swing triplet subdivision
    events = []

    # Ride cymbal: all 4 beats + swing "&" on 2 and 4
    for b in range(4):
        t = b * beat
        events.append((t, RIDE_CYMBAL, VEL_RIDE, beat // 2))
        if level != "beginner":
            # Swing eighth: triplet skip pattern (beat + 2/3 beat)
            swing_t = t + triplet * 2
            events.append((swing_t, RIDE_CYMBAL, VEL_RIDE - 15, beat // 3))

    # Hi-hat pedal on 2 and 4
    events.append((beat, HI_HAT_PEDAL, VEL_HH_PEDAL, beat // 4))
    events.append((beat * 3, HI_HAT_PEDAL, VEL_HH_PEDAL, beat // 4))

    if level == "beginner":
        # Simple: kick on 1 and 3
        events.append((0, KICK, VEL_KICK, beat // 2))
        events.append((beat * 2, KICK, VEL_KICK - 10, beat // 2))
    elif level == "intermediate":
        # Kick on 1, ghost snare on 2-and and 4-and
        events.append((0, KICK, VEL_KICK, beat // 2))
        events.append((beat + triplet * 2, SNARE, VEL_SNARE, beat // 4))
        events.append((beat * 3 + triplet * 2, SNARE, VEL_SNARE, beat // 4))
    else:
        # Advanced: kick on 1, syncopated kick on and-of-3, ghost snares
        events.append((0, KICK, VEL_KICK, beat // 2))
        events.append((beat * 2 + triplet * 2, KICK, VEL_KICK - 15, beat // 4))
        events.append((beat + triplet * 2, SNARE, VEL_SNARE, beat // 4))
        events.append((beat * 3 + triplet * 2, SNARE, VEL_SNARE, beat // 4))
        # Ride bell accent on beat 1
        events.append((0, RIDE_BELL, VEL_RIDE_ACCENT, beat // 2))

    return events


# ── Comping Patterns ──

def comp_whole_notes(chord_midi, bar_ticks=BAR):
    """Whole note comping - one chord per bar."""
    return [(0, chord_midi, BAR - 10, VEL_COMP)]


def comp_rhythmic(chord_midi, bar_ticks=BAR):
    """Rhythmic comping - Charleston pattern (beat 1, and-of-2)."""
    beat = bar_ticks // 4
    triplet = beat // 3
    events = []
    # Beat 1 (dotted quarter)
    events.append((0, chord_midi, beat + beat // 2, VEL_COMP_ACCENT))
    # And-of-2 (swing placement)
    events.append((beat + triplet * 2, chord_midi, beat, VEL_COMP))
    # Beat 4
    events.append((beat * 3, chord_midi, beat - 20, VEL_COMP))
    return events


def comp_syncopated(chord_midi, bar_ticks=BAR):
    """Syncopated comping - offbeat accents, Freddie Green style."""
    beat = bar_ticks // 4
    triplet = beat // 3
    events = []
    # And-of-1
    events.append((triplet * 2, chord_midi, beat // 2, VEL_COMP))
    # Beat 2
    events.append((beat, chord_midi, beat // 2, VEL_COMP_ACCENT))
    # And-of-3
    events.append((beat * 2 + triplet * 2, chord_midi, beat // 2, VEL_COMP))
    # And-of-4
    events.append((beat * 3 + triplet * 2, chord_midi, beat - 20, VEL_COMP))
    return events


COMP_FUNCS = {
    "whole_notes": comp_whole_notes,
    "rhythmic": comp_rhythmic,
    "syncopated": comp_syncopated,
}


# ── MIDI Generation ──

def get_level_tempos(ex):
    """Return tempo for each level from exercise data."""
    tr = ex.get("tempo_range", [48, 110])
    mid = ex.get("tempo_bpm", 72)
    return {
        "beginner": tr[0],
        "intermediate": mid,
        "advanced": tr[1],
    }


def get_comping_style(level):
    """Map level to comping style."""
    return {
        "beginner": "whole_notes",
        "intermediate": "rhythmic",
        "advanced": "syncopated",
    }[level]


def generate_midi(ex, level, bpm, outpath):
    """Generate a MIDI backing track for one exercise at one level."""
    mid = mido.MidiFile(ticks_per_beat=TPB)
    key_pc = PC_MAP.get(ex["key"], 0)
    chords = ex["chords"]
    loop_bars = ex["loop_bars"]
    comp_style = get_comping_style(level)
    comp_func = COMP_FUNCS[comp_style]

    # ── Track 0: Tempo + metadata ──
    meta_track = mido.MidiTrack()
    mid.tracks.append(meta_track)
    meta_track.append(mido.MetaMessage("track_name",
                                        name=f"{ex['title']} ({level})",
                                        time=0))
    meta_track.append(mido.MetaMessage("set_tempo",
                                        tempo=mido.bpm2tempo(bpm),
                                        time=0))
    meta_track.append(mido.MetaMessage("time_signature",
                                        numerator=4, denominator=4,
                                        time=0))

    # Total ticks
    total_bars = loop_bars * LOOPS
    total_ticks = total_bars * BAR
    meta_track.append(mido.MetaMessage("end_of_track", time=total_ticks))

    # ── Track 1: Comping (channel 0) ──
    comp_track = mido.MidiTrack()
    mid.tracks.append(comp_track)
    comp_track.append(mido.MetaMessage("track_name", name="Comping", time=0))
    comp_track.append(mido.Message("program_change", program=PROG_JAZZ_GUITAR,
                                    channel=0, time=0))

    # Build chord schedule: which chord at which bar
    # chords list maps to bars (one chord per bar, cycling if needed)
    chord_schedule = []
    for bar_idx in range(total_bars):
        loop_bar = bar_idx % loop_bars
        chord_idx = loop_bar % len(chords)
        chord_schedule.append(chords[chord_idx])

    # Generate comping events as absolute tick events
    comp_events = []
    for bar_idx, chord_sym in enumerate(chord_schedule):
        offset, quality = parse_chord_symbol(chord_sym)
        cnotes = chord_notes(key_pc, offset, quality, octave=3)
        bar_start = bar_idx * BAR
        pattern = comp_func(cnotes, BAR)

        for (t, notes_list, dur, vel) in pattern:
            abs_t = bar_start + t
            if isinstance(notes_list, list):
                for n in notes_list:
                    comp_events.append(("on", abs_t, n, vel, 0))
                    comp_events.append(("off", abs_t + dur, n, 0, 0))
            else:
                # notes_list is actually a single note
                comp_events.append(("on", abs_t, notes_list, vel, 0))
                comp_events.append(("off", abs_t + dur, notes_list, 0, 0))

    # Sort by time and convert to delta
    comp_events.sort(key=lambda e: (e[1], 0 if e[0] == "off" else 1))
    prev_t = 0
    for evt in comp_events:
        _, abs_t, note, vel, _ = evt
        delta = abs_t - prev_t
        if evt[0] == "on":
            comp_track.append(mido.Message("note_on", note=note, velocity=vel,
                                            channel=0, time=delta))
        else:
            comp_track.append(mido.Message("note_off", note=note, velocity=0,
                                            channel=0, time=delta))
        prev_t = abs_t

    comp_track.append(mido.MetaMessage("end_of_track", time=0))

    # ── Track 2: Walking Bass (channel 1) ──
    bass_track = mido.MidiTrack()
    mid.tracks.append(bass_track)
    bass_track.append(mido.MetaMessage("track_name", name="Walking Bass", time=0))
    bass_track.append(mido.Message("program_change", program=PROG_ACOUSTIC_BASS,
                                    channel=1, time=0))

    bass_events = []
    for bar_idx, chord_sym in enumerate(chord_schedule):
        offset, quality = parse_chord_symbol(chord_sym)
        root = bass_note(key_pc, offset, octave=2)
        bar_start = bar_idx * BAR

        # Use "last bar" pattern if this is the last bar of a loop section
        loop_bar = bar_idx % loop_bars
        if loop_bar == loop_bars - 1:
            bar_notes = walking_bass_bar_last(root, quality)
        else:
            bar_notes = walking_bass_bar(root, quality)

        for (t, note, dur, vel) in bar_notes:
            abs_t = bar_start + t
            bass_events.append(("on", abs_t, note, vel))
            bass_events.append(("off", abs_t + dur, note, 0))

    bass_events.sort(key=lambda e: (e[1], 0 if e[0] == "off" else 1))
    prev_t = 0
    for evt in bass_events:
        _, abs_t, note, vel = evt
        delta = abs_t - prev_t
        if evt[0] == "on":
            bass_track.append(mido.Message("note_on", note=note, velocity=vel,
                                            channel=1, time=delta))
        else:
            bass_track.append(mido.Message("note_off", note=note, velocity=0,
                                            channel=1, time=delta))
        prev_t = abs_t

    bass_track.append(mido.MetaMessage("end_of_track", time=0))

    # ── Track 3: Drums (channel 9) ──
    drum_track = mido.MidiTrack()
    mid.tracks.append(drum_track)
    drum_track.append(mido.MetaMessage("track_name", name="Drums", time=0))

    drum_events = []
    for bar_idx in range(total_bars):
        bar_start = bar_idx * BAR
        pattern = swing_drums_bar(level, BAR)
        for (t, note, vel, dur) in pattern:
            abs_t = bar_start + t
            drum_events.append(("on", abs_t, note, vel))
            drum_events.append(("off", abs_t + dur, note, 0))

    drum_events.sort(key=lambda e: (e[1], 0 if e[0] == "off" else 1))
    prev_t = 0
    for evt in drum_events:
        _, abs_t, note, vel = evt
        delta = abs_t - prev_t
        if evt[0] == "on":
            drum_track.append(mido.Message("note_on", note=note, velocity=vel,
                                            channel=9, time=delta))
        else:
            drum_track.append(mido.Message("note_off", note=note, velocity=0,
                                            channel=9, time=delta))
        prev_t = abs_t

    drum_track.append(mido.MetaMessage("end_of_track", time=0))

    # ── Save ──
    mid.save(outpath)


# ── Main ──

if __name__ == "__main__":
    midi_dir = os.path.join(ROOT, "exercises", "enclosures", "midi")
    os.makedirs(midi_dir, exist_ok=True)

    levels = ["beginner", "intermediate", "advanced"]
    total = 0

    for ex in exercises:
        tempos = get_level_tempos(ex)
        print(f"  {ex['id']}: ", end="")
        for level in levels:
            bpm = tempos[level]
            fname = f"{ex['id']}_{level}.mid"
            outpath = os.path.join(midi_dir, fname)
            generate_midi(ex, level, bpm, outpath)
            total += 1
        print(f"3 levels")

    print(f"\nTotal MIDI files: {total}")
    print(f"Output: {midi_dir}/")
