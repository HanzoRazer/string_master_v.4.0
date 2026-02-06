# SG Reaper Contract V1

This document is the single source of truth for Smart Guitar Reaper scripts.

## Scope
Applies to:
- scripts/reaper/*.lua
- sg-agentd endpoints used by those scripts

## ExtState Contract (SG_AGENTD section)
All keys live under:
- ExtState section: `SG_AGENTD`

### Keys written by the canonical shipper
The canonical shipper script must write these persistent keys (persist=true):
- `action_generate`         (string, _RS... command id)
- `action_pass_regen`       (string, _RS... command id)
- `action_struggle_regen`   (string, _RS... command id)
- `action_timeline`         (string, _RS... command id)
- `action_trend`            (string, _RS... command id)
- `session_id`              (string, non-empty)
- `host_port`               (string, host:port)

### Optional configuration keys
These keys may be set via one-time setter scripts (persist=true):
- `lan_mode`                (string: "true"|"false", default="false")
  - Controls LAN readiness evaluation in probe scripts
  - true: localhost/127.0.0.1 targets considered LAN-ready (per-machine labs)
  - false: loopback targets considered misconfigured for LAN deployment
- `transport`               (string: "curl"|"powershell"|empty)
  - Administrative override for HTTP transport selection
  - Empty/unset: auto-detect (curl preferred, powershell fallback)

### Defaults / fallbacks
If `host_port` is unset or invalid, scripts must fallback to:
- `127.0.0.1:8420`

### Validation rules
- host_port must match: `^[%w%.%-]+:%d+$`
- action ids must typically start with `_RS` (warn if not)
- action ids must resolve via `reaper.NamedCommandLookup(id)` (fail if present but not resolvable)

## JSON Dependency
All scripts must load:
- `scripts/reaper/json.lua` (rxi json; provides `json.encode` and `json.decode`)

No script may reference `dkjson.lua` in V1.

## Shared Helper Library (Phase 6)
`scripts/reaper/sg_http.lua` centralizes:
- ExtState reads/writes (host_port, session_id, action ids)
- HTTP via `reaper.ExecProcess` + curl (with timeouts)
- JSON loading (`sg.load_json()`)
- coach_hint extraction (`sg.pick_coach_hint(decoded)`)

Scripts using `sg_http.lua` must:
- `dofile(script_dir .. "sg_http.lua")` at top of script
- Use `sg.http_post_json(path, body, timeout_ms)` for POST calls
- Use `sg.http_get(path, timeout_ms)` for GET calls
- Use `sg.pick_coach_hint(decoded)` for coach hint extraction

## HTTP Dependency
All network scripts must use:
- `curl` via `reaper.ExecProcess(cmd, timeout_ms)`

No hotkey-bound script may use `os.execute` (prevents indefinite hang).

### Timeouts
- hotkeys (PASS/STRUGGLE): 5000 ms
- panel/doctor: 2500–8000 ms depending on polling behavior

## sg-agentd Endpoints Used by Reaper
- `GET /status` (doctor reachability check)
- verdict/regen endpoint(s) consumed by PASS/STRUGGLE scripts (implementation-defined)

Scripts must:
- build API base as `http://` + host_port
- never assume https or path prefixes in V1

## coach_hint Contract (canonical output + backward compatibility)
Canonical location for coach hint:
1) `suggested_adjustment.coach_hint`

Backward-compat fallbacks supported:
2) `regen.suggested.coach_hint`
3) `coach_hint`

Scripts must implement lookup in that priority order.

If no coach hint exists, scripts must not error; they may print no narrative.

## Versioning
- Scripts must include: `-- CONTRACT: SG_REAPER_CONTRACT_V1`
- Any breaking change requires a V2 doc and matching header bump in scripts.
