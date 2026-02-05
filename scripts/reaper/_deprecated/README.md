# Deprecated Reaper Scripts (Do Not Use)

These scripts are kept only for historical reference.

## Why deprecated?
They are strict subsets of the canonical shipper:
- `reaper_sg_bundle_shipper_set_all.lua`

Keeping multiple "setter" scripts causes classroom/operator error:
- users run the wrong setter
- required keys are missing (host_port / session_id)
- panel and autorun behave inconsistently

## Use instead
Run this once:
- `../reaper_sg_bundle_shipper_set_all.lua`

Then run:
- `../reaper_sg_setup_doctor.lua`
- `../reaper_sg_panel.lua`
