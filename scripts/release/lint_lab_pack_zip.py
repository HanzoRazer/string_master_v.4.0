#!/usr/bin/env python3
"""
scripts/release/lint_lab_pack_zip.py

Phase 10.8: Structure lint for Lab Pack zip.

Validates:
- Required files exist in zip
- SG_BUNDLE_VERSION.txt present + non-empty
- Lua scripts in scripts/reaper/ contain required header markers
- Optional: bundle version matches tag (when CI_TAG env provided)

Usage:
  python scripts/release/lint_lab_pack_zip.py dist/Lab_Pack_SG_*.zip
or:
  python scripts/release/lint_lab_pack_zip.py   (auto-detect dist/)
"""

from __future__ import annotations

from pathlib import Path
import os
import re
import sys
import zipfile

REPO_ROOT = Path(__file__).resolve().parents[2]

# Required files for a functional lab pack (adjust as you standardize)
REQUIRED_REAPER_FILES = [
    "SG_BUNDLE_VERSION.txt",
    "json.lua",
    "sg_http.lua",
    "reaper_sg_setup_doctor.lua",
    "reaper_sg_probe_endpoints.lua",
    "reaper_sg_lab_bootstrap.lua",
]

# Required header markers for Lua scripts (minimal but meaningful)
# We enforce that each Lua begins with at least one of these contract markers.
LUA_REQUIRED_PATTERNS = [
    re.compile(r"^\s*--\s*CONTRACT:\s*SG_REAPER_CONTRACT_V1", re.IGNORECASE | re.MULTILINE),
]

# Recommended (not strictly required) markers to help long-term hygiene.
LUA_RECOMMENDED_PATTERNS = [
    re.compile(r"^\s*--\s*Phase\s*\d+", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^\s*--\s*scripts/reaper/", re.IGNORECASE | re.MULTILINE),
]

def find_zip(argv: list[str]) -> Path:
    if len(argv) >= 2:
        p = Path(argv[1])
        if p.exists():
            return p
    dist = REPO_ROOT / "dist"
    zips = sorted(dist.glob("Lab_Pack_SG_*.zip"))
    if not zips:
        raise FileNotFoundError("No dist/Lab_Pack_SG_*.zip found")
    return zips[0]

def read_text_from_zip(z: zipfile.ZipFile, name: str) -> str | None:
    try:
        data = z.read(name)
    except KeyError:
        return None
    # decode leniently; scripts are plain text
    return data.decode("utf-8", errors="replace")

def main(argv: list[str]) -> int:
    try:
        zip_path = find_zip(argv)
    except Exception as e:
        print(f"LINT ERR: {e}", file=sys.stderr)
        return 2

    ci_tag = os.environ.get("CI_TAG") or os.environ.get("GITHUB_REF_NAME") or ""

    errors: list[str] = []
    warns: list[str] = []

    with zipfile.ZipFile(zip_path, "r") as z:
        names = z.namelist()

        # 1) Required files
        for fn in REQUIRED_REAPER_FILES:
            full = f"scripts/reaper/{fn}"
            if full not in names:
                errors.append(f"missing required file: {full}")

        # 2) Bundle version sanity
        bv_path = "scripts/reaper/SG_BUNDLE_VERSION.txt"
        bv_text = read_text_from_zip(z, bv_path)
        if bv_text is None:
            errors.append(f"missing: {bv_path}")
            bundle_version = ""
        else:
            bundle_version = bv_text.strip()
            if not bundle_version:
                errors.append("SG_BUNDLE_VERSION.txt is empty")

        # 3) Optional tag sanity: if CI tag looks like a version, ensure it matches bundle version (best-effort)
        # This is intentionally conservative: only enforce if both are present and tag is a "release-ish" tag.
        if ci_tag and bundle_version:
            # enforce only if tag begins with v / reaper-bundle- / labpack-
            if ci_tag.startswith(("v", "reaper-bundle-", "labpack-")):
                # We don't require exact equality because teams differ; we require bundle_version to be a substring
                # of tag or vice versa to catch obvious mismatches.
                if (bundle_version not in ci_tag) and (ci_tag not in bundle_version):
                    warns.append(f"tag/bundle mismatch? tag='{ci_tag}' bundle='{bundle_version}'")

        # 4) Lua header lint for scripts/reaper/*.lua
        lua_files = [n for n in names if n.startswith("scripts/reaper/") and n.endswith(".lua")]
        for lf in sorted(lua_files):
            txt = read_text_from_zip(z, lf)
            if txt is None:
                errors.append(f"cannot read lua: {lf}")
                continue

            # Basic "has contract marker" requirement
            if not any(p.search(txt) for p in LUA_REQUIRED_PATTERNS):
                errors.append(f"lua missing required header marker (CONTRACT): {lf}")

            # Recommended markers (warnings only)
            if not any(p.search(txt) for p in LUA_RECOMMENDED_PATTERNS):
                warns.append(f"lua missing recommended header marker (phase/path): {lf}")

            # Extra: ensure file starts with a comment header (hygiene)
            head = txt.lstrip()[:2]
            if head != "--":
                warns.append(f"lua does not start with comment header: {lf}")

    # Report
    if errors:
        print(f"LINT FAIL: {zip_path}", file=sys.stderr)
        for e in errors:
            print(f"  ERR: {e}", file=sys.stderr)
    else:
        print(f"LINT OK: {zip_path}")

    if warns:
        print("LINT WARN:")
        for w in warns:
            print(f"  WARN: {w}")

    return 1 if errors else 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
