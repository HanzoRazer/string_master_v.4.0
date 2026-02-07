#!/usr/bin/env python3
"""
Generate SPDX SBOM for verifier scripts that are published as release assets.

Outputs:
  dist/verifiers.spdx.json

Includes:
  - scripts/release/verify_release.sh
  - scripts/release/verify_release.ps1
  - scripts/release/verify_attestations.sh

This SBOM describes the verifier artifacts themselves (not the Lab Pack zip).
"""

from __future__ import annotations
from pathlib import Path
import hashlib
import json
from datetime import datetime, timezone

REPO_ROOT = Path(__file__).resolve().parents[2]

VERIFIERS = [
    REPO_ROOT / "scripts" / "release" / "verify_release.sh",
    REPO_ROOT / "scripts" / "release" / "verify_release.ps1",
    REPO_ROOT / "scripts" / "release" / "verify_attestations.sh",
]

def sha256_bytes(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()

def main() -> int:
    dist = REPO_ROOT / "dist"
    dist.mkdir(parents=True, exist_ok=True)

    created = datetime.now(timezone.utc).isoformat()
    files = []
    rels = []
    pkg_id = "SPDXRef-Package-Verifiers"

    for p in VERIFIERS:
        if not p.exists():
            # allow missing if you intentionally don't ship one of them yet
            continue
        data = p.read_bytes()
        h = sha256_bytes(data)
        rel = p.relative_to(REPO_ROOT).as_posix()
        spdxid = "SPDXRef-File-" + hashlib.sha1(rel.encode("utf-8")).hexdigest()

        files.append({
            "fileName": rel,
            "SPDXID": spdxid,
            "checksums": [{"algorithm": "SHA256", "checksumValue": h}],
            "licenseConcluded": "NOASSERTION",
            "licenseInfoInFile": ["NOASSERTION"],
            "copyrightText": "NOASSERTION",
        })
        rels.append({
            "spdxElementId": pkg_id,
            "relationshipType": "CONTAINS",
            "relatedSpdxElement": spdxid,
        })

    doc = {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": "SmartGuitar-Release-Verifiers",
        "documentNamespace": "https://spdx.org/spdxdocs/smart-guitar-release-verifiers-" + hashlib.sha1(created.encode()).hexdigest(),
        "creationInfo": {
            "created": created,
            "creators": ["Tool: generate_verifier_sbom.py"],
        },
        "packages": [{
            "name": "SmartGuitar-Release-Verifiers",
            "SPDXID": pkg_id,
            "downloadLocation": "NOASSERTION",
            "filesAnalyzed": True,
            "licenseConcluded": "NOASSERTION",
            "licenseDeclared": "NOASSERTION",
            "supplier": "NOASSERTION",
        }],
        "files": files,
        "relationships": rels,
    }

    out = dist / "verifiers.spdx.json"
    out.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    print(f"OK: wrote {out}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
