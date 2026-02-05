# Reaper Scripts for Smart Guitar

Reaper DAW integration scripts for sg-agentd.

This folder is designed to be copied as a bundle and used with a single canonical setup path.

## Quick Start (Blessed Path)

### 1) Copy bundle into Reaper scripts folder
Copy this entire folder:
- `scripts/reaper/`

Into your Reaper scripts directory.

### 2) Load scripts in Reaper
Reaper: **Actions → Show action list → ReaScript → Load**

Load these scripts:

**One-time configuration**
- `reaper_sg_bundle_shipper_set_all.lua`

**Verification**
- `reaper_sg_setup_doctor.lua`

**Panel**
- `reaper_sg_panel.lua`

**Hotkeys**
- `reaper_sg_pass_and_regen.lua` (recommended: F9)
- `reaper_sg_struggle_and_regen.lua` (recommended: F10)

**Optional**
- `reaper_sg_setup_autorun_generate_then_pass.lua`

## Requirements

- `curl` in PATH (HTTP requests)
- sg-agentd running (default: `127.0.0.1:8420`)

## Server target (host_port)

The canonical server target is stored in Reaper ExtState:

- `SG_AGENTD/host_port`

If unset, scripts fall back to:
- `127.0.0.1:8420`

To change server target:
- re-run `reaper_sg_bundle_shipper_set_all.lua` after editing `HOST_PORT`

LAN examples:
- `192.168.1.50:8420`

## Episode 11: Coach Hints

After a successful verdict, the console displays a coach narrative:

```
SG: PASS → regen queued (clip_id=abc123)
SG: coach → Nice improvement. Keep the groove steady... Tempo up by 3 BPM. Density: medium. Sync: light.
```

## Server Response Shape (coach_hint)

The verdict scripts handle multiple response shapes for backward compatibility:

```json
{ "suggested_adjustment": { "coach_hint": "..." } }
{ "regen": { "suggested": { "coach_hint": "..." } } }
{ "coach_hint": "..." }
```

If coach_hint is missing, no narrative is printed (graceful fallback).

## Deprecated setters

Legacy setter scripts have been moved to:

* `scripts/reaper/_deprecated/`

Do not use them. Use the canonical shipper:

* `reaper_sg_bundle_shipper_set_all.lua`

## Inventory

See:

* `scripts/reaper/MANIFEST.md`
