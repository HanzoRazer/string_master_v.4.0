#!/usr/bin/env python3
"""
emit_motive_midi.py

Reads .ztprog files from programs/blues_motives/ and generates .mid backing
tracks for each key at each difficulty level (beginner, intermediate, advanced).

Output: programs/blues_motives/midi/{key}_{level}.mid

Each MIDI has two tracks:
  - Bass: walking bass line (root-5th-root-5th per bar)
  - Comping: chord voicings with rhythm appropriate to level
"""
import os, re
import mido
from mido import MidiFile, MidiTrack, Message, MetaMessage
from zone_tritone_tools import pc, name_from_pc

# ── Parse .ztprog files ──

def parse_ztprog(path):
    """Parse a .ztprog YAML file into a dict (simple key:value parser)."""
    data = {}
    current_section = None
    current_subsection = None

    with open(path, encoding="utf-8") as f:
        for line in f:
            stripped = line.rstrip()
            if not stripped:
                continue

            # Top-level key: value
            m = re.match(r'^(\w[\w_]*)\s*:\s*(.+)$', stripped)
            if m and not stripped.startswith(' '):
                key, val = m.group(1), m.group(2).strip()
                # Strip quotes
                if val.startswith(("'", '"')) and val.endswith(("'", '"')):
                    val = val[1:-1]
                data[key] = val
                current_section = key
                current_subsection = None
                continue

            # Section header (no value)
            m = re.match(r'^(\w[\w_]*):\s*$', stripped)
            if m and not stripped.startswith(' '):
                current_section = m.group(1)
                data[current_section] = {}
                current_subsection = None
                continue

            # Subsection (2-space indent)
            m = re.match(r'^  (\w[\w_]*):\s*$', stripped)
            if m and current_section:
                current_subsection = m.group(1)
                if isinstance(data[current_section], dict):
                    data[current_section][current_subsection] = {}
                continue

            # Sub-key: value (4-space indent)
            m = re.match(r'^    (\w[\w_]*)\s*:\s*(.+)$', stripped)
            if m and current_section and current_subsection:
                key, val = m.group(1), m.group(2).strip()
                if isinstance(data.get(current_section), dict):
                    if current_subsection not in data[current_section]:
                        data[current_section][current_subsection] = {}
                    data[current_section][current_subsection][key] = val
                continue

            # List item (- value)
            m = re.match(r'^- (.+)$', stripped)
            if m and current_section:
                val = m.group(1).strip()
                if not isinstance(data.get(current_section), list):
                    data[current_section] = []
                data[current_section].append(val)

    return data


def parse_chord(chord_str):
    """Parse chord symbol to (root_pc, quality).
    Quality: 'dom7', 'min7', 'maj7', 'dim7', etc."""
    chord_str = chord_str.strip()
    # Extract root
    if len(chord_str) > 1 and chord_str[1] in ('#', 'b'):
        root_str = chord_str[:2]
        suffix = chord_str[2:]
    else:
        root_str = chord_str[0]
        suffix = chord_str[1:]

    root_pc = pc(root_str)

    if suffix in ('m7', 'min7'):
        quality = 'min7'
    elif suffix in ('maj7', 'M7'):
        quality = 'maj7'
    elif suffix in ('dim7', 'o7'):
        quality = 'dim7'
    elif suffix in ('7',):
        quality = 'dom7'
    elif suffix in ('m',):
        quality = 'min'
    else:
        quality = 'dom7'  # default for blues

    return root_pc, quality


# ── MIDI voicing helpers ──

def midi_note(pitch_class, octave):
    return 12 * (octave + 1) + (pitch_class % 12)


def bass_note(root_pc):
    """Bass note: root in octave 2."""
    return midi_note(root_pc, 2)


def fifth_note(root_pc):
    """Bass 5th: perfect fifth above root in octave 2."""
    return midi_note((root_pc + 7) % 12, 2)


