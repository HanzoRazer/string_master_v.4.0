#!/usr/bin/env python3
"""
build_canonical_motives.py

Reads blues_40_motives_index.xlsx and produces blues_40_motives_canonical.json
with fixed parsing, canonical archetype IDs, gravity mapping, and refined metadata.
"""
import openpyxl, json, re
from collections import Counter

wb = openpyxl.load_workbook("blues_40_motives_index.xlsx")
ws = wb.active
rows = list(ws.iter_rows(values_only=True))
headers = rows[0]
data = [dict(zip(headers, r)) for r in rows[1:]]

# ── Phase 1: Fix difficulty/key/style parsing ──
for d in data:
    raw_diff = d["difficulty"] or ""
    m = re.match(
        r"(Easy|Advanced)\s*(acoustic)?\s*(?:in\s+)?([A-G][b#]?m?)?\s*$",
        raw_diff, re.I,
    )
    if m:
        d["difficulty_level"] = m.group(1).title()
        d["style_qualifier"] = m.group(2).lower() if m.group(2) else None
        if m.group(3) and not d.get("key"):
            d["key"] = m.group(3)
    else:
        d["difficulty_level"] = raw_diff.title() if raw_diff else None
        d["style_qualifier"] = None
    if d.get("key"):
        k = d["key"]
        d["key"] = k[0].upper() + k[1:]

# ── Phase 2: Canonical Archetype Assignment ──
# 10 archetypes derived from zone-tritone framework + Barrett's descriptions:
#
# DESC_LINE_TURNAROUND    Descending chromatic/diatonic line, often implying dim passing or V-I
# ASC_LINE_TURNAROUND     Ascending bass/melodic line to V chord setup
# SEMITONE_APPROACH       bII->I (or bVI->V) semitone resolution cadence
# DIM_PASSING_ENGINE      Diminished chord as chromatic passing device between dominants
# DOUBLESTOP_EXPRESSIVE   Double-stop bends/licks as primary texture
# CHORDAL_COLOR           Extended voicings (9ths, 13ths, #9) as harmonic color
# STATIC_RIFF             Repetitive riff/vamp, no turnaround motion
# PENTATONIC_LEAD         Pentatonic-based solo/lick phrasing
# EXPRESSIVE_MINIMAL      Minimal notes, maximum expression (bends/vibrato/touch)
# ROCK_BLUES_HYBRID       Rock-influenced energy (gain, power, Page/Van Halen)

