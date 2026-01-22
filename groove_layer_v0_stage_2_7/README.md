# Groove Layer v0 – Stage 2.7 (Vector 07: Probe Scoring + Persist Outcomes)

This cut adds **Vector 07** on top of Stage 2.6.

## New behavior
When a probe completes:
- Score the window from available event fields (confidence + strength)
- Persist:
  - `probe_last_score`
  - `probe_last_outcome` (success/fail)
  - `probe_history` append

Schedule adapts minimally:
- success (>=0.90): `probe_interval_windows -= 1` (min 2)
- fail (<0.90): `probe_interval_windows += 1` (max 6) + cooldown(3)

## New fixtures
- `fixtures/vectors/07a_probe_success_decreases_interval.json`
- `fixtures/vectors/07b_probe_fail_increases_interval_sets_cooldown.json`

## Run
```bash
python -m pytest -q
```
