# Phase 11.2: CI Verification Gate

**Status**: ✅ Complete (commit 5771318)  
**Date**: 2026-02-02

---

## Overview

Phase 11.2 adds **pre-publish verification automation** to the release pipeline. The workflow now verifies artifacts (SHA256 + cosign bundle) BEFORE creating the GitHub Release, ensuring published assets are always verifiable.

---

## Architecture

### Verification Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. build-lab-pack (matrix: Ubuntu/Windows/macOS)              │
│    - Build deterministic zip + metadata                        │
│    - Policy + structure validation                             │
│    - Upload: lab-pack-tag-{os}                                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. guard-compare-builds                                         │
│    - Assert manifest + sha256 identical across all OS          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. verify-ubuntu-artifacts (NEW)                                │
│    - Download Ubuntu artifacts                                  │
│    - cosign sign-blob → .sigstore.json bundle                  │
│    - Run verify_release.sh (SHA256 + cosign verify-blob)      │
│    - Upload: lab-pack-verified-ubuntu (includes bundle)        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. publish-ubuntu-only                                          │
│    - Download verified artifacts (with .sigstore.json)         │
│    - Generate provenance + SBOM                                 │
│    - Verify .sigstore.json exists (created by verify job)      │
│    - Create GitHub attestations (build provenance + SBOM)      │
│    - Upload all assets to GitHub Release                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## What Changed

### New Job: `verify-ubuntu-artifacts`

**Purpose**: Cryptographically sign and verify artifacts before publish.

**Steps**:
1. Download Ubuntu build artifacts
2. Install cosign via `sigstore/cosign-installer@v3`
3. Create sigstore bundle:
   ```bash
   cosign sign-blob "$ZIP" --yes --bundle "${ZIP}.sigstore.json"
   ```
4. Run verification script:
   ```bash
   scripts/release/verify_release.sh --no-gh
   ```
5. Verify metadata exists (sha256, manifest, sigstore bundle)
6. Upload verified artifacts to `lab-pack-verified-ubuntu`

**Permissions**:
- `id-token: write` — for cosign verification (keyless signing)
- `contents: read` — for checkout

---

### Updated Job: `publish-ubuntu-only`

**Changes**:

| Before | After |
|--------|-------|
| `needs: [determinism-test, guard-compare-builds]` | `needs: [determinism-test, guard-compare-builds, verify-ubuntu-artifacts]` |
| Downloads from `lab-pack-tag-ubuntu-latest` | Downloads from `lab-pack-verified-ubuntu` |
| Runs `cosign sign-blob` to create bundle | Verifies bundle exists (created by verify job) |
| Uses locally created .sigstore.json | Uses pre-verified .sigstore.json from verify job |

**Retained Steps**:
- Generate provenance + SBOM (SPDX)
- Create GitHub attestations (build provenance + SBOM)
- Upload all assets to GitHub Release

**Removed Steps**:
- ❌ `Install Cosign` step (no longer needed)
- ❌ `Cosign sign (keyless) Lab Pack zip` step (bundle created by verify job)

---

## Why This Matters

### Problem

Without verification gate, the workflow could publish artifacts that:
- Have corrupted SHA256 checksums
- Cannot be verified with cosign
- Fail verification when users try `verify_release.sh`

### Solution

**Verification runs BEFORE release creation**:
- If verification fails → workflow stops → no release published
- If verification passes → artifacts uploaded to GitHub Release

**Result**: Published artifacts are **guaranteed verifiable** by end users.

---

## Determinism Guarantee

The workflow now has **7 validation layers**:

1. **determinism-test**: Build twice, assert SHA256 match
2. **Policy check**: Only blessed files in zip
3. **Structure lint**: Required files + CONTRACT headers
4. **guard-compare-builds**: Cross-OS parity (manifest + SHA256)
5. **verify-ubuntu-artifacts**: SHA256 + cosign bundle verification ⭐ NEW
6. **GitHub attestations**: Build provenance + SBOM attestations
7. **Release notes**: Checksum + manifest in release body

---

## Testing

### Manual Test (Local)

```bash
# Build Lab Pack
python scripts/release/build_lab_pack.py
python scripts/release/make_release_metadata.py

# Sign with cosign
ZIP="$(ls -1 dist/Lab_Pack_SG_*.zip | head -n 1)"
cosign sign-blob "$ZIP" --yes --bundle "${ZIP}.sigstore.json"

# Verify
./scripts/release/verify_release.sh --no-gh
```

