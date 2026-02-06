#!/usr/bin/env python3
"""
scripts/release/build_lab_pack.py
Phase 10.1: Build "Lab Pack" zip layout deterministically.

Output:
  dist/Lab_Pack_SG_<bundle_version>.zip

Source of truth:
  scripts/reaper/ (the Reaper bundle files)

This builder:
- Copies specific blessed files into Lab_Pack_SG/scripts/reaper/
- Adds README_LAB.txt
- Writes/overrides SG_BUNDLE_VERSION.txt in the pack (from source file)
- Zips the pack
"""

from __future__ import annotations

import os
import shutil
import sys
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_REAPER = REPO_ROOT / "scripts" / "reaper"
DIST_DIR = REPO_ROOT / "dist"
BUILD_DIR = DIST_DIR / "Lab_Pack_SG"

# Canonical Lab Pack inventory (add/remove here only)
BLESSED_REAPER_FILES = [
    "SG_BUNDLE_VERSION.txt",
    "json.lua",
    "sg_http.lua",
    "reaper_sg_installer_register_all.lua",
    "reaper_sg_setup_doctor.lua",
    "reaper_sg_probe_endpoints.lua",
    "reaper_sg_lab_bootstrap.lua",
    "reaper_sg_set_transport.lua",
    "reaper_sg_set_lan_mode.lua",
    "reaper_sg_ping_status.lua",
    "reaper_sg_transport_status.lua",
    # Minimal action stubs / core actions (ensure installer MAP works out of the box)
    "reaper_sg_generate.lua",
    "reaper_sg_pass_and_regen.lua",
    "reaper_sg_struggle_and_regen.lua",
    "reaper_sg_timeline.lua",
    "reaper_sg_trend.lua",
    # Optional: panel (include if you want labs to have UI)
    "reaper_sg_panel.lua",
]

README_LAB = """\
Smart Guitar — Lab Pack

Install:
1) Open Reaper -> Options -> Show REAPER resource path...
2) Create folder:
     Scripts/SmartGuitar/
3) Copy the contents of:
     Lab_Pack_SG/scripts/reaper/
   into:
     REAPER_RESOURCE_PATH/Scripts/SmartGuitar/

Run:
- Actions -> ReaScript -> Load -> select:
    reaper_sg_lab_bootstrap.lua
  Run once.

Outputs:
- Reports saved to:
    REAPER_RESOURCE_PATH/SG_reports/
"""

def read_bundle_version(src_reaper: Path) -> str:
    p = src_reaper / "SG_BUNDLE_VERSION.txt"
    if not p.exists():
        return "unknown"
    v = p.read_text(encoding="utf-8", errors="replace").strip()
    return v or "unknown"

def safe_copy(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)

def zip_dir(src_dir: Path, zip_path: Path) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted(src_dir.rglob("*")):
            if p.is_dir():
                continue
            rel = p.relative_to(src_dir)
            z.write(p, rel.as_posix())

def main() -> int:
    if not SRC_REAPER.exists():
        print(f"ERR: missing {SRC_REAPER}", file=sys.stderr)
        return 2

    bundle_version = read_bundle_version(SRC_REAPER)
    out_zip = DIST_DIR / f"Lab_Pack_SG_{bundle_version}.zip"

    # Clean build dir
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    (BUILD_DIR / "scripts" / "reaper").mkdir(parents=True, exist_ok=True)

    # Write README
    (BUILD_DIR / "README_LAB.txt").write_text(README_LAB, encoding="utf-8")

    # Copy blessed files
    missing = []
    for fn in BLESSED_REAPER_FILES:
        src = SRC_REAPER / fn
        if not src.exists():
            missing.append(fn)
            continue
        dst = BUILD_DIR / "scripts" / "reaper" / fn
        safe_copy(src, dst)

    if missing:
        print("WARN: missing files (not copied):")
        for fn in missing:
            print(f"  - {fn}")

    # Zip it
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    if out_zip.exists():
        out_zip.unlink()
    zip_dir(BUILD_DIR, out_zip)

    print("OK: built lab pack:")
    print(f"  {out_zip}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
