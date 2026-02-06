# sg-agentd Endpoint Inventory V1 (Reaper Surface)

This document enumerates HTTP endpoints used by Reaper scripts and how they are probed for compatibility.

## Base URL
Reaper scripts construct:
- api_base = http://{SG_AGENTD/host_port}

Default host_port fallback:
- 127.0.0.1:8420

Transport:
- SG_AGENTD/transport = auto|curl|pwsh (optional override)
- Implemented in scripts/reaper/sg_http.lua

## Endpoint Compatibility Rules
- "OK" = HTTP 2xx
- "WARN" = HTTP 3xx or 4xx (endpoint exists but requires params/auth/body) depending on endpoint
- "FAIL" = transport error, timeout, DNS, refused, or 5xx

### 1) Health / Identity
- GET /status
  - Expect: 200 with text or JSON indicating service is up
  - Required for: Doctor, Ping scripts, transport probe

### 2) Session Index / Trends
- GET /session_index?session_id={id}
  - Expect: 200 JSON object (recommended)
  - Used by: Panel, Timeline/Trend minimal actions
  - If missing: panel should degrade gracefully

Optional candidates (probe-only; may or may not exist):
- GET /timeline?session_id={id}
- GET /trend?session_id={id}

### 3) Generation
- POST /generate
  - Content-Type: application/json
  - Minimal payload suggested:
    { "session_id": "...", "request_id": "..." }
  - Expected response: JSON (preferred) but scripts should tolerate text
  - coach_hint compatibility chain:
    1) suggested_adjustment.coach_hint
    2) regen.suggested.coach_hint
    3) coach_hint

### 4) Feedback + Regen (PASS/STRUGGLE)
Implementation-defined endpoint(s). The repo historically used PASS/STRUGGLE scripts that POST to a feedback/regen route.
Because naming may differ between deployments, the probe script tests multiple candidate routes.

Candidate routes (probe-only; configure to match your server):
- POST /feedback_and_regen
- POST /pass_and_regen
- POST /struggle_and_regen
- POST /regen

Payload shape (minimal probe):
{ "session_id": "...", "clip_id": "probe_clip", "verdict": "PASS"|"STRUGGLE" }

Expected response:
- Any 2xx accepted.
- If JSON, coach_hint chain applies.

## Probe Script Behavior
The probe script:
- Reads host_port + session_id from ExtState (with fallbacks)
- Uses sg_http.lua chosen transport
- Probes endpoints with safe minimal requests
- Prints a matrix row per endpoint with: METHOD, PATH, HTTP, RESULT, NOTE
