#!/usr/bin/env python3
"""
emit_bluegrass_midi.py

Reads bluegrass_canonical.json and generates MIDI backing tracks for all
12 backing tracks at 3 difficulty levels (beginner/intermediate/advanced).

Output: exercises/bluegrass/midi/{id}_{level}.mid  (12 x 3 = 36 files)

Each backing track provides:
  - Acoustic guitar strumming (channel 0) - boom-chick / strum patterns
  - Acoustic bass (channel 1) - root-fifth alternating bass
  - Brushes/percussion (channel 9) - light straight-feel drums

All exercises use straight feel (no swing).  Supports 4/4 and 3/4 meters.
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

with open(os.path.join(ROOT, "bluegrass_canonical.json"), encoding="utf-8") as f:
    canon = json.load(f)

backing_tracks = canon["backing_tracks"]

# ── MIDI Constants ──
TPB = 480               # ticks per beat
LOOPS = 4               # number of loops per file

# Programs
PROG_STEEL_GUITAR = 25  # Acoustic Guitar (Steel)
PROG_ACOUSTIC_BASS = 32 # Acoustic Bass

# Percussion (channel 9) — brushes / light
KICK = 36
SNARE = 38
SIDE_STICK = 37
HI_HAT_CLOSED = 42
HI_HAT_OPEN = 46
HI_HAT_PEDAL = 44

# Velocity levels
VEL_STRUM = 75
VEL_STRUM_ACCENT = 90
VEL_BASS = 80
VEL_BASS_SOFT = 65
VEL_KICK = 60
VEL_SNARE = 50          # brushes / side stick
VEL_HH = 45

# ── Pitch Class Map ──
PC_MAP = {
    "C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3,
    "E": 4, "Fb": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7,
    "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11, "Cb": 11,
}

# ── Chord Voicings (open-position style) ──
CHORD_INTERVALS = {
    "major": [0, 4, 7],          # R 3 5
    "major_full": [0, 4, 7, 12], # R 3 5 R8
    "7":     [0, 4, 7, 10],      # R 3 5 b7
}

# Roman numeral → (interval_from_key, quality)
RN_MAP = {
    "I":   (0, "major"),
    "IV":  (5, "major"),
    "V":   (7, "major"),
    "V7":  (7, "7"),
}


def parse_chord(sym):
    sym = sym.strip()
    if sym in RN_MAP:
        return RN_MAP[sym]
    return (0, "major")


def chord_notes(key_pc, offset, quality, octave=3):
    intervals = CHORD_INTERVALS.get(quality, CHORD_INTERVALS["major"])
    base = 12 * octave + key_pc + offset
    return [base + iv for iv in intervals]


def bass_root(key_pc, offset, octave=2):
    return 12 * octave + key_pc + offset


def bass_fifth(key_pc, offset, octave=2):
    return 12 * octave + key_pc + offset + 7


# ── Bar duration helper ──

def bar_ticks(meter):
    if meter == "3/4":
        return TPB * 3
    return TPB * 4


# ── Comping Patterns (straight feel) ──

def comp_whole(cnotes, bt):
    """Beginner: one strum per bar on beat 1."""
    return [(0, cnotes, bt - 20, VEL_STRUM)]


def comp_boom_chick_44(cnotes, bt):
    """Intermediate 4/4: strum on 2 and 4 (chick)."""
    beat = bt // 4
    return [
        (beat, cnotes, beat - 20, VEL_STRUM),
        (beat * 3, cnotes, beat - 20, VEL_STRUM),
    ]


def comp_boom_chick_34(cnotes, bt):
    """Intermediate 3/4: strum on 2 and 3 (oom-pah-pah)."""
    beat = bt // 3
    return [
        (beat, cnotes, beat - 20, VEL_STRUM),
        (beat * 2, cnotes, beat - 20, VEL_STRUM),
    ]


def comp_driving_44(cnotes, bt):
    """Advanced 4/4: all-beat strumming with accents on 2 and 4."""
    beat = bt // 4
    return [
        (0, cnotes, beat - 20, VEL_STRUM - 10),
        (beat, cnotes, beat - 20, VEL_STRUM_ACCENT),
        (beat * 2, cnotes, beat - 20, VEL_STRUM - 10),
        (beat * 3, cnotes, beat - 20, VEL_STRUM_ACCENT),
    ]


def comp_driving_34(cnotes, bt):
    """Advanced 3/4: all-beat strumming with accent on 1."""
    beat = bt // 3
    return [
        (0, cnotes, beat - 20, VEL_STRUM_ACCENT),
        (beat, cnotes, beat - 20, VEL_STRUM),
        (beat * 2, cnotes, beat - 20, VEL_STRUM),
    ]


# ── Bass Patterns ──

def bass_simple(root, fifth, bt, meter):
    """Beginner: root on beat 1 only."""
    return [(0, root, bt - 20, VEL_BASS)]


def bass_alternating_44(root, fifth, bt, meter):
    """Intermediate 4/4: root on 1, fifth on 3."""
    beat = bt // 4
    return [
        (0, root, beat * 2 - 20, VEL_BASS),
        (beat * 2, fifth, beat * 2 - 20, VEL_BASS_SOFT),
    ]


def bass_alternating_34(root, fifth, bt, meter):
    """Intermediate 3/4: root on 1 (half note feel)."""
    beat = bt // 3
    return [
        (0, root, beat * 2 - 20, VEL_BASS),
        (beat * 2, fifth, beat - 20, VEL_BASS_SOFT),
    ]


def bass_walking_44(root, fifth, bt, meter):
    """Advanced 4/4: root, passing, fifth, approach."""
    beat = bt // 4
    passing = root + 4  # major 3rd as passing tone
    approach = root - 1  # chromatic below
    return [
        (0, root, beat - 10, VEL_BASS),
        (beat, passing, beat - 10, VEL_BASS_SOFT),
        (beat * 2, fifth, beat - 10, VEL_BASS),
        (beat * 3, approach, beat - 10, VEL_BASS_SOFT),
    ]


def bass_walking_34(root, fifth, bt, meter):
    """Advanced 3/4: root, fifth, approach."""
    beat = bt // 3
    approach = root - 1
    return [
        (0, root, beat - 10, VEL_BASS),
        (beat, fifth, beat - 10, VEL_BASS_SOFT),
        (beat * 2, approach, beat - 10, VEL_BASS_SOFT),
    ]


# ── Drum Patterns (straight feel, light) ──

def drums_none(bt, meter):
    """Beginner: no drums."""
    return []


def drums_brushes_44(bt, meter):
    """Intermediate 4/4: side stick on 2 and 4, hi-hat pedal on all beats."""
    beat = bt // 4
    events = []
    for b in range(4):
        events.append((b * beat, HI_HAT_CLOSED, VEL_HH, beat // 2))
    events.append((beat, SIDE_STICK, VEL_SNARE, beat // 2))
    events.append((beat * 3, SIDE_STICK, VEL_SNARE, beat // 2))
    return events


def drums_brushes_34(bt, meter):
    """Intermediate 3/4: side stick on 2, hi-hat on all beats."""
    beat = bt // 3
    events = []
    for b in range(3):
        events.append((b * beat, HI_HAT_CLOSED, VEL_HH, beat // 2))
    events.append((beat, SIDE_STICK, VEL_SNARE, beat // 2))
    return events


def drums_full_44(bt, meter):
    """Advanced 4/4: kick on 1 and 3, snare on 2 and 4, hi-hat eighths."""
    beat = bt // 4
    eighth = beat // 2
    events = []
    # Hi-hat eighths
    for i in range(8):
        events.append((i * eighth, HI_HAT_CLOSED, VEL_HH, eighth - 5))
    # Kick on 1 and 3
    events.append((0, KICK, VEL_KICK, beat // 2))
    events.append((beat * 2, KICK, VEL_KICK - 10, beat // 2))
    # Snare/side stick on 2 and 4
    events.append((beat, SNARE, VEL_SNARE + 10, beat // 2))
    events.append((beat * 3, SNARE, VEL_SNARE + 10, beat // 2))
    return events


def drums_full_34(bt, meter):
    """Advanced 3/4: kick on 1, snare on 3, hi-hat on all."""
    beat = bt // 3
    events = []
    for b in range(3):
        events.append((b * beat, HI_HAT_CLOSED, VEL_HH, beat // 2))
    events.append((0, KICK, VEL_KICK, beat // 2))
    events.append((beat * 2, SNARE, VEL_SNARE, beat // 2))
    return events


# ── Level dispatch ──

def get_comp_func(level, meter):
    if level == "beginner":
        return comp_whole
    elif level == "intermediate":
        return comp_boom_chick_34 if meter == "3/4" else comp_boom_chick_44
    else:
        return comp_driving_34 if meter == "3/4" else comp_driving_44


def get_bass_func(level, meter):
    if level == "beginner":
        return bass_simple
    elif level == "intermediate":
        return bass_alternating_34 if meter == "3/4" else bass_alternating_44
    else:
        return bass_walking_34 if meter == "3/4" else bass_walking_44


def get_drum_func(level, meter):
    if level == "beginner":
        return drums_none
    elif level == "intermediate":
        return drums_brushes_34 if meter == "3/4" else drums_brushes_44
    else:
        return drums_full_34 if meter == "3/4" else drums_full_44


# ── Absolute event helpers ──

def events_to_track(events, channel, track_name, program=None):
    """Convert absolute-time events to a mido MidiTrack with delta times."""
    track = mido.MidiTrack()
    track.append(mido.MetaMessage("track_name", name=track_name, time=0))
    if program is not None:
        track.append(mido.Message("program_change", program=program,
                                  channel=channel, time=0))

    # Flatten note events into on/off pairs
    flat = []
    for (t, notes, dur, vel) in events:
        if isinstance(notes, list):
            for n in notes:
                flat.append(("on", t, n, vel))
                flat.append(("off", t + dur, n, 0))
        else:
            flat.append(("on", t, notes, vel))
            flat.append(("off", t + dur, notes, 0))

    flat.sort(key=lambda e: (e[1], 0 if e[0] == "off" else 1))

    prev_t = 0
    for kind, abs_t, note, vel in flat:
        delta = abs_t - prev_t
        if kind == "on":
            track.append(mido.Message("note_on", note=note, velocity=vel,
                                      channel=channel, time=delta))
        else:
            track.append(mido.Message("note_off", note=note, velocity=0,
                                      channel=channel, time=delta))
        prev_t = abs_t

    track.append(mido.MetaMessage("end_of_track", time=0))
    return track


def drum_events_to_track(events, track_name):
    """Convert drum events (tick, note, vel, dur) to a mido MidiTrack."""
    track = mido.MidiTrack()
    track.append(mido.MetaMessage("track_name", name=track_name, time=0))

    flat = []
    for (t, note, vel, dur) in events:
        flat.append(("on", t, note, vel))
        flat.append(("off", t + dur, note, 0))

    flat.sort(key=lambda e: (e[1], 0 if e[0] == "off" else 1))

    prev_t = 0
    for kind, abs_t, note, vel in flat:
        delta = abs_t - prev_t
        if kind == "on":
            track.append(mido.Message("note_on", note=note, velocity=vel,
                                      channel=9, time=delta))
        else:
            track.append(mido.Message("note_off", note=note, velocity=0,
                                      channel=9, time=delta))
        prev_t = abs_t

    track.append(mido.MetaMessage("end_of_track", time=0))
    return track


# ── Main generation ──

def generate_midi(bt, level, bpm, outpath):
    """Generate a MIDI backing track for one backing track at one level."""
    mid = mido.MidiFile(ticks_per_beat=TPB)
    key_pc = PC_MAP.get(bt["root"], 0)
    meter = bt["meter"]
    chords = bt["chords"]
    loop_bars = bt["loop_bars"]
    bt_len = bar_ticks(meter)
    total_bars = loop_bars * LOOPS
    total_ticks = total_bars * bt_len

    # Time signature
    if meter == "3/4":
        ts_num, ts_den = 3, 4
    else:
        ts_num, ts_den = 4, 4

    # ── Track 0: Tempo + metadata ──
    meta_track = mido.MidiTrack()
    mid.tracks.append(meta_track)
    meta_track.append(mido.MetaMessage("track_name",
                                        name=f"{bt['title']} ({level})",
                                        time=0))
    meta_track.append(mido.MetaMessage("set_tempo",
                                        tempo=mido.bpm2tempo(bpm), time=0))
    meta_track.append(mido.MetaMessage("time_signature",
                                        numerator=ts_num, denominator=ts_den,
                                        time=0))
    meta_track.append(mido.MetaMessage("end_of_track", time=total_ticks))

    # ── Build chord schedule ──
    chord_schedule = []
    for bar_idx in range(total_bars):
        loop_bar = bar_idx % loop_bars
        chord_idx = loop_bar % len(chords)
        chord_schedule.append(chords[chord_idx])

    # ── Track 1: Guitar comping ──
    comp_func = get_comp_func(level, meter)
    comp_events = []
    for bar_idx, sym in enumerate(chord_schedule):
        offset, quality = parse_chord(sym)
        cnotes = chord_notes(key_pc, offset, quality, octave=3)
        bar_start = bar_idx * bt_len
        pattern = comp_func(cnotes, bt_len)
        for (t, notes, dur, vel) in pattern:
            comp_events.append((bar_start + t, notes, dur, vel))

    mid.tracks.append(events_to_track(comp_events, 0, "Guitar",
                                       PROG_STEEL_GUITAR))

    # ── Track 2: Bass ──
    bass_func = get_bass_func(level, meter)
    bass_events = []
    for bar_idx, sym in enumerate(chord_schedule):
        offset, quality = parse_chord(sym)
        root = bass_root(key_pc, offset, octave=2)
        fifth = bass_fifth(key_pc, offset, octave=2)
        bar_start = bar_idx * bt_len
        pattern = bass_func(root, fifth, bt_len, meter)
        for (t, note, dur, vel) in pattern:
            bass_events.append((bar_start + t, note, dur, vel))

    mid.tracks.append(events_to_track(bass_events, 1, "Bass",
                                       PROG_ACOUSTIC_BASS))

    # ── Track 3: Drums ──
    drum_func = get_drum_func(level, meter)
    drum_events_all = []
    for bar_idx in range(total_bars):
        bar_start = bar_idx * bt_len
        pattern = drum_func(bt_len, meter)
        for (t, note, vel, dur) in pattern:
            drum_events_all.append((bar_start + t, note, vel, dur))

    if drum_events_all:
        mid.tracks.append(drum_events_to_track(drum_events_all, "Drums"))

    mid.save(outpath)


# ── Main ──

if __name__ == "__main__":
    midi_dir = os.path.join(ROOT, "exercises", "bluegrass", "midi")
    os.makedirs(midi_dir, exist_ok=True)

    levels = ["beginner", "intermediate", "advanced"]
    total = 0

    for bt in backing_tracks:
        tr = bt.get("tempo_range", [60, 130])
        mid_tempo = bt.get("tempo_bpm", 90)
        tempos = {
            "beginner": tr[0],
            "intermediate": mid_tempo,
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
