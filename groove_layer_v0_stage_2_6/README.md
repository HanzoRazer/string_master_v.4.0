# Groove Layer v0 – Stage 2.6 (Probe Scheduling + Cooldown Decay)

This cut adds **Vector 06** on top of Stage 2.5 probing + revert.

## New behavior
- `probe_cooldown_windows` decays each window (blocks probe start until 0).
- `next_probe_in_windows` schedules probes so we don't probe every stable window.
  - Scheduler ticks down on **stable** windows only.
  - Probe can start only when `next_probe_in_windows == 0` and cooldown is 0.

## New fixtures
- `06a_cooldown_blocks_probe.json` → remains baseline `medium`
- `06b_cooldown_expired_probe_starts.json` → probe starts (`dense`)
- `06c_scheduler_blocks_until_zero.json` → remains baseline `medium`

## Run
```bash
python -m pytest -q
```
