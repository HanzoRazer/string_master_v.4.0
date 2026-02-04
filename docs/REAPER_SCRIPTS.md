# Smart Guitar — Reaper Scripts Reference

All scripts are in `scripts/reaper/`. Each prints status to the Reaper console.

---

## Setup Scripts

### reaper_sg_setup_doctor.lua

**Purpose**: First-run diagnostics and environment check.

**What it checks**:
- dkjson.lua presence
- Server reachability (GET /status)
- SG_COMP / SG_BASS tracks (creates if missing)
- Chord markers in project
- ExtState chain readiness
- Project meter at cursor

**Inputs**: None

**Side Effects**:
- Creates SG_COMP and SG_BASS tracks if missing

**Console Output**:
```
SG OK:   dkjson.lua: present + loadable
SG OK:   Server: reachable (GET /status 200)
SG OK:   Track exists: SG_COMP
SG OK:   Markers: 4 (e.g., Dm7, G7, Cmaj7, Fmaj7)
SG WARN: ExtState last_clip_id: missing
```

---

### reaper_sg_setup_doctor_autorun.lua

**Purpose**: Setup Doctor + configurable action autorun.

**Inputs** (dialog):
- `configure_action_ids` (0/1): Prompt for action IDs
- `autorun` (0/1): Run the action sequence
- `dry_run` (0/1): Preview without executing

**ExtState Keys Used**:
- `SG_AGENTD/action_generate`
- `SG_AGENTD/action_pass_regen`
- `SG_AGENTD/action_struggle_regen`
- `SG_AGENTD/action_timeline`
- `SG_AGENTD/action_trend`

**Side Effects**:
- Saves action IDs to ExtState (if configuring)
- Runs actions (if autorun enabled)

---

### reaper_sg_set_action_ids_once.lua

**Purpose**: One-time ExtState setter for action command IDs.

**Usage**:
1. Edit the script: paste your `_RS...` IDs into `GEN_ID` and `PASS_ID`
2. Run once
3. IDs are persisted to ExtState

**ExtState Keys Set**:
- `SG_AGENTD/action_generate`
- `SG_AGENTD/action_pass_regen`

**Validation**:
- Refuses to save placeholder text
- Verifies IDs resolve to real Reaper actions

---

### reaper_sg_setup_autorun_generate_then_pass.lua

**Purpose**: Zero-prompt autorun — always runs Generate then PASS+REGEN.

**Inputs**: None (reads from ExtState)

**ExtState Keys Read**:
- `SG_AGENTD/action_generate`
- `SG_AGENTD/action_pass_regen`

**Side Effects**:
- Runs Generate action
- Runs PASS+REGEN action (deferred)

**Error Behavior**:
- If ExtState keys missing, prints fix instructions (no dialog)

---

## Core Generation Scripts

### reaper_sg_generate.lua

**Purpose**: Generate MIDI from chord markers.

**Inputs**:
- Chord markers in project
- Time selection (optional, limits scope)

**Response Fields Used**:
- `status`
- `clip_id`
- `bundle_dir`

**ExtState Keys Set**:
- `SG_AGENTD/last_clip_id`

**Side Effects**:
- Inserts MIDI items on SG_COMP and SG_BASS tracks
- Writes bundle to `~/Downloads/sg-bundles/`

---

### reaper_sg_generate_queued_nextbar.lua

**Purpose**: Generate starting at the next bar boundary.

**Behavior**: Same as generate, but aligns to bar grid.

---

### reaper_sg_regenerate.lua

**Purpose**: Regenerate with adjusted difficulty.

**Inputs**:
- `last_clip_id` from ExtState
- Difficulty signal (from feedback history)

**Response Fields Used**:
- `status`
- `clip_id`
- `bundle_dir`

---

### reaper_sg_regenerate_queued_nextbar.lua

**Purpose**: Regenerate starting at the next bar boundary.

---

## Practice Loop Scripts

### reaper_sg_pass_and_regen.lua

**Purpose**: Submit PASS verdict + regenerate (slightly harder).

**Inputs**:
- `last_clip_id` from ExtState

**Response Fields Used**:
- `status`
- `suggested_adjustment.coach_hint`
- New `clip_id`

**ExtState Keys Updated**:
- `SG_AGENTD/last_clip_id`

**Console Output**:
```
SG OK:   Feedback submitted: pass
SG OK:   Coach: "Solid feel — bumping density slightly."
SG OK:   Regenerated: <new_clip_id>
```

---

### reaper_sg_struggle_and_regen.lua

**Purpose**: Submit STRUGGLE verdict + regenerate (slightly easier).

**Behavior**: Same as pass_and_regen, but signals difficulty reduction.

---

### reaper_sg_practice_loop.lua

**Purpose**: Combined feedback + regenerate with verdict prompt.

**Inputs** (dialog):
- Verdict selection (PASS/STRUGGLE)

---

## Visibility Scripts

### reaper_sg_session_timeline.lua

**Purpose**: Print session history as timeline.

**Reads**:
- `session.index.json` from bundle directory

**Console Output**:
```
============================================================
Smart Guitar — Session Timeline
============================================================
[10:30:15] clip_abc123 | pass    | density +0.1
[10:32:45] clip_def456 | struggle | density -0.1
[10:35:12] clip_ghi789 | pass    | density +0.05
============================================================
```

---

### reaper_sg_session_trend_summary.lua

**Purpose**: Print session trend analysis.

**Console Output**:
```
============================================================
Smart Guitar — Session Trend Summary
============================================================
Total clips: 12
Pass rate: 75%
Trend: improving (3 consecutive passes)
Current density: 0.65
============================================================
```

---

### reaper_sg_session_trend_compact.lua

**Purpose**: One-line trend summary.

**Console Output**:
```
SG TREND: 12 clips | 75% pass | improving | density=0.65
```

---

## Script Dependencies

All scripts require:
- `dkjson.lua` in the same folder
- sg-agentd server running at `http://127.0.0.1:8420`

---

## ExtState Keys Reference

| Key | Set By | Read By |
|-----|--------|---------|
| `SG_AGENTD/last_clip_id` | generate, regenerate | feedback, regenerate |
| `SG_AGENTD/action_generate` | set_action_ids_once, setup_doctor_autorun | autorun scripts |
| `SG_AGENTD/action_pass_regen` | set_action_ids_once, setup_doctor_autorun | autorun scripts |
| `SG_AGENTD/action_struggle_regen` | setup_doctor_autorun | autorun scripts |
| `SG_AGENTD/action_timeline` | setup_doctor_autorun | autorun scripts |
| `SG_AGENTD/action_trend` | setup_doctor_autorun | autorun scripts |

---

## Hotkey Recommendations

| Action | Suggested Key |
|--------|---------------|
| Setup Doctor | F12 |
| Generate (queued) | F5 |
| PASS + Regen | F9 |
| STRUGGLE + Regen | F10 |
| Timeline | F11 |
