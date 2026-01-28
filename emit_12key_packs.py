#!/usr/bin/env python3
"""
emit_12key_packs.py

Reads blues_40_motives_canonical.json and emits 12-key transposition packs:
  programs/blues_motives/blues_12bar_{key}.ztprog     (24 total: 12 major + 12 minor)
  exercises/blues_motives_12key/{key}/*.ztex           (40 motives x 12 keys = 480)
  playlists/blues_motives_12key_cycle_{archetype}.ztplay  (10 archetype cycle playlists)

Major-key motives are transposed to all 12 major keys.
Minor-key motives are transposed to all 12 minor keys.
"""
import json, os
from zone_tritone_tools import pc, name_from_pc

# ── Load canonical data ──
with open("blues_40_motives_canonical.json", encoding="utf-8") as f:
    canon = json.load(f)

motives = canon["motives"]

# ── Pitch-class transposition helpers ──

ALL_MAJOR_KEYS = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]
ALL_MINOR_KEYS = ["Cm", "C#m", "Dm", "Ebm", "Em", "Fm", "F#m", "Gm", "Abm", "Am", "Bbm", "Bm"]

# Preferred spelling for chord symbols (blues convention: flats for most, sharps for F#/C#/G#)
MAJOR_KEY_PREFER_FLATS = {
    "C": True, "Db": True, "D": False, "Eb": True, "E": False, "F": True,
    "Gb": True, "G": False, "Ab": True, "A": False, "Bb": True, "B": False,
}
MINOR_KEY_PREFER_FLATS = {
    "Cm": True, "C#m": False, "Dm": False, "Ebm": True, "Em": False, "Fm": True,
    "F#m": False, "Gm": True, "Abm": True, "Am": False, "Bbm": True, "Bm": False,
}

def key_root_pc(key):
    """Extract root pitch class from key name (e.g. 'Gm' -> pc('G'))."""
    root = key.rstrip("m")
    return pc(root)

def is_minor_key(key):
    return key.endswith("m") and len(key) > 1

def transpose_interval(from_key, to_key):
    """Semitones to shift from from_key to to_key."""
    return (key_root_pc(to_key) - key_root_pc(from_key)) % 12

def transpose_chord(chord, interval, prefer_flats=True):
    """Transpose a chord symbol by interval semitones. E.g. 'E7' +5 -> 'A7'."""
    # Parse root from chord
    if len(chord) > 1 and chord[1] in ("#", "b"):
        root_str = chord[:2]
        suffix = chord[2:]
    else:
        root_str = chord[0]
        suffix = chord[1:]
    root_pc = pc(root_str)
    new_pc = (root_pc + interval) % 12
    new_root = name_from_pc(new_pc, prefer_flats=prefer_flats)
    return new_root + suffix

def blues_12bar_chords(key):
    """Generate 12-bar blues chord string for any key."""
    minor = is_minor_key(key)
    root_pc = key_root_pc(key)
    prefer_flats = (MINOR_KEY_PREFER_FLATS if minor else MAJOR_KEY_PREFER_FLATS).get(key, True)

    I_pc = root_pc
    IV_pc = (root_pc + 5) % 12
    V_pc = (root_pc + 7) % 12

    I_name = name_from_pc(I_pc, prefer_flats)
    IV_name = name_from_pc(IV_pc, prefer_flats)
    V_name = name_from_pc(V_pc, prefer_flats)

    if minor:
        I = f"{I_name}m7"
        IV = f"{IV_name}m7"
        V = f"{V_name}m7"
    else:
        I = f"{I_name}7"
        IV = f"{IV_name}7"
        V = f"{V_name}7"

    # I I I I | IV IV I I | V IV I V
    return f"{I} {I} {I} {I} {IV} {IV} {I} {I} {V} {IV} {I} {V}"


# ── Import emit helpers from emit_motive_pack.py ──
# Re-declare the constants we need (avoid coupling to the other script's globals)

