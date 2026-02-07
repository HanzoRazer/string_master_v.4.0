#!/usr/bin/env bash
set -euo pipefail

# drift_gate_multi.sh
#
# Runs drift gate across multiple canonical receipts.
#
# Usage:
#   ./drift_gate_multi.sh --old-dir receipts_prev --new-dir receipts_current --policy scripts/release/drift_gate_policy.json
#
# Override:
#   DRIFT_OVERRIDE=1 to bypass failures (still prints drift)

OLD_DIR=""
NEW_DIR=""
POLICY=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --old-dir) OLD_DIR="$2"; shift 2 ;;
    --new-dir) NEW_DIR="$2"; shift 2 ;;
    --policy) POLICY="$2"; shift 2 ;;
    *) echo "ERR: unknown arg $1"; exit 2 ;;
  esac
done

if [[ -z "$OLD_DIR" || -z "$NEW_DIR" || -z "$POLICY" ]]; then
  echo "Usage: $0 --old-dir <dir> --new-dir <dir> --policy <file>"
  exit 2
fi

if [[ ! -d "$NEW_DIR" ]]; then
  echo "ERR: new-dir not found: $NEW_DIR"
  exit 2
fi

if [[ ! -f "$POLICY" ]]; then
  echo "ERR: policy not found: $POLICY"
  exit 2
fi

# Canonical receipt basenames we expect in release assets:
RECEIPTS=(
  "policy_receipt_zip.canonical.json"
  "policy_receipt_verify_release.sh.canonical.json"
  "policy_receipt_verify_release.ps1.canonical.json"
  "policy_receipt_verify_attestations.sh.canonical.json"
)

echo "== Drift gate multi =="
echo "old: $OLD_DIR"
echo "new: $NEW_DIR"
echo "policy: $POLICY"
echo "override: ${DRIFT_OVERRIDE:-0}"
echo

# If OLD_DIR missing or empty, treat as first release and skip.
if [[ ! -d "$OLD_DIR" ]]; then
  echo "No old-dir present; drift gate skipped."
  exit 0
fi

FAIL=0
for r in "${RECEIPTS[@]}"; do
  NEW_PATH="$NEW_DIR/$r"
  OLD_PATH="$OLD_DIR/$r"

  if [[ ! -f "$NEW_PATH" ]]; then
    echo "WARN: missing new receipt (skipping): $NEW_PATH"
    continue
  fi

  if [[ ! -f "$OLD_PATH" ]]; then
    echo "WARN: missing old receipt (skipping): $OLD_PATH"
    continue
  fi

  echo "-- Subject: $r --"
  if python scripts/release/drift_gate.py --old "$OLD_PATH" --new "$NEW_PATH" --policy "$POLICY"; then
    echo "OK: $r"
  else
    echo "FAIL: $r"
    FAIL=1
  fi
  echo
done

if [[ "$FAIL" -ne 0 ]]; then
  if [[ "${DRIFT_OVERRIDE:-0}" == "1" || "${DRIFT_OVERRIDE:-}" == "true" ]]; then
    echo "DRIFT GATE MULTI: OVERRIDDEN (one or more subjects drifted)"
    exit 0
  fi
  echo "DRIFT GATE MULTI: FAIL (one or more subjects drifted)"
  exit 1
fi

echo "DRIFT GATE MULTI: PASS (no protected drift across checked subjects)"
