"""
v1.0 Golden Update Guard: Controlled fixture regeneration.

Default behavior: goldens are immutable → replay mismatch fails and prints regeneration command.
Explicit behavior: --update-golden (or env var) → writes assignment_v0_6.json fixtures.

Usage:
    # Strict gate (no writes)
    python -m sg_coach.golden_update_v1_0 fixtures/golden --seed 123

    # Regenerate (explicit)
    python -m sg_coach.golden_update_v1_0 fixtures/golden --seed 123 --update-golden

    # Alternate explicit unlock
    SG_COACH_UPDATE_GOLDEN=1 python -m sg_coach.golden_update_v1_0 fixtures/golden --seed 123
"""
from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from .replay_gate_v0_8 import replay_vector_dir
from .replay_utils_v0_9 import normalize_assignment_for_compare


@dataclass
class GoldenUpdateResultV1_0:
    """Result of golden update operation."""

    ok: bool
    updated: int
    total: int
    failures: List[str]


def _load_json(p: Path) -> Dict[str, Any]:
    return json.loads(p.read_text(encoding="utf-8"))


def _write_json(p: Path, data: Dict[str, Any]) -> None:
    p.write_text(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _vector_dirs(golden_root: Path) -> List[Path]:
    return sorted([p for p in golden_root.iterdir() if p.is_dir() and p.name.startswith("vector_")])


def _produce_assignment_json(vector_dir: Path, *, seed: int | None) -> Optional[Dict[str, Any]]:
    """
    Runs replay once and returns the produced assignment JSON (normalized for deterministic compare).
    Requires existing expected fixture to normalize created_at_utc if present.
    
    Returns None if the vector doesn't have required fixtures to produce an assignment.
    """
    expected_path = vector_dir / "assignment_v0_6.json"
    expected = _load_json(expected_path) if expected_path.exists() else {}

    res = replay_vector_dir(vector_dir, db_path=":memory:", seed=seed, print_diff_on_fail=False)

    # replay_vector_dir returns ReplayDiffV0_9; on mismatch it contains produced/expected.
    if res.ok:
        # When OK, res doesn't include produced; we re-run mismatch-producing path by forcing expected empty is messy.
        # Instead: use the already-defined invariant: produced matches expected; just load expected.
        # This still supports "refresh formatting" if needed by rewrite.
        produced_norm = normalize_assignment_for_compare(expected, expected, seed=seed)
        return produced_norm

    if res.produced is None:
        # Missing required fixtures (e.g., evaluation.json, feedback.json) - skip this vector
        return None

    # If expected didn't exist, res.expected will be None; just use produced as-is.
    prod = res.produced
    if expected:
        prod = normalize_assignment_for_compare(prod, expected, seed=seed)
    return prod


def update_goldens(
    golden_root: Path,
    *,
    seed: int | None = None,
    allow_update: bool = False,
) -> GoldenUpdateResultV1_0:
    """
    Golden update guard:
      - If allow_update=False: never writes. Reports mismatches and prints regeneration command.
      - If allow_update=True: writes/overwrites assignment_v0_6.json for any failing vector.

    Note:
      This generator only updates assignment fixtures (v1.0 scope).
    """
    vecs = _vector_dirs(golden_root)
    failures: List[str] = []
    updated = 0

    for vd in vecs:
        res = replay_vector_dir(vd, db_path=":memory:", seed=seed, print_diff_on_fail=False)
        if res.ok:
            continue

        failures.append(vd.name)
        if not allow_update:
            continue

        # Generate produced assignment JSON and write expected fixture
        produced = _produce_assignment_json(vd, seed=seed)
        if produced is None:
            # Missing required fixtures - can't update this vector
            continue
        _write_json(vd / "assignment_v0_6.json", produced)
        updated += 1

    ok = (len(failures) == 0) or allow_update
    return GoldenUpdateResultV1_0(ok=ok, updated=updated, total=len(vecs), failures=failures)


def main() -> int:
    """CLI entrypoint for golden update guard."""
    ap = argparse.ArgumentParser(
        prog="golden_update_v1_0",
        description="Golden fixture update guard with explicit regeneration control",
    )
    ap.add_argument("golden_root", help="Path to fixtures/golden (contains vector_* dirs)")
    ap.add_argument("--seed", type=int, default=None, help="Seed for deterministic timestamps (optional)")
    ap.add_argument(
        "--update-golden",
        action="store_true",
        help="WRITE updated golden fixtures (assignment_v0_6.json). Guarded by policy.",
    )
    args = ap.parse_args()

    # Two-key guard: flag OR env var (useful in local dev)
    env_ok = os.getenv("SG_COACH_UPDATE_GOLDEN", "").strip().lower() in ("1", "true", "yes")
    allow_update = bool(args.update_golden or env_ok)

    res = update_goldens(Path(args.golden_root), seed=args.seed, allow_update=allow_update)

    if res.ok and res.updated == 0 and not res.failures:
        print(f"[golden] PASS ({res.total}/{res.total})")
        return 0

    if not allow_update:
        print(f"[golden] FAIL: {len(res.failures)} vector(s) mismatched: {res.failures}")
        print(
            "[golden] To regenerate fixtures locally:\n"
            f"  python -m sg_coach.golden_update_v1_0 {args.golden_root} --seed {args.seed or 123} --update-golden\n"
            "  (or set SG_COACH_UPDATE_GOLDEN=1)\n"
        )
        return 1

    print(f"[golden] UPDATED {res.updated} fixture(s); mismatched vectors were: {res.failures}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "GoldenUpdateResultV1_0",
    "update_goldens",
    "main",
]