ARCHETYPE_NAMES = {
    "DESC_LINE_TURNAROUND":  "Descending Line Turnaround",
    "ASC_LINE_TURNAROUND":   "Ascending Line Turnaround",
    "SEMITONE_APPROACH":     "Semitone Approach",
    "DIM_PASSING_ENGINE":    "Diminished Passing Engine",
    "DOUBLESTOP_EXPRESSIVE": "Double-Stop Expressive",
    "CHORDAL_COLOR":         "Chordal Color",
    "STATIC_RIFF":           "Static Riff",
    "PENTATONIC_LEAD":       "Pentatonic Lead",
    "EXPRESSIVE_MINIMAL":    "Expressive Minimal",
    "ROCK_BLUES_HYBRID":     "Rock-Blues Hybrid",
}

EXERCISE_TYPE_MAP = {
    "DESC_LINE_TURNAROUND":  "phrase_accuracy",
    "ASC_LINE_TURNAROUND":   "phrase_accuracy",
    "SEMITONE_APPROACH":     "phrase_accuracy",
    "DIM_PASSING_ENGINE":    "voicing_memory",
    "DOUBLESTOP_EXPRESSIVE": "lead_phrase",
    "CHORDAL_COLOR":         "voicing_memory",
    "STATIC_RIFF":           "lead_phrase",
    "PENTATONIC_LEAD":       "lead_phrase",
    "EXPRESSIVE_MINIMAL":    "lead_phrase",
    "ROCK_BLUES_HYBRID":     "lead_phrase",
}

STYLE_MAP = {
    "DESC_LINE_TURNAROUND":  "swing_basic",
    "ASC_LINE_TURNAROUND":   "swing_basic",
    "SEMITONE_APPROACH":     "swing_basic",
    "DIM_PASSING_ENGINE":    "swing_basic",
    "DOUBLESTOP_EXPRESSIVE": "swing_basic",
    "CHORDAL_COLOR":         "jazz_blues",
    "STATIC_RIFF":           "swing_basic",
    "PENTATONIC_LEAD":       "swing_basic",
    "EXPRESSIVE_MINIMAL":    "ballad_basic",
    "ROCK_BLUES_HYBRID":     "swing_basic",
}

GOALS_BY_ARCHETYPE = {
    "DESC_LINE_TURNAROUND": [
        "Execute descending chromatic/diatonic line with even timing",
        "Feel the zone-crossing gravity as each half-step pulls toward resolution",
    ],
    "ASC_LINE_TURNAROUND": [
        "Walk the ascending bass line with rhythmic precision",
        "Build energy toward the V chord arrival",
    ],
    "SEMITONE_APPROACH": [
        "Land the bII-to-I semitone resolution with conviction",
        "Feel the maximum zone-crossing gravity of the half-step cadence",
    ],
    "DIM_PASSING_ENGINE": [
        "Voice the diminished passing chord cleanly between dominants",
        "Hear how the diminished bridges two tritone axes",
    ],
    "DOUBLESTOP_EXPRESSIVE": [
        "Execute double-stops with parallel voice motion",
        "Control bend pitch when two strings move together",
    ],
    "CHORDAL_COLOR": [
        "Memorize extended voicing shapes (9ths, 13ths, #9)",
        "Voice-lead smoothly between color chords",
    ],
    "STATIC_RIFF": [
        "Lock the riff into a steady groove without rushing",
        "Build rhythmic intensity without harmonic motion",
    ],
    "PENTATONIC_LEAD": [
        "Phrase pentatonic lines with rhythmic variety",
        "Target chord tones on strong beats",
    ],
    "EXPRESSIVE_MINIMAL": [
        "Wring maximum emotion from minimum notes",
        "Focus on bend accuracy, vibrato evenness, and dynamic control",
    ],
    "ROCK_BLUES_HYBRID": [
        "Drive the rhythm with rock-influenced attack and energy",
        "Keep the straight-four feel tight and punchy",
    ],
}

