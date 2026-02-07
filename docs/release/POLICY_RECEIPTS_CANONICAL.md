# Policy Receipt Canonicalization & Drift Detection (Phase 11.7.6)

## Overview

**Phase 11.7.6** makes policy receipts **deterministic and diff-friendly** by:

1. **Canonical JSON formatting** — sorted keys, stable indentation
2. **Normalized timestamps** — volatile fields moved to runtime block
3. **Stable list ordering** — attestations sorted by content, reasons sorted
4. **Content hashing** — detect policy allowlist drift across releases
5. **Split receipts** — canonical (diffable) + runtime (volatile) separation

---

## Why Canonical Receipts?

**Problem:** Raw receipts contain volatile fields that change every run:
- Run IDs, workflow IDs, attempt numbers
- Temporary download paths (`/tmp/attestations/abc123`)
- Timestamps (`generated_at_utc`)
- Variable list ordering

**Solution:** Canonicalization produces **stable receipts** that diff cleanly across releases while preserving all policy-relevant information.

---

## Receipt Layers

### Canonical Receipt (`.receipt.json`)

**Diffable, stable, policy-relevant**

```json
{
  "canonical_version": "11.7.6",
  "kind": "SmartGuitarAttestationPolicyReceipt",
  "policy_engine_version": "11.7.5",
  "profile": "lab_pack_zip",
  "repo": "OWNER/REPO",
  "tag": "v1.2.3",
  "ref": "refs/tags/v1.2.3",
  "subject": {
    "name": "Lab_Pack_SG_v1.2.3.zip",
    "path": "Lab_Pack_SG_v1.2.3.zip",
    "sha256": "abc123..."
  },
  "policy": {
    "expanded_allowlists": {...},
    "policy_content_hash": "def456...",
    "policy_file": "scripts/release/attestation_policy.json",
    "required_attestation_types": ["provenance"],
    "schema_file": "scripts/release/attestation_schema_min.json",
    "strict": {}
  },
  "attestations": [
    {
      "attestation_file": "abc123.json",
      "attestation_file_sha256": "...",
      "extracted": {
        "configSource_digest": {"sha1": "..."},
        "configSource_uri": "git+https://github.com/...",
        "runner_environment": "github-hosted",
        "subject_digest": {"sha256": "..."},
        "workflow_path": ".github/workflows/release_lab_pack.yml"
      },
      "fail_reason": "",
      "policy_ok": true,
      "predicateType": "https://slsa.dev/provenance/v1",
      "schema_ok": true
    }
  ],
  "result": {
    "any_pass": true,
    "ok": true,
    "reasons": []
  },
  "runtime": {
    "download.download_dir": "/tmp/attestations/...",
    "download.downloaded_count": 1,
    "gh.run_attempt": "1",
    "gh.run_id": "1234567890"
  }
}
```

**Key properties:**
- Paths normalized to basenames (no `/tmp/...` or `C:\...`)
- Attestations sorted by `(predicateType, subject sha, configSource uri, workflow path)`
- Reasons sorted alphabetically
- Policy content hash computed for drift detection
- Runtime block included but not used for diffs

### Runtime Receipt (`.runtime.json`)

**Volatile operational context (optional)**

```json
{
  "kind": "SmartGuitarAttestationPolicyReceiptRuntime",
  "canonical_hash": "xyz789...",
  "runtime": {
    "download.download_dir": "/tmp/attestations/abc123",
    "download.downloaded_count": 1,
    "gh.run_attempt": "1",
    "gh.run_id": "1234567890",
    "gh.workflow": "Release Lab Pack"
  }
}
```

**Purpose:**
- Preserves operational metadata
- Links back to canonical via `canonical_hash`
- Excluded from diffs
- Useful for debugging specific runs

---

## Normalization Rules

### 1. Path Normalization

```python
# Before
"path": "/tmp/attestations/abc123/file.json"
"path": "C:\\verify\\dist\\Lab_Pack_SG_v1.2.3.zip"

# After (canonical)
"path": "file.json"
"path": "Lab_Pack_SG_v1.2.3.zip"
```

### 2. Volatile Field Extraction