MANUAL_ARCHETYPE = {
    # ── Intros ──
    ("Intro",  1): "DESC_LINE_TURNAROUND",
    ("Intro",  2): "CHORDAL_COLOR",            # expanded chord voicings, jazzier
    ("Intro",  3): "ASC_LINE_TURNAROUND",
    ("Intro",  4): "ASC_LINE_TURNAROUND",
    ("Intro",  5): "DIM_PASSING_ENGINE",        # 7th+dim chords, ascending chromatic
    ("Intro",  6): "PENTATONIC_LEAD",           # pentatonic licks, Robben Ford chromatic
    ("Intro",  7): "STATIC_RIFF",
    ("Intro",  8): "DOUBLESTOP_EXPRESSIVE",
    ("Intro",  9): "EXPRESSIVE_MINIMAL",        # few notes, bends and vibrato
    ("Intro", 10): "EXPRESSIVE_MINIMAL",        # intense, muscle memory
    ("Intro", 11): "DIM_PASSING_ENGINE",
    ("Intro", 12): "PENTATONIC_LEAD",           # Beano-era Clapton, quarter-tone bends
    ("Intro", 13): "DESC_LINE_TURNAROUND",
    ("Intro", 14): "DESC_LINE_TURNAROUND",
    ("Intro", 15): "ROCK_BLUES_HYBRID",         # straight four, gain, Jimmy Page
    ("Intro", 16): "EXPRESSIVE_MINIMAL",        # wailing solo-fest, bends+vibrato
    ("Intro", 17): "STATIC_RIFF",              # "no turnarounds or diminished chords"
    ("Intro", 18): "DOUBLESTOP_EXPRESSIVE",
    ("Intro", 19): "CHORDAL_COLOR",            # 9th chords, Eric Johnson
    ("Intro", 20): "DOUBLESTOP_EXPRESSIVE",
    # ── Outros ──
    ("Outro",  1): "SEMITONE_APPROACH",
    ("Outro",  2): "DESC_LINE_TURNAROUND",
    ("Outro",  3): "SEMITONE_APPROACH",
    ("Outro",  4): "CHORDAL_COLOR",            # D11, 7#9 chords
    ("Outro",  5): "SEMITONE_APPROACH",
    ("Outro",  6): "SEMITONE_APPROACH",
    ("Outro",  7): "DESC_LINE_TURNAROUND",
    ("Outro",  8): "EXPRESSIVE_MINIMAL",        # Clapton, vibrato, quarter-tone bends
    ("Outro",  9): "PENTATONIC_LEAD",           # simple pentatonic phrase, V setup
    ("Outro", 10): "DOUBLESTOP_EXPRESSIVE",
    ("Outro", 11): "SEMITONE_APPROACH",
    ("Outro", 12): "PENTATONIC_LEAD",           # E major pentatonic, soloing ideas
    ("Outro", 13): "DOUBLESTOP_EXPRESSIVE",     # doublestops, V as minor chord
    ("Outro", 14): "PENTATONIC_LEAD",
    ("Outro", 15): "ROCK_BLUES_HYBRID",         # rock to blues, bass part, big C finish
    ("Outro", 16): "PENTATONIC_LEAD",
    ("Outro", 17): "DOUBLESTOP_EXPRESSIVE",
    ("Outro", 18): "DOUBLESTOP_EXPRESSIVE",
    ("Outro", 19): "CHORDAL_COLOR",
    ("Outro", 20): "DOUBLESTOP_EXPRESSIVE",
}

# ── Phase 3: Gravity mapping ──
# front_door:    V->I standard dominant resolution
# semitone:      bII->I or bVI->V chromatic approach
# dim_chromatic: diminished passing between dominants
# static:        no harmonic motion (riff/vamp)
# expressive:    no cadential motion, expression-focused
# mixed:         combines multiple gravity types

MANUAL_GRAVITY = {
    ("Intro",  1): {"primary": "front_door",  "secondary": None},
    ("Intro",  2): {"primary": "front_door",  "secondary": None},
    ("Intro",  3): {"primary": "front_door",  "secondary": None},
    ("Intro",  4): {"primary": "front_door",  "secondary": None},
    ("Intro",  5): {"primary": "front_door",  "secondary": "dim_chromatic"},
    ("Intro",  6): {"primary": "front_door",  "secondary": None},
    ("Intro",  7): {"primary": "static",      "secondary": None},
    ("Intro",  8): {"primary": "static",      "secondary": None},
    ("Intro",  9): {"primary": "expressive",  "secondary": None},
    ("Intro", 10): {"primary": "expressive",  "secondary": None},
    ("Intro", 11): {"primary": "front_door",  "secondary": "dim_chromatic"},
    ("Intro", 12): {"primary": "front_door",  "secondary": None},
    ("Intro", 13): {"primary": "front_door",  "secondary": None},
    ("Intro", 14): {"primary": "front_door",  "secondary": None},
    ("Intro", 15): {"primary": "static",      "secondary": None},
    ("Intro", 16): {"primary": "expressive",  "secondary": None},
    ("Intro", 17): {"primary": "static",      "secondary": None},
    ("Intro", 18): {"primary": "static",      "secondary": None},
    ("Intro", 19): {"primary": "front_door",  "secondary": None},
    ("Intro", 20): {"primary": "front_door",  "secondary": None},
    ("Outro",  1): {"primary": "semitone",    "secondary": None},
    ("Outro",  2): {"primary": "front_door",  "secondary": None},
    ("Outro",  3): {"primary": "semitone",    "secondary": None},
    ("Outro",  4): {"primary": "front_door",  "secondary": None},
    ("Outro",  5): {"primary": "semitone",    "secondary": "front_door"},
    ("Outro",  6): {"primary": "semitone",    "secondary": None},
    ("Outro",  7): {"primary": "front_door",  "secondary": None},
    ("Outro",  8): {"primary": "expressive",  "secondary": None},
    ("Outro",  9): {"primary": "front_door",  "secondary": "semitone"},
    ("Outro", 10): {"primary": "front_door",  "secondary": None},
    ("Outro", 11): {"primary": "semitone",    "secondary": "front_door"},
    ("Outro", 12): {"primary": "front_door",  "secondary": None},
    ("Outro", 13): {"primary": "front_door",  "secondary": None},
    ("Outro", 14): {"primary": "expressive",  "secondary": None},
    ("Outro", 15): {"primary": "front_door",  "secondary": None},
    ("Outro", 16): {"primary": "expressive",  "secondary": None},
    ("Outro", 17): {"primary": "expressive",  "secondary": None},
    ("Outro", 18): {"primary": "front_door",  "secondary": None},
    ("Outro", 19): {"primary": "front_door",  "secondary": None},
    ("Outro", 20): {"primary": "expressive",  "secondary": None},
}


