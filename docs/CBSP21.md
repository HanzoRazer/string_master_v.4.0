# CBSP21: Code-Based Source Protection Policy

## Version 2.0 — Unified Governance Framework

**Policy Classification:** Quality Control / Governance Gate  
**Effective Date:** 2026-01-14  
**Applies To:** AI Agents AND Human Contributors  
**Scope:** Entire Repository  
**Review Cycle:** Per-Release

---

## 1. Purpose & Scope

### 1.1 Why This Policy Exists

CBSP21 is a **quality control gate** that ensures all contributions—whether from AI agents or human developers—do not produce outputs that exceed the coverage of verified source inputs.

This policy prevents:

- **Hallucinated code structures** — AI generating code without scanning dependencies
- **Silent regressions** — Changes that subtly alter existing behavior
- **Incomplete patches** — Modifications based on partial understanding
- **Drift from ground truth** — Deviations from canonical patterns

### 1.2 Core Principle

> **No output may exceed the coverage of the inputs.**

If the contributor (AI or human) cannot demonstrate ≥95% coverage of relevant source material, the output is **BLOCKED**.

### 1.3 Repository-Wide Scope

CBSP21 applies to the **entire Smart Guitar repository**:

| Directory | Description | Protection Level |
|-----------|-------------|------------------|
| `src/shared/zone_tritone/` | Core theory engine | STABLE (see GOVERNANCE.md) |
| `src/zt_band/` | MIDI accompaniment engine | LOCKED modules exist |
| `src/sg_coach/` | Mode-1 coaching spine | Contract-versioned |
| `tests/` | All test suites | Golden vectors protected |
| `scripts/` | CI/CD and utility scripts | Standard |
| `.github/workflows/` | GitHub Actions | Standard |
| `docs/` | Documentation and contracts | Reference material |
| `programs/`, `exercises/`, `seeds/` | Practice materials | Content files |
| `cbsp21/` | CBSP21 source tracking | Governance material |

### 1.4 Relationship to Other Governance Documents

CBSP21 is part of a governance ecosystem:

| Document | Purpose | Relationship |
|----------|---------|--------------|
| [GOVERNANCE.md](GOVERNANCE.md) | Canon change approval | CBSP21 enforces pre-change verification |
| [CANON.md](CANON.md) | Immutable axioms | CBSP21 protects against accidental drift |
| [GLOSSARY.md](GLOSSARY.md) | Frozen terminology | CBSP21 ensures term consistency |
| [docs/contracts/CORE_LOCK_REPORT.md](docs/contracts/CORE_LOCK_REPORT.md) | Locked module list | CBSP21 blocks unauthorized edits |
| [docs/contracts/MIDI_RUNTIME_CONTRACT_V1.md](docs/contracts/MIDI_RUNTIME_CONTRACT_V1.md) | MIDI generation rules | CBSP21 validates contract compliance |
| [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) | Import protocols | CBSP21 verifies namespace adherence |

---

## 2. Roles & Responsibilities

### 2.1 AI Agent Requirements

AI coding agents operating in this repository MUST:

| Requirement | Description | Enforcement |
|-------------|-------------|-------------|
| **Scan before output** | Read all relevant source files before generating code | STOP if coverage < 95% |
| **Declare coverage** | Include `file_context_coverage_percent` in responses | CI audit |
| **Honor STOP conditions** | Halt immediately if threshold not met | Hard block |
| **Respect locked modules** | Never modify files listed in CORE_LOCK_REPORT.md | CI gate |
| **Use canonical terminology** | Reference GLOSSARY.md for all terms | Review check |
| **Follow import protocols** | Use patterns from DEVELOPER_GUIDE.md | Lint/test |

### 2.2 Human Contributor Requirements

Human contributors to this repository MUST:

| Requirement | Description | Enforcement |
|-------------|-------------|-------------|
| **Create manifest** | Provide `.cbsp21/patch_input.json` for code changes | CI gate |
| **Declare intent** | Document `what_changed` and `why_not_redundant` | PR review |
| **Review diffs** | Present diffs for behavior-changing modifications | Required approval |
| **Maintain ground truth** | Keep `cbsp21/full_source/` immutable | Write protection |
| **Run verification** | Execute `verify_lock.py` before commits | Pre-commit hook |

### 2.3 CI/CD Requirements

Automated systems MUST:

