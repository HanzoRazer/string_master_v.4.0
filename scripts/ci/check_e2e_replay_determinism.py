#!/usr/bin/env python3
# scripts/ci/check_e2e_replay_determinism.py
"""
CI gate: Verify all e2e vectors replay deterministically.

Runs the full intent → arranger → pattern → humanizer pipeline on each vector
and compares (after normalization) against expected.json.

Exit codes:
  0 = All vectors pass
  1 = One or more vectors failed replay
"""
from __future__ import annotations

from pathlib import Path

from zt_band.e2e.e2e_replay_gate_v1 import replay_all, ENGINE_IDENTITY


def main() -> int:
    root = Path(__file__).resolve().parents[2] / "fixtures" / "golden" / "e2e_vectors"
    res = replay_all(root, update_golden=False, changelog_path=(root / "CHANGELOG.md"), bump_changelog_reason=None)

    prefix = f"[e2e-replay][engine={ENGINE_IDENTITY}]"
    if res.ok:
        print(f"{prefix} PASS: {res.message}")
        return 0

    print(f"{prefix} FAIL: {res.message}")
    print(f"{prefix} Tip: run locally:")
    print(f"{prefix}   python -m zt_band.e2e.e2e_replay_gate_v1 fixtures/golden/e2e_vectors")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