STEPS_BY_MODEL = {
    "bend": [
        "Play at slow tempo, isolating each bend",
        "Check bend pitch against fretted reference note",
        "Gradually increase tempo while maintaining pitch accuracy",
    ],
    "bend_quarter": [
        "Play at slow tempo, isolating each quarter-tone bend",
        "Quarter-tone target is BETWEEN frets — use your ear, not a tuner",
        "Practice the 'blues curl': push just enough to blur the zone boundary",
    ],
    "bend_vibrato": [
        "Play at slow tempo, nailing bend targets first",
        "Add vibrato only after the bend reaches pitch",
        "Vibrato should oscillate evenly — time it to the pulse",
    ],
    "fingerstyle": [
        "Practice thumb-and-fingers plucking on isolated chords",
        "All notes in a chord should sound simultaneously",
        "Work for even dynamics across all plucked strings",
    ],
}

DEFAULT_STEPS = [
    "Play at slow tempo (beginner level)",
    "Loop 4 times, then increase tempo",
    "Focus on phrasing and articulation",
]

ASSESSMENT_BY_MODEL = {
    "bend":          {"what": ["bend_pitch_accuracy", "timing_consistency_ms"],
                      "criteria": {"bend_pitch_deviation_cents": 15, "max_timing_deviation_ms": 35}},
    "bend_quarter":  {"what": ["quarter_tone_pitch_accuracy", "timing_consistency_ms"],
                      "criteria": {"quarter_tone_deviation_cents": 10, "max_timing_deviation_ms": 35}},
    "bend_vibrato":  {"what": ["bend_pitch_accuracy", "vibrato_evenness", "timing_consistency_ms"],
                      "criteria": {"bend_pitch_deviation_cents": 15, "max_timing_deviation_ms": 35}},
    "fingerstyle":   {"what": ["note_separation_ms", "timing_consistency_ms", "dynamic_evenness"],
                      "criteria": {"max_timing_deviation_ms": 30}},
}

DEFAULT_ASSESSMENT = {
    "what": ["timing_consistency_ms", "phrase_length_control"],
    "criteria": {"max_timing_deviation_ms": 35},
}


def yaml_str(s):
    if any(c in s for c in ":{}[]&*?|>!%@`#,"):
        return f'"{s}"'
    if s.startswith(("'", '"', "-", " ")):
        return f'"{s}"'
    return f'"{s}"'


# ── Emitters ──

def emit_ztprog(key, outdir):
    """Emit a 12-bar blues .ztprog for the given key (major or minor)."""
    fname = f"blues_12bar_{key}.ztprog"
    path = os.path.join(outdir, fname)
    if os.path.exists(path):
        return fname  # already emitted by emit_motive_pack.py

    chords = blues_12bar_chords(key)
    minor = is_minor_key(key)
    label = f"{key} Minor Blues" if minor else f"{key} Blues"
    tempo = 72 if minor else 80

    lines = [
        f"name: {yaml_str(f'12-Bar {label} (Barrett Motives)')}",
        f"chords: {chords}",
        f"style: swing_basic",
        f"bars_per_chord: 1",
        f"tritone_mode: none",
        f"outfile: blues_12bar_{key}_backing.mid",
        f"tempo_bpm: {tempo}",
        f"tempo_range:",
        f"- 52",
        f"- 140",
        f"levels:",
        f"  beginner:",
        f"    tempo_bpm: 52",
        f"    comping: whole_notes",
        f"  intermediate:",
        f"    tempo_bpm: {tempo}",
        f"    comping: rhythmic",
        f"  advanced:",
        f"    tempo_bpm: 140",
        f"    comping: syncopated",
    ]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return fname