Fields moved to `runtime` block:
- `gh.run_id`
- `gh.run_attempt`
- `download.download_dir`
- `download.downloaded_count`
- `generated_at_utc` (if present)

### 3. List Sorting

**Attestations** sorted by:
```python
(predicateType, subject_sha256, configSource_uri, workflow_path)
```

**Reasons** sorted alphabetically

### 4. Dictionary Sorting

All JSON keys sorted recursively (canonical JSON)

### 5. Policy Content Hash

```python
policy_content_hash = sha256(expanded_allowlists)
```

Detects when allowlists change across releases

---

## CLI Usage

### Generate Canonical Receipt

```bash
# During policy engine run
python scripts/release/attestation_policy_engine.py \
  --subject Lab_Pack_SG_v1.2.3.zip \
  --repo OWNER/REPO \
  --tag v1.2.3 \
  --policy attestation_policy.json \
  --schema attestation_schema_min.json \
  --profile lab_pack_zip \
  --receipt-out lab_pack.receipt.json \
  --receipt-canonical \
  --receipt-split
```

**Output:**
- `lab_pack.receipt.json` (canonical)
- `lab_pack.runtime.json` (runtime)

### Normalize Existing Receipt

```bash
# Normalize after the fact
python scripts/release/receipt_canonicalize.py \
  --in lab_pack.receipt.json \
  --out lab_pack.canonical.json \
  --split \
  --runtime-out lab_pack.runtime.json
```

### Compare Receipts (Drift Detection)

```bash
# Compare two releases
python scripts/release/receipt_diff.py \
  v1.2.2/lab_pack.receipt.json \
  v1.2.3/lab_pack.receipt.json

# Fail if policy drifted
python scripts/release/receipt_diff.py \
  v1.2.2/lab_pack.receipt.json \
  v1.2.3/lab_pack.receipt.json \
  --fail-on-policy-drift

# JSON output
python scripts/release/receipt_diff.py \
  v1.2.2/lab_pack.receipt.json \
  v1.2.3/lab_pack.receipt.json \
  --json
```

---

## Diff Tool Output

### Human-Readable

```
Receipt Diff Report
============================================================
Left:  v1.2.2/lab_pack.receipt.json
Right: v1.2.3/lab_pack.receipt.json

✗ Receipts differ (3 differences)

⚠ POLICY DRIFT DETECTED
  Left policy hash:  abc123def456...
  Right policy hash: fed654cba321...

POLICY (2 diffs):
  - policy.expanded_allowlists.workflow_path[0]: '.github/workflows/release.yml' → '.github/workflows/release_lab_pack.yml'
  - policy.expanded_allowlists.source_uri_allow_prefixes: added prefix 'git+https://github.com/...'

ATTESTATIONS (1 diff):
  - attestations[0].extracted.workflow_path: '.github/workflows/release.yml' → '.github/workflows/release_lab_pack.yml'

OTHER (0 diffs):
```

### JSON Output

```json
{
  "identical": false,
  "left_hash": "abc123...",
  "right_hash": "def456...",
  "policy_drifted": true,
  "left_policy_hash": "abc123...",
  "right_policy_hash": "fed654...",
  "diff_summary": {
    "total_diffs": 3,
    "policy_diffs": 2,
    "attestation_diffs": 1,
    "result_diffs": 0,
    "other_diffs": 0
  },
  "diffs": {
    "policy": [
      "policy.expanded_allowlists.workflow_path[0]: '.github/workflows/release.yml' → '.github/workflows/release_lab_pack.yml'"
    ],
    "attestations": [...],
    "result": [],
    "other": []
  }
}
```

---

## Workflow Integration

### CI/CD (GitHub Actions)

