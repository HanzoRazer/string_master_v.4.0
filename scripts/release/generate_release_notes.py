#!/usr/bin/env python3
"""
Generate release notes body that includes:
- Bundle version (from SG_BUNDLE_VERSION.txt inside the zip)
- SHA256 (from .sha256 file)
- Manifest excerpt (first N lines) + total entries

Usage:
  python scripts/release/generate_release_notes.py dist/Lab_Pack_SG_*.zip
Produces:
  dist/release_notes.md
"""

from __future__ import annotations
from pathlib import Path
import sys
import zipfile

REPO_ROOT = Path(__file__).resolve().parents[2]

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

def read_bundle_version_from_zip(zip_path: Path) -> str:
    with zipfile.ZipFile(zip_path, "r") as z:
        data = z.read("scripts/reaper/SG_BUNDLE_VERSION.txt")
    v = data.decode("utf-8", errors="replace").strip()
    return v or "unknown"

def main(argv: list[str]) -> int:
    try:
        zip_path = find_zip_arg(argv)
    except Exception as e:
        print(f"ERR: {e}", file=sys.stderr)
        return 2

    sha_path = zip_path.with_suffix(zip_path.suffix + ".sha256")
    man_path = zip_path.with_suffix(".manifest.txt")
    out_path = zip_path.parent / "release_notes.md"

    if not sha_path.exists():
        print(f"ERR: missing {sha_path}", file=sys.stderr)
        return 2
    if not man_path.exists():
        print(f"ERR: missing {man_path}", file=sys.stderr)
        return 2

    bundle_version = read_bundle_version_from_zip(zip_path)
    sha_line = sha_path.read_text(encoding="utf-8", errors="replace").strip()

    manifest_lines = man_path.read_text(encoding="utf-8", errors="replace").splitlines()
    total_entries = len([ln for ln in manifest_lines if ln.strip()])
    excerpt_n = 25
    excerpt = "\n".join(manifest_lines[:excerpt_n])

    body = f"""\
## Smart Guitar Lab Pack

**Bundle version:** `{bundle_version}`

### Assets
- `{zip_path.name}`
- `{sha_path.name}`
- `{man_path.name}`

### SHA256
```text
{sha_line}
```

### Manifest (first {excerpt_n} entries of {total_entries})
```text
{excerpt}
```

### Verifiers (download + verify)
- `verify_release.sh` (+ `.sigstore.json`)
- `verify_release.ps1` (+ `.sigstore.json`)
- `verify_attestations.sh` (+ `.sigstore.json`)
- `verifiers.spdx.json` (combined SBOM for all verifiers)

### Verifier SBOMs (one per subject)
- `verify_release.sh.spdx.json`
- `verify_release.ps1.spdx.json`
- `verify_attestations.sh.spdx.json`

Each SBOM is attested to its corresponding verifier artifact.

### Notes

This release is gated by: **policy + lint + determinism + cross-OS parity checks**.

If you need to validate integrity: download the zip and compare SHA256 to the `.sha256` file.
"""

    out_path.write_text(body, encoding="utf-8")
    print(f"OK: wrote {out_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
