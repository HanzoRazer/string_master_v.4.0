#!/usr/bin/env python3
"""
diff_receipts.py

Human-friendly diff for canonical receipts.
Focuses on: policy fingerprints, allowlists, and key extracted fields.
"""

from __future__ import annotations
from pathlib import Path
import json
import sys
from typing import Any, Dict, List, Tuple


def load(p: Path) -> Dict[str, Any]:
    return json.loads(p.read_text(encoding="utf-8", errors="replace"))


def jget(d: Dict[str, Any], path: List[str], default=None):
    cur: Any = d
    for k in path:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


def print_section(title: str):
    print()
    print("=" * len(title))
    print(title)
    print("=" * len(title))


def dict_diff(a: Dict[str, Any], b: Dict[str, Any], prefix="") -> List[str]:
    lines: List[str] = []
    keys = sorted(set(a.keys()) | set(b.keys()))
    for k in keys:
        pa = a.get(k, "__MISSING__")
        pb = b.get(k, "__MISSING__")
        if pa == pb:
            continue
        if isinstance(pa, dict) and isinstance(pb, dict):
            lines.extend(dict_diff(pa, pb, prefix + k + "."))
        else:
            lines.append(f"{prefix}{k}: {pa} -> {pb}")
    return lines


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python scripts/release/diff_receipts.py <old.canonical.json> <new.canonical.json>")
        return 2

    oldp = Path(sys.argv[1])
    newp = Path(sys.argv[2])
    a = load(oldp)
    b = load(newp)

    print_section("Fingerprints")
    fa = jget(a, ["fingerprints", "policy_fingerprint_sha256"], "")
    fb = jget(b, ["fingerprints", "policy_fingerprint_sha256"], "")
    print(f"policy_fingerprint: {fa} -> {fb}")
    if fa == fb:
        print("OK: policy fingerprint unchanged")
    else:
        print("DRIFT: policy fingerprint changed")

    print_section("Policy allowlists diff (expanded_allowlists)")
    allow_a = jget(a, ["policy", "expanded_allowlists"], {}) or {}
    allow_b = jget(b, ["policy", "expanded_allowlists"], {}) or {}
    if isinstance(allow_a, dict) and isinstance(allow_b, dict):
        lines = dict_diff(allow_a, allow_b)
        if not lines:
            print("OK: allowlists unchanged")
        else:
            for ln in lines:
                print(" - " + ln)

    print_section("Core identity fields")
    core_fields = [
        ("repo", ["repo"]),
        ("tag", ["tag"]),
        ("ref", ["ref"]),
        ("profile", ["profile"]),
        ("workflow_path", ["attestations", "0", "extracted", "workflow_path"]),
        ("runner_environment", ["attestations", "0", "extracted", "runner_environment"]),
        ("configSource_uri", ["attestations", "0", "extracted", "configSource_uri"]),
    ]
    for name, path in core_fields:
        # allow numeric path element
        cur_a: Any = a
        for k in path:
            if k.isdigit():
                idx = int(k)
                if isinstance(cur_a, list) and len(cur_a) > idx:
                    cur_a = cur_a[idx]
                else:
                    cur_a = ""
                    break
            else:
                if isinstance(cur_a, dict) and k in cur_a:
                    cur_a = cur_a[k]
                else:
                    cur_a = ""
                    break

        cur_b: Any = b
        for k in path:
            if k.isdigit():
                idx = int(k)
                if isinstance(cur_b, list) and len(cur_b) > idx:
                    cur_b = cur_b[idx]
                else:
                    cur_b = ""
                    break
            else:
                if isinstance(cur_b, dict) and k in cur_b:
                    cur_b = cur_b[k]
                else:
                    cur_b = ""
                    break

        if cur_a == cur_b:
            print(f"{name}: OK ({cur_a})")
        else:
            print(f"{name}: DRIFT ({cur_a} -> {cur_b})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
