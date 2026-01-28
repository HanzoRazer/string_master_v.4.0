#!/usr/bin/env python3
"""
emit_flamenco_midi.py

Generates MIDI backing tracks from flamenco .ztprog metadata.
Reads backing track info from flamenco_canonical.json.

Output: exercises/flamenco/midi/{id}_{level}.mid

Each MIDI has three tracks:
  - Comping: shell voicings (channel 0, nylon guitar)
  - Bass: root/pedal/walking (channel 1, acoustic bass)
  - Percussion: palmas/cajon accents (channel 9)

Supports:
  - 12-beat compas (solea, bulerias) with authentic accent patterns
  - Binary 4/4 (tangos, tientos, rumba, zambra)
  - Ternary 3/4 (fandango)
  - Free/rubato (malaguena) at slow default tempo
"""
import json
import os
import sys

import mido
from mido import MidiFile, MidiTrack, Message, MetaMessage
from zone_tritone_tools import pc

# Fix Windows console encoding
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.abspath(__file__))

# ── Load canonical data ──
with open(os.path.join(ROOT, "flamenco_canonical.json"), encoding="utf-8") as f:
    canon = json.load(f)

BACKING_TRACKS = canon["backing_tracks"]

# ── Constants ──

TPB = 480  # ticks per beat (quarter note)
LOOPS = 4  # number of times to loop the progression

# MIDI program numbers
PROG_NYLON_GUITAR = 24   # Nylon string guitar
PROG_ACOUSTIC_BASS = 32  # Acoustic bass
PROG_FINGER_BASS = 33    # Finger electric bass

# MIDI percussion notes (channel 9)
PERC_BASS_DRUM = 36
PERC_SNARE = 38
PERC_HAND_CLAP = 39
PERC_CLOSED_HH = 42
PERC_OPEN_HH = 46
PERC_TAMBOURINE = 54
PERC_COWBELL = 56

# Palmas: use hand clap for main accents, closed hi-hat for soft taps
PALMAS_ACCENT = PERC_HAND_CLAP
PALMAS_GHOST = PERC_CLOSED_HH
CAJON_SLAP = PERC_SNARE
CAJON_BASS = PERC_BASS_DRUM

# ── Pitch / Chord Helpers ──

NOTE_PC = {
    "C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3,
    "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8, "Ab": 8,
    "A": 9, "A#": 10, "Bb": 10, "B": 11,
}

# Chord quality intervals (semitones from root)
QUALITY_INTERVALS = {
    "major": [0, 4, 7],
    "minor": [0, 3, 7],
    "dom7":  [0, 4, 7, 10],
    "min7":  [0, 3, 7, 10],
    "maj7":  [0, 4, 7, 11],
    "dim":   [0, 3, 6],
}

# Roman numeral -> (semitone_offset, quality)
# Phrygian mode (natural)
PHRYGIAN_RN = {
    "i":    (0, "minor"),
    "bII":  (1, "major"),
    "bIII": (3, "major"),
    "iv":   (5, "minor"),
    "v":    (7, "minor"),
    "bVI":  (8, "major"),
    "bVII": (10, "major"),
}

# Phrygian Dominant mode
PHRYGIAN_DOM_RN = {
    "I":    (0, "major"),
    "bII":  (1, "major"),
    "iv":   (5, "minor"),
    "v":    (7, "minor"),
    "bVI":  (8, "major"),
    "bVII": (10, "major"),
}


def midi_note(pitch_class, octave):
    """MIDI note number from pitch class and octave."""
    return 12 * (octave + 1) + (pitch_class % 12)


def parse_chord_symbol(sym):
    """Parse a concrete chord symbol to (pitch_class, quality).
    Examples: 'E' -> (4, 'major'), 'Am' -> (9, 'minor'), 'Eb' -> (3, 'major')
    """
    sym = sym.strip()
    if len(sym) > 1 and sym[1] in ('#', 'b'):
        root_str = sym[:2]
        suffix = sym[2:]
    else:
        root_str = sym[0]
        suffix = sym[1:]

    root_pc = NOTE_PC.get(root_str)
    if root_pc is None:
        return 0, "major"

    if suffix in ("m", "min"):
        return root_pc, "minor"
    elif suffix == "7":
        return root_pc, "dom7"
    elif suffix in ("m7", "min7"):
        return root_pc, "min7"
    elif suffix in ("M7", "maj7"):
        return root_pc, "maj7"
    elif suffix == "dim":
        return root_pc, "dim"
    else:
        return root_pc, "major"


