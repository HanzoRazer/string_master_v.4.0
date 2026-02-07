#!/usr/bin/env python3
"""Receipt canonicalization and normalization for deterministic diffs.

Phase 11.7.6 — Makes policy receipts stable and comparable across runs by:
- Canonical JSON formatting (sorted keys, stable indentation)
- Normalized timestamps (moved to runtime block)
- Stable list ordering (attestations, reasons)
- Content hashing for drift detection
"""
from __future__ import annotations
import hashlib
import json
from typing import Any, Dict, List

VOLATILE_PATHS = [
    # Runtime fields that vary per run (moved to runtime block)
    ("gh", "run_id"),
    ("gh", "run_attempt"),
    ("download", "download_dir"),
    ("download", "downloaded_count"),
    ("generated_at_utc",),
    ("result", "evaluated_at_utc"),
]

def _delete_path(obj: Dict[str, Any], path: tuple[str, ...]) -> None:
    """Delete nested key from dict if it exists."""
    cur: Any = obj
    for k in path[:-1]:
        if not isinstance(cur, dict) or k not in cur:
            return
        cur = cur[k]
    if isinstance(cur, dict):
        cur.pop(path[-1], None)

def _get_path(obj: Dict[str, Any], path: tuple[str, ...]) -> Any:
    """Get nested value from dict."""
    cur: Any = obj
    for k in path:
        if not isinstance(cur, dict) or k not in cur:
            return None
        cur = cur[k]
    return cur

def canonical_dumps(obj: Any) -> str:
    """Canonical JSON: sorted keys, stable separators, fixed indentation.
    
    ensure_ascii=False so diffs aren't polluted by escapes.
    Trailing newline for proper file format.
    """
    return json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False) + "\n"

def stable_hash(obj: Any) -> str:
    """Compute SHA256 hash of canonical JSON for drift detection."""
    s = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def normalize_receipt(receipt: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize receipt for deterministic diffs.
    
    Returns canonical receipt (diffable) after:
    - Dropping volatile runtime fields
    - Normalizing paths to basenames
    - Sorting attestations and reasons
    - Computing policy hash
    """
    r = json.loads(json.dumps(receipt))  # deep copy

    # Extract volatile fields into runtime block (before deletion)
    runtime: Dict[str, Any] = {}
    for p in VOLATILE_PATHS:
        val = _get_path(r, p)
        if val is not None:
            # Use dotted path as key
            runtime[".".join(p)] = val

    # Drop volatile paths from canonical receipt
    for p in VOLATILE_PATHS:
        _delete_path(r, p)

    # Normalize subject path to basename only (avoid machine-specific paths)
    subj = r.get("subject", {})
    if isinstance(subj, dict) and "path" in subj and isinstance(subj["path"], str):
        subj["path"] = subj["path"].split("/")[-1].split("\\")[-1]  # handle both separators

    # Normalize attestation_file paths to basenames
    atts = r.get("attestations", [])
    if isinstance(atts, list):
        for a in atts:
            if isinstance(a, dict):
                af = a.get("attestation_file")
                if isinstance(af, str):
                    a["attestation_file"] = af.split("/")[-1].split("\\")[-1]
                
                # Sort extracted fields for stability
                extracted = a.get("extracted", {})
                if isinstance(extracted, dict):
                    a["extracted"] = dict(sorted(extracted.items()))

        # Sort attestations by stable key: (predicateType, subject sha, configSource uri, workflow path)
        def att_sort_key(a: Dict[str, Any]) -> tuple:
            pred = a.get("predicateType", "")
            subj_dig = a.get("extracted", {}).get("subject_digest", {})
            subj_sha = subj_dig.get("sha256", "") if isinstance(subj_dig, dict) else ""
            cs_uri = a.get("extracted", {}).get("configSource_uri", "")
            wf = a.get("extracted", {}).get("workflow_path", "")
            return (pred, subj_sha, cs_uri, wf)
        
        r["attestations"] = sorted(atts, key=att_sort_key)

    # Sort reasons for stability
    result = r.get("result", {})
    if isinstance(result, dict):
        reasons = result.get("reasons", [])
        if isinstance(reasons, list):
            result["reasons"] = sorted(reasons)

    # Compute policy content hash for drift detection
    policy = r.get("policy", {})
    if isinstance(policy, dict):
        policy["policy_content_hash"] = stable_hash(policy.get("expanded_allowlists", {}))

    # Add runtime block (separated for optional diff exclusion)
    r["runtime"] = runtime

    # Add canonical version marker
    r["canonical_version"] = "11.7.6"

    return r

def split_receipt(receipt: Dict[str, Any]) -> tuple[Dict[str, Any], Dict[str, Any]]:
    """Split receipt into canonical (diffable) and runtime (volatile) parts.
    
    Returns:
        (canonical_receipt, runtime_receipt)
    """
    canonical = normalize_receipt(receipt)
    runtime_block = canonical.pop("runtime", {})
    
    # Build standalone runtime receipt
    runtime_receipt = {
        "kind": "SmartGuitarAttestationPolicyReceiptRuntime",
        "canonical_hash": stable_hash(canonical),
        "runtime": runtime_block,
    }
    
    return canonical, runtime_receipt

def main() -> int:
    """CLI: Normalize receipt JSON from stdin or file."""
    import sys
    import argparse
    
    ap = argparse.ArgumentParser(description="Normalize policy receipt for deterministic diffs")
    ap.add_argument("--in", dest="input", help="Input receipt file (default: stdin)")
    ap.add_argument("--out", help="Output canonical receipt file (default: stdout)")
    ap.add_argument("--split", action="store_true", help="Split into canonical + runtime files")
    ap.add_argument("--runtime-out", help="Output runtime receipt file (requires --split)")
    args = ap.parse_args()
    
    # Read input
    if args.input:
        with open(args.input, "r", encoding="utf-8") as f:
            receipt = json.load(f)
    else:
        receipt = json.load(sys.stdin)
    
    # Normalize or split
    if args.split:
        canonical, runtime = split_receipt(receipt)
        
        # Write canonical
        if args.out:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(canonical_dumps(canonical))
        else:
            sys.stdout.write(canonical_dumps(canonical))
        
        # Write runtime
        if args.runtime_out:
            with open(args.runtime_out, "w", encoding="utf-8") as f:
                f.write(canonical_dumps(runtime))
        else:
            sys.stderr.write("(runtime block written to stderr)\n")
            sys.stderr.write(canonical_dumps(runtime))
    else:
        canonical = normalize_receipt(receipt)
        
        # Write output
        if args.out:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(canonical_dumps(canonical))
        else:
            sys.stdout.write(canonical_dumps(canonical))
    
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
