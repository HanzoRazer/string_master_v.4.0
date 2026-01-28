#!/usr/bin/env python3
"""
emit_got_rhythm_midi.py

Reads got_rhythm_canonical.json and generates MIDI backing tracks for all
4 backing tracks at 3 difficulty levels (beginner/intermediate/advanced).

Output: exercises/got_rhythm/midi/{id}_{level}.mid  (4 x 3 = 12 files)

Each backing track provides:
  - Shell voicing comping (channel 0) - jazz guitar
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

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(ROOT, "got_rhythm_canonical.json"), encoding="utf-8") as f:
    canon = json.load(f)

backing_tracks = canon["backing_tracks"]


def _latin1_safe(s):
    """Replace non-Latin-1 characters for MIDI track names."""
    return s.replace("\u2013", "-").replace("\u2192", "->").encode(
        "latin-1", errors="replace").decode("latin-1")


# ── MIDI Constants ──
TPB = 480
BAR = TPB * 4
LOOPS = 4

# Programs
PROG_JAZZ_GUITAR = 26
PROG_ACOUSTIC_BASS = 32

# Percussion (channel 9)
RIDE_CYMBAL = 51
RIDE_BELL = 53
KICK = 36
SNARE = 38
HI_HAT_CLOSED = 42
HI_HAT_PEDAL = 44

# Velocity
VEL_COMP = 70
VEL_COMP_ACCENT = 85
VEL_BASS = 80
VEL_RIDE = 75
VEL_RIDE_ACCENT = 90
VEL_KICK = 70
VEL_SNARE = 55
VEL_HH_PEDAL = 40

# ── Pitch Class Map ──
PC_MAP = {
    "C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3,
    "E": 4, "Fb": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7,
    "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11, "Cb": 11,
}

# ── Chord Voicings ──
CHORD_VOICINGS = {
    "maj7":  [0, 4, 7, 11],
    "6":     [0, 4, 7, 9],
    "7":     [0, 4, 7, 10],
    "m7":    [0, 3, 7, 10],
}

# Roman numeral → (interval_from_key, quality)
RN_MAP = {
    "I7":     (0, "7"),
    "IV7":    (5, "7"),
    "V7":     (7, "7"),
    "VI7":    (9, "7"),
    "ii7":    (2, "m7"),
    "IVmaj7": (5, "maj7"),
    "bVII7":  (10, "7"),
}


def parse_chord(sym):
    sym = sym.strip()
    if sym in RN_MAP:
        return RN_MAP[sym]
    return (0, "7")


def chord_notes(key_pc, offset, quality, octave=3):
    intervals = CHORD_VOICINGS.get(quality, CHORD_VOICINGS["7"])
    base = 12 * octave + key_pc + offset
    return [base + iv for iv in intervals]


def bass_note(key_pc, offset, octave=2):
    return 12 * octave + key_pc + offset


# ── Walking Bass ──

def walking_bass_bar(root_midi, quality):
    beat = BAR // 4
    intervals = CHORD_VOICINGS.get(quality, [0, 4, 7, 10])
    notes = [
        (0, root_midi, beat - 10, VEL_BASS),
        (beat, root_midi + intervals[1], beat - 10, VEL_BASS - 5),
        (beat * 2, root_midi + intervals[2], beat - 10, VEL_BASS - 5),
        (beat * 3, root_midi - 1, beat - 10, VEL_BASS - 10),
    ]
    return notes


def walking_bass_bar_last(root_midi, quality):
    beat = BAR // 4
    intervals = CHORD_VOICINGS.get(quality, [0, 4, 7, 10])
    notes = [
        (0, root_midi, beat - 10, VEL_BASS),
        (beat, root_midi + intervals[2], beat - 10, VEL_BASS - 5),
        (beat * 2, root_midi + intervals[1], beat - 10, VEL_BASS - 5),
        (beat * 3, root_midi, beat - 10, VEL_BASS),
    ]
    return notes


# ── Swing Drums ──

def swing_drums_bar(level):
    beat = BAR // 4
    triplet = beat // 3
    events = []

    for b in range(4):
        t = b * beat
        events.append((t, RIDE_CYMBAL, VEL_RIDE, beat // 2))
        if level != "beginner":
            events.append((t + triplet * 2, RIDE_CYMBAL, VEL_RIDE - 15, beat // 3))

    events.append((beat, HI_HAT_PEDAL, VEL_HH_PEDAL, beat // 4))
    events.append((beat * 3, HI_HAT_PEDAL, VEL_HH_PEDAL, beat // 4))

    if level == "beginner":
        events.append((0, KICK, VEL_KICK, beat // 2))
        events.append((beat * 2, KICK, VEL_KICK - 10, beat // 2))
    elif level == "intermediate":
        events.append((0, KICK, VEL_KICK, beat // 2))
        events.append((beat + triplet * 2, SNARE, VEL_SNARE, beat // 4))
        events.append((beat * 3 + triplet * 2, SNARE, VEL_SNARE, beat // 4))
    else:
        events.append((0, KICK, VEL_KICK, beat // 2))
        events.append((beat * 2 + triplet * 2, KICK, VEL_KICK - 15, beat // 4))
        events.append((beat + triplet * 2, SNARE, VEL_SNARE, beat // 4))
        events.append((beat * 3 + triplet * 2, SNARE, VEL_SNARE, beat // 4))
        events.append((0, RIDE_BELL, VEL_RIDE_ACCENT, beat // 2))

    return events


# ── Comping Patterns ──

def comp_whole_notes(cnotes):
    return [(0, cnotes, BAR - 10, VEL_COMP)]


def comp_rhythmic(cnotes):
    beat = BAR // 4
    triplet = beat // 3
    return [
        (0, cnotes, beat + beat // 2, VEL_COMP_ACCENT),
        (beat + triplet * 2, cnotes, beat, VEL_COMP),
        (beat * 3, cnotes, beat - 20, VEL_COMP),
    ]


def comp_syncopated(cnotes):
    beat = BAR // 4
    triplet = beat // 3
    return [
        (triplet * 2, cnotes, beat // 2, VEL_COMP),
        (beat, cnotes, beat // 2, VEL_COMP_ACCENT),
        (beat * 2 + triplet * 2, cnotes, beat // 2, VEL_COMP),
        (beat * 3 + triplet * 2, cnotes, beat - 20, VEL_COMP),
    ]


COMP_FUNCS = {
    "beginner": comp_whole_notes,
    "intermediate": comp_rhythmic,
    "advanced": comp_syncopated,
}


# ── Event helpers ──

def flatten_note_events(events):
    flat = []
    for (t, notes, dur, vel) in events:
        if isinstance(notes, list):
            for n in notes:
                flat.append(("on", t, n, vel))
                flat.append(("off", t + dur, n, 0))
        else:
            flat.append(("on", t, notes, vel))
            flat.append(("off", t + dur, notes, 0))
    return flat


def write_track(mid, flat_events, channel, track_name, program=None):
    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.MetaMessage("track_name", name=track_name, time=0))
    if program is not None:
        track.append(mido.Message("program_change", program=program,
                                  channel=channel, time=0))

    flat_events.sort(key=lambda e: (e[1], 0 if e[0] == "off" else 1))
    prev_t = 0
    for kind, abs_t, note, vel in flat_events:
        delta = abs_t - prev_t
        if kind == "on":
            track.append(mido.Message("note_on", note=note, velocity=vel,
                                      channel=channel, time=delta))
        else:
            track.append(mido.Message("note_off", note=note, velocity=0,
                                      channel=channel, time=delta))
        prev_t = abs_t

    track.append(mido.MetaMessage("end_of_track", time=0))


# ── Main generation ──

def generate_midi(bt, level, bpm, outpath):
    mid = mido.MidiFile(ticks_per_beat=TPB)
    key_pc = PC_MAP.get(bt["root"], 0)
    chords = bt["chords"]
    loop_bars = bt["loop_bars"]
    total_bars = loop_bars * LOOPS
    total_ticks = total_bars * BAR
    comp_func = COMP_FUNCS[level]

    # Track 0: Tempo + metadata
    meta_track = mido.MidiTrack()
    mid.tracks.append(meta_track)
    meta_track.append(mido.MetaMessage("track_name",
                                        name=_latin1_safe(f"{bt['title']} ({level})"),
                                        time=0))
    meta_track.append(mido.MetaMessage("set_tempo",
                                        tempo=mido.bpm2tempo(bpm), time=0))
    meta_track.append(mido.MetaMessage("time_signature",
                                        numerator=4, denominator=4, time=0))
    meta_track.append(mido.MetaMessage("end_of_track", time=total_ticks))

    # Build chord schedule
    chord_schedule = []
    for bar_idx in range(total_bars):
        loop_bar = bar_idx % loop_bars
        chord_idx = loop_bar % len(chords)
        chord_schedule.append(chords[chord_idx])

    # Track 1: Comping
    comp_events = []
    for bar_idx, sym in enumerate(chord_schedule):
        offset, quality = parse_chord(sym)
        cnotes = chord_notes(key_pc, offset, quality, octave=3)
        bar_start = bar_idx * BAR
        pattern = comp_func(cnotes)
        for (t, notes, dur, vel) in pattern:
            comp_events.append((bar_start + t, notes, dur, vel))

    write_track(mid, flatten_note_events(comp_events), 0, "Comping",
                PROG_JAZZ_GUITAR)

    # Track 2: Walking Bass
    bass_events = []
    for bar_idx, sym in enumerate(chord_schedule):
        offset, quality = parse_chord(sym)
        root = bass_note(key_pc, offset, octave=2)
        bar_start = bar_idx * BAR
        loop_bar = bar_idx % loop_bars
        if loop_bar == loop_bars - 1:
            bar_notes = walking_bass_bar_last(root, quality)
        else:
            bar_notes = walking_bass_bar(root, quality)
        for (t, note, dur, vel) in bar_notes:
            bass_events.append((bar_start + t, note, dur, vel))

    write_track(mid, flatten_note_events(bass_events), 1, "Walking Bass",
                PROG_ACOUSTIC_BASS)

    # Track 3: Drums
    drum_flat = []
    for bar_idx in range(total_bars):
        bar_start = bar_idx * BAR
        pattern = swing_drums_bar(level)
        for (t, note, vel, dur) in pattern:
            drum_flat.append(("on", bar_start + t, note, vel))
            drum_flat.append(("off", bar_start + t + dur, note, 0))

    write_track(mid, drum_flat, 9, "Drums")

    mid.save(outpath)


if __name__ == "__main__":
    midi_dir = os.path.join(ROOT, "exercises", "got_rhythm", "midi")
    os.makedirs(midi_dir, exist_ok=True)

    levels = ["beginner", "intermediate", "advanced"]
    total = 0

    for bt in backing_tracks:
        tr = bt.get("tempo_range", [80, 180])
        tempos = {
            "beginner": tr[0],
            "intermediate": bt.get("tempo_bpm", 120),
            "advanced": tr[1],
        }

        print(f"  {bt['id']}: ", end="")
        for level in levels:
            bpm = tempos[level]
            fname = f"{bt['id']}_{level}.mid"
            outpath = os.path.join(midi_dir, fname)
            generate_midi(bt, level, bpm, outpath)
            total += 1
        print("3 levels")

    print(f"\nTotal MIDI files: {total}")
    print(f"Output: {midi_dir}/")
