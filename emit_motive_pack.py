#!/usr/bin/env python3
"""
emit_motive_pack.py

Reads blues_40_motives_canonical.json and emits:
  exercises/blues_motives/*.ztex     (40 exercise files)
  programs/blues_motives/*.ztprog    (7 backing tracks, one per native key)
  playlists/blues_motives_*.ztplay   (10 archetype session playlists)
"""
import json, os, textwrap

# ── Load canonical data ──
with open("blues_40_motives_canonical.json", encoding="utf-8") as f:
    canon = json.load(f)

motives = canon["motives"]

# ── Constants ──

# 12-bar blues chord formula: I7 I7 I7 I7 | IV7 IV7 I7 I7 | V7 IV7 I7 V7
BLUES_12BAR = {
    "E":  "E7 E7 E7 E7 A7 A7 E7 E7 B7 A7 E7 B7",
    "G":  "G7 G7 G7 G7 C7 C7 G7 G7 D7 C7 G7 D7",
    "A":  "A7 A7 A7 A7 D7 D7 A7 A7 E7 D7 A7 E7",
    "Bb": "Bb7 Bb7 Bb7 Bb7 Eb7 Eb7 Bb7 Bb7 F7 Eb7 Bb7 F7",
    "C":  "C7 C7 C7 C7 F7 F7 C7 C7 G7 F7 C7 G7",
    # Minor keys: i7 iv7 v7 (natural minor blues)
    "Gm": "Gm7 Gm7 Gm7 Gm7 Cm7 Cm7 Gm7 Gm7 Dm7 Cm7 Gm7 Dm7",
    "Cm": "Cm7 Cm7 Cm7 Cm7 Fm7 Fm7 Cm7 Cm7 Gm7 Fm7 Cm7 Gm7",
}

# Style mapping by archetype
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

# Exercise type mapping by archetype
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

# Default tempo by difficulty
TEMPO_BY_DIFF = {"Easy": 72, "Advanced": 96}

# Assessment criteria by articulation_model
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

# Archetype human names
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

# Goals by archetype (pedagogical focus)
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

# Practice steps by articulation_model (when technique IS the objective)
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


def yaml_str(s):
    """Quote a string for YAML output if needed."""
    if any(c in s for c in ":{}[]&*?|>!%@`#,"):
        return f'"{s}"'
    if s.startswith(("'", '"', "-", " ")):
        return f'"{s}"'
    return f'"{s}"'


def emit_ztprog(key, outdir):
    """Emit a 12-bar blues .ztprog backing track for the given key."""
    fname = f"blues_12bar_{key}.ztprog"
    chords = BLUES_12BAR[key]
    minor = key.endswith("m")
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
    path = os.path.join(outdir, fname)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return fname


