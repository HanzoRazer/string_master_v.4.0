# Reaper Bundle Release Process

## Versioning
- Bundle version tracks repo release tags: `reaper-bundle-vX.Y.Z`
- Patch releases are allowed for script-only changes.

## Pre-release checklist
1) Run guard:
   - `python3 scripts/release/guard_reaper_bundle.py`

2) Build bundle:
   - `python3 scripts/release/build_reaper_bundle.py`

3) Verify zip contents:
   - includes `scripts/reaper/` (no `_deprecated/`)
   - includes `docs/contracts/SG_REAPER_CONTRACT_V1.md`

## Tag and publish
1) Create tag:
   - `git tag reaper-bundle-vX.Y.Z`
   - `git push origin reaper-bundle-vX.Y.Z`

2) CI will attach `smart_guitar_reaper_bundle.zip` as build artifact.
