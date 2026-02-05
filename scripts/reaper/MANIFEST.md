# Smart Guitar — Reaper Script Manifest (Blessed)

This folder is the **single blessed bundle** for Reaper integration with sg-agentd.

## Canonical setup order (recommended)
1. `reaper_sg_bundle_shipper_set_all.lua`  
   One-time config shipper. Writes persistent ExtState keys:
   - action IDs (5)
   - session_id
   - host_port

2. `reaper_sg_setup_doctor.lua`  
   Verifies installation health (files present, server reachable, tracks/markers sanity).

3. `reaper_sg_panel.lua`  
   UI panel for session status, timeline, trends, and one-click actions.

4. Hotkeys
   - `reaper_sg_pass_and_regen.lua` (F9 recommended)
   - `reaper_sg_struggle_and_regen.lua` (F10 recommended)

5. Optional autorun
   - `reaper_sg_setup_autorun_generate_then_pass.lua`

## Scripts (blessed)
| Script | Purpose | Requires ExtState |
|---|---|---|
| `reaper_sg_bundle_shipper_set_all.lua` | One-time config shipper | writes all |
| `reaper_sg_setup_doctor.lua` | Installation verifier | reads host_port (fallback ok) |
| `reaper_sg_setup_doctor_autorun.lua` | Guided setup + autorun helper | reads/writes some keys |
| `reaper_sg_panel.lua` | Panel UI + session tools | reads host_port/session_id/actions |
| `reaper_sg_pass_and_regen.lua` | PASS verdict + regen | reads host_port (fallback ok) |
| `reaper_sg_struggle_and_regen.lua` | STRUGGLE verdict + regen | reads host_port (fallback ok) |
| `reaper_sg_setup_autorun_generate_then_pass.lua` | zero-prompt generate→pass | reads action_generate/action_pass_regen |

## Deprecated
Legacy setters live in: `scripts/reaper/_deprecated/`

They must not be referenced in docs or onboarding.