def emit_transposed_ztex(motive, target_key, outdir):
    """Emit a transposed .ztex exercise for a single motive in target_key."""
    mid = motive["id"]
    arch = motive["archetype"]
    native_key = motive["key"]
    kind = motive["kind"]
    diff = motive["difficulty_level"]
    art_model = motive["articulation_model"]
    gravity = motive["gravity"]

    fname = f"{mid}_{arch.lower()}.ztex"
    # Depth from exercises/blues_motives_12key/{key}/ to programs/blues_motives/
    prog_ref = f"../../../programs/blues_motives/blues_12bar_{target_key}.ztprog"
    ex_type = EXERCISE_TYPE_MAP.get(arch, "lead_phrase")

    arch_name = ARCHETYPE_NAMES.get(arch, arch)
    if target_key == native_key:
        title = f"Barrett {kind} {motive['num']:02d}: {arch_name} ({target_key})"
    else:
        title = f"Barrett {kind} {motive['num']:02d}: {arch_name} ({target_key}, from {native_key})"

    goals = list(GOALS_BY_ARCHETYPE.get(arch, ["Practice this motive"]))
    if target_key != native_key:
        goals.append(f"Transpose from native key {native_key} — same shapes, new position")
    if art_model and art_model in STEPS_BY_MODEL:
        technique_name = art_model.replace("_", " ").title()
        goals.append(f"Primary technique focus: {technique_name}")

    if art_model and art_model in STEPS_BY_MODEL:
        steps = STEPS_BY_MODEL[art_model]
    else:
        steps = DEFAULT_STEPS

    tags = {
        "archetype": arch,
        "gravity": gravity["primary"],
        "difficulty": diff.lower(),
        "phrase_type": kind.lower(),
        "key": target_key,
        "native_key": native_key,
        "source": "Barrett_40_Motives",
        "pack": "12key",
    }
    if art_model:
        tags["articulation_model"] = art_model
    if gravity["secondary"]:
        tags["gravity_secondary"] = gravity["secondary"]

    if art_model and art_model in ASSESSMENT_BY_MODEL:
        assess = ASSESSMENT_BY_MODEL[art_model]
    else:
        assess = DEFAULT_ASSESSMENT

    lines = [
        f"id: {mid}_{target_key.lower().replace('#', 's')}",
        f"title: {yaml_str(title)}",
        f"program_ref: {prog_ref}",
        f"exercise_type: {ex_type}",
        "",
        "goals:",
    ]
    for g in goals:
        lines.append(f"  - {yaml_str(g)}")
    lines.append("")
    lines.append("practice_steps:")
    for s in steps:
        lines.append(f"  - {yaml_str(s)}")
    lines.append("")
    lines.append("tags:")
    for tk, tv in tags.items():
        lines.append(f"  {tk}: {tv}")
    lines.append("")
    lines.append("assessment:")
    lines.append("  what_to_measure:")
    for w in assess["what"]:
        lines.append(f"    - {w}")
    lines.append("  pass_criteria:")
    for ck, cv in assess["criteria"].items():
        lines.append(f"    {ck}: {cv}")

    path = os.path.join(outdir, fname)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return fname


