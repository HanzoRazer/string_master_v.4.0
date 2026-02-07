#!/usr/bin/env python3
"""
Full attestation policy engine:
- Download GitHub attestation(s) for a subject file via gh CLI
- Validate against a local JSON Schema (subset)
- Enforce allowlists (repo, workflow path, ref/tag, runner env, source uri)
- Hard fail on any violation

Usage:
  python scripts/release/attestation_policy_engine.py \
    --subject dist/Lab_Pack_SG_*.zip \
    --repo OWNER/REPO \
    --tag v1.2.3 \
    --policy scripts/release/attestation_policy.json \
    --schema scripts/release/attestation_schema_min.json \
    --profile lab_pack_zip

Profiles:
  - lab_pack_zip
  - verifiers
"""

from __future__ import annotations
from pathlib import Path
import argparse
import json
import os
import re
import subprocess
import sys
import hashlib
from typing import Any

def run(cmd: list[str], *, cwd: Path | None = None) -> str:
    p = subprocess.run(cmd, cwd=str(cwd) if cwd else None, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"Command failed ({p.returncode}): {' '.join(cmd)}\nSTDERR:\n{p.stderr.strip()}")
    return p.stdout

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def load_json(p: Path) -> Any:
    return json.loads(p.read_text(encoding="utf-8", errors="replace"))

def expand_vars(obj: Any, vars_map: dict[str, str]) -> Any:
    if isinstance(obj, str):
        for k, v in vars_map.items():
            obj = obj.replace("${" + k + "}", v)
        return obj
    if isinstance(obj, list):
        return [expand_vars(x, vars_map) for x in obj]
    if isinstance(obj, dict):
        return {k: expand_vars(v, vars_map) for k, v in obj.items()}
    return obj

def schema_validate(schema: dict[str, Any], doc: dict[str, Any]) -> None:
    # Prefer jsonschema if available; otherwise do a minimal required-field check.
    try:
        import jsonschema  # type: ignore
        jsonschema.validate(instance=doc, schema=schema)
        return
    except ImportError:
        pass

    # Minimal fallback: required top-level keys + required predicate fields from our schema
    req_top = ["predicateType", "subject", "predicate"]
    for k in req_top:
        if k not in doc:
            raise ValueError(f"schema missing required top-level key: {k}")
    pred = doc.get("predicate", {})
    inv = pred.get("invocation", {})
    cs = inv.get("configSource", {})
    if "uri" not in cs or "digest" not in cs:
        raise ValueError("schema missing predicate.invocation.configSource.(uri,digest)")
    bd = pred.get("buildDefinition", {})
    if "externalParameters" not in bd or "internalParameters" not in bd:
        raise ValueError("schema missing predicate.buildDefinition.(externalParameters,internalParameters)")

def get_workflow_path(att: dict[str, Any]) -> str:
    # Try multiple likely locations
    # Common: predicate.buildDefinition.externalParameters.workflow.path or similar.
    pred = att.get("predicate", {})
    bd = pred.get("buildDefinition", {})
    ext = bd.get("externalParameters", {}) if isinstance(bd, dict) else {}
    # Some provenance puts workflow path under "workflow" object
    for keypath in [
        ("workflow", "path"),
        ("github", "workflow_ref"),
        ("github", "workflow_path"),
        ("workflow_path",),
        ("workflow",),
    ]:
        cur = ext
        ok = True
        for k in keypath:
            if isinstance(cur, dict) and k in cur:
                cur = cur[k]
            else:
                ok = False
                break
        if ok and isinstance(cur, str):
            return cur
    # Try internalParameters
    internal = bd.get("internalParameters", {}) if isinstance(bd, dict) else {}
    if isinstance(internal, dict):
        for k in ["workflow_path", "workflow"]:
            v = internal.get(k)
            if isinstance(v, str):
                return v
    return ""

def get_runner_env(att: dict[str, Any]) -> str:
    pred = att.get("predicate", {})
    bd = pred.get("buildDefinition", {})
    internal = bd.get("internalParameters", {}) if isinstance(bd, dict) else {}
    if isinstance(internal, dict):
        v = internal.get("runner_environment")
        if isinstance(v, str):
            return v
        # common GitHub provenance has runner info nested
        r = internal.get("runner")
        if isinstance(r, dict):
            for k in ["environment", "runnerEnvironment", "type"]:
                vv = r.get(k)
                if isinstance(vv, str):
                    return vv
    return ""

def get_config_source_uri(att: dict[str, Any]) -> str:
    pred = att.get("predicate", {})
    inv = pred.get("invocation", {})
    cs = inv.get("configSource", {})
    uri = cs.get("uri") if isinstance(cs, dict) else None
    return uri if isinstance(uri, str) else ""

def get_config_source_digest(att: dict[str, Any]) -> dict[str, str]:
    pred = att.get("predicate", {})
    inv = pred.get("invocation", {})
    cs = inv.get("configSource", {})
    dig = cs.get("digest") if isinstance(cs, dict) else None
    if isinstance(dig, dict):
        return {str(k): str(v) for k, v in dig.items()}
    return {}

def get_subject_digest(att: dict[str, Any]) -> dict[str, str]:
    subj = att.get("subject")
    if isinstance(subj, list) and subj:
        dig = subj[0].get("digest")
        if isinstance(dig, dict):
            return {str(k): str(v) for k, v in dig.items()}
    return {}

