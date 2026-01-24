"""
v0.8 Replay Gate: Deterministic replay for golden vector directories.

Provides:
- replay_vector_dir(): Replay a golden vector and assert match
- CLI entrypoint for local replay testing

Usage:
    python -m sg_coach.replay_gate_v0_8 fixtures/golden/vector_006 --db :memory:
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from .evaluation_v0_3 import CoachFeedbackV0, EvaluationV0_3
from .sqlite_store_v0_8 import SQLiteCoachStoreV0_8, SqliteStoreConfigV0_8


@dataclass
class ReplayResultV0_8:
    """Result of a replay operation."""

    ok: bool
    message: str


def _load_json(p: Path) -> Dict[str, Any]:
    return json.loads(p.read_text(encoding="utf-8"))


def _normalize_assignment_for_compare(
    prod: Dict[str, Any], expected: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Golden fixtures often include a fixed created_at_utc.
    Normalize timestamps so equality checks are deterministic.
    """
    prod = dict(prod)
    if "created_at_utc" in expected:
        prod["created_at_utc"] = expected["created_at_utc"]
    return prod


def replay_vector_dir(vector_dir: Path, db_path: str = ":memory:") -> ReplayResultV0_8:
    """
    Replay contract:
      vector_dir contains:
        - evaluation.json
        - feedback.json
        - history_assignments.json   (optional)
        - history_evaluations.json   (optional)
        - assignment_v0_6.json       (expected)

    Behavior:
      - seed sqlite store with history (if present)
      - run next_assignment once
      - compare produced assignment to expected fixture
    """
    required = ["evaluation.json", "feedback.json", "assignment_v0_6.json"]
    for name in required:
        if not (vector_dir / name).exists():
            return ReplayResultV0_8(False, f"Missing required fixture: {name}")

    store = SQLiteCoachStoreV0_8(SqliteStoreConfigV0_8(db_path=db_path))

    try:
        ev = EvaluationV0_3.model_validate(_load_json(vector_dir / "evaluation.json"))
        fb = CoachFeedbackV0.model_validate(_load_json(vector_dir / "feedback.json"))

        # Seed session
        store.get_or_create_session(ev.session_id, ev.instrument_id)

        # Seed history (optional)
        ha = vector_dir / "history_assignments.json"
        if ha.exists():
            history = _load_json(ha)
            # Store expects v0.6 assignment objects; but we may have v0.5 seeded history.
            # We'll insert raw blobs directly into assignments table for replay purposes.
            # (Planner uses duck typing; on read we return SimpleNamespace(**blob))
            for item in history:
                # minimal insert: keep schema_version, tempo_nudge_bpm, density_cap, allow_probe, etc.
                store._conn.execute(
                    "INSERT INTO assignments(session_id, instrument_id, created_at_utc, payload_json) VALUES(?,?,?,?)",
                    (
                        ev.session_id,
                        ev.instrument_id,
                        item.get("created_at_utc"),
                        json.dumps(item, separators=(",", ":"), sort_keys=True),
                    ),
                )
            store._conn.commit()

        he = vector_dir / "history_evaluations.json"
        if he.exists():
            history_e = _load_json(he)
            for item in history_e:
                eobj = EvaluationV0_3.model_validate(item)
                store.append_evaluation(eobj)

        produced = store.next_assignment(ev, fb)
        prod_json = produced.model_dump(mode="json")

        expected = _load_json(vector_dir / "assignment_v0_6.json")
        prod_norm = _normalize_assignment_for_compare(prod_json, expected)

        if prod_norm != expected:
            return ReplayResultV0_8(
                False,
                "Replay mismatch: produced assignment != expected.\n"
                "Tip: print diff in test or inspect produced JSON.",
            )

        return ReplayResultV0_8(True, "Replay OK")

    finally:
        store.close()


def main() -> int:
    """CLI entrypoint for replay gate."""
    ap = argparse.ArgumentParser(
        prog="replay_gate_v0_8",
        description="Replay a golden vector directory and verify deterministic output",
    )
    ap.add_argument(
        "vector_dir",
        help="Path to a golden vector directory (e.g., fixtures/golden/vector_006)",
    )
    ap.add_argument(
        "--db", default=":memory:", help="SQLite db path (default: :memory:)"
    )
    args = ap.parse_args()

    res = replay_vector_dir(Path(args.vector_dir), db_path=args.db)
    if res.ok:
        print(f"[replay] PASS: {res.message}")
        return 0
    print(f"[replay] FAIL: {res.message}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "ReplayResultV0_8",
    "replay_vector_dir",
]
