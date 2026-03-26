#!/usr/bin/env python3
"""
patch_b_flamenco_exercises.py

Phase B corpus remediation — flamenco_canonical.json

Adds an `exercises` array in corpus-standard format alongside the existing
rich domain schema (palo_taxonomy, modes, etc.).  The file's native exercise
list already exists; this script maps its fields to the standard shape.

Field mapping:
    palo            → harmonic_context (e.g. "solea", "bulerias")
    exercise_type   → technique        ("falseta", "cadence_study", …)
    generation      → (used to infer difficulty — see table below)
    mode            → stored in extra field, not mapped to standard
    backing_track   → program_ref      (value kept, .ztprog suffix normalised)

Difficulty inference:
    generation=theory  + type=melodic_study   → "beginner"
    generation=theory  + type=cadence_cycle   → "intermediate"
    generation=groove  + type=falseta         → "intermediate"
    generation=groove  + palo=bulerias        → "advanced"  (tempo 140-240)
"""
import json
import pathlib

CORPUS = pathlib.Path(__file__).parents[2] / "data" / "corpus"

PALO_TEMPO = {
    "solea":     [60,  90],
    "bulerias":  [140, 240],
    "tangos":    [80,  130],
    "tientos":   [55,  75],
    "rumba":     [90,  140],
    "fandango":  [80,  140],
    "malaguena": [60,  100],
    "zambra":    [70,  120],
    "cross_palo":[60,  140],
}

PALO_METER = {
    "solea":     "12/8",
    "bulerias":  "12/8",
    "tangos":    "4/4",
    "tientos":   "4/4",
    "rumba":     "4/4",
    "fandango":  "3/4",
    "malaguena": "3/4",
    "zambra":    "4/4",
    "cross_palo":"4/4",
}


def infer_difficulty(ex: dict) -> str:
    palo = ex.get("palo", "")
    gen  = ex.get("generation", "")
    typ  = ex.get("exercise_type", "")

    if palo == "bulerias":
        return "advanced"
    if gen == "theory":
        return "beginner" if typ == "melodic_study" else "intermediate"
    if gen == "groove" and typ == "falseta":
        return "intermediate"
    if typ in ("cadence_study", "cadence_cycle"):
        return "intermediate"
    return "intermediate"


def normalise_program_ref(raw: str) -> str:
    """Ensure value ends in .ztprog, strip double extension if already present."""
    if not raw:
        return raw
    if raw.endswith(".ztprog"):
        return f"programs/{raw}"
    return f"programs/{raw}.ztprog"


def to_standard_exercise(ex: dict) -> dict:
    """Map flamenco-native exercise fields to corpus-standard shape."""
    palo = ex.get("palo", "cross_palo")
    backing = ex.get("backing_track", "")

    return {
        "id":               ex["id"],
        "title":            ex.get("title", ex["id"].replace("_", " ").title()),
        "style_family":     "flamenco",
        "technique":        ex.get("exercise_type", "falseta"),
        "harmonic_context": palo,
        "key":              ex.get("key", "E_phrygian"),
        "meter":            ex.get("meter", PALO_METER.get(palo, "4/4")),
        "tempo_range":      ex.get("tempo_range", PALO_TEMPO.get(palo, [60, 140])),
        "difficulty":       infer_difficulty(ex),
        "program_ref":      normalise_program_ref(backing),
        # flamenco-specific extensions (pass-through for consumers that know them)
        "palo":             palo,
        "mode":             ex.get("mode"),
        "generation":       ex.get("generation"),
        "bars":             ex.get("bars"),
        "focus":            ex.get("focus"),
    }


def main() -> None:
    print("=== Phase B1: flamenco exercises surface ===\n")

    path = CORPUS / "flamenco_canonical.json"
    if not path.exists():
        print(f"  SKIP: {path.name} not found")
        return

    with open(path) as f:
        doc = json.load(f)

    native = doc.get("exercises", [])
    if not native:
        print("  WARNING: no native exercises found — nothing to map")
        return

    standard = [to_standard_exercise(ex) for ex in native]

    # Replace the native exercises list with the corpus-standard mapped version.
    # The rich domain metadata (palo_taxonomy, modes, backing_tracks) is preserved.
    doc["exercises"] = standard
    doc["schema_version"] = "1.1"

    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)

    print(f"  wrote {len(standard)} standard exercises to {path.name}")
    print("\nPhase B1 complete.")


if __name__ == "__main__":
    main()