def refined_cadential_intent(kind, num, desc):
    d = desc.lower()
    if kind == "Intro":
        if "v chord" in d or "turnaround" in d:
            return "V_SETUP"
        return "OPEN_STATEMENT"
    else:
        if "home" in d or "finish" in d or "final" in d or "big" in d:
            return "I_FINAL"
        if "v chord" in d or "turnaround" in d:
            return "V_TO_I"
        if "semitone" in d:
            return "SEMITONE_TO_I"
        return "CLOSE"


def refined_articulation(desc):
    d = desc.lower()
    arts = []
    if "quarter-tone" in d or "quarter tone" in d:
        arts.append("bend_quarter")
    elif "bend" in d:
        arts.append("bend")
    if "vibrato" in d:
        arts.append("vibrato")
    if "rake" in d or "raked" in d:
        arts.append("rake")
    if "double-stop" in d or "double stop" in d or "doublestop" in d:
        arts.append("doublestop")
    if "thumb and fingers" in d or "fingerstyle" in d:
        arts.append("fingerstyle")
    if "tremolo" in d:
        arts.append("tremolo")
    return arts if arts else None


# ── Build canonical output ──
canonical = []
for d in data:
    k = (d["kind"], d["num"])
    entry = {
        "id": f"{d['kind'].lower()}_{d['num']:02d}",
        "kind": d["kind"],
        "num": d["num"],
        "difficulty_level": d["difficulty_level"],
        "style_qualifier": d.get("style_qualifier"),
        "key": d.get("key"),
        "version": d.get("version"),
        "archetype": MANUAL_ARCHETYPE.get(k, "UNCLASSIFIED"),
        "gravity": MANUAL_GRAVITY.get(k, {"primary": None, "secondary": None}),
        "cadential_intent": refined_cadential_intent(
            d["kind"], d["num"], d["description"]
        ),
        "articulation_tags": refined_articulation(d["description"]),
        "description": d["description"],
    }
    canonical.append(entry)

# ── Summary ──
unclassified = [e for e in canonical if e["archetype"] == "UNCLASSIFIED"]
print(f"Total: {len(canonical)}, Unclassified: {len(unclassified)}")
print()

arch_counts = Counter(e["archetype"] for e in canonical)
print("Archetype distribution:")
for a, c in sorted(arch_counts.items(), key=lambda x: -x[1]):
    print(f"  {a:<28} {c}")

print()
grav_counts = Counter(e["gravity"]["primary"] for e in canonical)
print("Gravity distribution:")
for g, c in sorted(grav_counts.items(), key=lambda x: -x[1]):
    print(f"  {g:<16} {c}")

# ── Write ──
with open("blues_40_motives_canonical.json", "w", encoding="utf-8") as f:
    json.dump(
        {
            "schema_version": "1.0",
            "source": "40 Essential Blues Guitar Intros and Outros (Richard Barrett, Guitar Techniques, 2011)",
            "archetypes": sorted(set(MANUAL_ARCHETYPE.values())),
            "motives": canonical,
        },
        f,
        indent=2,
        ensure_ascii=False,
    )

print()
print("Wrote blues_40_motives_canonical.json")
