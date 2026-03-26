#!/usr/bin/env python3
"""
patch_a_field_renames.py

Phase A corpus remediation:
  - bluegrass_canonical.json:  backing_track→program_ref, style→style_family,
                                focus→technique, inject difficulty + tempo_range
  - got_rhythm_canonical.json: backing_track→program_ref, inject style_family,
                                difficulty, tempo_range

Safe to run multiple times (idempotent — skips already-renamed fields).
"""
import json
import pathlib

CORPUS = pathlib.Path(__file__).parents[2] / "data" / "corpus"


# ── Difficulty rules for bluegrass by category ──────────────────────────────
BLUEGRASS_DIFFICULTY = {
    "licks":         "beginner",
    "folk_melodies": "intermediate",
    "fiddle_tunes":  "intermediate",
    "intro_phrases": "intermediate",
}

BLUEGRASS_DIFFICULTY_OVERRIDES = {
    "blackberry_blossom_b1":  "advanced",
    "blackberry_blossom_b1a": "advanced",
    "olde_joe_clark_etude":   "intermediate",
}

# Tempo ranges by category — conservative min, idiomatic max
BLUEGRASS_TEMPO = {
    "licks":         [80, 160],
    "folk_melodies": [60, 110],
    "fiddle_tunes":  [100, 190],
    "intro_phrases": [100, 160],
}

# Got Rhythm studies — all bebop, swing feel
GOT_RHYTHM_DIFFICULTY = {
    "got_rhythm_bb7_eb7_study1":    "intermediate",
    "got_rhythm_enclosure_study2":  "intermediate",
    "got_rhythm_fm7_bb7_study3":    "advanced",
    "got_rhythm_backdoor_study4":   "advanced",
}
GOT_RHYTHM_TEMPO = [100, 220]


def patch_bluegrass(path: pathlib.Path) -> dict:
    with open(path) as f:
        doc = json.load(f)

    patched = 0
    for ex in doc.get("exercises", []):
        # backing_track → program_ref
        if "backing_track" in ex and "program_ref" not in ex:
            ex["program_ref"] = f"programs/bluegrass_{ex['backing_track']}.ztprog"
            del ex["backing_track"]
            patched += 1

        # style → style_family  (keep original style value for bluegrass/folk/traditional/old_time)
        if "style" in ex and "style_family" not in ex:
            raw = ex.pop("style")
            # Normalise everything to "bluegrass" for the corpus-standard style_family field.
            # Retain genre nuance in technique field below.
            ex["style_family"] = "bluegrass"
            ex["_style_original"] = raw   # preserve for downstream; strip before release if unwanted

        # focus → technique
        if "focus" in ex and "technique" not in ex:
            ex["technique"] = ex.pop("focus")

        # inject harmonic_context from category if absent
        if "harmonic_context" not in ex:
            cat = ex.get("category", "")
            ex["harmonic_context"] = {
                "licks":         "I_IV_V_blues",
                "folk_melodies": "diatonic_folk",
                "fiddle_tunes":  "diatonic_major",
                "intro_phrases": "I_IV_V_blues",
            }.get(cat, "diatonic_major")

        # inject difficulty
        if "difficulty" not in ex:
            cat = ex.get("category", "")
            ex["difficulty"] = BLUEGRASS_DIFFICULTY_OVERRIDES.get(
                ex["id"],
                BLUEGRASS_DIFFICULTY.get(cat, "intermediate")
            )

        # inject tempo_range
        if "tempo_range" not in ex:
            cat = ex.get("category", "")
            ex["tempo_range"] = BLUEGRASS_TEMPO.get(cat, [80, 160])

    print(f"  bluegrass: patched {patched} field renames, injected stubs where missing")
    return doc


def patch_got_rhythm(path: pathlib.Path) -> dict:
    with open(path) as f:
        doc = json.load(f)

    patched = 0
    for ex in doc.get("exercises", []):
        # backing_track → program_ref
        if "backing_track" in ex and "program_ref" not in ex:
            ex["program_ref"] = f"programs/{ex['backing_track']}.ztprog"
            del ex["backing_track"]
            patched += 1

        # inject style_family
        if "style_family" not in ex:
            ex["style_family"] = "jazz"

        # inject difficulty
        if "difficulty" not in ex:
            ex["difficulty"] = GOT_RHYTHM_DIFFICULTY.get(ex["id"], "intermediate")

        # inject tempo_range
        if "tempo_range" not in ex:
            ex["tempo_range"] = GOT_RHYTHM_TEMPO

    print(f"  got_rhythm: patched {patched} field renames, injected stubs where missing")
    return doc


def write(path: pathlib.Path, doc: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)
    print(f"  wrote {path.name}")


def main() -> None:
    print("=== Phase A: field renames + stub injection ===\n")

    bg_path = CORPUS / "bluegrass_canonical.json"
    gr_path = CORPUS / "got_rhythm_canonical.json"

    for p in [bg_path, gr_path]:
        if not p.exists():
            print(f"  SKIP: {p.name} not found")

    if bg_path.exists():
        write(bg_path, patch_bluegrass(bg_path))

    if gr_path.exists():
        write(gr_path, patch_got_rhythm(gr_path))

    print("\nPhase A complete.")


if __name__ == "__main__":
    main()
