# Smart Guitar — Snapshot v1.0.0-offline

**Release Date**: February 4, 2026  
**Status**: Production-ready for offline use

---

## Version Set

This snapshot defines the known-good version combination for the Smart Guitar offline trainer.

| Component | Repository | Commit | Tag |
|-----------|------------|--------|-----|
| **string_master** | HanzoRazer/string_master_v.4.0 | `1947d33` | v1.0.0-offline |
| **sg-agentd** | (local) | `4424250` | v1.0.0-offline |
| **sg-coach** | (local) | `f556a5b` | v1.0.0-offline |
| **sg-spec** | (dependency) | — | v1-locked |

---

## Reaper Scripts Version

**Folder**: `scripts/reaper/`

| Script | Purpose |
|--------|---------|
| `dkjson.lua` | JSON parser dependency |
| `reaper_sg_setup_doctor.lua` | FTUE diagnostics |
| `reaper_sg_setup_doctor_autorun.lua` | Configurable autorun |
| `reaper_sg_set_action_ids_once.lua` | One-time action ID setter |
| `reaper_sg_setup_autorun_generate_then_pass.lua` | Zero-prompt autorun |
| `reaper_sg_generate.lua` | Core generation |
| `reaper_sg_generate_queued_nextbar.lua` | Bar-aligned generation |
| `reaper_sg_regenerate.lua` | Regeneration |
| `reaper_sg_regenerate_queued_nextbar.lua` | Bar-aligned regeneration |
| `reaper_sg_pass_and_regen.lua` | PASS verdict + regen |
| `reaper_sg_struggle_and_regen.lua` | STRUGGLE verdict + regen |
| `reaper_sg_practice_loop.lua` | Combined feedback loop |
| `reaper_sg_session_timeline.lua` | Session history view |
| `reaper_sg_session_trend_summary.lua` | Trend analysis |
| `reaper_sg_session_trend_compact.lua` | One-line trend |

---

## Compatibility

| Software | Minimum Version | Tested On |
|----------|-----------------|-----------|
| Reaper | 6.0+ | 7.x |
| Python | 3.10+ | 3.14 |
| OS | Windows 10+, macOS 12+, Linux | Windows 11 |

---

## Bundle Layout

Generated artifacts at `~/Downloads/sg-bundles/{date}/{clip_id}/`:

```
clip.mid            # Combined MIDI
clip.comp.mid       # Comping track
clip.bass.mid       # Bass track
clip.tags.json      # Metadata
clip.runlog.json    # Provenance
clip.coach.json     # Deterministic coach hint
```

Session index at `~/Downloads/sg-bundles/{date}/session.index.json`

---

## API Endpoints

Server: `http://127.0.0.1:8420`

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/status` | GET | Health check |
| `/generate` | POST | Generate MIDI |
| `/regenerate` | POST | Regenerate with adjustment |
| `/feedback` | POST | Submit verdict |
| `/feedback_and_regen` | POST | Feedback + regenerate |
| `/session_index` | GET | Session history |

---

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `SG_AGENTD_HOST` | `127.0.0.1` | Server bind host |
| `SG_AGENTD_PORT` | `8420` | Server bind port |
| `SG_AGENTD_BUNDLE_DIR` | `~/Downloads/sg-bundles` | Bundle output |
| `SG_BUNDLE_TTL_HOURS` | `168` | Retention (7 days) |
| `SG_BUNDLE_COLLISION_POLICY` | `overwrite` | Collision handling |
| `SG_EMIT_ERROR_BUNDLES` | `true` | Write error artifacts |

---

## Support Boundaries

This release is:
- ✅ **Offline-first** — no internet required
- ✅ **No SaaS** — no accounts or subscriptions
- ✅ **Deterministic** — reproducible outputs
- ✅ **Self-contained** — bundles are source of truth

Optional enhancements (AI coach, cloud sync) are **not included** in this snapshot.

---

## Release Checklist

- [x] All docs in place (START_HERE, CONTRACTS, REAPER_SCRIPTS, ACCEPTANCE)
- [x] Setup Doctor works
- [x] Generate/Regenerate produce valid bundles
- [x] PASS/STRUGGLE feedback loop works
- [x] Session index appends correctly
- [x] 3/4 and 6/8 meters handled
- [ ] Tag: `v1.0.0-offline`

---

## Verification

To verify this snapshot:

1. Clone string_master at commit `1947d33`
2. Run Setup Doctor in Reaper
3. Complete acceptance matrix (see ACCEPTANCE.md)
4. Confirm all bundle files present

---

## Known Limitations

- Single-user only (no multi-session coordination)
- No cloud backup of bundles
- AI coach features require separate installation
- Windows-primary testing (macOS/Linux should work but less tested)

---

## Changelog Since Last Snapshot

- Added Episode 12 FTUE (Setup Doctor)
- Added Episode 12.1 Autorun variants
- Added one-time action ID setter
- Removed misplaced sg_agentd code from string_master
- Added hardening documentation

---

**This snapshot is the "freeze point" for offline-first v1.0.**