def emit_12key_cycle_playlist(archetype, arch_motives, outdir):
    """Emit a 12-key cycle playlist for one archetype.
    Cycles through all keys for each motive in the family."""
    arch_name = ARCHETYPE_NAMES.get(archetype, archetype)
    slug = archetype.lower()
    fname = f"blues_motives_12key_cycle_{slug}.ztplay"

    # Determine if this archetype has minor motives, major motives, or both
    has_major = any(not is_minor_key(m["key"]) for m in arch_motives)
    has_minor = any(is_minor_key(m["key"]) for m in arch_motives)

    lines = [
        f"id: blues_motives_12key_cycle_{slug}",
        f"title: {yaml_str(f'12-Key Cycle: {arch_name}')}",
        f"category: twelve_key_cycle",
        f"tags: [barrett_40, blues, {slug}, 12key_cycle]",
        "",
        "defaults:",
        f"  tempo: 80",
        f"  bars_per_chord: 1",
        f"  style: {STYLE_MAP.get(archetype, 'swing_basic')}",
        "",
        "items:",
    ]

    # Pick one representative motive per difficulty (Easy first, then Advanced)
    # Cycle it through all 12 keys
    major_motives = sorted(
        [m for m in arch_motives if not is_minor_key(m["key"])],
        key=lambda m: (m["difficulty_level"] != "Easy", m["num"])
    )
    minor_motives = sorted(
        [m for m in arch_motives if is_minor_key(m["key"])],
        key=lambda m: (m["difficulty_level"] != "Easy", m["num"])
    )

    if major_motives:
        rep = major_motives[0]  # easiest major motive
        lines.append(f"  # Major keys — {rep['kind']} {rep['num']:02d} ({rep['difficulty_level']})")
        for key in ALL_MAJOR_KEYS:
            label = f"{rep['kind']} {rep['num']:02d} in {key}"
            prog_path = f"programs/blues_motives/blues_12bar_{key}.ztprog"
            lines.append(f"  - name: {yaml_str(label)}")
            lines.append(f"    file: {yaml_str(prog_path)}")
            lines.append(f"    repeats: 2")
            lines.append("")

    if minor_motives:
        rep = minor_motives[0]
        lines.append(f"  # Minor keys — {rep['kind']} {rep['num']:02d} ({rep['difficulty_level']})")
        for key in ALL_MINOR_KEYS:
            label = f"{rep['kind']} {rep['num']:02d} in {key}"
            prog_path = f"programs/blues_motives/blues_12bar_{key}.ztprog"
            lines.append(f"  - name: {yaml_str(label)}")
            lines.append(f"    file: {yaml_str(prog_path)}")
            lines.append(f"    repeats: 2")
            lines.append("")

    path = os.path.join(outdir, fname)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return fname


# ── Main ──
if __name__ == "__main__":
    prog_dir = os.path.join("programs", "blues_motives")
    ex_12key_dir = os.path.join("exercises", "blues_motives_12key")
    play_dir = "playlists"

    os.makedirs(prog_dir, exist_ok=True)
    os.makedirs(play_dir, exist_ok=True)

    # 1. Emit all 24 backing tracks (12 major + 12 minor)
    new_progs = 0
    all_keys = ALL_MAJOR_KEYS + ALL_MINOR_KEYS
    for key in all_keys:
        fname = emit_ztprog(key, prog_dir)
        if fname:
            new_progs += 1
    print(f"Backing tracks: {new_progs} total ({len(all_keys)} keys)")

    # 2. Emit transposed exercises: 40 motives x 12 keys
    total_ex = 0
    for m in motives:
        native_key = m["key"]
        minor = is_minor_key(native_key)
        target_keys = ALL_MINOR_KEYS if minor else ALL_MAJOR_KEYS

        for target_key in target_keys:
            key_dir = os.path.join(ex_12key_dir, target_key)
            os.makedirs(key_dir, exist_ok=True)
            emit_transposed_ztex(m, target_key, key_dir)
            total_ex += 1

    print(f"Transposed exercises: {total_ex}")

    # 3. Emit 12-key cycle playlists (one per archetype)
    archetypes = {}
    for m in motives:
        archetypes.setdefault(m["archetype"], []).append(m)

    print(f"\n12-key cycle playlists:")
    for arch in sorted(archetypes):
        fname = emit_12key_cycle_playlist(arch, archetypes[arch], play_dir)
        print(f"  {fname}")

    # Summary
    print(f"\nSummary:")
    print(f"  Backing tracks: {len(all_keys)} (.ztprog)")
    print(f"  Exercises:      {total_ex} (.ztex)")
    print(f"  Playlists:      {len(archetypes)} (.ztplay)")
    print(f"  Total new files: {len(all_keys) + total_ex + len(archetypes)}")
