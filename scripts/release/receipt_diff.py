#!/usr/bin/env python3
"""Diff tool for policy receipts to detect policy drift.

Phase 11.7.6 — Compare canonical receipts across tags to detect:
- Policy allowlist changes
- Attestation format drift
- Workflow/runner environment changes
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

try:
    from receipt_canonicalize import normalize_receipt, canonical_dumps, stable_hash
except ImportError:
    # Allow running from scripts/release directory
    sys.path.insert(0, str(Path(__file__).parent))
    from receipt_canonicalize import normalize_receipt, canonical_dumps, stable_hash


def deep_diff(a: Any, b: Any, path: str = "") -> List[str]:
    """Recursive diff of two JSON structures.
    
    Returns list of human-readable differences.
    """
    diffs: List[str] = []
    
    if type(a) != type(b):
        diffs.append(f"{path}: type mismatch ({type(a).__name__} vs {type(b).__name__})")
        return diffs
    
    if isinstance(a, dict):
        all_keys = set(a.keys()) | set(b.keys())
        for k in sorted(all_keys):
            new_path = f"{path}.{k}" if path else k
            if k not in a:
                diffs.append(f"{new_path}: added in right")
            elif k not in b:
                diffs.append(f"{new_path}: removed in right")
            else:
                diffs.extend(deep_diff(a[k], b[k], new_path))
    
    elif isinstance(a, list):
        if len(a) != len(b):
            diffs.append(f"{path}: list length changed ({len(a)} vs {len(b)})")
        for i, (av, bv) in enumerate(zip(a, b)):
            diffs.extend(deep_diff(av, bv, f"{path}[{i}]"))
    
    else:
        if a != b:
            diffs.append(f"{path}: {repr(a)} → {repr(b)}")
    
    return diffs


def compare_receipts(left: Dict[str, Any], right: Dict[str, Any]) -> Dict[str, Any]:
    """Compare two receipts and return structured diff report."""
    
    # Normalize both receipts
    left_norm = normalize_receipt(left)
    right_norm = normalize_receipt(right)
    
    # Compute hashes
    left_hash = stable_hash(left_norm)
    right_hash = stable_hash(right_norm)
    
    # Policy hash comparison
    left_policy_hash = left_norm.get("policy", {}).get("policy_content_hash", "")
    right_policy_hash = right_norm.get("policy", {}).get("policy_content_hash", "")
    
    # Deep diff
    diffs = deep_diff(left_norm, right_norm)
    
    # Categorize diffs
    policy_diffs = [d for d in diffs if d.startswith("policy.")]
    attestation_diffs = [d for d in diffs if d.startswith("attestations.")]
    result_diffs = [d for d in diffs if d.startswith("result.")]
    other_diffs = [d for d in diffs if not any(d.startswith(p) for p in ["policy.", "attestations.", "result."])]
    
    return {
        "identical": left_hash == right_hash,
        "left_hash": left_hash,
        "right_hash": right_hash,
        "policy_drifted": left_policy_hash != right_policy_hash,
        "left_policy_hash": left_policy_hash,
        "right_policy_hash": right_policy_hash,
        "diff_summary": {
            "total_diffs": len(diffs),
            "policy_diffs": len(policy_diffs),
            "attestation_diffs": len(attestation_diffs),
            "result_diffs": len(result_diffs),
            "other_diffs": len(other_diffs),
        },
        "diffs": {
            "policy": policy_diffs,
            "attestations": attestation_diffs,
            "result": result_diffs,
            "other": other_diffs,
        },
    }


def main() -> int:
    """CLI: Compare two policy receipts."""
    import argparse
    
    ap = argparse.ArgumentParser(description="Compare policy receipts to detect drift")
    ap.add_argument("left", help="Left receipt file (baseline)")
    ap.add_argument("right", help="Right receipt file (comparison)")
    ap.add_argument("--json", action="store_true", help="Output JSON report")
    ap.add_argument("--fail-on-policy-drift", action="store_true", 
                    help="Exit 1 if policy allowlists changed")
    ap.add_argument("--fail-on-any-diff", action="store_true",
                    help="Exit 1 if any difference detected")
    args = ap.parse_args()
    
    # Load receipts
    with open(args.left, "r", encoding="utf-8") as f:
        left = json.load(f)
    with open(args.right, "r", encoding="utf-8") as f:
        right = json.load(f)
    
    # Compare
    report = compare_receipts(left, right)
    
    # Output
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        # Human-readable report
        print(f"Receipt Diff Report")
        print(f"{'='*60}")
        print(f"Left:  {args.left}")
        print(f"Right: {args.right}")
        print()
        
        if report["identical"]:
            print("✓ Receipts are identical (canonical)")
        else:
            print(f"✗ Receipts differ ({report['diff_summary']['total_diffs']} differences)")
            print()
            
            if report["policy_drifted"]:
                print("⚠ POLICY DRIFT DETECTED")
                print(f"  Left policy hash:  {report['left_policy_hash'][:16]}...")
                print(f"  Right policy hash: {report['right_policy_hash'][:16]}...")
                print()
            
            # Show categorized diffs
            for category, diffs in report["diffs"].items():
                if diffs:
                    print(f"{category.upper()} ({len(diffs)} diffs):")
                    for d in diffs[:20]:  # limit output
                        print(f"  - {d}")
                    if len(diffs) > 20:
                        print(f"  ... ({len(diffs) - 20} more)")
                    print()
    
    # Exit codes
    if args.fail_on_any_diff and not report["identical"]:
        return 1
    if args.fail_on_policy_drift and report["policy_drifted"]:
        return 1
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
