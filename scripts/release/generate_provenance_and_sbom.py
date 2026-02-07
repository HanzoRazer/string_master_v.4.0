#!/usr/bin/env python3
"""
Generate:
- dist/provenance.json (SBOM-ish metadata: git/run info, bundle version, zip SHA256, manifest stats)
- dist/labpack.spdx.json (SPDX 2.3 JSON: file inventory with SHA256 per file extracted from zip)

Requires:
- dist/Lab_Pack_SG_*.zip
- dist/Lab_Pack_SG_*.zip.sha256
- dist/Lab_Pack_SG_*.zip.manifest.txt

Environment (optional but recommended in CI):
- GITHUB_REPOSITORY
- GITHUB_SHA
- GITHUB_REF_NAME
- GITHUB_RUN_ID
- GITHUB_RUN_ATTEMPT
- GITHUB_WORKFLOW
- GITHUB_SERVER_URL
"""

from __future__ import annotations

from pathlib import Path
import json
import os
import sys
import zipfile
import hashlib
from datetime import datetime, timezone

REPO_ROOT = Path(__file__).resolve().parents[2]

def find_zip(dist: Path) -> Path:
    zips = sorted(dist.glob("Lab_Pack_SG_*.zip"))
    if not zips:
        raise FileNotFoundError("No dist/Lab_Pack_SG_*.zip found")
    return zips[0]

def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")

def sha256_bytes(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()

def read_bundle_version_from_zip(zip_path: Path) -> str:
    with zipfile.ZipFile(zip_path, "r") as z:
        data = z.read("scripts/reaper/SG_BUNDLE_VERSION.txt")
    v = data.decode("utf-8", errors="replace").strip()
    return v or "unknown"

def spdx_doc(zip_path: Path, bundle_version: str) -> dict:
    # SPDX 2.3 JSON (lightweight but standard)
    doc_ns = f"https://spdx.org/spdxdocs/smart-guitar-lab-pack-{bundle_version}-{sha256_bytes(zip_path.name.encode())}"
    created = datetime.now(timezone.utc).isoformat()

    packages = [{
        "name": f"SmartGuitar-LabPack-{bundle_version}",
        "SPDXID": "SPDXRef-Package-LabPack",
        "downloadLocation": "NOASSERTION",
        "filesAnalyzed": True,
        "licenseConcluded": "NOASSERTION",
        "licenseDeclared": "NOASSERTION",
        "supplier": "NOASSERTION",
        "versionInfo": bundle_version,
    }]

    files = []
    relationships = []

    with zipfile.ZipFile(zip_path, "r") as z:
        for name in sorted(z.namelist()):
            # ignore directory entries
            if name.endswith("/"):
                continue
            data = z.read(name)
            h = sha256_bytes(data)
            spdxid = "SPDXRef-File-" + hashlib.sha1(name.encode("utf-8")).hexdigest()

            files.append({
                "fileName": name,
                "SPDXID": spdxid,
                "checksums": [{"algorithm": "SHA256", "checksumValue": h}],
                "licenseConcluded": "NOASSERTION",
                "licenseInfoInFile": ["NOASSERTION"],
                "copyrightText": "NOASSERTION",
            })
            relationships.append({
                "spdxElementId": "SPDXRef-Package-LabPack",
                "relationshipType": "CONTAINS",
                "relatedSpdxElement": spdxid,
            })

    return {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": f"SmartGuitar-LabPack-{bundle_version}",
        "documentNamespace": doc_ns,
        "creationInfo": {
            "created": created,
            "creators": ["Tool: generate_provenance_and_sbom.py"],
        },
        "packages": packages,
        "files": files,
        "relationships": relationships,
    }

def main() -> int:
    dist = REPO_ROOT / "dist"
    dist.mkdir(parents=True, exist_ok=True)

    zip_path = find_zip(dist)
    sha_path = zip_path.with_suffix(zip_path.suffix + ".sha256")
    man_path = zip_path.with_suffix(".manifest.txt")

    if not sha_path.exists():
        raise FileNotFoundError(f"Missing {sha_path}")
    if not man_path.exists():
        raise FileNotFoundError(f"Missing {man_path}")

    bundle_version = read_bundle_version_from_zip(zip_path)
    sha_line = read_text(sha_path).strip()
    manifest_lines = [ln for ln in read_text(man_path).splitlines() if ln.strip()]
    manifest_entry_count = len(manifest_lines)

    # CI context
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    sha = os.environ.get("GITHUB_SHA", "")
    tag = os.environ.get("GITHUB_REF_NAME", "")
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    run_attempt = os.environ.get("GITHUB_RUN_ATTEMPT", "")
    workflow = os.environ.get("GITHUB_WORKFLOW", "")
    server_url = os.environ.get("GITHUB_SERVER_URL", "https://github.com")

    run_url = ""
    if repo and run_id:
        run_url = f"{server_url}/{repo}/actions/runs/{run_id}"

    provenance = {
        "kind": "SmartGuitarLabPackProvenance",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "repo": repo or "unknown",
        "git_sha": sha or "unknown",
        "tag": tag or "unknown",
        "workflow": workflow or "unknown",
        "run_id": run_id or "unknown",
        "run_attempt": run_attempt or "unknown",
        "run_url": run_url or "unknown",
        "bundle_version": bundle_version,
        "artifacts": {
            "zip": zip_path.name,
            "zip_sha256_line": sha_line,
            "manifest": man_path.name,
            "manifest_entry_count": manifest_entry_count,
        },
    }

    # Include verifier artifacts (if present in workspace)
    ver_list = []
    for rel in [
        "scripts/release/verify_release.sh",
        "scripts/release/verify_release.ps1",
        "scripts/release/verify_attestations.sh",
    ]:
        p = REPO_ROOT / rel
        if p.exists():
            ver_list.append({"path": rel, "sha256": sha256_bytes(p.read_bytes())})
    provenance["verifiers"] = ver_list

    (dist / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")

    sbom = spdx_doc(zip_path, bundle_version)
    (dist / "labpack.spdx.json").write_text(json.dumps(sbom, indent=2) + "\n", encoding="utf-8")

    print("OK: dist/provenance.json")
    print("OK: dist/labpack.spdx.json")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        print(f"ERR: {e}", file=sys.stderr)
        raise SystemExit(2)
