#!/usr/bin/env bash
set -euo pipefail

# verify_verifier_attestations_strict.sh
#
# Hard fail unless GitHub attestations exist and verify for EACH verifier script:
#   - scripts/release/verify_release.sh
#   - scripts/release/verify_release.ps1
#   - scripts/release/verify_attestations.sh
#
# Requires:
#   - gh CLI
#   - authenticated gh (GITHUB_TOKEN in CI)
#
# Usage:
#   ./verify_verifier_attestations_strict.sh --owner OWNER --repo REPO
#
# Notes:
# - This is "maximum strictness": no soft-skips for policy/plan.
# - Use only in environments where attestations are guaranteed to work.

OWNER=""
REPO=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --owner) OWNER="$2"; shift 2 ;;
    --repo)  REPO="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 2 ;;
  esac
done

if [[ -z "$OWNER" || -z "$REPO" ]]; then
  echo "ERR: --owner and --repo are required"
  exit 2
fi

if ! command -v gh >/dev/null 2>&1; then
  echo "ERR: gh CLI not found"
  exit 2
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "ERR: gh not authenticated (set GITHUB_TOKEN)"
  exit 2
fi

echo "== Verifier attestation strict gate =="
echo "Repo: ${OWNER}/${REPO}"
echo

SUBJECTS=(
  "scripts/release/verify_release.sh"
  "scripts/release/verify_release.ps1"
  "scripts/release/verify_attestations.sh"
)

for s in "${SUBJECTS[@]}"; do
  if [[ ! -f "$s" ]]; then
    echo "ERR: missing verifier subject file in workspace: $s"
    exit 1
  fi
done

for s in "${SUBJECTS[@]}"; do
  echo "Verifying attestation for: $s"
  gh attestation verify "$s" --owner "$OWNER" >/dev/null
  echo "OK: $s"
done

echo
echo "STRICT OK: all verifier attestations exist and verify."