| Requirement | Description | Implementation |
|-------------|-------------|----------------|
| **Enforce coverage gates** | Block merges below threshold | `check_cbsp21_gate.py` |
| **Audit all checks** | Append results to JSONL log | `cbsp21_audit.jsonl` |
| **Preserve artifacts** | Upload audit logs as workflow artifacts | GitHub Actions |
| **Validate contracts** | Check version pins on protected modules | Contract enforcement job |
| **Run golden tests** | Verify blessed vectors unchanged | `@pytest.mark.contract` |

---

## 3. Coverage Requirements

### 3.1 Metrics

| Metric | Threshold | Scope |
|--------|-----------|-------|
| `repo_coverage_percent` | ≥ 95% | Byte ratio of scanned vs. full source |
| `file_context_coverage_percent` | ≥ 95% | Per-file coverage for changed files |
| File completeness | 100% | All files claimed as context fully scanned |

### 3.2 Calculation

```python
# Repo-level coverage
repo_coverage = scanned_bytes / full_source_bytes

# File-level coverage (per changed file)
file_coverage = lines_with_context / total_lines_in_file
```

### 3.3 Verification

All coverage claims MUST be:

1. **Logged** — Append to `logs/cbsp21_audit.jsonl`
2. **Reproducible** — Derivable from declared inputs
3. **Attached** — Included in PR or commit metadata

---

## 4. STOP Conditions

Output is **PROHIBITED** if any of the following are true:

| Code | Condition | Recovery |
|------|-----------|----------|
| **STOP-01** | `repo_coverage_percent < 95%` | Scan more files |
| **STOP-02** | Changed file not in `files_expected_to_change` | Update manifest |
| **STOP-03** | `.cbsp21/patch_input.json` missing for code changes | Create manifest |
| **STOP-04** | File claimed as context but not fully scanned | Complete the scan |
| **STOP-05** | Locked module modification without approval | Request governance review |
| **STOP-06** | Golden vector mismatch without `UPDATE_GOLDEN=1` | Validate changes or update vector |
| **STOP-07** | Contract version mismatch | Bump version per protocol |

### 4.1 Recovery Procedure

```
1. IDENTIFY the STOP condition triggered
2. GATHER additional context (read more files)
3. UPDATE manifest with new sources
4. RE-RUN verification scripts
5. DOCUMENT exception if bypass is necessary (Section 10)
```

---

## 5. Repository Structure

### 5.1 CBSP21 Governance Layout

```
cbsp21/
├── full_source/              # Immutable ground truth (human-controlled)
│   └── [original content]    # NEVER modified by AI or automation
├── scanned_source/           # Scanned/captured representation
│   └── [processed content]   # Updated during coverage checks
└── patch_packets/            # Structured FILE: packets
    └── [patch files]         # Format: FILE: path/to/file.ext

.cbsp21/
├── patch_input.json          # PR manifest (REQUIRED for code changes)
├── patch_input.json.example  # Template for manifest
├── exemptions.json           # Exempt paths (auto-generated, migrations)
└── incident_log.json         # Recovery documentation

logs/
├── cbsp21_audit.jsonl        # Append-only audit log
└── [other logs]

scripts/cbsp21/
├── cbsp21_coverage_check.py          # Basic coverage validator
├── cbsp21_coverage_with_audit.py     # Coverage + audit logger
└── check_patch_packet_format.py      # Patch format validator

scripts/ci/
└── check_cbsp21_gate.py              # PR gate enforcement
```

### 5.2 Source Code Layout

```
src/
├── shared/
│   ├── __init__.py
│   └── zone_tritone/         # Core theory engine (PROTECTED)
│       ├── __init__.py
│       ├── __about__.py      # Version metadata
│       ├── cli.py            # zt-gravity CLI
│       ├── pc.py             # Pitch class: int 0-11 (C=0)
│       ├── zones.py          # Zone 1 (even) / Zone 2 (odd)
│       ├── tritones.py       # 6 tritone axes
│       ├── gravity.py        # Dominant chains (cycle of 4ths)
│       ├── corpus.py         # Chord symbol parsing
│       ├── markov.py         # Transition probability
│       └── types.py          # Type aliases (PitchClass, etc.)
│
├── zt_band/                  # MIDI accompaniment engine
│   ├── __init__.py
│   ├── cli.py                # zt-band CLI
│   ├── engine.py             # Main pipeline: .ztprog → .mid
│   ├── midi_out.py           # LOCKED: deterministic writer (tpb=480)
│   ├── musical_contract.py   # LOCKED: runtime validation
│   ├── expressive_layer.py   # LOCKED: velocity-only shaping
│   ├── patterns.py           # Style registry
│   └── contracts.py          # MIDI_CONTRACT_VERSION = "v1"
│
└── sg_coach/                 # Mode-1 coaching spine
    ├── __init__.py
    ├── models.py             # Pydantic v2 models
    ├── assignment_policy.py  # Deterministic planner
    ├── assignment_serializer.py  # UUID-safe JSON export
    ├── ota_payload.py        # OTA wrapper with SHA256+HMAC
    ├── cli.py                # sg-coach CLI
    └── contract.py           # COACH_CONTRACT_VERSION = "v1"
```

