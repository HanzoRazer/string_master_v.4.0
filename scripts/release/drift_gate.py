#!/usr/bin/env python3
"""
drift_gate.py

Compares two canonical receipts and fails if protected fields drift.
Used as a release gate.

Usage:
  python scripts/release/drift_gate.py \
    --old old.canonical.json \
    --new new.canonical.json \
    --policy scripts/release/drift_gate_policy.json

Override:
  set env DRIFT_OVERRIDE=1 (or pass --override) to allow drift but print a report.
"""

from __future__ import annotations
from pathlib import Path
import argparse
import json
import os
import re
from typing import Any, Dict, List, Tuple, Set


def load(p: Path) -> Dict[str, Any]:
    return json.loads(p.read_text(encoding="utf-8", errors="replace"))


def flatten(obj: Any, prefix: str = "") -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{prefix}.{k}" if prefix else k
            out.update(flatten(v, p))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            p = f"{prefix}.{i}" if prefix else str(i)
            out.update(flatten(v, p))
    else:
        out[prefix] = obj
    return out


def differs(a: Any, b: Any) -> bool:
    return a != b


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--old", required=True)
    ap.add_argument("--new", required=True)
    ap.add_argument("--policy", required=True)
    ap.add_argument("--override", action="store_true")
    args = ap.parse_args()

    override = args.override or (os.environ.get("DRIFT_OVERRIDE", "").strip() not in ("", "0", "false", "False"))
    old = load(Path(args.old))
    new = load(Path(args.new))
    pol = load(Path(args.policy))

    protected: List[str] = pol.get("protected", [])
    protected_regex: List[str] = pol.get("protected_regex", [])
    fail_on_fp = bool(pol.get("fail_on_policy_fingerprint_change", True))

    old_flat = flatten(old)
    new_flat = flatten(new)

    all_keys = sorted(set(old_flat.keys()) | set(new_flat.keys()))

    # Compute drift set
    drift: List[Tuple[str, Any, Any]] = []
    for k in all_keys:
        if differs(old_flat.get(k, "__MISSING__"), new_flat.get(k, "__MISSING__")):
            drift.append((k, old_flat.get(k, "__MISSING__"), new_flat.get(k, "__MISSING__")))

    # Determine if any drift is protected
    protected_set: Set[str] = set(protected)
    protected_re = [re.compile(r) for r in protected_regex]

    protected_drift: List[Tuple[str, Any, Any]] = []
    for k, a, b in drift:
        if k in protected_set:
            protected_drift.append((k, a, b))
            continue
        if any(rx.match(k) for rx in protected_re):
            protected_drift.append((k, a, b))
            continue

    # Special: policy fingerprint change
    old_fp = old.get("fingerprints", {}).get("policy_fingerprint_sha256", "")
    new_fp = new.get("fingerprints", {}).get("policy_fingerprint_sha256", "")
    fp_changed = (old_fp != new_fp)

    if fp_changed and fail_on_fp:
        protected_drift.append(("fingerprints.policy_fingerprint_sha256", old_fp, new_fp))

    # Report
    print("=== Drift Gate Report ===")
    print(f"old: {args.old}")
    print(f"new: {args.new}")
    print(f"override: {override}")
    print(f"total_drift_keys: {len(drift)}")
    print(f"protected_drift_keys: {len(protected_drift)}")
    print()

    if protected_drift:
        print("PROTECTED DRIFT:")
        for k, a, b in protected_drift:
            # Avoid giant prints
            a_s = str(a)
            b_s = str(b)
            if len(a_s) > 400:
                a_s = a_s[:400] + "...(truncated)"
            if len(b_s) > 400:
                b_s = b_s[:400] + "...(truncated)"
            print(f"- {k}: {a_s} -> {b_s}")
        print()

    # Non-protected drift (optional output)
    non_prot = [x for x in drift if x not in protected_drift]
    if non_prot:
        print("NON-PROTECTED DRIFT (info):")
        for k, a, b in non_prot[:50]:
            print(f"- {k}")
        if len(non_prot) > 50:
            print(f"... and {len(non_prot)-50} more")
        print()

    if protected_drift and not override:
        print("DRIFT GATE: FAIL (protected drift detected; set DRIFT_OVERRIDE=1 to bypass)")
        return 1

    if protected_drift and override:
        print("DRIFT GATE: OVERRIDDEN (protected drift detected but override enabled)")
        return 0

    print("DRIFT GATE: PASS (no protected drift)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
