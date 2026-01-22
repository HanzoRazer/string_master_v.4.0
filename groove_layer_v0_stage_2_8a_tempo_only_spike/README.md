# Groove Layer v0 — Stage 2.8a (Tempo-only Spike) ⚠️ NON-CANONICAL

This bundle is **intentionally NOT** the official Stage 2.8 in the Groove Layer sequence.

## What it is
A *tempo-drift-only* spike used to explore Vector 08 mechanics in isolation:
- onset-based tempo estimate
- drift clamp
- drift accumulation
- "correct_drift" vs "follow_player" policy

## What it is NOT
It does **not** include the staged behaviors from prior cuts (Vectors 02–07), such as:
- stability gating
- recovery / hysteresis
- probing + revert
- probe cooldown scheduling
- probe scoring + persistence

## Canonical Stage 2.8
Use **Stage 2.8 FIXED (non-regressing)** instead:
- `groove_layer_v0_stage_2_8_fixed.zip`

## Running tests
```bash
python -m pytest -q
```

## Why this exists
To preserve the tempo-drift exploration as a separate artifact without confusing it with the additive stage chain.
