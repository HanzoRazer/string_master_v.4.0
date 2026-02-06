# Release Scripts

Build and release automation for Smart Guitar.

## Build Lab Pack

Creates a deterministic zip file for laboratory deployment.

```bash
python scripts/release/build_lab_pack.py
python scripts/release/generate_checksums.py
```

**Outputs**: 
- `dist/Lab_Pack_SG_<bundle_version>.zip`
- `dist/Lab_Pack_SG_<bundle_version>.zip.sha256`
- `dist/Lab_Pack_SG_<bundle_version>.manifest.txt`

**Contents**:
- `README_LAB.txt` - Installation instructions
- `scripts/reaper/` - Blessed Reaper scripts for lab setup
  - Bootstrap script (`reaper_sg_lab_bootstrap.lua`)
  - Setup and diagnostic tools (doctor, probe, ping)
  - Configuration setters (transport, lan_mode)
  - Core action scripts (generate, pass/struggle, timeline, trend)
  - Panel UI (optional)

**Versioning**: Reads version from `scripts/reaper/SG_BUNDLE_VERSION.txt`

**Determinism**: Only files listed in `BLESSED_REAPER_FILES` are included.

## Usage

From repository root:

```bash
# Build lab pack
python scripts/release/build_lab_pack.py

# Check output
ls dist/Lab_Pack_SG_*.zip
```

## Adding Files to Lab Pack

Edit `BLESSED_REAPER_FILES` list in `build_lab_pack.py`:

```python
BLESSED_REAPER_FILES = [
    "SG_BUNDLE_VERSION.txt",
    "json.lua",
    "sg_http.lua",
   Verify Release

Verify downloaded Lab Pack integrity:

```bash
# Linux/macOS
sha256sum -c Lab_Pack_SG_<bundle_version>.zip.sha256

# Windows PowerShell
$hash = (Get-FileHash -Algorithm SHA256 Lab_Pack_SG_<bundle_version>.zip).Hash.ToLower()
$expected = (Get-Content Lab_Pack_SG_<bundle_version>.zip.sha256).Split()[0]
if ($hash -eq $expected) { Write-Host "OK: checksum verified" } else { Write-Host "FAIL: checksum mismatch" }
```

## CI/CD Integration

### GitHub Actions

Workflow: `.github/workflows/release_lab_pack.yml`
- Triggers on tags: `v*`, `labpack-*`, `reaper-bundle-*`
- Builds zip, generates checksums/manifest
- Creates GitHub Release with all artifacts

### GitLab CI

Config: `.gitlab-ci.yml`
- Same tag trigger patterns
- Outputs artifacts to job storage
- Creates GitLab Release with asset links

## CI/CD Integration (Future)

Optional Phase 10.2: Add GitHub Actions workflow to build and attach Lab Pack zip on tagged releases.