```yaml
- name: Policy engine gate + receipt (11.7.6 canonical)
  run: |
    python scripts/release/attestation_policy_engine.py \
      --subject Lab_Pack_SG_*.zip \
      --repo ${{ github.repository }} \
      --tag ${{ github.ref_name }} \
      --policy attestation_policy.json \
      --schema attestation_schema_min.json \
      --profile lab_pack_zip \
      --receipt-out policy_receipts/lab_pack.receipt.json \
      --receipt-canonical \
      --receipt-split

- name: Policy drift detection (11.7.6)
  run: |
    # Download previous release receipt
    PREV_TAG=$(gh release list | head -n 2 | tail -n 1)
    gh release download "$PREV_TAG" --pattern "lab_pack.receipt.json" --dir prev_receipts
    
    # Compare
    python scripts/release/receipt_diff.py \
      prev_receipts/lab_pack.receipt.json \
      policy_receipts/lab_pack.receipt.json \
      --fail-on-policy-drift || echo "Policy drift detected"
  continue-on-error: true
```

### Local Makefile

```bash
# Compare receipts locally
make diff-receipts \
  LEFT=v1.2.2/lab_pack.receipt.json \
  RIGHT=v1.2.3/lab_pack.receipt.json
```

---

## Use Cases

### 1. Policy Evolution Tracking

**Scenario:** Security team wants to audit all policy changes over time.

```bash
# Download all historical receipts
for tag in v1.2.0 v1.2.1 v1.2.2 v1.2.3; do
  mkdir -p receipts/$tag
  gh release download $tag --pattern "*.receipt.json" --dir receipts/$tag
done

# Compare adjacent releases
for i in v1.2.0 v1.2.1 v1.2.2; do
  j=$(echo $i | awk -F. '{$NF+=1; print}' OFS=.)
  echo "=== $i → $j ==="
  python scripts/release/receipt_diff.py \
    receipts/$i/lab_pack.receipt.json \
    receipts/$j/lab_pack.receipt.json
done
```

### 2. Regression Detection

**Scenario:** New release accidentally loosens policy constraints.

```bash
# Fail build if policy drifted
python scripts/release/receipt_diff.py \
  baseline/lab_pack.receipt.json \
  current/lab_pack.receipt.json \
  --fail-on-policy-drift
```

### 3. Compliance Auditing

**Scenario:** External auditor needs proof that policy remained stable.

```bash
# Auditor downloads canonical receipts
gh release download v1.2.2 --pattern "*.receipt.json"
gh release download v1.2.3 --pattern "*.receipt.json"

# Verify signatures
cosign verify-blob --bundle lab_pack.receipt.json.sigstore.json lab_pack.receipt.json

# Compare policies
python scripts/release/receipt_diff.py \
  v1.2.2/lab_pack.receipt.json \
  v1.2.3/lab_pack.receipt.json \
  --json > diff_report.json

# Check policy_drifted flag
jq '.policy_drifted' diff_report.json  # false = stable
```

### 4. Attestation Format Evolution

**Scenario:** GitHub changes attestation schema; detect impact.

```bash
# Compare attestation structure
python scripts/release/receipt_diff.py \
  old_format/lab_pack.receipt.json \
  new_format/lab_pack.receipt.json

# Inspect attestation diffs
jq '.diffs.attestations' diff_report.json
```

---

## Canonical Receipt Properties

| Property | Before (11.7.5) | After (11.7.6) |
|----------|-----------------|----------------|
| **Diff stability** | High false positives (timestamps, paths, run IDs) | Clean diffs (only policy changes show) |
| **Git tracking** | Not suitable (volatile fields) | Suitable (deterministic output) |
| **Policy hash** | Not present | `policy.policy_content_hash` |
| **Path normalization** | Machine-specific (`/tmp/...`, `C:\...`) | Basenames only |
| **List ordering** | Insertion order (variable) | Content-sorted (stable) |
| **Runtime separation** | Mixed with policy data | Split into `.runtime.json` |
| **Canonical marker** | None | `canonical_version: "11.7.6"` |

---

## Drift Detection Modes

### Informational (CI default)

```yaml
- name: Policy drift detection
  run: |
    python scripts/release/receipt_diff.py ... || echo "Drift detected (informational)"
  continue-on-error: true
```

**Behavior:** Report drift but don't fail build

### Hard Enforcement

```yaml
- name: Policy drift detection
  run: |
    python scripts/release/receipt_diff.py ... --fail-on-policy-drift
```

**Behavior:** Fail build if policy changed (requires manual approval/documentation)

### Custom Gates