### 5.3 Test Layout

```
tests/
├── conftest.py               # Shared fixtures
├── test_pc.py                # Pitch class tests
├── test_zones.py             # Zone membership tests
├── test_tritones.py          # Tritone axis tests
├── test_gravity.py           # Gravity chain tests
├── test_markov.py            # Markov analysis tests
├── test_cli_smoke.py         # CLI integration tests
├── test_musical_contract.py  # Contract enforcement tests
├── test_assignment_policy.py # Mode-1 planner tests
├── test_assignment_serializer.py  # JSON export tests
├── test_ota_payload.py       # OTA signing tests
├── test_mode1_golden_assignment.py  # Golden vector test (@pytest.mark.contract)
└── golden/
    └── mode1_assignment_v1.json  # Blessed golden vector
```

### 5.4 Protected Files

Files requiring governance approval to modify (per [GOVERNANCE.md](GOVERNANCE.md)):

| Category | Files | Protection |
|----------|-------|------------|
| **Canon** | `CANON.md`, `GLOSSARY.md`, `PEDAGOGY.md` | Immutable / Frozen |
| **Governance** | `GOVERNANCE.md`, `CBSP21.md` | Requires approval |
| **Locked Modules** | `midi_out.py`, `musical_contract.py`, `expressive_layer.py` | Pass `verify_lock.py` |
| **Contract Pins** | `contracts.py`, `contract.py` | Version bump protocol |
| **Golden Vectors** | `tests/golden/*.json` | Update only with `UPDATE_GOLDEN=1` |

---

## 6. Patch Input Manifest

### 6.1 Required Manifest

Every code change MUST include a manifest at:

```
.cbsp21/patch_input.json
```

### 6.2 Schema (v1)

```json
{
  "$schema": "cbsp21_patch_input_v1",
  "patch_id": "BUNDLE_001",
  "title": "Add assignment policy for Mode-1 coaching",
  "intent": "Implement deterministic planner that converts SessionRecord + CoachEvaluation to PracticeAssignment",
  "change_type": "code",
  "behavior_change": "compatible",
  "risk_level": "medium",
  "scope": {
    "paths_in_scope": ["src/sg_coach/", "tests/"],
    "files_expected_to_change": [
      "src/sg_coach/assignment_policy.py",
      "tests/test_assignment_policy.py"
    ]
  },
  "diff_range": {
    "base": "origin/main",
    "head": "HEAD"
  },
  "changed_files_count": 2,
  "changed_files_exact": [
    "src/sg_coach/assignment_policy.py",
    "tests/test_assignment_policy.py"
  ],
  "diff_articulation": {
    "what_changed": [
      "Added Mode1Planner class with plan() method",
      "Implemented tempo ramp calculation",
      "Added success criteria based on focus_recommendation",
      "Created 3 unit tests for planner"
    ],
    "why_not_redundant": "No prior planner implementation existed. This is greenfield code."
  },
  "verification": {
    "commands_run": [
      "python -m pytest tests/test_assignment_policy.py -v",
      "python verify_lock.py"
    ],
    "results": "All tests pass"
  },
  "overall_file_context_coverage": 98.5
}
```

### 6.3 Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `$schema` | string | Must be `"cbsp21_patch_input_v1"` |
| `patch_id` | string | Unique identifier for the patch |
| `title` | string | One-line summary |
| `intent` | string | 1-3 sentences describing purpose |
| `change_type` | enum | `code`, `docs`, `ci`, `mixed` |
| `behavior_change` | enum | `none`, `compatible`, `breaking` |
| `risk_level` | enum | `low`, `medium`, `high` |
| `scope.paths_in_scope` | string[] | Directories allowed to be modified |
| `scope.files_expected_to_change` | string[] | Explicit file list |
| `diff_range.base` | string | Base ref for diff |
| `diff_range.head` | string | Head ref for diff |
| `changed_files_exact` | string[] | Exact files changed |
| `diff_articulation.what_changed` | string[] | 5-15 bullets of changes |
| `diff_articulation.why_not_redundant` | string | Explanation of uniqueness |

