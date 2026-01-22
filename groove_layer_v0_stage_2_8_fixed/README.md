# Groove Layer v0 – Stage 2.8 (Vector 08: Tempo Drift Clamp + Correction) — FIXED (non-regressing)

This stage is **Stage 2.7 + Vector 08**. It does **not** remove prior vectors (05–07).

## Vector 08 behavior
- Estimate player tempo from onset deltas (median delta)
- Clamp per-window drift to **±5%**
- Accumulate drift across windows (`drift_accum_pct`)
- If accumulated drift exceeds **±3%**, emit:
  - `tempo.policy = "correct_drift"`
  - `nudge_strength` clamped to **±0.30**
  - reset accumulator

Otherwise emit:
- `tempo.policy = "follow_player"`
- `nudge_strength = drift_pct` (±0.05 clamp)

## New fixtures
- `fixtures/vectors/08a_small_drift_follow_player.json`
- `fixtures/vectors/08b_accumulated_drift_triggers_correct.json`

## Run
```bash
python -m pytest -q
```
