#!/usr/bin/env python3
"""
Generate one SPDX SBOM per verifier script.

Outputs (examples):
  dist/verifiers/verify_release.sh.spdx.json
  dist/verifiers/verify_release.ps1.spdx.json
  dist/verifiers/verify_attestations.sh.spdx.json

Each SBOM describes a SINGLE subject file and includes:
- file SHA256
- a minimal SPDX package containing the file

This supports "one SBOM per artifact" compliance models.
"""

from __future__ import annotations
from pathlib import Path
import hashlib
import json
from datetime import datetime, timezone

REPO_ROOT = Path(__file__).resolve().parents[2]
DIST = REPO_ROOT / "dist" / "verifiers"

SUBJECTS = [
    REPO_ROOT / "scripts" / "release" / "verify_release.sh",
    REPO_ROOT / "scripts" / "release" / "verify_release.ps1",
    REPO_ROOT / "scripts" / "release" / "verify_attestations.sh",
]

def sha256_bytes(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()

def make_spdx_for_subject(subject: Path) -> dict:
    created = datetime.now(timezone.utc).isoformat()
    rel = subject.relative_to(REPO_ROOT).as_posix()
    data = subject.read_bytes()
    h = sha256_bytes(data)

    doc_ns = "https://spdx.org/spdxdocs/" + hashlib.sha1((rel + created).encode("utf-8")).hexdigest()
    pkg_id = "SPDXRef-Package-" + hashlib.sha1(rel.encode("utf-8")).hexdigest()
    file_id = "SPDXRef-File-" + hashlib.sha1(rel.encode("utf-8")).hexdigest()

    return {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": f"SmartGuitar-Verifier-SBOM:{rel}",
        "documentNamespace": doc_ns,
        "creationInfo": {
            "created": created,
            "creators": ["Tool: generate_verifier_sboms_per_subject.py"],
        },
        "packages": [{
            "name": f"SmartGuitar-Verifier:{subject.name}",
            "SPDXID": pkg_id,
            "downloadLocation": "NOASSERTION",
            "filesAnalyzed": True,
            "licenseConcluded": "NOASSERTION",
            "licenseDeclared": "NOASSERTION",
            "supplier": "NOASSERTION",
        }],
        "files": [{
            "fileName": rel,
            "SPDXID": file_id,
            "checksums": [{"algorithm": "SHA256", "checksumValue": h}],
            "licenseConcluded": "NOASSERTION",
            "licenseInfoInFile": ["NOASSERTION"],
            "copyrightText": "NOASSERTION",
        }],
        "relationships": [{
            "spdxElementId": pkg_id,
            "relationshipType": "CONTAINS",
            "relatedSpdxElement": file_id,
        }],
    }

def main() -> int:
    DIST.mkdir(parents=True, exist_ok=True)

    wrote = 0
    for s in SUBJECTS:
        if not s.exists():
            # If you intentionally don't ship one of these yet, skip.
            continue
        spdx = make_spdx_for_subject(s)
        out = DIST / f"{s.name}.spdx.json"
        out.write_text(json.dumps(spdx, indent=2) + "\n", encoding="utf-8")
        print(f"OK: {out}")
        wrote += 1

    if wrote == 0:
        print("ERR: no verifier subjects found", flush=True)
        return 2

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