### 6.4 Validation Rules

CI MUST fail if:

- `.cbsp21/patch_input.json` is missing for code changes
- Required fields are missing or invalid
- `changed_files_exact` differs from actual `git diff` result
- Files changed are not in `files_expected_to_change` or `paths_in_scope`
- `behavior_change != "none"` but `why_not_redundant` is empty

---

## 7. Diff Review Gate

### 7.1 When Review is Required

| Risk Level | Trigger | Requirement |
|------------|---------|-------------|
| **Low** | Pure additions (new files) | Manifest only |
| **Medium** | Modifications to existing functions | Show diff, await confirmation |
| **High** | Guards, restrictions, control flow changes | Show diff + explain impact, explicit approval |

### 7.2 Redundancy Check Protocol

Before declaring a patch "REDUNDANT", verify:

1. **Keyword scan** — Function/variable names exist in codebase
2. **Functional equivalence** — Behavior matches, not just presence
3. **Coverage analysis** — Feature is complete with no gaps

A patch is only "redundant" if:

- `git diff` is empty, OR
- Changes are purely formatting/comments, OR
- Equivalence proven with validation command

### 7.3 Pre-Commit Checklist

For `behavior_change: "medium"` or `"high"`:

```markdown
## Pre-Commit Review

- [ ] Diff shown (not just described)
- [ ] Behavior change explained
- [ ] Impact on existing workflows documented
- [ ] Approval received

If guard/restriction added:
- [ ] Existing functionality preserved OR explicitly deprecated
- [ ] Fallback behavior documented
- [ ] Migration path provided if breaking
```

---

## 8. CI Enforcement

### 8.1 Workflow: Coverage Gate

**File:** `.github/workflows/cbsp21_coverage_gate.yml`

```yaml
name: CBSP21 Coverage Gate

on:
  pull_request:
    paths:
      - "cbsp21/**"
      - "scripts/cbsp21/**"
  push:
    branches: [main, master]
    paths:
      - "cbsp21/**"

jobs:
  cbsp21-coverage:
    runs-on: ubuntu-latest
    env:
      CBSP21_THRESHOLD: "0.95"
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: CBSP21 Coverage Check
        run: |
          python scripts/cbsp21/cbsp21_coverage_with_audit.py \
            --full cbsp21/full_source \
            --scanned cbsp21/scanned_source \
            --threshold $CBSP21_THRESHOLD \
            --log logs/cbsp21_audit.jsonl
      - uses: actions/upload-artifact@v4
        with:
          name: cbsp21_audit
          path: logs/cbsp21_audit.jsonl
```

### 8.2 Workflow: PR Gate

**File:** `.github/workflows/cbsp21_gate.yml`

```yaml
name: CBSP21 PR Gate

on:
  pull_request:
    paths:
      - "src/**"
      - "tests/**"
      - "scripts/**"
      - ".github/workflows/**"

jobs:
  cbsp21-pr-gate:
    runs-on: ubuntu-latest
    env:
      CBSP21_MIN_COVERAGE: "0.95"
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: CBSP21 PR Gate Check
        run: python scripts/ci/check_cbsp21_gate.py
```

### 8.3 Workflow: Patch Format

**File:** `.github/workflows/cbsp21_patch_packet_format.yml`

```yaml
name: CBSP21 Patch Packet Format

on:
  pull_request:
    paths:
      - "cbsp21/patch_packets/**"

jobs:
  cbsp21-patch-format:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Validate Patch Packets
        run: |
          python scripts/cbsp21/check_patch_packet_format.py \
            --glob "cbsp21/patch_packets/**/*.*" \
            --disallow-ellipsis-in-code
```

---

## 9. Audit Logging

### 9.1 Log Format

All CBSP21 checks append to `logs/cbsp21_audit.jsonl`:

