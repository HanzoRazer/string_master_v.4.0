#!/usr/bin/env python3
"""
receipt_canonicalize.py

Deterministic receipt support:
- normalize_receipt(): remove/normalize volatile fields and stabilize ordering
- canonical_dumps(): stable JSON formatting (sorted keys)
- stable_hash(): deterministic content hash for policy drift detection
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Tuple


# Paths in the receipt that are inherently run-specific and not diff-friendly.
# We remove these from the canonical receipt.
VOLATILE_PATHS: List[Tuple[str, ...]] = [
    ("generated_at_utc",),
    ("download", "download_dir"),
    ("download", "downloaded_count"),
    ("gh", "run_id"),
    ("gh", "run_attempt"),
    ("gh", "workflow"),
    ("gh", "server_url"),
]

# Keys that frequently contain machine-specific file paths; canonicalize to basenames.
PATH_KEYS = [
    ("subject", "path"),
]


def _deepcopy(obj: Any) -> Any:
    return json.loads(json.dumps(obj))


def _delete_path(obj: Dict[str, Any], path: Tuple[str, ...]) -> None:
    cur: Any = obj
    for k in path[:-1]:
        if not isinstance(cur, dict) or k not in cur:
            return
        cur = cur[k]
    if isinstance(cur, dict):
        cur.pop(path[-1], None)


def _basename(p: str) -> str:
    p = p.replace("\\", "/")
    return p.split("/")[-1]


def canonical_dumps(obj: Any) -> str:
    # Stable key order, stable indentation; UTF-8-friendly.
    return json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def stable_hash(obj: Any) -> str:
    # Deterministic hash of canonicalized JSON without whitespace.
    s = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _sort_reasons(receipt: Dict[str, Any]) -> None:
    res = receipt.get("result")
    if isinstance(res, dict):
        reasons = res.get("reasons")
        if isinstance(reasons, list):
            res["reasons"] = sorted([str(x) for x in reasons])


def _sort_attestations(receipt: Dict[str, Any]) -> None:
    atts = receipt.get("attestations")
    if not isinstance(atts, list):
        return

    def key_fn(a: Any) -> Tuple[str, str, str, str]:
        if not isinstance(a, dict):
            return ("", "", "", "")
        pred = str(a.get("predicateType", ""))
        subj = a.get("extracted", {}).get("subject_digest", {}) if isinstance(a.get("extracted"), dict) else {}
        subj_sha = ""
        if isinstance(subj, dict):
            subj_sha = str(subj.get("sha256") or subj.get("SHA256") or "")
        cs_uri = ""
        extracted = a.get("extracted")
        if isinstance(extracted, dict):
            cs_uri = str(extracted.get("configSource_uri", ""))
        wf = ""
        if isinstance(extracted, dict):
            wf = str(extracted.get("workflow_path", ""))
        return (pred, subj_sha, cs_uri, wf)

    receipt["attestations"] = sorted(atts, key=key_fn)


def _normalize_paths(receipt: Dict[str, Any]) -> None:
    # Subject path
    subj = receipt.get("subject")
    if isinstance(subj, dict):
        p = subj.get("path")
        if isinstance(p, str):
            subj["path"] = _basename(p)

    # Attestation file fields
    atts = receipt.get("attestations")
    if isinstance(atts, list):
        for a in atts:
            if isinstance(a, dict):
                af = a.get("attestation_file")
                if isinstance(af, str):
                    a["attestation_file"] = _basename(af)


def policy_fingerprint(receipt: Dict[str, Any]) -> str:
    """
    Fingerprint *policy inputs* rather than runtime results.
    This is the main drift detector key.

    Includes:
      - profile
      - expanded_allowlists
      - required_attestation_types
      - schema_file name (basename)
      - policy_file name (basename)
    """
    pol = receipt.get("policy", {})
    profile = str(receipt.get("profile", ""))
    allow = pol.get("expanded_allowlists", {})
    req_types = pol.get("required_attestation_types", [])
    schema_file = str(pol.get("schema_file", ""))
    policy_file = str(pol.get("policy_file", ""))

    core = {
        "profile": profile,
        "expanded_allowlists": allow,
        "required_attestation_types": req_types,
        "schema_file": _basename(schema_file),
        "policy_file": _basename(policy_file),
    }
    return stable_hash(core)


def normalize_receipt(runtime_receipt: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a runtime receipt into a deterministic, diff-friendly canonical receipt.
    """
    r: Dict[str, Any] = _deepcopy(runtime_receipt)

    # Remove volatile runtime keys
    for p in VOLATILE_PATHS:
        _delete_path(r, p)

    # Normalize selected paths
    for p in PATH_KEYS:
        # already handled by _normalize_paths
        pass
    _normalize_paths(r)

    # Normalize ordering
    _sort_reasons(r)
    _sort_attestations(r)

    # Add fingerprints (deterministic)
    r.setdefault("fingerprints", {})
    fps = r["fingerprints"]
    if isinstance(fps, dict):
        fps["policy_fingerprint_sha256"] = policy_fingerprint(r)
        fps["receipt_canonical_sha256"] = stable_hash(r)

    return r
