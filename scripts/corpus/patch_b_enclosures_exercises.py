#!/usr/bin/env python3
"""
patch_b_enclosures_exercises.py

Phase B corpus remediation — enclosures_canonical.json

Adds corpus-standard fields to each exercise. The file's exercises are already
well-structured; they just use different field names and are missing
style_family, technique (in the standard sense), harmonic_context, difficulty,
and program_ref.

Field mapping:
    enclosure_type  → technique       (the primary learning object)
    chord_context   → harmonic_context
    difficulty_tier → difficulty      (mapped via tier table below)
    tempo_bpm       → (scalar, kept as extension; tempo_range already present)
    chords          → kept as extension
    target_note     → kept as extension
    focus           → kept as extension

Difficulty tier → standard difficulty:
    foundations   → "beginner"
    chord_quality → "intermediate"
    progressions  → "intermediate"
    advanced      → "advanced"
"""
import json
import pathlib

CORPUS = pathlib.Path(__file__).parents[2] / "data" / "corpus"

TIER_TO_DIFFICULTY = {
    "foundations":   "beginner",
    "chord_quality": "intermediate",
    "progressions":  "intermediate",
    "advanced":      "advanced",
}

# program_ref is inferred from id — actual .ztprog files to be authored separately
def infer_program_ref(ex_id: str) -> str:
    return f"programs/enclosures_{ex_id}.ztprog"


def to_standard_exercise(ex: dict) -> dict:
    tier       = ex.get("difficulty_tier", "foundations")
    ctx        = ex.get("chord_context", "major")
    enc_type   = ex.get("enclosure_type", "chromatic")

    return {
        "id":               ex["id"],
        "title":            ex.get("title", ex["id"].replace("_", " ").title()),
        "style_family":     "jazz",
        "technique":        enc_type,
        "harmonic_context": ctx,
        "key":              ex.get("key", "C"),
        "meter":            ex.get("meter", "4/4"),
        "tempo_range":      ex.get("tempo_range", [48, 110]),
        "difficulty":       TIER_TO_DIFFICULTY.get(tier, "intermediate"),
        "program_ref":      infer_program_ref(ex["id"]),
        # enclosure-specific extensions
        "enclosure_type":   enc_type,
        "difficulty_tier":  tier,
        "target_note":      ex.get("target_note"),
        "target_pitch":     ex.get("target_pitch"),
        "chords":           ex.get("chords"),
        "loop_bars":        ex.get("loop_bars"),
        "tempo_bpm":        ex.get("tempo_bpm"),
        "focus":            ex.get("focus"),
    }


def main() -> None:
    print("=== Phase B2: enclosures exercises surface ===\n")

    path = CORPUS / "enclosures_canonical.json"
    if not path.exists():
        print(f"  SKIP: {path.name} not found")
        return

    with open(path) as f:
        doc = json.load(f)

    native = doc.get("exercises", [])
    if not native:
        print("  WARNING: no exercises found")
        return

    standard = [to_standard_exercise(ex) for ex in native]
    doc["exercises"] = standard
    doc["schema_version"] = "1.1"

    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)

    print(f"  wrote {len(standard)} standard exercises to {path.name}")
    print("\nPhase B2 complete.")


if __name__ == "__main__":
    main()
