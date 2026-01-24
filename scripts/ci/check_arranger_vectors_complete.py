# scripts/ci/check_arranger_vectors_complete.py
"""
CI gate: ensure all arranger vector fixtures have required files.
"""
from __future__ import annotations

from pathlib import Path

REQUIRED = ["intent.json", "expected_plan.json", "meta.json"]


def main() -> int:
    root = Path(__file__).resolve().parents[2] / "fixtures" / "golden" / "arranger_vectors"
    if not root.exists():
        print(f"[arranger-vectors] FAIL: missing root: {root}")
        return 2

    vec_dirs = sorted([p for p in root.iterdir() if p.is_dir() and p.name.startswith("vector_")])
    if not vec_dirs:
        print(f"[arranger-vectors] FAIL: no vector_* dirs under {root}")
        return 2

    failures = []
    for vd in vec_dirs:
        missing = [f for f in REQUIRED if not (vd / f).exists()]
        if missing:
            failures.append((vd.name, missing))

    if failures:
        print("[arranger-vectors] FAIL:")
        for name, miss in failures:
            print(f"  - {name}: missing {miss}")
        return 1

    print(f"[arranger-vectors] PASS: {len(vec_dirs)} vector(s) complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
