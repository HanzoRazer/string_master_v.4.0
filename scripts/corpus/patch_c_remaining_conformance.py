#!/usr/bin/env python3
"""
patch_c_remaining_conformance.py

Phase C corpus remediation — fixes the three files that still fail
conformance after Phases A and B:

1. blues_canonical.json
   - 28 exercises missing program_ref (all have id → infer path)

2. gospel_canonical.json
   - 2 "movable" exercises missing key (multi-key by design → use "C")

3. blues_40_motives_canonical.json
   - motives key exists but standard exercises key is absent
   - Adds an exercises bridge array mapping motive fields to standard shape
   - Mirrors the fix from build_canonical_motives.py discussion

Safe to run multiple times (idempotent).
"""
import json
import pathlib

CORPUS = pathlib.Path(__file__).parents[2] / "data" / "corpus"


# ── 1. blues_canonical — inject missing program_ref ─────────────────────────

def patch_blues(path: pathlib.Path) -> dict:
    with open(path) as f:
        doc = json.load(f)

    patched = 0
    for ex in doc.get("exercises", []):
        if "program_ref" not in ex:
            ex["program_ref"] = f"programs/blues_{ex['id']}.ztprog"
            patched += 1

    print(f"  blues: injected program_ref into {patched} exercises")
    return doc


# ── 2. gospel_canonical — inject missing key for movable exercises ───────────

def patch_gospel(path: pathlib.Path) -> dict:
    with open(path) as f:
        doc = json.load(f)

    patched = 0
    for ex in doc.get("exercises", []):
        if "key" not in ex:
            # "Movable (C / G / D)" exercises are multi-key by design.
            # Use "C" as the canonical key (first in the title's list)
            # and add a keys_all extension for consumers that need the full set.
            ex["key"] = "C"
            ex["keys_all"] = ["C", "G", "D"]
            patched += 1

    print(f"  gospel: injected key into {patched} movable exercises")
    return doc


# ── 3. blues_40_motives — add exercises bridge array ────────────────────────

# Gravity primary value → harmonic_context string for the bridge
GRAVITY_TO_CONTEXT = {
    "front_door":    "blues_major",
    "semitone":      "turnaround_minor",
    "dim_chromatic": "blues_major",
    "static":        "blues_major",
    "expressive":    "blues_major",
    "mixed":         "blues_major",
}

# Archetype → technique string
ARCHETYPE_TO_TECHNIQUE = {
    "DESC_LINE_TURNAROUND":  "melodic",
    "ASC_LINE_TURNAROUND":   "melodic",
    "SEMITONE_APPROACH":     "harmonic",
    "DIM_PASSING_ENGINE":    "harmonic",
    "DOUBLESTOP_EXPRESSIVE": "articulation",
    "CHORDAL_COLOR":         "harmonic",
    "STATIC_RIFF":           "melodic",
    "PENTATONIC_LEAD":       "melodic",
    "EXPRESSIVE_MINIMAL":    "articulation",
    "ROCK_BLUES_HYBRID":     "melodic",
}


def motive_to_exercise(m: dict) -> dict:
    archetype = m.get("archetype", "UNCLASSIFIED")
    gravity   = m.get("gravity", {})
    grav_prim = gravity.get("primary") or "front_door"

    return {
        "id":               m["id"],
        "title":            f"Blues {m['kind']} {m['num']:02d} — {archetype.replace('_', ' ').title()}",
        "style_family":     "blues",
        "technique":        ARCHETYPE_TO_TECHNIQUE.get(archetype, "melodic"),
        "harmonic_context": GRAVITY_TO_CONTEXT.get(grav_prim, "blues_major"),
        "key":              m.get("key") or "E",
        "meter":            "4/4",
        "tempo_range":      [60, 100],
        "difficulty":       (m.get("difficulty_level") or "intermediate").lower(),
        "program_ref":      f"programs/blues_motives_{m['id']}.ztprog",
        # motives-specific extensions
        "archetype":            archetype,
        "gravity":              gravity,
        "cadential_intent":     m.get("cadential_intent"),
        "articulation_model":   m.get("articulation_model"),
        "articulation_tags":    m.get("articulation_tags"),
        "kind":                 m.get("kind"),
        "num":                  m.get("num"),
        "description":          m.get("description"),
    }


def patch_blues_40_motives(path: pathlib.Path) -> dict:
    with open(path) as f:
        doc = json.load(f)

    # Already has exercises key from a previous run? Rebuild it.
    motives = doc.get("motives", [])
    if not motives:
        print("  blues_40_motives: no motives found — skipping")
        return doc

    doc["exercises"] = [motive_to_exercise(m) for m in motives]
    doc["schema_version"] = "1.1"

    print(f"  blues_40_motives: built exercises bridge for {len(motives)} motives")
    return doc


def write(path: pathlib.Path, doc: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)
    print(f"  wrote {path.name}")


def main() -> None:
    print("=== Phase C: remaining conformance fixes ===\n")

    targets = {
        "blues_canonical.json":          patch_blues,
        "gospel_canonical.json":         patch_gospel,
        "blues_40_motives_canonical.json": patch_blues_40_motives,
    }

    for fname, patcher in targets.items():
        path = CORPUS / fname
        if not path.exists():
            print(f"  SKIP: {fname} not found")
            continue
        write(path, patcher(path))
        print()

    print("Phase C complete.")


if __name__ == "__main__":
    main()
