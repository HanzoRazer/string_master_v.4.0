# End-to-End Vectors Changelog

This changelog must be updated whenever `expected.json` is updated via `--update-golden`.

Format:
- YYYY-MM-DD — vector_name — short reason

- 2026-01-24 — vector_001_loose_follow_swing — initial e2e canary: intent → arranger → choose_pattern → jitter schedule
- 2026-01-25 — vector_003_challenge_shuffle_dense — add vector_003 challenge shuffle dense canary
- 2026-01-25 — vector_003_challenge_shuffle — add third e2e canary for challenge/shuffle with same events
- 2026-01-25 — vector_002_stabilize_tight_straight — initialize challenge/shuffle e2e vector expected outputs
- 2026-01-25 — [all vectors] — E2E.2 performance controls: derive effective_humanize_ms + velocity_mul from intent signals
- 2026-01-25 — [all vectors] — E2E.3: add note-only anticipation_bias micro-offset (±2–6ms) to schedule targets
- 2026-01-25 — vector_005_velocity_assist_note_on — add velocity assist e2e canary (note_on scaling)
