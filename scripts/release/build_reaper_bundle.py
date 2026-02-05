#!/usr/bin/env python3
"""
Deterministic Reaper bundle packer.

Outputs:
  dist/smart_guitar_reaper_bundle.zip

Includes:
  scripts/reaper/** (excluding scripts/reaper/_deprecated/**)
  docs/contracts/SG_REAPER_CONTRACT_V1.md

Determinism:
  - stable file ordering
  - stable timestamps in zip entries
  - normalized path separators
"""

from __future__ import annotations

import os
import sys
import zipfile
from pathlib import Path
from typing import Iterable, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
DIST_DIR = REPO_ROOT / "dist"
OUT_ZIP = DIST_DIR / "smart_guitar_reaper_bundle.zip"

# ZIP timestamp (1980-01-01 is min supported by ZIP)
FIXED_ZIP_DT = (1980, 1, 1, 0, 0, 0)

INCLUDE: List[Tuple[Path, str]] = []

def _collect_files() -> List[Tuple[Path, str]]:
    items: List[Tuple[Path, str]] = []

    # scripts/reaper (excluding _deprecated)
    reaper_dir = REPO_ROOT / "scripts" / "reaper"
    if not reaper_dir.exists():
        raise FileNotFoundError(f"Missing: {reaper_dir}")

    for p in sorted(reaper_dir.rglob("*")):
        if p.is_dir():
            continue
        # exclude deprecated
        if "_deprecated" in p.parts:
            continue
        arc = p.relative_to(REPO_ROOT).as_posix()
        items.append((p, arc))

    # contract doc
    contract = REPO_ROOT / "docs" / "contracts" / "SG_REAPER_CONTRACT_V1.md"
    if not contract.exists():
        raise FileNotFoundError(f"Missing: {contract}")
    items.append((contract, contract.relative_to(REPO_ROOT).as_posix()))

    # de-dup, stable order
    seen = set()
    deduped: List[Tuple[Path, str]] = []
    for p, arc in sorted(items, key=lambda x: x[1]):
        if arc in seen:
            continue
        seen.add(arc)
        deduped.append((p, arc))
    return deduped

def _zip_write(zf: zipfile.ZipFile, src: Path, arcname: str) -> None:
    data = src.read_bytes()
    info = zipfile.ZipInfo(filename=arcname, date_time=FIXED_ZIP_DT)
    # regular file perms 0644
    info.external_attr = (0o100644 << 16)
    info.compress_type = zipfile.ZIP_DEFLATED
    zf.writestr(info, data)

def main() -> int:
    DIST_DIR.mkdir(parents=True, exist_ok=True)

    files = _collect_files()

    # overwrite deterministically
    if OUT_ZIP.exists():
        OUT_ZIP.unlink()

    with zipfile.ZipFile(OUT_ZIP, "w") as zf:
        for src, arc in files:
            _zip_write(zf, src, arc)

    print(f"WROTE: {OUT_ZIP}")
    print(f"FILES: {len(files)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