def chord_voicing(root_pc, quality):
    """Return a list of MIDI notes for a chord voicing in octave 3-4."""
    r = root_pc
    if quality == 'dom7':
        return [midi_note(r, 3), midi_note((r+4)%12, 3),
                midi_note((r+7)%12, 3), midi_note((r+10)%12, 4)]
    elif quality == 'min7':
        return [midi_note(r, 3), midi_note((r+3)%12, 3),
                midi_note((r+7)%12, 3), midi_note((r+10)%12, 4)]
    elif quality == 'maj7':
        return [midi_note(r, 3), midi_note((r+4)%12, 3),
                midi_note((r+7)%12, 3), midi_note((r+11)%12, 4)]
    elif quality == 'dim7':
        return [midi_note(r, 3), midi_note((r+3)%12, 3),
                midi_note((r+6)%12, 3), midi_note((r+9)%12, 4)]
    else:
        # Fallback: power chord
        return [midi_note(r, 3), midi_note((r+7)%12, 3)]


# ── MIDI generation ──

def write_chord_on(track, notes, velocity, time=0):
    """Write note_on messages for a chord."""
    for i, n in enumerate(notes):
        track.append(Message('note_on', note=n, velocity=velocity,
                             time=time if i == 0 else 0, channel=0))


def write_chord_off(track, notes, duration):
    """Write note_off messages for a chord."""
    for i, n in enumerate(notes):
        track.append(Message('note_off', note=n, velocity=0,
                             time=duration if i == 0 else 0, channel=0))


def write_note(track, note, velocity, duration, time=0, channel=1):
    """Write a single note on/off pair."""
    track.append(Message('note_on', note=note, velocity=velocity,
                         time=time, channel=channel))
    track.append(Message('note_off', note=note, velocity=0,
                         time=duration, channel=channel))


def generate_blues_midi(chords_str, bpm, level, outpath, tpb=480, loops=4):
    """Generate a 12-bar blues MIDI file.

    Args:
        chords_str: space-separated chord symbols (12 chords for 12 bars)
        bpm: tempo in BPM
        level: 'beginner', 'intermediate', 'advanced'
        outpath: output .mid file path
        tpb: ticks per beat
        loops: number of times to repeat the 12-bar form
    """
    chords = chords_str.split()
    BAR = tpb * 4       # 4 beats per bar
    BEAT = tpb           # 1 beat
    HALF = tpb // 2      # half beat (8th note)

    mid = MidiFile(ticks_per_beat=tpb)

    # ── Track 0: Tempo + meta ──
    meta_track = MidiTrack()
    mid.tracks.append(meta_track)
    meta_track.append(MetaMessage('set_tempo', tempo=mido.bpm2tempo(bpm), time=0))
    meta_track.append(MetaMessage('time_signature', numerator=4, denominator=4, time=0))
    meta_track.append(MetaMessage('track_name', name='Blues Backing', time=0))

    # ── Track 1: Comping (piano, channel 0) ──
    comp_track = MidiTrack()
    mid.tracks.append(comp_track)
    comp_track.append(MetaMessage('track_name', name='Comping', time=0))
    comp_track.append(Message('program_change', program=0, time=0, channel=0))  # Acoustic piano

    # ── Track 2: Bass (channel 1) ──
    bass_track = MidiTrack()
    mid.tracks.append(bass_track)
    bass_track.append(MetaMessage('track_name', name='Bass', time=0))
    bass_track.append(Message('program_change', program=32, time=0, channel=1))  # Acoustic bass

    for loop_num in range(loops):
        for bar_idx, chord_sym in enumerate(chords):
            root_pc, quality = parse_chord(chord_sym)
            voicing = chord_voicing(root_pc, quality)
            b_root = bass_note(root_pc)
            b_fifth = fifth_note(root_pc)

            # ── Comping patterns by level ──
            if level == 'beginner':
                # Whole note chords
                write_chord_on(comp_track, voicing, velocity=72, time=0)
                write_chord_off(comp_track, voicing, BAR)

            elif level == 'intermediate':
                # Half-note rhythm: hit on 1 and 3
                write_chord_on(comp_track, voicing, velocity=76, time=0)
                write_chord_off(comp_track, voicing, 2 * BEAT)
                write_chord_on(comp_track, voicing, velocity=68, time=0)
                write_chord_off(comp_track, voicing, 2 * BEAT)

            else:  # advanced
                # Syncopated: hits on 1, 2-and, 4
                write_chord_on(comp_track, voicing, velocity=80, time=0)
                write_chord_off(comp_track, voicing, BEAT)
                # Beat 2-and
                write_chord_on(comp_track, voicing, velocity=64, time=HALF)
                write_chord_off(comp_track, voicing, HALF)
                # Beat 3 rest, beat 4 hit
                write_chord_on(comp_track, voicing, velocity=72, time=BEAT)
                write_chord_off(comp_track, voicing, BEAT)

            # ── Bass: root-5th walking pattern ──
            if level == 'beginner':
                # Half notes: root, fifth
                write_note(bass_track, b_root, 80, 2 * BEAT, time=0, channel=1)
                write_note(bass_track, b_fifth, 70, 2 * BEAT, time=0, channel=1)
            else:
                # Quarter note walk: root, 3rd/5th, 5th, approach
                b_third = midi_note((root_pc + 3) % 12 if quality == 'min7' else (root_pc + 4) % 12, 2)
                # Chromatic approach to next bar's root
                next_idx = (bar_idx + 1) % len(chords)
                next_root_pc = parse_chord(chords[next_idx])[0]
                # Approach from semitone below
                approach = midi_note((next_root_pc - 1) % 12, 2)

                write_note(bass_track, b_root, 80, BEAT, time=0, channel=1)
                write_note(bass_track, b_third, 72, BEAT, time=0, channel=1)
                write_note(bass_track, b_fifth, 76, BEAT, time=0, channel=1)
                write_note(bass_track, approach, 68, BEAT, time=0, channel=1)

    # End-of-track
    for track in mid.tracks:
        track.append(MetaMessage('end_of_track', time=0))

    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    mid.save(outpath)
    return outpath


