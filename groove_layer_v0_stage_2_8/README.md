# Groove Layer v0 – Stage 2.8 (Vector 08: Tempo Drift Detection + Correction)

This cut adds **Vector 08** on top of Stage 2.7.

## All Vectors (cumulative)

| Vector | Stage | Feature |
|--------|-------|---------|
| 01 | 2.1 | Stable baseline |
| 02 | 2.2 | Hard instability corrective mode |
| 03 | 2.3 | Recovery / hysteresis |
| 04 | 2.4 | Missing engine context freeze |
| 05 | 2.5 | Probing + revert |
| 06 | 2.6 | Probe scheduling + cooldown decay |
| 07 | 2.7 | Probe success scoring + persist outcomes |
| 08 | 2.8 | **Tempo drift detection + correction** |

## New behavior (Vector 08)

When stable, the system now tracks tempo drift:

1. **Estimate player BPM** from event inter-onset intervals
2. **Compute drift percentage** from target tempo
3. **Accumulate drift** across windows (clamped to ±5% per window)
4. **Trigger correction** when accumulated drift exceeds ±3%:
   - `policy: "correct_drift"` with nudge proportional to accumulated drift
   - Reset accumulator after correction

Small drift (< 3% accumulated):
- `policy: "follow_player"` — gently track the player

Large drift (≥ 3% accumulated):
- `policy: "correct_drift"` — actively nudge tempo back toward target

## State additions

```python
# Tempo drift tracking (Vector 08)
last_tempo_bpm: Optional[float] = None
drift_accum: float = 0.0  # accumulated drift percentage
```

## New fixtures

- `fixtures/vectors/08a_small_drift_follow.json` → expects `policy: "follow_player"`
- `fixtures/vectors/08b_large_drift_correct.json` → expects `policy: "correct_drift"`

### 08a: Small drift (player ~98 BPM vs target 100 BPM)

```json
{
  "engine_context": {"tempo_bpm_target": 100},
  "events": [
    {"t_onset_ms": 0},
    {"t_onset_ms": 610},
    {"t_onset_ms": 1220}
  ]
}
```

Inter-onset: 610ms → ~98 BPM → drift ~-2% → `follow_player`

### 08b: Large drift (player ~80 BPM vs target 100 BPM)

```json
{
  "engine_context": {"tempo_bpm_target": 100},
  "events": [
    {"t_onset_ms": 0},
    {"t_onset_ms": 750},
    {"t_onset_ms": 1500}
  ]
}
```

Inter-onset: 750ms → 80 BPM → drift -20% → clamped to -5% → accumulates → `correct_drift`

## Run

```bash
cd groove_layer_v0_stage_2_8
python -m pytest -q
```

## Drift reset conditions

The drift accumulator is reset to 0.0 when:
- Instability is detected (Vector 02)
- Engine context is missing (Vector 04)
- Correction is triggered (drift exceeds threshold)

This prevents stale drift from affecting recovery.
