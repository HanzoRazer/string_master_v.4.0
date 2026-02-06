# Bookmark: sg_coach_v1_spec.md Viability Review

**Created:** 2026-02-06
**Status:** PENDING REVIEW
**Owner:** TBD

---

## Question

Is `Mode 1_Coach v1_models_policies_serializer_tests.txt` (79KB spec file) still viable, or has it been superseded?

---

## Known Implementations

| Location | Type | Files |
|----------|------|-------|
| `string_master_v.4.0/src/sg_coach/` | Embedded package | `cli.py`, `evaluation.py`, `ota.py`, `assignment.py`, `serializer.py`, `planners/` |
| `HanzoRazer/sg-coach` | Standalone repo | Full package (created 2026-01-22, pushed 2026-02-02) |

---

## Review Checklist

- [ ] Compare spec file models (`SessionRecord`, `CoachEvaluation`, `PracticeAssignment`) against `sg-coach` repo
- [ ] Check if OTA bundle logic from spec is implemented in `ota.py`
- [ ] Check if CLI (`sgc`) matches spec
- [ ] Determine which repo is canonical: `src/sg_coach/` or `sg-coach`?
- [ ] If superseded: archive spec to `docs/archive/` with "SUPERSEDED" header
- [ ] If viable: extract unimplemented features as backlog items

---

## Decision Options

1. **SUPERSEDED** — Spec fully implemented in `sg-coach` repo. Archive with note.
2. **PARTIAL** — Some features implemented, some remain. Extract backlog.
3. **VIABLE** — Spec represents different/future direction. Keep as design doc.

---

## Next Action

Run diff between spec pseudocode and actual `sg-coach/src/sg_coach/` implementation.

```bash
# Quick check
gh api repos/HanzoRazer/sg-coach/contents/src/sg_coach --jq '.[].name'
```

---

*This bookmark exists to prevent accidental deletion of potentially valuable design work.*
