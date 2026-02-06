# Release Scripts

Build and release automation for Smart Guitar.

## Build Lab Pack

Creates a deterministic zip file for laboratory deployment.

```bash
python scripts/release/build_lab_pack.py
```

**Output**: `dist/Lab_Pack_SG_<bundle_version>.zip`

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
    # ... add new files here ...
]
```

## CI/CD Integration (Future)

Optional Phase 10.2: Add GitHub Actions workflow to build and attach Lab Pack zip on tagged releases.
