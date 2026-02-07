#!/usr/bin/env bash
set -euo pipefail

# verify_release.sh
# Verifies:
#  1) SHA256 matches *.sha256 file
#  2) cosign verifies blob using *.sigstore.json bundle
#  3) (optional) GitHub attestations presence via gh (best-effort)
#  4) (optional) Self-integrity pin check against provenance.json
#
# Usage:
#   ./verify_release.sh [--repo OWNER/REPO] [--tag TAG] [--no-gh] [--pin off|warn|strict] [--pin-file FILE]
#
# Verifier pinning:
#   --pin off      Do not check verifier pins (default)
#   --pin warn     Print warnings if mismatch but continue
#   --pin strict   Exit with failure if mismatch
#   --pin-file     Path to provenance.json (default: provenance.json)
#
# Environment:
#   PIN_MODE       Sets pin mode (overridden by --pin)
#   PIN_FILE       Sets pin file (overridden by --pin-file)
#
# Notes:
# - Does not download assets; run in a directory containing the release files.

# Pin mode defaults
PIN_MODE="${PIN_MODE:-off}"
PIN_FILE="${PIN_FILE:-provenance.json}"

REPO=""
TAG=""
USE_GH="yes"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo) REPO="$2"; shift 2 ;;
    --tag)  TAG="$2"; shift 2 ;;
    --no-gh) USE_GH="no"; shift ;;
    --pin) PIN_MODE="$2"; shift 2 ;;
    --pin-file) PIN_FILE="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 2 ;;
  esac
done

# Helper: compute SHA256 of a file
sha256_of_file() {
  local f="$1"
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$f" | awk '{print $1}'
  elif command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$f" | awk '{print $1}'
  else
    echo "ERR: no sha256sum or shasum available" >&2
    return 1
  fi
}

# Helper: extract pin SHA256 for a given verifier name from provenance.json
get_pin_sha() {
  local name="$1"
  local pin_file="$2"
  
  # Try python3 first
  if command -v python3 >/dev/null 2>&1; then
    python3 -c "
import json, sys
with open('$pin_file', 'r', encoding='utf-8') as f:
    data = json.load(f)
pins = data.get('verifier_pins', {}).get('pins', [])
for pin in pins:
    if pin.get('name') == '$name':
        print(pin.get('sha256', ''))
        sys.exit(0)
" 2>/dev/null || true
  elif command -v jq >/dev/null 2>&1; then
    # Fallback to jq if available
    jq -r ".verifier_pins.pins[] | select(.name == \"$name\") | .sha256" "$pin_file" 2>/dev/null || true
  fi
}

# Self-integrity check: verify this verifier script matches pinned hash
self_pin_check() {
  local mode="$1"
  local pin_file="$2"
  
  if [[ "$mode" == "off" ]]; then
    return 0
  fi
  
  if [[ ! -f "$pin_file" ]]; then
    if [[ "$mode" == "strict" ]]; then
      echo "ERR: Pin file not found: $pin_file (strict mode)" >&2
      exit 2
    elif [[ "$mode" == "warn" ]]; then
      echo "WARN: Pin file not found: $pin_file" >&2
    fi
    return 0
  fi
  
  local script_name="verify_release.sh"
  local expected_sha
  expected_sha="$(get_pin_sha "$script_name" "$pin_file")"
  
  if [[ -z "$expected_sha" ]]; then
    if [[ "$mode" == "strict" ]]; then
      echo "ERR: No pin found for $script_name in $pin_file (strict mode)" >&2
      exit 2
    elif [[ "$mode" == "warn" ]]; then
      echo "WARN: No pin found for $script_name in $pin_file" >&2
    fi
    return 0
  fi
  
  local actual_sha
  actual_sha="$(sha256_of_file "$0")"
  
  if [[ "$actual_sha" != "$expected_sha" ]]; then
    echo "ERR: Verifier integrity mismatch for $script_name" >&2
    echo "  Expected: $expected_sha" >&2
    echo "  Actual:   $actual_sha" >&2
    if [[ "$mode" == "strict" ]]; then
      echo "  (strict mode: FAIL)" >&2
      exit 2
    elif [[ "$mode" == "warn" ]]; then
      echo "  (warn mode: continuing)" >&2
    fi
  else
    echo "OK: Verifier pin check passed for $script_name" >&2
  fi
}