```json
{
  "timestamp_utc": "2026-01-14T10:30:00Z",
  "policy": "CBSP21",
  "full_path": "cbsp21/full_source",
  "scanned_path": "cbsp21/scanned_source",
  "full_bytes": 150000,
  "scanned_bytes": 145000,
  "coverage_ratio": 0.9667,
  "repo_coverage_percent": 96.67,
  "threshold": 0.95,
  "status": "pass",
  "ci": {
    "github_run_id": "12345",
    "github_sha": "abc123",
    "github_ref": "refs/pull/42/merge",
    "github_actor": "contributor",
    "github_repo": "HanzoRazer/string_master_v.4.0"
  }
}
```

### 9.2 Retention

- Audit logs are **append-only**
- Retained for the life of the repository
- Uploaded as artifacts on each CI run

---

## 10. Exceptions

### 10.1 Exempt Paths

Some paths are exempt from full coverage validation:

**File:** `.cbsp21/exemptions.json`

```json
{
  "exempt_patterns": [
    "**/*.generated.ts",
    "**/migrations/**",
    "docs/**",
    "*.md"
  ],
  "exempt_reasons": {
    "migrations": "Auto-generated by ORM",
    "docs": "Documentation-only changes"
  }
}
```

### 10.2 Exception Process

For legitimate bypass:

1. **Document** the exception in PR description
2. **Justify** why coverage cannot be met
3. **Obtain** explicit reviewer approval
4. **Log** to `.cbsp21/incident_log.json`

### 10.3 Emergency Hotfix

For production emergencies:

1. **Apply** the fix immediately
2. **Create** post-merge audit within 24 hours
3. **Update** manifest retroactively
4. **Document** in incident log

---

## 11. Implementation Scripts

### 11.1 Coverage Check

**File:** `scripts/cbsp21/cbsp21_coverage_check.py`

```python
#!/usr/bin/env python
"""
CBSP21 Coverage Check

Usage:
    python scripts/cbsp21/cbsp21_coverage_check.py \
        --full-path cbsp21/full_source \
        --scanned-path cbsp21/scanned_source \
        --threshold 0.95
"""

import argparse
from pathlib import Path


def total_bytes_in_dir(root: Path) -> int:
    return sum(f.stat().st_size for f in root.rglob("*") if f.is_file())


def compute_bytes(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size
    if path.is_dir():
        return total_bytes_in_dir(path)
    raise ValueError(f"Path not found: {path}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--full-path", required=True)
    ap.add_argument("--scanned-path", required=True)
    ap.add_argument("--threshold", type=float, default=0.95)
    args = ap.parse_args()

    full = Path(args.full_path)
    scanned = Path(args.scanned_path)

    if not full.exists():
        raise SystemExit(f"Full path does not exist: {full}")
    if not scanned.exists():
        raise SystemExit(f"Scanned path does not exist: {scanned}")

    if full.is_file() != scanned.is_file():
        raise SystemExit("CBSP21 ERROR: full-path and scanned-path must both be files or directories.")

    full_bytes = compute_bytes(full)
    scanned_bytes = compute_bytes(scanned)

    if not full_bytes:
        raise SystemExit("CBSP21 ERROR: full source empty.")

    coverage = scanned_bytes / full_bytes
    print(f"CBSP21 Coverage: {coverage * 100:.2f}%")

    if coverage < args.threshold:
        print("CBSP21 FAIL: Coverage below threshold.")
        return 1

    print("CBSP21 PASS: Coverage requirement satisfied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

### 11.2 PR Gate Check

**File:** `scripts/ci/check_cbsp21_gate.py`

```python
#!/usr/bin/env python3
"""
CBSP21 PR Gate

Validates PRs have valid patch_input.json with sufficient coverage.

Env:
  CBSP21_MIN_COVERAGE     default 0.95
  CBSP21_MANIFEST_PATH    default .cbsp21/patch_input.json
"""

import json
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Set


def get_changed_files() -> List[str]:
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "origin/main...HEAD"],
            capture_output=True, text=True, check=True
        )
        return [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]
    except subprocess.CalledProcessError:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~1"],
            capture_output=True, text=True, check=True
        )
        return [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]


def is_code_file(path: str, skip_exts: Set[str]) -> bool:
    ext = Path(path).suffix.lower()
    if ext in skip_exts:
        return False
    code_exts = {".py", ".ts", ".tsx", ".js", ".jsx", ".yaml", ".yml", ".sh", ".ps1"}
    return ext in code_exts


