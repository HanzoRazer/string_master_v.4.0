# Smart Guitar — Acceptance Testing

This document defines the acceptance matrix and verification procedures.

---

## Acceptance Matrix (10–20 Runs)

Complete this matrix to verify the system works correctly.

| Run | Meter | Chords | Verdict | Expected Behavior | ✓ |
|-----|-------|--------|---------|-------------------|---|
| 1 | 4/4 | Dm7 G7 Cmaj7 | — | Generate succeeds, bundle created | |
| 2 | 4/4 | Dm7 G7 Cmaj7 | PASS | Density increases, new clip generated | |
| 3 | 4/4 | Dm7 G7 Cmaj7 | PASS | Density increases again | |
| 4 | 4/4 | Dm7 G7 Cmaj7 | STRUGGLE | Density decreases | |
| 5 | 4/4 | Am7 D7 Gmaj7 | — | Generate with different chords | |
| 6 | 4/4 | Am7 D7 Gmaj7 | PASS | Coach hint reflects upward trend | |
| 7 | 3/4 | Dm7 G7 Cmaj7 | — | Waltz meter handled correctly | |
| 8 | 3/4 | Dm7 G7 Cmaj7 | PASS | 3/4 MIDI plays correctly | |
| 9 | 6/8 | Dm7 G7 Cmaj7 | — | Compound meter handled | |
| 10 | 6/8 | Dm7 G7 Cmaj7 | STRUGGLE | Density reduces in 6/8 | |
| 11 | 4/4 | Fmaj7 Bb7 Ebmaj7 Abmaj7 | — | 4-chord progression | |
| 12 | 4/4 | Fmaj7 Bb7 Ebmaj7 Abmaj7 | PASS | Longer progression works | |
| 13 | 4/4 | Dm7 | — | Single chord | |
| 14 | 4/4 | Dm7 G7 | — | Two chords | |
| 15 | 4/4 | (8 bars of ii-V-I) | — | Extended progression | |

---

## Meter Spot Checks

### 3/4 Waltz

1. Set project tempo to 120 BPM
2. Set time signature to 3/4
3. Create markers: Dm7, G7, Cmaj7
4. Run Generate
5. **Verify**:
   - MIDI aligns to 3-beat bars
   - Playback sounds like waltz feel
   - No notes extend past bar boundaries

### 6/8 Compound

1. Set project tempo to 120 BPM
2. Set time signature to 6/8
3. Create markers: Dm7, G7, Cmaj7
4. Run Generate
5. **Verify**:
   - MIDI aligns to 6/8 feel
   - Grouped in 3+3 subdivision
   - Bar alignment correct

---

## Idempotency Checks

### Duplicate attempt_id

1. Run Generate → note the `clip_id`
2. Manually call `/generate` again with same `attempt_id`
3. **Verify**: Second call returns same `clip_id` (or rejects as duplicate)

### Bundle Collision

1. Set `SG_BUNDLE_COLLISION_POLICY=error`
2. Generate a clip
3. Attempt to generate again with same `clip_id`
4. **Verify**: Error returned, original bundle preserved

---

## Bundle Verification

After each successful generation, verify bundle contents:

```bash
ls ~/Downloads/sg-bundles/YYYY-MM-DD/<clip_id>/
```

**Required files**:
- [ ] `clip.mid`
- [ ] `clip.comp.mid`
- [ ] `clip.bass.mid`
- [ ] `clip.tags.json`
- [ ] `clip.runlog.json`
- [ ] `clip.coach.json`

**Check clip.tags.json**:
```bash
cat ~/Downloads/sg-bundles/YYYY-MM-DD/<clip_id>/clip.tags.json
```

Verify:
- [ ] `clip_id` matches
- [ ] `chords` array matches input
- [ ] `tempo_bpm` matches project
- [ ] `meter` matches project

---

## Session Index Verification

After multiple runs:

```bash
cat ~/Downloads/sg-bundles/YYYY-MM-DD/session.index.json
```

Verify:
- [ ] Entries append correctly
- [ ] Timestamps are sequential
- [ ] Verdicts recorded correctly
- [ ] Coach hints present

---

## Setup Doctor Verification

Run `reaper_sg_setup_doctor.lua` and verify:

### Expected OK Lines

```
SG OK:  Script dir: ...
SG OK:  dkjson.lua: present + loadable
SG OK:  Server: reachable (GET /status 200)
SG OK:  Track exists: SG_COMP
SG OK:  Track exists: SG_BASS
SG OK:  Chord markers in project: N (e.g., ...)
SG OK:  Project meter @ cursor: 4/4
```

### Expected Warnings (First Run)

```
SG WARN: ExtState last_clip_id: missing
```

This is expected before first Generate.

### Error Recovery

| Error | Fix | Verify Fix |
|-------|-----|------------|
| "dkjson.lua not found" | Copy dkjson.lua to scripts folder | Re-run Doctor |
| "Server unreachable" | Start sg-agentd | Re-run Doctor |
| "Markers: 0" | Add chord markers | Re-run Doctor |

---

## Console Log Capture

For each acceptance run, capture:

1. **Reaper Console Output**:
   - Copy full console text
   - Note any SG ERR lines

2. **Screenshot**:
   - Reaper timeline showing MIDI items
   - Track names visible (SG_COMP, SG_BASS)

3. **Bundle Directory Listing**:
   ```bash
   ls -la ~/Downloads/sg-bundles/YYYY-MM-DD/<clip_id>/
   ```

---

## Proof Artifacts

For formal acceptance, collect:

| Artifact | Format | Purpose |
|----------|--------|---------|
| Console log | Text file | Verify script output |
| Screenshot | PNG | Visual confirmation |
| Bundle listing | Text file | File presence check |
| session.index.json | JSON | Session continuity |
| clip.coach.json | JSON | Coach hint verification |

---

## Pass/Fail Criteria

### PASS

- [ ] All 15 matrix runs complete without errors
- [ ] 3/4 and 6/8 meters produce correct output
- [ ] Idempotency guards work
- [ ] Setup Doctor reports all OK (after setup)
- [ ] Bundle contains all required files
- [ ] Session index appends correctly

### FAIL

- Any `SG ERR` that is not recoverable
- Missing bundle files after "ok" status
- MIDI does not play in DAW
- Meter alignment visibly wrong
- Coach hint missing from feedback response

---

## Sign-Off

| Tester | Date | Result | Notes |
|--------|------|--------|-------|
| | | | |
| | | | |