```bash
# Fail only if specific allowlists changed
diff_json=$(python scripts/release/receipt_diff.py ... --json)
workflow_changed=$(echo "$diff_json" | jq '.diffs.policy[] | select(contains("workflow_path"))')

if [ -n "$workflow_changed" ]; then
  echo "Workflow allowlist changed - requires security review"
  exit 1
fi
```

---

## Testing Canonicalization

### Test Stability

```bash
# Generate receipt twice (should be identical)
python attestation_policy_engine.py ... --receipt-out r1.json --receipt-canonical
python attestation_policy_engine.py ... --receipt-out r2.json --receipt-canonical

# Compare (should have no diffs)
diff r1.json r2.json
```

### Test Normalization

```python
from receipt_canonicalize import normalize_receipt
import json

receipt = json.load(open("raw_receipt.json"))
canonical = normalize_receipt(receipt)

# Paths normalized
assert "/" not in canonical["subject"]["path"]
assert "\\" not in canonical["subject"]["path"]

# Runtime block present
assert "runtime" in canonical

# Policy hash present
assert "policy_content_hash" in canonical["policy"]
```

---

## Security Considerations

### Canonical Receipts Are Not Signatures

**Canonicalization** makes receipts diffable, but does NOT replace cryptographic signatures:

```bash
# Canonical receipt alone: NOT TAMPER-EVIDENT
lab_pack.receipt.json

# Canonical receipt + signature: TAMPER-EVIDENT
lab_pack.receipt.json
lab_pack.receipt.json.sigstore.json  # cosign signature

# Verify integrity
cosign verify-blob --bundle lab_pack.receipt.json.sigstore.json lab_pack.receipt.json
```

### Runtime Block Trust

**Runtime receipts** are signed separately but are **NOT diffable**:

```bash
# Runtime receipt (volatile)
lab_pack.runtime.json
lab_pack.runtime.json.sigstore.json  # signed but not for diffs
```

Use runtime receipts for debugging, NOT for policy compliance checks.

---

## Migration from 11.7.5 to 11.7.6

### Backward Compatibility

**11.7.6 receipts work with 11.7.5 tooling** (graceful fallback):

```python
# If receipt_canonicalize module unavailable
try:
    from receipt_canonicalize import canonical_dumps
except ImportError:
    def canonical_dumps(obj):
        return json.dumps(obj, indent=2) + "\n"
```

### Upgrade Path

1. **First release with 11.7.6:** Generate both formats
   ```bash
   --receipt-out lab_pack.receipt.json           # regular
   --receipt-out lab_pack.canonical.json --receipt-canonical  # canonical
   ```

2. **Subsequent releases:** Use `--receipt-canonical` by default

3. **Compare against 11.7.5 receipts:** Normalize legacy receipt first
   ```bash
   python receipt_canonicalize.py --in legacy.json --out legacy_normalized.json
   python receipt_diff.py legacy_normalized.json current_canonical.json
   ```

---

## Troubleshooting

### Diff shows false positives

**Cause:** Comparing non-canonical receipts

**Fix:** Normalize both before comparison
```bash
python receipt_canonicalize.py --in left.json --out left_canonical.json
python receipt_canonicalize.py --in right.json --out right_canonical.json
python receipt_diff.py left_canonical.json right_canonical.json
```

### Policy hash mismatch but no allowlist changes

**Cause:** JSON key ordering differs

**Fix:** Use canonical mode (keys auto-sorted)
```bash
--receipt-canonical
```

### Runtime block missing

**Cause:** Using 11.7.5 receipt or forgot `--receipt-canonical`

**Fix:** Re-generate with `--receipt-canonical` or normalize existing receipt

---

## Summary

Phase 11.7.6 transforms policy receipts from **operational logs** into **auditable policy artifacts**:

✅ **Diff-friendly** — clean comparisons across releases  
✅ **Git-trackable** — deterministic output suitable for version control  
✅ **Drift detection** — automated policy evolution tracking  
✅ **Compliance-ready** — portable proof of policy stability  
✅ **Backward compatible** — graceful fallback to 11.7.5 behavior  

---

**Version:** Phase 11.7.6  
**Last Updated:** 2026-02-07
