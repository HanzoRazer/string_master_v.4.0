#!/usr/bin/env python3
"""
rebuild_corpus.py

Master runner — executes all corpus remediation phases in order.

Usage (from repo root):
    python scripts/corpus/rebuild_corpus.py [--phase A|B|D|all]

Default is --phase all.
"""
import argparse
import importlib.util
import pathlib
import sys

SCRIPTS = pathlib.Path(__file__).parent

PHASES = {
    "A": SCRIPTS / "patch_a_field_renames.py",
    "B1": SCRIPTS / "patch_b_flamenco_exercises.py",
    "B2": SCRIPTS / "patch_b_enclosures_exercises.py",
    "C": SCRIPTS / "patch_a_field_renames.py",   # C stubs are folded into A
    "D": SCRIPTS / "build_country_canonical.py",
}


def run_script(path: pathlib.Path) -> None:
    spec = importlib.util.spec_from_file_location("_mod", path)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if hasattr(mod, "main"):
        mod.main()


def main() -> None:
    parser = argparse.ArgumentParser(description="Rebuild corpus files")
    parser.add_argument(
        "--phase",
        default="all",
        help="Which phase(s) to run: A, B1, B2, D, or all (default: all)",
    )
    args = parser.parse_args()

    phases = (
        list(PHASES.keys())
        if args.phase.lower() == "all"
        else [p.upper() for p in args.phase.split(",")]
    )

    # Deduplicate (C is folded into A)
    seen = set()
    for phase in phases:
        if phase == "C":
            phase = "A"
        if phase in seen:
            continue
        seen.add(phase)

        script = PHASES.get(phase)
        if not script:
            print(f"Unknown phase: {phase}", file=sys.stderr)
            continue
        if not script.exists():
            print(f"Script not found: {script}", file=sys.stderr)
            continue

        print(f"\n{'='*52}")
        print(f"  Running Phase {phase}: {script.name}")
        print(f"{'='*52}")
        run_script(script)

    print("\n\nAll requested phases complete.")


if __name__ == "__main__":
    main()
