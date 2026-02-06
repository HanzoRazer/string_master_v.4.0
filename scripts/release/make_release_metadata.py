#!/usr/bin/env python3
"""
scripts/release/generate_checksums.py
Phase 10.3: Generate SHA256 checksums and manifest for Lab Pack releases.

Outputs:
  dist/Lab_Pack_SG_<bundle_version>.zip.sha256
  dist/Lab_Pack_SG_<bundle_version>.manifest.txt

Manifest includes:
- File list with sizes
- Checksums
- Build metadata
"""

from __future__ import annotations

import hashlib
import sys
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DIST_DIR = REPO_ROOT / "dist"


def sha256_file(path: Path) -> str:
    """Compute SHA256 hash of file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def manifest_from_zip(zip_path: Path) -> str:
    """Generate manifest with per-file hashes."""
    lines = []
    with zipfile.ZipFile(zip_path, "r") as z:
        infos = sorted(z.infolist(), key=lambda i: i.filename)
        for i in infos:
            data = z.read(i.filename)
            h = hashlib.sha256(data).hexdigest()
            lines.append(f"{i.file_size:>10}  {h}  {i.filename}")
    return "\n".join(lines) + "\n"


def generate_manifest(zip_path: Path, sha256: str) -> str:
    """Generate manifest text."""
    lines = [
        "Smart Guitar — Lab Pack Release Manifest",
        "=" * 60,
        f"Package: {zip_path.name}",
        f"Size: {zip_path.stat().st_size:,} bytes",
        f"SHA256: {sha256}",
        "",
        "Contents (size, sha256, filename):",
        "-" * 60,
    ]

    try:
        file_manifest = manifest_from_zip(zip_path)
        lines.append(file_manifest.rstrip())
        file_count = len(file_manifest.strip().split("\n"))
        lines.append("-" * 60)
        lines.append(f"Total files: {file_count}")
    except Exception as e:
        lines.append(f"ERROR: Failed to list zip contents: {e}")

    lines.append("")
    return "\n".join(lines)


def main() -> int:
    if not DIST_DIR.exists():
        print(f"ERR: dist/ directory not found: {DIST_DIR}", file=sys.stderr)
        return 2

    # Find Lab Pack zip
    zips = list(DIST_DIR.glob("Lab_Pack_SG_*.zip"))
    if not zips:
        print("ERR: no Lab_Pack_SG_*.zip found in dist/", file=sys.stderr)
        return 2

    # Use most recent if multiple
    zip_path = max(zips, key=lambda p: p.stat().st_mtime)

    print(f"Generating checksums for: {zip_path.name}")

    # Generate SHA256
    sha256 = sha256_file(zip_path)
    sha256_path = zip_path.with_suffix(zip_path.suffix + ".sha256")
    sha256_path.write_text(f"{sha256}  {zip_path.name}\n", encoding="utf-8")
    print(f"  SHA256: {sha256_path.name}")

    # Generate manifest
    manifest = generate_manifest(zip_path, sha256)
    manifest_path = zip_path.with_suffix(".manifest.txt")
    manifest_path.write_text(manifest, encoding="utf-8")
    print(f"  Manifest: {manifest_path.name}")

    print("\nOK: checksums and manifest generated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