def fail(msg: str) -> None:
    print(f"POLICY FAIL: {msg}", file=sys.stderr)

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--subject", required=True, help="Path or glob to the subject file")
    ap.add_argument("--repo", required=True, help="OWNER/REPO")
    ap.add_argument("--tag", required=True, help="Tag name (e.g., v1.2.3)")
    ap.add_argument("--policy", required=True)
    ap.add_argument("--schema", required=True)
    ap.add_argument("--profile", required=True, choices=["lab_pack_zip", "verifiers"])
    ap.add_argument("--attestation-type", default="provenance", help="gh attestation type to download (provenance|sbom)")
    args = ap.parse_args()

    # Resolve subject
    subj_path = Path(run(["bash", "-c", f"ls -1 {args.subject} 2>/dev/null | head -n 1"]).strip())
    if not subj_path.exists():
        raise FileNotFoundError(f"Subject not found: {subj_path}")

    policy = load_json(Path(args.policy))
    schema = load_json(Path(args.schema))

    vars_map = {
        "REPO": args.repo,
        "TAG": args.tag,
    }
    policy = expand_vars(policy, vars_map)
    prof = policy["subjects"][args.profile]
    allow = prof["allow"]

    # Download attestations to a temp dir
    out_dir = Path(".attest_tmp") / args.profile
    out_dir.mkdir(parents=True, exist_ok=True)

    # gh attestation download <file> --repo OWNER/REPO --format json --type provenance --output-dir ...
    cmd = [
        "gh", "attestation", "download", str(subj_path),
        "--repo", args.repo,
        "--format", "json",
        "--type", args.attestation_type,
        "--dir", str(out_dir),
    ]
    try:
        run(cmd)
    except Exception as e:
        fail(str(e))
        return 1

    att_files = sorted(out_dir.glob("*.json"))
    if not att_files:
        fail(f"no attestations downloaded for {subj_path.name}")
        return 1

    # Compute expected digest for subject file (sha256)
    expected_subject_sha = sha256_file(subj_path)

    ok = True
    reasons: list[str] = []

    tag = args.tag
    ref = f"refs/tags/{tag}"

    # Basic tag allow rules
    tag_ok = any(tag.startswith(pfx) for pfx in allow.get("tag_allow_prefixes", []))
    if not tag_ok:
        ok = False
        reasons.append(f"tag '{tag}' not allowed by tag_allow_prefixes")

    # Enforce ref prefix
    if not ref.startswith(tuple(allow.get("ref_prefix", ["refs/tags/"]))):
        ok = False
        reasons.append(f"ref '{ref}' does not match allowed ref_prefix")

    # Validate each attestation and require at least one to pass fully
    any_pass = False
    for af in att_files:
        att = load_json(af)

        try:
            schema_validate(schema, att)
        except Exception as e:
            ok = False
            reasons.append(f"{af.name}: schema validation failed: {e}")
            continue

        # Subject digest check (attestation subject must match file digest)
        subj_dig = get_subject_digest(att)
        att_sha = subj_dig.get("sha256") or subj_dig.get("SHA256") or ""
        if att_sha.lower() != expected_subject_sha.lower():
            ok = False
            reasons.append(f"{af.name}: subject sha256 mismatch (att={att_sha} expected={expected_subject_sha})")
            continue

        # Config source uri allowlist
        cs_uri = get_config_source_uri(att)
        uri_ok = any(cs_uri.startswith(p) for p in allow.get("source_uri_allow_prefixes", []))
        if not uri_ok:
            ok = False
            reasons.append(f"{af.name}: configSource.uri not allowed: {cs_uri}")
            continue

        # Config source digest should include git sha; enforce exact match if available
        cs_dig = get_config_source_digest(att)
        git_sha = os.environ.get("GITHUB_SHA", "")
        if git_sha:
            # accept common keys: sha1, git, commit
            dig_vals = " ".join([v.lower() for v in cs_dig.values()])
            if git_sha.lower() not in dig_vals:
                ok = False
                reasons.append(f"{af.name}: configSource.digest does not contain GITHUB_SHA")
                continue

        # Workflow path allowlist (best-effort extract)
        wf = get_workflow_path(att)
        if wf:
            # Some formats use full ref, some use path. We accept if any allow entry is contained.
            wf_allow = allow.get("workflow_path", [])
            wf_ok = any(a in wf for a in wf_allow)
            if not wf_ok:
                ok = False
                reasons.append(f"{af.name}: workflow path not allowed: {wf}")
                continue
        else:
            ok = False
            reasons.append(f"{af.name}: could not extract workflow path")
            continue

        # Runner environment allowlist (best-effort extract)
        renv = get_runner_env(att)
        if renv:
            renv_ok = renv in allow.get("runner_environment_allow", [])
            if not renv_ok:
                ok = False
                reasons.append(f"{af.name}: runner environment not allowed: {renv}")
                continue
        else:
            ok = False
            reasons.append(f"{af.name}: could not extract runner environment")
            continue

        any_pass = True

    if not any_pass:
        ok = False
        reasons.append("no attestation satisfied full policy")

    if ok:
        print(f"POLICY OK: {args.profile} subject={subj_path.name} tag={tag}")
        return 0

    for r in reasons:
        fail(r)
    return 1

if __name__ == "__main__":
    raise SystemExit(main())
