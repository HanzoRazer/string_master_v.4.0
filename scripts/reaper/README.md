# Reaper Scripts for Smart Guitar

FAST feedback scripts for Reaper DAW integration with sg-agentd.

## Scripts

| Script | Hotkey | Description |
|--------|--------|-------------|
| `reaper_sg_pass_and_regen.lua` | F9 | Report PASS verdict, request next clip |
| `reaper_sg_struggle_and_regen.lua` | F10 | Report STRUGGLE verdict, request easier clip |

## Installation

1. Copy the `scripts/reaper/` folder to your Reaper scripts directory
2. In Reaper: Actions → Show action list → Load ReaScript
3. Load both `.lua` files
4. Bind to hotkeys (recommended: F9/F10)

## Requirements

- `curl` in PATH (for HTTP requests)
- sg-agentd running on `localhost:7878`

## Episode 11: Coach Hints

After a successful verdict, the console displays a coach narrative:

```
SG: PASS → regen queued (clip_id=abc123)
SG: coach → Nice improvement. Keep the groove steady... Tempo up by 3 BPM. Density: medium. Sync: light.
```

The hint is policy-driven and deterministic (5 score bands × 3 trend buckets).

## Server Response Shape

The scripts handle three possible response shapes:

```lua
-- Preferred (top-level suggested)
{ "status": "ok", "regen": {...}, "suggested": { "coach_hint": "..." } }

-- Alternate (nested under regen)
{ "status": "ok", "regen": { "suggested": { "coach_hint": "..." } } }

-- Minimal (top-level coach_hint)
{ "status": "ok", "regen": {...}, "coach_hint": "..." }
```

If `coach_hint` is missing, no narrative is printed (graceful fallback).