# Optional: check sibling verifier scripts against pins
check_sibling() {
  local mode="$1"
  local pin_file="$2"
  local script_name="$3"
  local script_path="$4"
  
  if [[ "$mode" == "off" ]]; then
    return 0
  fi
  
  if [[ ! -f "$script_path" ]]; then
    return 0  # Not present, skip
  fi
  
  local expected_sha
  expected_sha="$(get_pin_sha "$script_name" "$pin_file")"
  
  if [[ -z "$expected_sha" ]]; then
    return 0  # No pin, skip
  fi
  
  local actual_sha
  actual_sha="$(sha256_of_file "$script_path")"
  
  if [[ "$actual_sha" != "$expected_sha" ]]; then
    echo "WARN: Sibling verifier mismatch: $script_name" >&2
    echo "  Expected: $expected_sha" >&2
    echo "  Actual:   $actual_sha" >&2
    if [[ "$mode" == "strict" ]]; then
      echo "  (strict mode: FAIL)" >&2
      exit 2
    fi
  else
    echo "OK: Sibling verifier pin check passed for $script_name" >&2
  fi
}

# Run self-integrity check early
self_pin_check "$PIN_MODE" "$PIN_FILE"

# Check sibling verifiers if in warn/strict mode
if [[ "$PIN_MODE" != "off" && -f "$PIN_FILE" ]]; then
  check_sibling "$PIN_MODE" "$PIN_FILE" "verify_release.ps1" "verify_release.ps1"
  check_sibling "$PIN_MODE" "$PIN_FILE" "verify_attestations.sh" "verify_attestations.sh"
fi

ZIP="$(ls -1 Lab_Pack_SG_*.zip 2>/dev/null | head -n 1 || true)"
SHA="${ZIP}.sha256"
BUNDLE="${ZIP}.sigstore.json"

if [[ -z "${ZIP}" ]]; then
  echo "ERR: no Lab_Pack_SG_*.zip found in current directory"
  exit 2
fi
if [[ ! -f "${SHA}" ]]; then
  echo "ERR: missing ${SHA}"
  exit 2
fi
if [[ ! -f "${BUNDLE}" ]]; then
  echo "ERR: missing ${BUNDLE}"
  exit 2
fi

echo "== Files =="
echo "ZIP:    ${ZIP}"
echo "SHA:    ${SHA}"
echo "BUNDLE: ${BUNDLE}"
echo

echo "== SHA256 =="
if command -v sha256sum >/dev/null 2>&1; then
  sha256sum -c "${SHA}"
else
  # macOS typically uses shasum
  shasum -a 256 -c "${SHA}"
fi
echo

echo "== Cosign verify-blob =="
if ! command -v cosign >/dev/null 2>&1; then
  echo "ERR: cosign not found in PATH"
  echo "Install: https://docs.sigstore.dev/quickstart/quickstart-cosign/"
  exit 2
fi

cosign verify-blob --bundle "${BUNDLE}" "${ZIP}"
echo

if [[ "${USE_GH}" == "yes" ]]; then
  if command -v gh >/dev/null 2>&1; then
    if [[ -n "${REPO}" && -n "${TAG}" ]]; then
      echo "== GitHub release presence (best-effort) =="
      gh release view "${TAG}" --repo "${REPO}" >/dev/null
      echo "OK: release exists: ${REPO} ${TAG}"
      echo
      echo "NOTE: Attestation verification is org-policy/tooling dependent."
      echo "See: https://docs.github.com/actions/security-for-github-actions/using-artifact-attestations/"
    else
      echo "== GH check skipped (missing --repo and/or --tag) =="
      echo "Tip: ./verify_release.sh --repo OWNER/REPO --tag vX.Y.Z"
    fi
  else
    echo "== GH check skipped (gh not installed) =="
  fi
fi

echo
echo "VERIFIED: OK"