def resolve_chord(sym, root_pc, mode):
    """Resolve a chord symbol (Roman numeral or concrete) to (pitch_class, quality)."""
    sym = sym.strip()

    # Try Roman numeral lookup
    if mode in ("phrygian_dominant", "phrygian_dominant_mixed", "phrygian_mixed"):
        if sym in PHRYGIAN_DOM_RN:
            offset, quality = PHRYGIAN_DOM_RN[sym]
            return (root_pc + offset) % 12, quality
    if sym in PHRYGIAN_RN:
        offset, quality = PHRYGIAN_RN[sym]
        return (root_pc + offset) % 12, quality

    # Fall back to concrete chord parsing
    return parse_chord_symbol(sym)


def shell_voicing(chord_pc, quality, octave=3):
    """Return MIDI notes for a shell voicing (root + 3rd/4th + 7th or 5th)."""
    intervals = QUALITY_INTERVALS.get(quality, [0, 4, 7])
    return [midi_note((chord_pc + iv) % 12, octave) for iv in intervals]


def bass_note_for(chord_pc, octave=2):
    """Bass note: root in low octave."""
    return midi_note(chord_pc, octave)


def fifth_of(chord_pc, octave=2):
    """Perfect fifth above root in bass octave."""
    return midi_note((chord_pc + 7) % 12, octave)


# ── MIDI Writing Helpers ──

def write_chord_on(track, notes, velocity, time=0, channel=0):
    for i, n in enumerate(notes):
        track.append(Message('note_on', note=n, velocity=velocity,
                             time=time if i == 0 else 0, channel=channel))


def write_chord_off(track, notes, duration, channel=0):
    for i, n in enumerate(notes):
        track.append(Message('note_off', note=n, velocity=0,
                             time=duration if i == 0 else 0, channel=channel))


def write_note(track, note, velocity, duration, time=0, channel=1):
    track.append(Message('note_on', note=note, velocity=velocity,
                         time=time, channel=channel))
    track.append(Message('note_off', note=note, velocity=0,
                         time=duration, channel=channel))


