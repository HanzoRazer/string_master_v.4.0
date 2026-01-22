# Groove Layer v0 – Stage 2.9 (Vector 09: Density / Tempo Guardrails)

Adds a hard interaction rule between **tempo correction** and **density probing**.

## Vector 09 rules
Density probes are **forbidden** when:
- tempo.policy == "correct_drift"
- system is unstable
- last_loop_policy == "micro_loop"

This prevents simultaneous adaptation along orthogonal axes.

## New fixtures
- 09a_no_probe_during_tempo_correction.json
- 09b_no_probe_during_micro_loop.json

## Run
```bash
python -m pytest -q
```