### CI Test (Push Tag)

```bash
git tag -a labpack-test-v11.2 -m "Test Phase 11.2 verification gate"
git push origin labpack-test-v11.2
```

**Expected behavior**:
1. `determinism-test` passes (build twice, match)
2. `build-lab-pack` passes (all 3 OS)
3. `guard-compare-builds` passes (cross-OS parity)
4. `verify-ubuntu-artifacts` passes (SHA + cosign verification)
5. `publish-ubuntu-only` runs (creates GitHub Release)

**If verification fails**: Workflow stops at step 4, no release published.

---

## Verification Script Usage

### In CI (verify-ubuntu-artifacts job)

```bash
cd verify/dist
chmod +x ../../scripts/release/verify_release.sh
../../scripts/release/verify_release.sh --no-gh
```

**Flags**:
- `--no-gh`: Skip GitHub attestation check (not needed in CI, assets not yet published)

### End Users (After Download)

```bash
# Download release assets
gh release download labpack-v1.0.0 -R owner/repo

# Verify with script
./verify_release.sh  # Full verification (SHA + cosign + GH attestations)
```

---

## File Changes

### Modified: `.github/workflows/release_lab_pack.yml`

**Additions** (+76 lines):
- New `verify-ubuntu-artifacts` job (68 lines)
- Updated `publish-ubuntu-only` dependencies
- Changed artifact download source
- Added bundle existence check

**Removals** (-12 lines):
- Duplicate cosign installation
- Duplicate signing step

**Net**: +64 lines (76 - 12)

---

## Dependencies

**Runtime**:
- `cosign` (installed via `sigstore/cosign-installer@v3`)
- `verify_release.sh` (in `scripts/release/`)
- `sha256sum` or `shasum` (system utility)

**Permissions**:
- `id-token: write` — for cosign keyless signing
- `contents: write` — for GitHub Release creation
- `attestations: write` — for GitHub attestations

---

## Security Properties

### Cryptographic Guarantees

1. **SHA256**: Detects corruption/tampering (256-bit collision resistance)
2. **Cosign bundle**: Keyless signature via Sigstore (ECDSA + transparency log)
3. **GitHub attestations**: Build provenance tied to commit + workflow

### Verification Chain

```
Build (deterministic) → Sign (cosign) → Verify (script) → Publish (GH Release)
                                              ↑
                                         GATE: If verify fails,
                                               publish blocked
```

**Property**: Published assets = verified assets (no gap).

---

## Future Extensions

### Optional Phase 11.3

**Automated attestation verification**:
- Add step to `verify-ubuntu-artifacts` job
- Use `gh attestation verify` to check uploaded attestations
- Blocks publish if attestation verification fails

**Implementation**:
```yaml
- name: Verify GitHub attestations (optional)
  run: |
    gh attestation verify "$ZIP_PATH" -R ${{ github.repository }}
```

---

## Related Phases

- **Phase 10.6**: Deterministic zip generation (byte-identical across OS)
- **Phase 10.7**: Determinism unit test (double-build validation)
- **Phase 10.9**: Release gate + enriched release notes
- **Phase 11**: Provenance + SBOM + signing + attestations
- **Phase 11.1**: User verification docs + scripts
- **Phase 11.2**: CI verification automation (this document) ⭐

---

## Rollback Plan

If Phase 11.2 causes issues, revert to Phase 11.1 state:

```bash
git revert 5771318
git push origin master
```

**Effect**: Removes `verify-ubuntu-artifacts` job, restores duplicate signing in publish job.

---

## Success Criteria

✅ **Verification gate works**:
- Job runs successfully with valid artifacts
- Job fails (blocks publish) with invalid artifacts

✅ **No duplicate work**:
- Cosign signing happens once (verify job)
- Publish job uses pre-verified bundle

✅ **Published artifacts verifiable**:
- Users can run `verify_release.sh` successfully
- SHA256 + cosign + GitHub attestations all pass

✅ **Workflow is resilient**:
- If verification fails, workflow stops before publishing
- If verification passes, release is created normally

---

**Status**: ✅ Production-ready (commit 5771318)
