# sg_agentd — Redirect Notice

**This directory is a stub.**

The authoritative FastAPI server for the Smart Guitar practice coaching agent has been moved to its own repository:

**https://github.com/HanzoRazer/sg-agentd**

## What is sg-agentd?

`sg-agentd` is a FastAPI daemon that wraps the `zt_band` practice pattern engine for HTTP-accessible practice sessions. It runs on the Pi 5 Music Brain embedded in the Smart Guitar.

### Runtime Configuration
- **Host:** 127.0.0.1
- **Port:** 8420
- **Entry:** `sg_agentd.main:app`

### Key Endpoints
| Path | Method | Description |
|------|--------|-------------|
| `/generate` | POST | Generate a new clip bundle |
| `/regenerate` | POST | Regenerate with modified params |
| `/bundle/{clip_id}` | GET | Retrieve a clip bundle |
| `/exercises` | GET | List available exercises |
| `/tags` | GET | List all tags |

## Why the Split?

The `sg-agentd` server is deployed independently on the Pi 5, while `string_master` (and its `zt_band` engine) remains the source library. This separation allows:

1. Independent versioning of server vs. engine
2. Cleaner deployment to embedded hardware
3. Luthiers ToolBox can proxy to sg-agentd without bundling the full server

## Related Files

- `src/zt_band/` — The pattern generation engine (still in this repo)
- `src/shared/zone_tritone/` — Tritone zone theory (still in this repo)

---

*Last updated: 2026-03-25*
