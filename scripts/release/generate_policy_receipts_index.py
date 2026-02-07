#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import hashlib
import json
from datetime import datetime, timezone
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def main() -> int:
    tag = (Path.cwd() / ".tag").read_text().strip() if (Path.cwd() / ".tag").exists() else ""
    repo = (Path.cwd() / ".repo").read_text().strip() if (Path.cwd() / ".repo").exists() else ""

    receipts_dir = REPO_ROOT / "dist" / "receipts" / "canonical"
    if not receipts_dir.exists():
        print(f"ERR: canonical receipts dir missing: {receipts_dir}", file=sys.stderr)
        return 2

    files = []
    for p in sorted(receipts_dir.glob("*.json")):
        files.append({
            "path": f"canonical/{p.name}",
            "sha256": sha256_file(p),
            "size_bytes": p.stat().st_size,
        })

        # include bundle if present
        b = Path(str(p) + ".sigstore.json")
        if b.exists():
            files.append({
                "path": f"canonical/{b.name}",
                "sha256": sha256_file(b),
                "size_bytes": b.stat().st_size,
            })

    # Extract policy fingerprint from canonical receipts when present
    receipts_meta = []
    for p in sorted(receipts_dir.glob("*.canonical.json")):
        try:
            obj = json.loads(p.read_text(encoding="utf-8", errors="replace"))
            fp = obj.get("fingerprints", {}).get("policy_fingerprint_sha256", "")
            if fp:
                receipts_meta.append({
                    "receipt": p.name,
                    "policy_fingerprint_sha256": fp,
                })
        except Exception as e:
            print(f"WARN: could not extract fingerprint from {p.name}: {e}", file=sys.stderr)

    index = {
        "version": "1.0",
        "tag": tag,
        "repo": repo,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "files": files,
        "receipts_meta": receipts_meta,
    }

    out_path = REPO_ROOT / "dist" / "receipts" / "policy-receipts-index.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(index, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Generated: {out_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
