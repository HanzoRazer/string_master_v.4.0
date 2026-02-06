#!/usr/bin/env python3
"""
scripts/release/check_lab_pack_policy.py

Zip content policy check for Lab Pack releases.

Policy:
- Zip must contain only expected paths:
  - README_LAB.txt
  - scripts/reaper/<BLESSED_REAPER_FILES...>

- No absolute paths
- No path traversal
- No backslashes in archive paths
- No duplicate entry names

Usage:
  python scripts/release/check_lab_pack_policy.py dist/Lab_Pack_SG_*.zip
or:
  python scripts/release/check_lab_pack_policy.py   (auto-detects in dist/)
"""

from __future__ import annotations

from pathlib import Path
import sys
import zipfile

REPO_ROOT = Path(__file__).resolve().parents[2]

def load_blessed_files() -> list[str]:
    """
    Single source of truth is build_lab_pack.py BLESSED_REAPER_FILES.
    We parse it in a minimal, robust way (no import side effects).
    """
    src = (REPO_ROOT / "scripts" / "release" / "build_lab_pack.py").read_text(
        encoding="utf-8", errors="replace"
    )
    # Very small parser: find the literal list block for BLESSED_REAPER_FILES = [ ... ]
    marker = "BLESSED_REAPER_FILES = ["
    i = src.find(marker)
    if i < 0:
        raise RuntimeError("Could not find BLESSED_REAPER_FILES in build_lab_pack.py")
    j = src.find("]", i)
    if j < 0:
        raise RuntimeError("Could not parse BLESSED_REAPER_FILES list (missing ])")

    block = src[i:j+1]

    # Extract quoted strings inside the list; supports "..." or '...'
    out: list[str] = []
    cur = ""
    in_str = False
    quote = ""
    esc = False

    for ch in block:
        if not in_str:
            if ch in ("'", '"'):
                in_str = True
                quote = ch
                cur = ""
            continue

        # in_str
        if esc:
            cur += ch
            esc = False
            continue
        if ch == "\\":
            esc = True
            continue
        if ch == quote:
            out.append(cur)
            in_str = False
            quote = ""
            cur = ""
            continue
        cur += ch

    if not out:
        raise RuntimeError("Parsed BLESSED_REAPER_FILES but found no entries")
    return out

def find_zip_arg(argv: list[str]) -> Path:
    if len(argv) >= 2:
        p = Path(argv[1])
        if p.exists():
            return p

    dist = REPO_ROOT / "dist"
    zips = sorted(dist.glob("Lab_Pack_SG_*.zip"))
    if not zips:
        raise FileNotFoundError("No dist/Lab_Pack_SG_*.zip found")
    return zips[0]

def is_bad_path(name: str) -> str | None:
    # Zip names must be forward-slash only
    if "\\" in name:
        return "contains backslash"
    # No absolute paths
    if name.startswith("/") or name.startswith("\\"):
        return "absolute path"
    # No traversal
    parts = name.split("/")
    if any(p == ".." for p in parts):
        return "path traversal (..)"
    # No empty segments except possible trailing slash (directories)
    if any(p == "" for p in parts[:-1]):
        return "empty path segment"
    return None

def main(argv: list[str]) -> int:
    try:
        zip_path = find_zip_arg(argv)
        blessed = load_blessed_files()
    except Exception as e:
        print(f"POLICY ERR: {e}", file=sys.stderr)
        return 2

    allowed = set()
    allowed.add("README_LAB.txt")
    for fn in blessed:
        allowed.add(f"scripts/reaper/{fn}")

    with zipfile.ZipFile(zip_path, "r") as z:
        names = z.namelist()

    # Directory entries are permitted only if they are canonical prefixes of allowed files.
    # We don't require explicit directory entries, but if present they must be safe.
    allowed_dirs = set()
    for a in allowed:
        parts = a.split("/")
        for k in range(1, len(parts)):
            allowed_dirs.add("/".join(parts[:k]) + "/")

    seen = set()
    unexpected = []
    badpaths = []
    dups = []

    for n in names:
        if n in seen:
            dups.append(n)
        seen.add(n)

        bad = is_bad_path(n)
        if bad:
            badpaths.append((n, bad))
            continue

        if n in allowed:
            continue
        if n in allowed_dirs:
            continue

        unexpected.append(n)

    ok = True
    if dups:
        ok = False
        print("POLICY FAIL: duplicate zip entry names:", file=sys.stderr)
        for n in dups:
            print(f"  - {n}", file=sys.stderr)

    if badpaths:
        ok = False
        print("POLICY FAIL: invalid zip paths:", file=sys.stderr)
        for n, why in badpaths:
            print(f"  - {n} ({why})", file=sys.stderr)

    if unexpected:
        ok = False
        print("POLICY FAIL: unexpected files in zip:", file=sys.stderr)
        for n in unexpected:
            print(f"  - {n}", file=sys.stderr)

        print("\nAllowed file roots:", file=sys.stderr)
        print("  - README_LAB.txt", file=sys.stderr)
        print("  - scripts/reaper/<BLESSED_REAPER_FILES...>", file=sys.stderr)

    if ok:
        print(f"POLICY OK: {zip_path}")
        return 0

    return 1

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