# ── Main ──

LEVELS = {
    'beginner':     {'tempo_key': 'beginner'},
    'intermediate': {'tempo_key': 'intermediate'},
    'advanced':     {'tempo_key': 'advanced'},
}

if __name__ == '__main__':
    prog_dir = os.path.join('programs', 'blues_motives')
    midi_dir = os.path.join(prog_dir, 'midi')
    os.makedirs(midi_dir, exist_ok=True)

    # Find all .ztprog files
    ztprog_files = sorted(
        f for f in os.listdir(prog_dir)
        if f.endswith('.ztprog')
    )

    total = 0
    for fname in ztprog_files:
        path = os.path.join(prog_dir, fname)
        prog = parse_ztprog(path)

        chords = prog.get('chords', '')
        if not chords:
            print(f"  SKIP {fname}: no chords")
            continue

        # Extract key name from filename: blues_12bar_{key}.ztprog
        m = re.match(r'blues_12bar_(.+)\.ztprog', fname)
        if not m:
            print(f"  SKIP {fname}: unrecognized filename pattern")
            continue
        key_name = m.group(1)

        # Get tempos from levels
        levels_data = prog.get('levels', {})
        default_bpm = int(prog.get('tempo_bpm', 80))

        for level in ('beginner', 'intermediate', 'advanced'):
            level_data = levels_data.get(level, {})
            bpm = int(level_data.get('tempo_bpm', default_bpm))

            out_fname = f"{key_name}_{level}.mid"
            out_path = os.path.join(midi_dir, out_fname)

            generate_blues_midi(
                chords_str=chords,
                bpm=bpm,
                level=level,
                outpath=out_path,
                loops=4,
            )
            total += 1

        print(f"  {key_name}: 3 levels")

    print(f"\nTotal MIDI files: {total}")
    print(f"Output: {midi_dir}/")
