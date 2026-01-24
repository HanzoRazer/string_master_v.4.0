# scripts/ci/check_arranger_replay_determinism.py
"""
CI gate: replay all arranger vectors and fail if any mismatch.
"""
from __future__ import annotations

from pathlib import Path

from zt_band.adapters.arranger_replay_gate_v1 import replay_all, ENGINE_IDENTITY


def main() -> int:
    root = Path(__file__).resolve().parents[2] / "fixtures" / "golden" / "arranger_vectors"
    changelog_path = root / "CHANGELOG.md"

    res = replay_all(
        root,
        update_golden=False,
        changelog_path=changelog_path,
        bump_changelog_reason=None,
    )

    prefix = f"[arranger-replay][engine={ENGINE_IDENTITY}]"
    if res.ok:
        print(f"{prefix} PASS: {res.message}")
        return 0

    print(f"{prefix} FAIL: {res.message}")
    print(f"{prefix} Tip: run locally:")
    print(f"{prefix}   python -m zt_band.adapters.arranger_replay_gate_v1 fixtures/golden/arranger_vectors")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
