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

## 5) Optional: Verifier pinning (self-integrity check)

The `verify_release.sh` script supports self-integrity checking to ensure the verifier itself hasn't been tampered with.

**Modes:**
- `--pin off` (default): No pin check
- `--pin warn`: Print warnings if mismatch but continue
- `--pin strict`: Fail if verifier hash doesn't match pinned hash in provenance.json

**Usage:**

### Linux/macOS
```bash
# Strict mode (recommended for automated systems)
./verify_release.sh --pin strict --pin-file provenance.json

# Warn mode (print warnings only)
./verify_release.sh --pin warn --pin-file provenance.json

# Default (no pin check)
./verify_release.sh
```

**Environment variables:**
```bash
export PIN_MODE=strict
export PIN_FILE=provenance.json
./verify_release.sh
```

**What it checks:**

**Triple-check security model (Phase 11.7.1):**
1. **Verifier file pin**: Computes SHA256 of `verify_release.sh` itself and compares against `verifier_pins.pins[].sha256` in provenance.json
2. **Bundle pin**: If `bundle_sha256` exists in provenance, verifies the `.sigstore.json` bundle file hash matches
3. **Cosign verification**: Uses cosign to cryptographically verify the bundle signature against the verifier file

This triple-check prevents:
- Verifier file tampering (pin check #1)
- Bundle swap attacks (pin check #2)
- Signature forgery (cosign verification #3)

Also checks sibling verifiers (verify_release.ps1, verify_attestations.sh) with the same triple-check if present.

**Example output (strict mode success):**
```
OK: Verifier pin check passed for verify_release.sh
OK: Verifier bundle pin check passed
OK: Cosign verified verifier bundle
OK: Sibling verifier pin check passed for verify_release.ps1
OK: Sibling bundle pin check passed for verify_release.ps1
OK: Cosign verified sibling bundle for verify_release.ps1
OK: Sibling verifier pin check passed for verify_attestations.sh
OK: Sibling bundle pin check passed for verify_attestations.sh
OK: Cosign verified sibling bundle for verify_attestations.sh
== Files ==
...
```

**Example output (strict mode failure):**
```
ERR: Verifier integrity mismatch for verify_release.sh
  Expected: abc123...
  Actual:   def456...
  (strict mode: FAIL)
```

**When to use:**
- **strict mode**: Automated CI/CD pipelines, production deployments
- **warn mode**: Development/testing environments where you want visibility but not blocking
- **off mode**: Manual verification on trusted machines

---

## 6) Strict mode (for orgs with attestations enabled - Phase 11.7.3)

If your organization guarantees artifact attestations are enabled, you can require maximum strictness:

**What strict mode enforces:**
1. Verifier scripts MUST have GitHub Artifact Attestations
2. Lab Pack zip MUST have GitHub Artifact Attestations
3. All attestations MUST verify successfully via `gh attestation verify`

**When attestations are enforced:**
- Pre-publish gate in CI: `verify_verifier_attestations_strict.sh` verifies all verifier attestations
- Cold-machine simulation: Strict attestation verification for verifiers + Lab Pack
- No soft-skips or policy fallbacks

**Verifier attestation strict check:**
```bash
# Requires gh CLI + GITHUB_TOKEN
./verify_verifier_attestations_strict.sh --owner OWNER --repo REPO
```

This verifies attestations exist and pass for:
- `verify_release.sh`
- `verify_release.ps1`
- `verify_attestations.sh`

**Lab Pack attestation check:**
```bash
gh attestation verify Lab_Pack_SG_*.zip --owner OWNER
```

**Full chain of trust (maximum strictness):**
```
Verifier pinned → Verifier signature verified → Verifier attestation verified
    ↓
Verifier verifies Lab Pack → Lab Pack signature verified → Lab Pack attestation verified
```

**Common failure modes:**

| Error | Cause | Fix |
|-------|-------|-----|
| `gh attestation verify` returns forbidden | Org policy/plan doesn't allow attestation access | Enable attestations in org settings or use policy-aware mode |
| Attestation exists for zip but not verifiers | Verifiers not attested | Ensure `actions/attest-build-provenance@v1` runs on verifier scripts |
| Cosign verifies but attestation fails | Signature valid but attestation missing/invalid | Check workflow has `attestations: write` permission |

**Policy-aware vs strict:**
- **Policy-aware** (`verify_attestations.sh`): Soft-skip if attestations blocked, continue with warning
- **Strict** (`verify_verifier_attestations_strict.sh`): Hard fail if attestations missing or blocked

Use strict mode only when your org guarantees attestations are available.
- **warn mode**: Development/testing environments where you want visibility but not blocking
- **off mode**: Manual verification on trusted machines

---

## Recommended deployment rule

**Only deploy the Lab Pack if:**

✅ SHA256 OK  
✅ cosign bundle verification OK  
✅ (optional) GitHub attestation checks OK  
✅ (optional, strict environments) Verifier pin check OK  
✅ (optional, maximum strictness) Verifier attestations OK + Lab Pack attestation OK
