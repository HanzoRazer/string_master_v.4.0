"""
Analyzer smoke test runner.

Runs only when SG_GROOVE_SERVICE_URL is set.
Exercises the service path of generate_intent() and validates response shape.

Usage:
    python scripts/ci/run_analyzer_smoke.py

Environment:
    SG_GROOVE_SERVICE_URL  - Required for test to run (else skips)
    SG_GROOVE_SERVICE_TOKEN - Optional bearer token
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from zt_band.groove.groove_layer_bridge import generate_intent


def _load(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser(description="Analyzer smoke test runner")
    ap.add_argument(
        "--timeout-s",
        type=float,
        default=None,
        help="Service timeout in seconds (default: 2.0)",
    )
    ap.add_argument(
        "--no-retry",
        action="store_true",
        help="Disable service retry",
    )
    ap.add_argument(
        "--retry-backoff-s",
        type=float,
        default=0.15,
        help="Base backoff before retry (default: 0.15)",
    )
    ap.add_argument(
        "--retry-jitter-s",
        type=float,
        default=0.10,
        help="Max jitter added to backoff (default: 0.10)",
    )
    args = ap.parse_args()

    base = os.environ.get("SG_GROOVE_SERVICE_URL", "").strip()
    if not base:
        print("[analyzer-smoke] SKIP: SG_GROOVE_SERVICE_URL not set")
        return 0

    root = Path(__file__).resolve().parents[2] / "fixtures" / "golden" / "analyzer_smoke" / "vector_001"
    prof = _load(root / "profile.json")
    window = _load(root / "window.json")

    # Use the same interface used by AnalyzerIntentProvider
    now = datetime.now(timezone.utc)
    intent = generate_intent(
        profile=prof,
        window=window,
        now_utc=now,
        timeout_s=args.timeout_s,
        retry=(not args.no_retry),
        retry_backoff_s=args.retry_backoff_s,
        retry_jitter_s=args.retry_jitter_s,
    )

    if not isinstance(intent, dict):
        print("[analyzer-smoke] FAIL: generate_intent returned non-dict")
        return 1

    # Minimal contract checks
    if intent.get("schema_id") != "groove_control_intent":
        print(f"[analyzer-smoke] FAIL: schema_id={intent.get('schema_id')!r}")
        return 1
    if intent.get("schema_version") != "v1":
        print(f"[analyzer-smoke] FAIL: schema_version={intent.get('schema_version')!r}")
        return 1
    if intent.get("profile_id") != prof.get("profile_id"):
        print(f"[analyzer-smoke] FAIL: profile_id mismatch: {intent.get('profile_id')!r} != {prof.get('profile_id')!r}")
        return 1

    # A couple of "must exist" fields (helps catch partial responses)
    required_fields = (
        "intent_id",
        "generated_at_utc",
        "horizon_ms",
        "control_modes",
        "tempo",
        "timing",
        "dynamics",
        "recovery",
    )
    for k in required_fields:
        if k not in intent:
            print(f"[analyzer-smoke] FAIL: missing field: {k}")
            return 1

    print("[analyzer-smoke] PASS: service generated valid GrooveControlIntentV1 shape")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
