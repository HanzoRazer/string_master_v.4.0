# Smart Guitar — Contracts

This document defines the **stable contracts** for bundle artifacts and API endpoints. Scripts and integrations should rely only on fields documented here.

**Rule**: Optional fields are optional. Do not hard-bind to extras.

---

## Bundle Files (Authoritative Offline Artifacts)

Each generation creates a bundle at:
```
~/Downloads/sg-bundles/{YYYY-MM-DD}/{clip_id}/
```

### Required Files

| File | Purpose | Stable Fields |
|------|---------|---------------|
| `clip.mid` | Combined MIDI (comp + bass) | Standard MIDI |
| `clip.comp.mid` | Comping track only | Standard MIDI |
| `clip.bass.mid` | Bass track only | Standard MIDI |
| `clip.tags.json` | Clip metadata | `clip_id`, `created_at`, `chords`, `tempo_bpm`, `meter` |
| `clip.runlog.json` | Generation provenance | `clip_id`, `attempt_id`, `seed`, `engine_version`, `status` |

### Optional Files

| File | Purpose | When Present |
|------|---------|--------------|
| `clip.coach.json` | Deterministic coach hint | Always (deterministic) |
| `clip.feedback.json` | User feedback record | After PASS/STRUGGLE |
| `clip.feedback.ref.json` | Feedback reference copy | After feedback submission |
| `clip.error.json` | Error details | On generation failure (if `SG_EMIT_ERROR_BUNDLES=true`) |

### Session Index

| File | Purpose | Location |
|------|---------|----------|
| `session.index.json` | Append-only session log | `~/Downloads/sg-bundles/{YYYY-MM-DD}/session.index.json` |

**Session Index Fields** (per entry):
- `clip_id` — unique identifier
- `timestamp` — ISO 8601
- `verdict` — `pass` | `struggle` | `null`
- `coach_hint` — deterministic narrative
- `adjustments` — density/syncopation changes

---

## API Endpoints (Minimal Stable Set)

Server runs at `http://127.0.0.1:8420` by default.

### GET /status

Health check.

**Response**:
```json
{"status": "ok"}
```

### POST /generate

Generate MIDI from chord progression.

**Request** (essentials):
```json
{
  "chords": ["Dm7", "G7", "Cmaj7"],
  "tempo_bpm": 120,
  "meter": "4/4",
  "bars": 4
}
```

**Response** (essentials):
```json
{
  "status": "ok",
  "clip_id": "...",
  "bundle_dir": "..."
}
```

**Status values**: `ok`, `partial`, `failed`

### POST /regenerate

Regenerate with adjusted difficulty.

**Request** (essentials):
```json
{
  "parent_clip_id": "...",
  "difficulty_signal": 0.3
}
```

**Response**: Same shape as `/generate`.

### POST /feedback

Submit practice verdict.

**Request** (essentials):
```json
{
  "clip_id": "...",
  "verdict": "pass"
}
```

**Verdict values**: `pass`, `struggle`

**Response**:
```json
{
  "status": "ok",
  "suggested_adjustment": {
    "density_delta": 0.1,
    "syncopation_delta": 0.05,
    "coach_hint": "..."
  }
}
```

### POST /feedback_and_regen

Submit feedback + regenerate in one call.

**Request**: Combines `/feedback` + `/regenerate` fields.

**Response**: Includes feedback result + new clip info.

### GET /session_index

Retrieve current day's session log.

**Response**:
```json
{
  "entries": [...]
}
```

---

## Error Codes (Additive-Only)

Error codes are never removed or changed, only added.

| Code | Meaning |
|------|---------|
| `ENGINE_UNAVAILABLE` | zt_band import failed |
| `GENERATION_ERROR` | Exception during generation |
| `REGENERATION_ERROR` | Exception during regeneration |
| `VALIDATION_ERROR` | Schema validation failure |

All errors return HTTP 200 with `status: "failed"` and `error_code` set.

---

## Contract Rules

1. **Bundle files are the source of truth** — if the server is unavailable, bundles remain valid
2. **Manifest-first** — always check `clip.tags.json` exists before assuming success
3. **Optional fields are optional** — scripts must not fail if extras are missing
4. **Error codes are additive-only** — never remove or rename existing codes
5. **Deterministic coach always present** — `clip.coach.json` is written even if enhancements fail

---

## Schema Ownership

Canonical schemas live in **sg-spec**. If schemas are duplicated elsewhere, they must match the sg-spec version exactly.

**SHA256 hashes** for locked schemas are tracked in `sg-spec/contracts/CHANGELOG.md`.