def emit_ztex(motive, prog_dir, outdir):
    """Emit a .ztex exercise file for a single motive."""
    mid = motive["id"]
    arch = motive["archetype"]
    key = motive["key"]
    kind = motive["kind"]
    diff = motive["difficulty_level"]
    art_model = motive["articulation_model"]
    art_tags = motive["articulation_tags"]
    gravity = motive["gravity"]

    fname = f"{mid}_{arch.lower()}.ztex"
    prog_ref = f"../../programs/blues_motives/blues_12bar_{key}.ztprog"
    ex_type = EXERCISE_TYPE_MAP.get(arch, "lead_phrase")

    # Title
    arch_name = ARCHETYPE_NAMES.get(arch, arch)
    title = f"Barrett {kind} {motive['num']:02d}: {arch_name} ({key})"

    # Goals: archetype goals + articulation-specific if model set
    goals = list(GOALS_BY_ARCHETYPE.get(arch, ["Practice this motive"]))
    if art_model and art_model in STEPS_BY_MODEL:
        technique_name = art_model.replace("_", " ").title()
        goals.append(f"Primary technique focus: {technique_name}")

    # Practice steps
    if art_model and art_model in STEPS_BY_MODEL:
        steps = STEPS_BY_MODEL[art_model]
    else:
        steps = DEFAULT_STEPS

    # Tags
    tags = {
        "archetype": arch,
        "gravity": gravity["primary"],
        "difficulty": diff.lower(),
        "phrase_type": kind.lower(),
        "key": key,
        "source": "Barrett_40_Motives",
    }
    if art_model:
        tags["articulation_model"] = art_model
    if gravity["secondary"]:
        tags["gravity_secondary"] = gravity["secondary"]

    # Assessment
    if art_model and art_model in ASSESSMENT_BY_MODEL:
        assess = ASSESSMENT_BY_MODEL[art_model]
    else:
        assess = DEFAULT_ASSESSMENT

    # Build YAML
    lines = [
        f"id: {mid}",
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


def emit_ztplay_archetype(archetype, arch_motives, outdir):
    """Emit a .ztplay session playlist for one archetype family."""
    arch_name = ARCHETYPE_NAMES.get(archetype, archetype)
    slug = archetype.lower()
    fname = f"blues_motives_{slug}.ztplay"

    # Sort by kind (Intro first) then num
    arch_motives = sorted(arch_motives, key=lambda m: (m["kind"] != "Intro", m["num"]))

    lines = [
        f"id: blues_motives_{slug}",
        f"title: {yaml_str(f'Barrett 40 Motives: {arch_name} Family')}",
        f"category: archetype_session",
        f"tags: [barrett_40, blues, {slug}]",
        "",
        "defaults:",
        f"  tempo: 80",
        f"  bars_per_chord: 1",
        f"  style: {STYLE_MAP.get(archetype, 'swing_basic')}",
        "",
        "items:",
    ]
    for m in arch_motives:
        mid = m["id"]
        kind = m["kind"]
        num = m["num"]
        key = m["key"]
        diff = m["difficulty_level"]
        label = f"{kind} {num:02d} ({diff}, {key})"
        prog_path = f"programs/blues_motives/blues_12bar_{key}.ztprog"
        lines.append(f"  - name: {yaml_str(label)}")
        lines.append(f"    file: {yaml_str(prog_path)}")
        lines.append(f"    repeats: 2")
        lines.append("")

    path = os.path.join(outdir, fname)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return fname


def emit_ztplay_master(motives, outdir):
    """Emit a master session playlist: all 40 motives grouped by key pair."""
    fname = "blues_motives_all_40.ztplay"
    sorted_motives = sorted(motives, key=lambda m: (m["key"], m["kind"] != "Intro", m["num"]))

    lines = [
        f"id: blues_motives_all_40",
        f'title: "Barrett 40 Motives: Complete Session"',
        f"category: archetype_session",
        f"tags: [barrett_40, blues, complete]",
        "",
        "defaults:",
        f"  tempo: 80",
        f"  bars_per_chord: 1",
        f"  style: swing_basic",
        "",
        "items:",
    ]
    for m in sorted_motives:
        mid = m["id"]
        kind = m["kind"]
        num = m["num"]
        key = m["key"]
        arch = m["archetype"]
        diff = m["difficulty_level"]
        label = f"{kind} {num:02d} — {ARCHETYPE_NAMES.get(arch, arch)} ({diff}, {key})"
        prog_path = f"programs/blues_motives/blues_12bar_{key}.ztprog"
        lines.append(f"  - name: {yaml_str(label)}")
        lines.append(f"    file: {yaml_str(prog_path)}")
        lines.append(f"    repeats: 1")
        lines.append("")

    path = os.path.join(outdir, fname)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return fname


# ── Main ──
if __name__ == "__main__":
    # Create output directories
    ex_dir = os.path.join("exercises", "blues_motives")
    prog_dir = os.path.join("programs", "blues_motives")
    play_dir = "playlists"

    os.makedirs(ex_dir, exist_ok=True)
    os.makedirs(prog_dir, exist_ok=True)
    os.makedirs(play_dir, exist_ok=True)

    # 1. Emit .ztprog backing tracks (one per native key)
    keys_used = sorted(set(m["key"] for m in motives))
    print(f"Emitting {len(keys_used)} backing tracks:")
    for key in keys_used:
        fname = emit_ztprog(key, prog_dir)
        print(f"  {fname}")

    # 2. Emit .ztex exercises (one per motive)
    print(f"\nEmitting {len(motives)} exercises:")
    for m in motives:
        fname = emit_ztex(m, prog_dir, ex_dir)
        print(f"  {fname}")

    # 3. Emit .ztplay archetype playlists (one per archetype)
    archetypes = {}
    for m in motives:
        archetypes.setdefault(m["archetype"], []).append(m)

    print(f"\nEmitting {len(archetypes)} archetype playlists:")
    for arch in sorted(archetypes):
        fname = emit_ztplay_archetype(arch, archetypes[arch], play_dir)
        count = len(archetypes[arch])
        print(f"  {fname} ({count} motives)")

    # 4. Emit master playlist (all 40)
    master = emit_ztplay_master(motives, play_dir)
    print(f"\nEmitting master playlist:")
    print(f"  {master} (40 motives)")

    # Summary
    total = len(keys_used) + len(motives) + len(archetypes) + 1
    print(f"\nTotal files emitted: {total}")
