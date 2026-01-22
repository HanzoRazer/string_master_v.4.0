# Groove Layer v0 — Stage 3.0 (Clean Engine Skeleton)

This cut **resets the implementation shape** (not the behavior) to prevent quote/patch corruption issues.
It is a **clean, structured baseline** intended for additive Stage 3.x development.

## Design goals
- **No source rewriting / string patching**. Changes must be authored as code.
- Split **fast window state** (per 10–30s window) vs **slow traits** (learned over sessions).
- Explicit guardrails so orthogonal adaptors (tempo, density, probing) can't fight.
- Minimal, testable surfaces:
  - `event_model.py` (input events)
  - `state.py` (fast/slow state + hydration)
  - `policy.py` (decision logic)
  - `engine.py` (orchestration + I/O contract)

## Run
```bash
python -m pytest -q
```

## Invariants (locked)
- Inputs are **event fixtures** (no audio/MIDI blobs in v0).
- Output is **control contract** (tempo/arrangement/looping hints).
- `prior_state_hint` is optional and may be partial.
