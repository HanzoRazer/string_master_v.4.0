# Verify Smart Guitar Lab Pack Releases

This guide verifies a Lab Pack release asset set.

**Required downloaded files from the Release:**
- `Lab_Pack_SG_<bundle>.zip`
- `Lab_Pack_SG_<bundle>.zip.sha256`
- `Lab_Pack_SG_<bundle>.zip.sigstore.json`

**Optional:**
- `labpack.spdx.json`
- `provenance.json`
- `Lab_Pack_SG_<bundle>.zip.manifest.txt` (integrity helper)
- GitHub attestations (online check via `gh`)

---

## 0) Tools

### macOS/Linux
- `sha256sum` (Linux) or `shasum` (macOS)
- `cosign` (recommended)
- `gh` (optional; to query GitHub attestations)

**Install cosign:**
- https://docs.sigstore.dev/quickstart/quickstart-cosign/

**Install gh:**
- https://cli.github.com/

### Windows
- PowerShell 5+ or PowerShell 7+
- `cosign.exe` (recommended)
- `gh.exe` (optional)

---

## 1) Offline integrity check (SHA256)

### Linux
```bash
sha256sum -c Lab_Pack_SG_*.zip.sha256
```

### macOS
```bash
shasum -a 256 -c Lab_Pack_SG_*.zip.sha256
```

### Windows PowerShell
```powershell
$zip = Get-ChildItem .\Lab_Pack_SG_*.zip | Select-Object -First 1
$sha = Get-Content ($zip.FullName + ".sha256")
$expected = ($sha -split "\s+")[0]
$actual = (Get-FileHash $zip.FullName -Algorithm SHA256).Hash.ToLower()
if ($expected.ToLower() -ne $actual) { throw "SHA256 mismatch" } else { "SHA256 OK" }
```

---

## 2) Verify Sigstore bundle signature (cosign keyless)

This verifies the downloaded zip against the bundle produced in CI.

### macOS/Linux
```bash
cosign verify-blob \
  --bundle Lab_Pack_SG_*.zip.sigstore.json \
  Lab_Pack_SG_*.zip
```

### Windows PowerShell
```powershell
cosign verify-blob --bundle .\Lab_Pack_SG_*.zip.sigstore.json .\Lab_Pack_SG_*.zip
```

**If verification fails, do NOT deploy.**

---

## 3) Optional: Verify GitHub attestations (online)

If your release workflow publishes GitHub artifact attestations, you can verify them with GitHub CLI.

**Prereqs:**
- `gh auth login`
- repo access

**Example** (replace owner/repo and tag if needed):
```bash
gh release view <TAG> --repo <OWNER>/<REPO>
```

Attestations can be viewed/verified depending on your org policy and tooling.
See GitHub documentation:
- https://docs.github.com/actions/security-for-github-actions/using-artifact-attestations/

---

## 4) Optional: Validate SBOM + provenance files are present

- `labpack.spdx.json` is an SPDX SBOM of the zip contents
- `provenance.json` records CI run metadata: commit, run id, bundle version, checksums

These are informational but useful for audit.

---

## Recommended deployment rule

**Only deploy the Lab Pack if:**

✅ SHA256 OK  
✅ cosign bundle verification OK  
✅ (optional) GitHub attestation checks OK