def write_perc(track, note, velocity, time=0):
    """Write a percussion hit on channel 9."""
    track.append(Message('note_on', note=note, velocity=velocity,
                         time=time, channel=9))
    track.append(Message('note_off', note=note, velocity=0,
                         time=TPB // 4, channel=9))  # short duration


# ── Chord Progression Parser ──

def parse_chord_function(chord_func_str, root_pc, mode):
    """Parse chord_function string from canonical JSON.

    Formats:
        'i (tonic pedal)' -> [root as minor]
        'I-I-bII-bII-iv-iv-I-I' -> list of resolved chords
        'E-E-F-E' -> list of concrete chords
        'iv-iv-bIII-bIII-bII-bII-i-i' -> list of resolved chords
    """
    # Strip parenthetical notes
    cf = chord_func_str.split("(")[0].strip()

    # Check for pedal/rubato patterns
    if cf in ("i", "I"):
        return [(root_pc, "minor" if cf == "i" else "major")]

    # Split on hyphens
    symbols = [s.strip() for s in cf.split("-")]
    chords = []
    for sym in symbols:
        if sym:
            cpc, cq = resolve_chord(sym, root_pc, mode)
            chords.append((cpc, cq))
    return chords


# ── 12-Beat Compas Generator (Solea / Bulerias) ──

def generate_12beat_compas(bt, bpm, level, outpath):
    """Generate MIDI for 12-beat compas (solea/bulerias).

    12-beat compas = 12 pulses (eighth notes).
    In MIDI: use 6/8 time (2 bars per compas) with 4 compas per loop.
    """
    palo = bt["palo"]
    root_pc = NOTE_PC.get(bt["root"], 4)
    mode = bt["mode"]
    chords = parse_chord_function(bt["chord_function"], root_pc, mode)

    # One compas = 12 eighth notes = 6 quarter notes worth
    EIGHTH = TPB // 2
    COMPAS = 12 * EIGHTH  # 6 * TPB ticks

    # Accent patterns (1-indexed beat positions)
    if palo == "solea":
        accents = {3, 6, 8, 10, 12}
        strong = {6, 10, 12}
    else:  # bulerias
        accents = {12, 3, 6, 8, 10}
        strong = {12, 3, 6}

    mid = MidiFile(ticks_per_beat=TPB)

    # Track 0: meta
    meta_track = MidiTrack()
    mid.tracks.append(meta_track)
    # For 12/8, tempo_bpm refers to dotted quarter beats
    # MIDI tempo is in microseconds per quarter note
    # dotted_quarter_bpm * 1.5 = quarter_bpm
    midi_bpm = bpm * 1.5
    meta_track.append(MetaMessage('set_tempo', tempo=mido.bpm2tempo(midi_bpm), time=0))
    meta_track.append(MetaMessage('time_signature', numerator=6, denominator=8,
                                  clocks_per_click=36, notated_32nd_notes_per_beat=8, time=0))
    meta_track.append(MetaMessage('track_name',
                                  name=f'{palo.title()} Backing ({level})', time=0))

    # Track 1: Comping
    comp_track = MidiTrack()
    mid.tracks.append(comp_track)
    comp_track.append(MetaMessage('track_name', name='Comping', time=0))
    comp_track.append(Message('program_change', program=PROG_NYLON_GUITAR,
                              time=0, channel=0))

    # Track 2: Bass
    bass_track = MidiTrack()
    mid.tracks.append(bass_track)
    bass_track.append(MetaMessage('track_name', name='Bass', time=0))
    bass_track.append(Message('program_change', program=PROG_ACOUSTIC_BASS,
                              time=0, channel=1))

    # Track 3: Percussion (palmas)
    perc_track = MidiTrack()
    mid.tracks.append(perc_track)
    perc_track.append(MetaMessage('track_name', name='Palmas', time=0))

    # If single chord (pedal), repeat for all 12 beats
    if len(chords) == 1:
        chord_seq = chords * 12
    else:
        # Distribute chords across 12 beats
        chord_seq = chords
        while len(chord_seq) < 12:
            chord_seq = chord_seq + chords
        chord_seq = chord_seq[:12]

    for loop in range(LOOPS):
        # --- Comping ---
        if level == "beginner":
            # Sustained chord for whole compas
            voicing = shell_voicing(chord_seq[0][0], chord_seq[0][1])
            write_chord_on(comp_track, voicing, velocity=68)
            write_chord_off(comp_track, voicing, COMPAS)
        elif level == "intermediate":
            # Hit on accent beats
            elapsed = 0
            for beat_idx in range(12):
                beat_num = beat_idx + 1  # 1-indexed
                cpc, cq = chord_seq[beat_idx % len(chord_seq)]
                voicing = shell_voicing(cpc, cq)

                if beat_num in accents:
                    vel = 80 if beat_num in strong else 68
                    write_chord_on(comp_track, voicing, velocity=vel,
                                   time=0 if beat_idx == 0 else 0)
                    write_chord_off(comp_track, voicing, EIGHTH)
                else:
                    # Rest
                    comp_track.append(Message('note_on', note=0, velocity=0,
                                             time=EIGHTH, channel=0))
                    comp_track.append(Message('note_off', note=0, velocity=0,
                                             time=0, channel=0))
            # Fix: for intermediate, we need proper delta timing
            # Let me redo this more carefully
        else:  # advanced
            pass  # handled below

        # For intermediate and advanced, use a cleaner approach
        if level in ("intermediate", "advanced"):
            # Reset - clear what we wrote above
            if level == "intermediate":
                comp_track.clear()
                comp_track.append(MetaMessage('track_name', name='Comping', time=0))
                comp_track.append(Message('program_change', program=PROG_NYLON_GUITAR,
                                          time=0, channel=0))

            # Rebuild comping for all loops at once
            if level == "intermediate":
                for l2 in range(LOOPS):
                    for beat_idx in range(12):
                        beat_num = beat_idx + 1
                        cpc, cq = chord_seq[beat_idx % len(chord_seq)]
                        voicing = shell_voicing(cpc, cq)

                        if beat_num in accents:
                            vel = 80 if beat_num in strong else 68
                            write_chord_on(comp_track, voicing, velocity=vel, time=0)
                            write_chord_off(comp_track, voicing, EIGHTH)
                        else:
                            # Silent eighth note rest
                            comp_track.append(Message('note_on', note=60, velocity=0,
                                                       time=EIGHTH, channel=0))
                            comp_track.append(Message('note_off', note=60, velocity=0,
                                                       time=0, channel=0))
                break  # exit the loop since we handled all loops above

            elif level == "advanced":
                comp_track.clear()
                comp_track.append(MetaMessage('track_name', name='Comping', time=0))
                comp_track.append(Message('program_change', program=PROG_NYLON_GUITAR,
                                          time=0, channel=0))

                for l2 in range(LOOPS):
                    for beat_idx in range(12):
                        beat_num = beat_idx + 1
                        cpc, cq = chord_seq[beat_idx % len(chord_seq)]
                        voicing = shell_voicing(cpc, cq)

                        if beat_num in strong:
                            write_chord_on(comp_track, voicing, velocity=84, time=0)
                            write_chord_off(comp_track, voicing, EIGHTH)
                        elif beat_num in accents:
                            # Shorter, syncopated
                            write_chord_on(comp_track, voicing, velocity=72, time=0)
                            write_chord_off(comp_track, voicing, EIGHTH // 2)
                            # Fill remaining with rest
                            comp_track.append(Message('note_on', note=60, velocity=0,
                                                       time=EIGHTH // 2, channel=0))
                            comp_track.append(Message('note_off', note=60, velocity=0,
                                                       time=0, channel=0))
                        else:
                            comp_track.append(Message('note_on', note=60, velocity=0,
                                                       time=EIGHTH, channel=0))
                            comp_track.append(Message('note_off', note=60, velocity=0,
                                                       time=0, channel=0))
                break

    # --- Bass: pedal tone ---
    b_root = bass_note_for(root_pc)
    b_fifth = fifth_of(root_pc)

    for loop in range(LOOPS):
        if level == "beginner":
            # Whole compas pedal
            write_note(bass_track, b_root, 76, COMPAS, channel=1)
        elif level == "intermediate":
            # Half-compas root, half-compas fifth
            write_note(bass_track, b_root, 76, 6 * EIGHTH, channel=1)
            write_note(bass_track, b_fifth, 68, 6 * EIGHTH, channel=1)
        else:
            # Walking: root on strong accents, fifth and approach on others
            for beat_idx in range(12):
                beat_num = beat_idx + 1
                if beat_num in strong:
                    write_note(bass_track, b_root, 80, EIGHTH, channel=1)
                elif beat_num in accents:
                    write_note(bass_track, b_fifth, 72, EIGHTH, channel=1)
                else:
                    # Chromatic approach
                    approach = midi_note((root_pc - 1) % 12, 2)
                    write_note(bass_track, approach, 60, EIGHTH, channel=1)

    # --- Percussion: palmas ---
    for loop in range(LOOPS):
        for beat_idx in range(12):
            beat_num = beat_idx + 1
            if beat_num in strong:
                write_perc(perc_track, PALMAS_ACCENT, velocity=100)
                # Pad rest to fill eighth note
                perc_track.append(Message('note_on', note=0, velocity=0,
                                          time=EIGHTH - TPB // 4, channel=9))
                perc_track.append(Message('note_off', note=0, velocity=0,
                                          time=0, channel=9))
            elif beat_num in accents:
                write_perc(perc_track, PALMAS_ACCENT, velocity=76)
                perc_track.append(Message('note_on', note=0, velocity=0,
                                          time=EIGHTH - TPB // 4, channel=9))
                perc_track.append(Message('note_off', note=0, velocity=0,
                                          time=0, channel=9))
            elif level != "beginner":
                # Ghost tap
                write_perc(perc_track, PALMAS_GHOST, velocity=40)
                perc_track.append(Message('note_on', note=0, velocity=0,
                                          time=EIGHTH - TPB // 4, channel=9))
                perc_track.append(Message('note_off', note=0, velocity=0,
                                          time=0, channel=9))
            else:
                # Rest
                perc_track.append(Message('note_on', note=0, velocity=0,
                                          time=EIGHTH, channel=9))
                perc_track.append(Message('note_off', note=0, velocity=0,
                                          time=0, channel=9))

    # End of track
    for track in mid.tracks:
        track.append(MetaMessage('end_of_track', time=0))

    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    mid.save(outpath)
    return outpath


# ── Binary 4/4 Generator (Tangos, Tientos, Rumba, Zambra) ──

def generate_binary_4_4(bt, bpm, level, outpath):
    """Generate MIDI for 4/4 time backing tracks."""
    palo = bt["palo"]
    root_pc = NOTE_PC.get(bt["root"], 4)
    mode = bt["mode"]
    chords = parse_chord_function(bt["chord_function"], root_pc, mode)
    loop_bars = bt["loop_bars"]

    BEAT = TPB
    BAR = 4 * BEAT
    HALF = BEAT // 2

    # If single chord (pedal), repeat for all bars
    if len(chords) == 1:
        chord_seq = chords * loop_bars
    else:
        chord_seq = chords
        while len(chord_seq) < loop_bars:
            chord_seq = chord_seq + chords
        chord_seq = chord_seq[:loop_bars]

    mid = MidiFile(ticks_per_beat=TPB)

    # Track 0: meta
    meta_track = MidiTrack()
    mid.tracks.append(meta_track)
    meta_track.append(MetaMessage('set_tempo', tempo=mido.bpm2tempo(bpm), time=0))
    meta_track.append(MetaMessage('time_signature', numerator=4, denominator=4, time=0))
    meta_track.append(MetaMessage('track_name',
                                  name=f'{palo.title()} Backing ({level})', time=0))

    # Track 1: Comping
    comp_track = MidiTrack()
    mid.tracks.append(comp_track)
    comp_track.append(MetaMessage('track_name', name='Comping', time=0))
    comp_track.append(Message('program_change', program=PROG_NYLON_GUITAR,
                              time=0, channel=0))

    # Track 2: Bass
    bass_track = MidiTrack()
    mid.tracks.append(bass_track)
    bass_track.append(MetaMessage('track_name', name='Bass', time=0))
    bass_track.append(Message('program_change', program=PROG_ACOUSTIC_BASS,
                              time=0, channel=1))

    # Track 3: Percussion
    perc_track = MidiTrack()
    mid.tracks.append(perc_track)
    perc_track.append(MetaMessage('track_name', name='Percussion', time=0))

    # Determine percussion style
    has_cajon = any("cajon" in i for i in bt.get("instruments", [])
                    if isinstance(i, str))
    if not has_cajon:
        has_cajon = any(i.get("type") if isinstance(i, dict) else ""
                        == "cajon" for i in bt.get("instruments", []))

    for loop in range(LOOPS):
        for bar_idx in range(loop_bars):
            cpc, cq = chord_seq[bar_idx]
            voicing = shell_voicing(cpc, cq)
            b_root = bass_note_for(cpc)
            b_fifth = fifth_of(cpc)

            # --- Comping ---
            if level == "beginner":
                # Whole note chord
                write_chord_on(comp_track, voicing, velocity=68)
                write_chord_off(comp_track, voicing, BAR)
            elif level == "intermediate":
                # Half notes: beats 1 and 3
                write_chord_on(comp_track, voicing, velocity=76)
                write_chord_off(comp_track, voicing, 2 * BEAT)
                write_chord_on(comp_track, voicing, velocity=68)
                write_chord_off(comp_track, voicing, 2 * BEAT)
            else:
                # Syncopated: 1, 2-and, 4
                write_chord_on(comp_track, voicing, velocity=80)
                write_chord_off(comp_track, voicing, BEAT)
                # Beat 2: rest for half, then hit on 2-and
                write_chord_on(comp_track, voicing, velocity=64, time=HALF)
                write_chord_off(comp_track, voicing, HALF)
                # Beat 3: rest
                write_chord_on(comp_track, voicing, velocity=72, time=BEAT)
                write_chord_off(comp_track, voicing, BEAT)

            # --- Bass ---
            if level == "beginner":
                # Half notes: root, fifth
                write_note(bass_track, b_root, 76, 2 * BEAT, channel=1)
                write_note(bass_track, b_fifth, 68, 2 * BEAT, channel=1)
            elif level == "intermediate":
                # Quarter note walk: root, 3rd, 5th, approach
                third_offset = 3 if cq in ("minor", "min7") else 4
                b_third = midi_note((cpc + third_offset) % 12, 2)
                # Approach to next bar's root
                next_idx = (bar_idx + 1) % loop_bars
                next_cpc = chord_seq[next_idx][0]
                approach = midi_note((next_cpc - 1) % 12, 2)
                write_note(bass_track, b_root, 80, BEAT, channel=1)
                write_note(bass_track, b_third, 72, BEAT, channel=1)
                write_note(bass_track, b_fifth, 76, BEAT, channel=1)
                write_note(bass_track, approach, 68, BEAT, channel=1)
            else:
                # Walking with chromatic approach and passing tones
                third_offset = 3 if cq in ("minor", "min7") else 4
                b_third = midi_note((cpc + third_offset) % 12, 2)
                next_idx = (bar_idx + 1) % loop_bars
                next_cpc = chord_seq[next_idx][0]
                approach = midi_note((next_cpc - 1) % 12, 2)
                # Chromatic passing tone between 5th and approach
                passing = midi_note((cpc + 6) % 12, 2)
                write_note(bass_track, b_root, 80, BEAT, channel=1)
                write_note(bass_track, b_third, 72, BEAT, channel=1)
                write_note(bass_track, b_fifth, 76, BEAT, channel=1)
                write_note(bass_track, approach, 68, BEAT, channel=1)

            # --- Percussion ---
            if palo == "rumba":
                # Cajon pattern: slap 1,3, bass 2,4
                if level == "beginner":
                    write_perc(perc_track, CAJON_SLAP, 80)
                    perc_track.append(Message('note_on', note=0, velocity=0,
                                              time=BEAT - TPB // 4, channel=9))
                    perc_track.append(Message('note_off', note=0, velocity=0, time=0, channel=9))
                    write_perc(perc_track, CAJON_BASS, 72)
                    perc_track.append(Message('note_on', note=0, velocity=0,
                                              time=BEAT - TPB // 4, channel=9))
                    perc_track.append(Message('note_off', note=0, velocity=0, time=0, channel=9))
                    write_perc(perc_track, CAJON_SLAP, 76)
                    perc_track.append(Message('note_on', note=0, velocity=0,
                                              time=BEAT - TPB // 4, channel=9))
                    perc_track.append(Message('note_off', note=0, velocity=0, time=0, channel=9))
                    write_perc(perc_track, CAJON_BASS, 68)
                    perc_track.append(Message('note_on', note=0, velocity=0,
                                              time=BEAT - TPB // 4, channel=9))
                    perc_track.append(Message('note_off', note=0, velocity=0, time=0, channel=9))
                else:
                    # With ghost notes on the "e" of each beat
                    for beat in range(4):
                        if beat % 2 == 0:
                            write_perc(perc_track, CAJON_SLAP, 80)
                        else:
                            write_perc(perc_track, CAJON_BASS, 72)
                        # Ghost on the "e" (eighth note after)
                        gap = HALF - TPB // 4
                        perc_track.append(Message('note_on', note=0, velocity=0,
                                                  time=gap, channel=9))
                        perc_track.append(Message('note_off', note=0, velocity=0, time=0, channel=9))
                        if level == "advanced":
                            write_perc(perc_track, PALMAS_GHOST, 36)
                            perc_track.append(Message('note_on', note=0, velocity=0,
                                                      time=HALF - TPB // 4, channel=9))
                            perc_track.append(Message('note_off', note=0, velocity=0, time=0, channel=9))
                        else:
                            perc_track.append(Message('note_on', note=0, velocity=0,
                                                      time=HALF, channel=9))
                            perc_track.append(Message('note_off', note=0, velocity=0, time=0, channel=9))
            else:
                # Palmas pattern: accents on 1 and 3
                for beat in range(4):
                    if beat in (0, 2):
                        vel = 84 if beat == 0 else 72
                        write_perc(perc_track, PALMAS_ACCENT, vel)
                        perc_track.append(Message('note_on', note=0, velocity=0,
                                                  time=BEAT - TPB // 4, channel=9))
                        perc_track.append(Message('note_off', note=0, velocity=0, time=0, channel=9))
                    elif level != "beginner":
                        write_perc(perc_track, PALMAS_GHOST, 40)
                        perc_track.append(Message('note_on', note=0, velocity=0,
                                                  time=BEAT - TPB // 4, channel=9))
                        perc_track.append(Message('note_off', note=0, velocity=0, time=0, channel=9))
                    else:
                        perc_track.append(Message('note_on', note=0, velocity=0,
                                                  time=BEAT, channel=9))
                        perc_track.append(Message('note_off', note=0, velocity=0, time=0, channel=9))

    # End of track
    for track in mid.tracks:
        track.append(MetaMessage('end_of_track', time=0))

    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    mid.save(outpath)
    return outpath


# ── Ternary 3/4 Generator (Fandango) ──

def generate_ternary_3_4(bt, bpm, level, outpath):
    """Generate MIDI for 3/4 time (fandango)."""
    palo = bt["palo"]
    root_pc = NOTE_PC.get(bt["root"], 4)
    mode = bt["mode"]
    chords = parse_chord_function(bt["chord_function"], root_pc, mode)
    loop_bars = bt["loop_bars"]

    BEAT = TPB
    BAR = 3 * BEAT

    if len(chords) == 1:
        chord_seq = chords * loop_bars
    else:
        chord_seq = chords
        while len(chord_seq) < loop_bars:
            chord_seq = chord_seq + chords
        chord_seq = chord_seq[:loop_bars]

    mid = MidiFile(ticks_per_beat=TPB)

    # Track 0: meta
    meta_track = MidiTrack()
    mid.tracks.append(meta_track)
    meta_track.append(MetaMessage('set_tempo', tempo=mido.bpm2tempo(bpm), time=0))
    meta_track.append(MetaMessage('time_signature', numerator=3, denominator=4, time=0))
    meta_track.append(MetaMessage('track_name',
                                  name=f'Fandango Backing ({level})', time=0))

    # Track 1: Comping
    comp_track = MidiTrack()
    mid.tracks.append(comp_track)
    comp_track.append(MetaMessage('track_name', name='Comping', time=0))
    comp_track.append(Message('program_change', program=PROG_NYLON_GUITAR,
                              time=0, channel=0))

    # Track 2: Bass
    bass_track = MidiTrack()
    mid.tracks.append(bass_track)
    bass_track.append(MetaMessage('track_name', name='Bass', time=0))
    bass_track.append(Message('program_change', program=PROG_ACOUSTIC_BASS,
                              time=0, channel=1))

    # Track 3: Percussion
    perc_track = MidiTrack()
    mid.tracks.append(perc_track)
    perc_track.append(MetaMessage('track_name', name='Palmas', time=0))

    for loop in range(LOOPS):
        for bar_idx in range(loop_bars):
            cpc, cq = chord_seq[bar_idx]
            voicing = shell_voicing(cpc, cq)
            b_root = bass_note_for(cpc)

            # --- Comping: waltz pattern ---
            if level == "beginner":
                # Dotted half note (whole bar)
                write_chord_on(comp_track, voicing, velocity=68)
                write_chord_off(comp_track, voicing, BAR)
            elif level == "intermediate":
                # Beat 1 accent, beats 2-3 lighter
                write_chord_on(comp_track, voicing, velocity=80)
                write_chord_off(comp_track, voicing, BEAT)
                write_chord_on(comp_track, voicing, velocity=56)
                write_chord_off(comp_track, voicing, BEAT)
                write_chord_on(comp_track, voicing, velocity=56)
                write_chord_off(comp_track, voicing, BEAT)
            else:
                # Ornamental: beat 1 accent, beat 2 ghost, beat 3 accent
                write_chord_on(comp_track, voicing, velocity=84)
                write_chord_off(comp_track, voicing, BEAT)
                write_chord_on(comp_track, voicing, velocity=48)
                write_chord_off(comp_track, voicing, BEAT)
                write_chord_on(comp_track, voicing, velocity=72)
                write_chord_off(comp_track, voicing, BEAT)

            # --- Bass: waltz root ---
            if level == "beginner":
                write_note(bass_track, b_root, 76, BAR, channel=1)
            else:
                b_fifth = fifth_of(cpc)
                write_note(bass_track, b_root, 80, BEAT, channel=1)
                write_note(bass_track, b_fifth, 64, BEAT, channel=1)
                write_note(bass_track, b_fifth, 64, BEAT, channel=1)

            # --- Palmas: accent on beat 1 ---
            write_perc(perc_track, PALMAS_ACCENT, 84)
            rest = BEAT - TPB // 4
            perc_track.append(Message('note_on', note=0, velocity=0,
                                      time=rest, channel=9))
            perc_track.append(Message('note_off', note=0, velocity=0, time=0, channel=9))

            if level != "beginner":
                write_perc(perc_track, PALMAS_GHOST, 36)
                perc_track.append(Message('note_on', note=0, velocity=0,
                                          time=BEAT - TPB // 4, channel=9))
                perc_track.append(Message('note_off', note=0, velocity=0, time=0, channel=9))
                write_perc(perc_track, PALMAS_GHOST, 36)
                perc_track.append(Message('note_on', note=0, velocity=0,
                                          time=BEAT - TPB // 4, channel=9))
                perc_track.append(Message('note_off', note=0, velocity=0, time=0, channel=9))
            else:
                perc_track.append(Message('note_on', note=0, velocity=0,
                                          time=2 * BEAT, channel=9))
                perc_track.append(Message('note_off', note=0, velocity=0, time=0, channel=9))

    for track in mid.tracks:
        track.append(MetaMessage('end_of_track', time=0))

    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    mid.save(outpath)
    return outpath


# ── Dispatcher ──

def get_level_tempos(bt):
    """Return {beginner, intermediate, advanced} tempos for a backing track."""
    tr = bt.get("tempo_range", [60, 120])
    mid_bpm = bt.get("tempo_bpm")

    # Handle rubato (tempo_range starts at 0)
    if tr[0] == 0:
        tr = [max(40, tr[1] // 3), tr[1]]

    if mid_bpm is None or mid_bpm == 0:
        mid_bpm = tr[0] + (tr[1] - tr[0]) // 2

    return {
        "beginner": tr[0],
        "intermediate": mid_bpm,
        "advanced": tr[1],
    }


def generate_midi(bt, level, bpm, outpath):
    """Dispatch to the appropriate generator based on time signature."""
    ts = bt.get("time_signature", "4/4")

    if ts == "12/8":
        return generate_12beat_compas(bt, bpm, level, outpath)
    elif ts == "3/4":
        return generate_ternary_3_4(bt, bpm, level, outpath)
    else:
        # 4/4, free, or default
        return generate_binary_4_4(bt, bpm, level, outpath)


# ── Main ──

if __name__ == "__main__":
    midi_dir = os.path.join(ROOT, "exercises", "flamenco", "midi")
    os.makedirs(midi_dir, exist_ok=True)

    total = 0
    for bt in BACKING_TRACKS:
        bt_id = bt["id"]
        tempos = get_level_tempos(bt)

        for level in ("beginner", "intermediate", "advanced"):
            bpm = tempos[level]
            outpath = os.path.join(midi_dir, f"{bt_id}_{level}.mid")
            generate_midi(bt, level, bpm, outpath)
            total += 1

        print(f"  {bt_id}: 3 levels")

    print(f"\nTotal MIDI files: {total}")
    print(f"Output: {midi_dir}/")
