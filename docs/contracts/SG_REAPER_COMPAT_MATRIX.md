# SG Reaper Compatibility Matrix (Template)

Use this template to record compatibility between:
- Reaper bundle version
- sg-agentd build/version
- OS + transport
- Endpoint availability

---

## Test Run Metadata

- Date (local):
- Operator:
- Machine / Lab ID:
- OS:
- Reaper version:
- Bundle version (`scripts/reaper/SG_BUNDLE_VERSION.txt`):
- sg-agentd host_port:
- Transport override (`SG_AGENTD/transport`):
- Transport chosen (sg_http.lua):

---

## Endpoint Results

Legend:
- OK = 2xx
- WARN = 3xx or 4xx (endpoint exists but may require params/body)
- FAIL = timeout/transport failure or 5xx

| Method | Path | HTTP | Result | Time (ms) | Notes |
|-------:|------|-----:|--------|----------:|-------|
| GET | /status |  |  |  |  |
| GET | /session_index?session_id=... |  |  |  |  |
| GET | /timeline?session_id=... |  |  |  |  |
| GET | /trend?session_id=... |  |  |  |  |
| POST | /generate |  |  |  |  |
| POST | /feedback_and_regen |  |  |  |  |
| POST | /pass_and_regen |  |  |  |  |
| POST | /struggle_and_regen |  |  |  |  |
| POST | /regen |  |  |  |  |

---

## Notes / Follow-ups

- 