def main() -> int:
    min_coverage = float(os.getenv("CBSP21_MIN_COVERAGE", "0.95"))
    manifest_path = Path(os.getenv("CBSP21_MANIFEST_PATH", ".cbsp21/patch_input.json"))
    skip_exts = {".md", ".txt"}

    changed_files = get_changed_files()
    code_files = [f for f in changed_files if is_code_file(f, skip_exts)]

    if not code_files:
        print("CBSP21 GATE: No code files changed - skipping.")
        return 0

    print(f"CBSP21 GATE: {len(code_files)} code file(s) changed")

    if not manifest_path.exists():
        print(f"❌ CBSP21 GATE FAIL: Missing manifest at {manifest_path}")
        return 1

    manifest: Dict[str, Any] = json.loads(manifest_path.read_text())
    declared_paths = {cf["path"] for cf in manifest.get("changed_files", [])}
    
    # Also check files_expected_to_change in scope
    scope = manifest.get("scope", {})
    expected = set(scope.get("files_expected_to_change", []))
    exact = set(manifest.get("changed_files_exact", []))
    all_declared = declared_paths | expected | exact

    missing = [f for f in code_files if f not in all_declared]
    if missing:
        print(f"❌ CBSP21 GATE FAIL: Undeclared files:")
        for m in missing:
            print(f"  - {m}")
        return 1

    print("✅ CBSP21 GATE PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

---

## 12. Quick Reference

### 12.1 For AI Agents

```
BEFORE generating code:
1. Scan all relevant source files
2. Verify coverage ≥ 95%
3. Check if target files are locked (CORE_LOCK_REPORT.md)
4. Use canonical terminology (GLOSSARY.md)
5. Follow import protocols (DEVELOPER_GUIDE.md)

IF coverage < 95%:
→ STOP
→ Request more context
→ Do not generate output

AFTER generating code:
1. Run tests: python -m pytest tests/ -v
2. Run lock verification: python verify_lock.py
3. Validate contract compliance
```

### 12.2 For Human Contributors

```
BEFORE submitting PR:
1. Create .cbsp21/patch_input.json manifest
2. Declare all files to be changed
3. Document intent and behavior impact
4. Run verification commands

REQUIRED for code changes:
- Manifest with patch_id, title, intent
- files_expected_to_change list
- diff_articulation with what_changed
- Verification results

REQUIRED for behavior changes:
- Diff review
- Impact documentation
- Explicit approval
```

### 12.3 Verification Commands

```bash
# Run full test suite
python -m pytest tests/ -v

# Run lock verification (5 tests)
python verify_lock.py

# Run contract tests only
python -m pytest tests/ -v -m contract

# Check coverage
python scripts/cbsp21/cbsp21_coverage_check.py \
    --full-path cbsp21/full_source \
    --scanned-path cbsp21/scanned_source
```

---

## 13. Revision History

| Rev | Date | Changes |
|-----|------|---------|
| 1.0 | 2026-01-01 | Initial release |
| 1.1 | 2026-01-02 | Added CI gates, patch packet format |
| 1.2 | 2026-01-03 | Added PR-level enforcement |
| 1.3 | 2026-01-03 | Added Diff Review Gate |
| 1.4 | 2026-01-03 | Added behavior preservation gate |
| 1.5 | 2026-01-03 | Added diff-range lock |
| 2.0 | 2026-01-14 | **Major rewrite**: Unified AI + human governance, repo-wide scope, integration with GOVERNANCE.md ecosystem, removed external references, added complete file structure documentation |

---

## 14. References

**Internal Documentation:**

- [GOVERNANCE.md](GOVERNANCE.md) — Change approval process
- [CANON.md](CANON.md) — Immutable axioms
- [GLOSSARY.md](GLOSSARY.md) — Frozen terminology
- [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) — Import protocols and patterns
- [CLI_DOCUMENTATION.md](CLI_DOCUMENTATION.md) — CLI reference
- [docs/contracts/CORE_LOCK_REPORT.md](docs/contracts/CORE_LOCK_REPORT.md) — Locked module list
- [docs/contracts/MIDI_RUNTIME_CONTRACT_V1.md](docs/contracts/MIDI_RUNTIME_CONTRACT_V1.md) — MIDI invariants

**Configuration Files:**

- `pyproject.toml` — Package configuration
- `pytest.ini` — Test configuration with contract markers
- `.github/workflows/tests.yml` — CI test workflow
- `.github/workflows/cbsp21_*.yml` — CBSP21 enforcement workflows

---

**Policy Owner:** Smart Guitar Project Governance  
**Last Updated:** 2026-01-14  
**Status:** Active
