# Groove Layer v0 – Stage 2.5 (Probing + Revert)

Adds **probing** (Vector 05) on top of Stage 2.4 recovery/hysteresis.

## New behavior (v0 minimal)
- Probing is allowed only when stable and not in cooldown.
- Deterministic trigger for fixtures: when `stable_windows >= 2` and even, start a **density probe** to `dense`.
- If instability is detected while probing, the system:
  1) **reverts** the probe immediately (sets cooldown)
  2) falls through to **instability safety** (`micro_loop` + `sparse`) so the player is protected.

## Fixtures
- `05a_probe_start_density.json` → expects `density_target = dense`
- `05b_probe_revert_on_instability.json` → expects revert + `micro_loop`

## Run
```bash
python -m pytest -q
```
