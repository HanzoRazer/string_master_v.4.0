#!/usr/bin/env python3
# scripts/ci/check_e2e_vectors_complete.py
"""
CI gate: Verify all e2e vectors have required files.

Exit codes:
  0 = All vectors complete
  1 = Missing files detected
  2 = Infrastructure error (missing root, etc.)
"""
from __future__ import annotations

from pathlib import Path

REQUIRED = ["intent.json", "events.json", "expected.json", "meta.json"]


def main() -> int:
    root = Path(__file__).resolve().parents[2] / "fixtures" / "golden" / "e2e_vectors"
    if not root.exists():
        print(f"[e2e-vectors] FAIL: missing root: {root}")
        return 2

    vec_dirs = sorted([p for p in root.iterdir() if p.is_dir() and p.name.startswith("vector_")])
    if not vec_dirs:
        print(f"[e2e-vectors] FAIL: no vector_* dirs under {root}")
        return 2

    failures = []
    for vd in vec_dirs:
        missing = [f for f in REQUIRED if not (vd / f).exists()]
        if missing:
            failures.append((vd.name, missing))

    if failures:
        print("[e2e-vectors] FAIL:")
        for name, miss in failures:
            print(f" - {name}: missing {miss}")
        return 1

    print(f"[e2e-vectors] PASS: {len(vec_dirs)} vector(s) complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
