# Smart Guitar — Start Here

**Offline-first deterministic practice trainer for guitarists.**

This is a complete, self-contained system. No cloud account required. No SaaS subscription. Everything runs locally.

---

## What This Is

A practice loop that:
1. **Generates** MIDI backing tracks from chord markers in your DAW
2. **Adapts** difficulty based on your PASS/STRUGGLE feedback
3. **Tracks** your session history for trend visibility

All processing is deterministic and reproducible. The same inputs always produce the same outputs.

---

## Required Components

| Component | Location | Purpose |
|-----------|----------|---------|
| **Reaper Scripts** | `scripts/reaper/` | DAW integration (generate, feedback, visibility) |
| **sg-agentd** | Separate repo | HTTP server for MIDI generation |
| **dkjson.lua** | `scripts/reaper/dkjson.lua` | JSON parsing for Lua scripts |
| **Bundle Directory** | `~/Downloads/sg-bundles/` | Generated MIDI + metadata artifacts |

---

## 5-Minute Quickstart

### 1. Start the Server

```bash
cd sg-agentd
pip install -e .
uvicorn sg_agentd.main:app --host 127.0.0.1 --port 8420
```

### 2. Run Setup Doctor

In Reaper:
- Load `scripts/reaper/reaper_sg_setup_doctor.lua` as an Action
- Run it
- Fix any red errors (missing dkjson, server unreachable, etc.)

### 3. Create Chord Markers

In your Reaper project:
- Add markers at bar lines named like chords: `Dm7`, `G7`, `Cmaj7`
- Set a time selection over the bars you want to practice

### 4. Run Generate

- Load `scripts/reaper/reaper_sg_generate_queued_nextbar.lua` as an Action
- Run it (or bind to a hotkey)
- MIDI items appear on SG_COMP and SG_BASS tracks

### 5. Practice Loop

After practicing the generated phrase:
- **PASS** (felt good): Run `reaper_sg_pass_and_regen.lua`
- **STRUGGLE** (need easier): Run `reaper_sg_struggle_and_regen.lua`

The system adjusts difficulty and regenerates.

---

## If Something Breaks

### First: Run Setup Doctor

```
reaper_sg_setup_doctor.lua
```

It checks everything and prints actionable fixes.

### Common Issues

| Problem | Fix |
|---------|-----|
| "Server unreachable" | Start sg-agentd: `uvicorn sg_agentd.main:app --port 8420` |
| "dkjson.lua not found" | Copy `dkjson.lua` to `scripts/reaper/` folder |
| "No chord markers" | Add markers named like chords at bar positions |
| "Missing SG_COMP track" | Setup Doctor creates it automatically |
| "ExtState missing" | Run Generate once to initialize the chain |

### Console Output

All scripts print status to the Reaper console. Look for:
- `SG OK:` — success
- `SG WARN:` — non-fatal issue
- `SG ERR:` — blocking error with fix instructions

---

## Support Boundaries

This system is:
- ✅ **Offline-first** — no internet required after initial setup
- ✅ **No SaaS** — no accounts, no subscriptions, no cloud dependencies
- ✅ **Deterministic** — same inputs always produce same outputs
- ✅ **Self-contained** — bundle artifacts are your source of truth

Optional enhancements (AI coach, cloud sync) may be added later but are **never required**.

---

## Next Steps

- [REAPER_SCRIPTS.md](REAPER_SCRIPTS.md) — Full script reference
- [CONTRACTS.md](CONTRACTS.md) — Bundle and API contracts
- [ACCEPTANCE.md](ACCEPTANCE.md) — How to verify the system works

---

**Version**: v1.0.0-offline  
**Status**: Production-ready for offline use
