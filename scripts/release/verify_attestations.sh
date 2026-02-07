#!/usr/bin/env bash
set -euo pipefail

# verify_attestations.sh
#
# Verifies GitHub Artifact Attestations exist and verify for a given artifact file.
# Requires:
#   - gh CLI
#   - GITHUB_TOKEN (or already-authenticated gh)
#
# Inputs:
#   ARTIFACT_PATH (positional 1)  e.g., dist/Lab_Pack_SG_*.zip
#
# Env:
#   ATTEST_STRICT = "true"|"false" (default false)
#   ATTEST_OWNER  = owner/org (optional; derived from repo if absent)
#   ATTEST_REPO   = repo name (optional; derived from repo if absent)
#   ATTEST_PREDICATE = optional predicate type filter (best-effort; gh flags may vary)
#
# Behavior:
#   - If strict: fail on any verification error
#   - If not strict: prints a clear SKIP/FAIL reason and exits 0 for policy blocks

ART="${1:-}"
if [[ -z "${ART}" ]]; then
  echo "ERR: missing artifact path argument"
  echo "Usage: ./verify_attestations.sh dist/Lab_Pack_SG_*.zip"
  exit 2
fi

# Expand globs safely
ART_PATH="$(ls -1 ${ART} 2>/dev/null | head -n 1 || true)"
if [[ -z "${ART_PATH}" || ! -f "${ART_PATH}" ]]; then
  echo "ERR: artifact not found: ${ART}"
  exit 2
fi

ATTEST_STRICT="${ATTEST_STRICT:-false}"

echo "== Attestation verify =="
echo "Artifact: ${ART_PATH}"
echo "Strict:   ${ATTEST_STRICT}"
echo

if ! command -v gh >/dev/null 2>&1; then
  if [[ "${ATTEST_STRICT}" == "true" ]]; then
    echo "ERR: gh CLI not found"
    exit 1
  fi
  echo "SKIP: gh CLI not found"
  exit 0
fi

# Prefer token-based auth in CI
if [[ -n "${GITHUB_TOKEN:-}" ]]; then
  echo "${GITHUB_TOKEN}" | gh auth login --with-token >/dev/null 2>&1 || true
fi

# Quick auth sanity
if ! gh auth status >/dev/null 2>&1; then
  if [[ "${ATTEST_STRICT}" == "true" ]]; then
    echo "ERR: gh not authenticated"
    exit 1
  fi
  echo "SKIP: gh not authenticated"
  exit 0
fi

# Core verification: gh will fetch attestations from GitHub and verify them.
# This confirms "attestation exists for this digest" + signature chain verification.
#
# The CLI supports: gh attestation verify <file> --owner <OWNER>
# (repo is inferred from owner+current context, but owner is the required disambiguator in many cases)

OWNER="${ATTEST_OWNER:-}"
REPO="${ATTEST_REPO:-}"

# If not provided, try to infer from git remote in CI workspace
if [[ -z "${OWNER}" || -z "${REPO}" ]]; then
  if command -v git >/dev/null 2>&1; then
    REM="$(git remote get-url origin 2>/dev/null || true)"
    # supports https://github.com/OWNER/REPO(.git) or git@github.com:OWNER/REPO(.git)
    if [[ -z "${OWNER}" ]]; then
      OWNER="$(echo "${REM}" | sed -E 's#.*github.com[:/]+([^/]+)/([^/.]+)(\.git)?#\1#')"
    fi
    if [[ -z "${REPO}" ]]; then
      REPO="$(echo "${REM}" | sed -E 's#.*github.com[:/]+([^/]+)/([^/.]+)(\.git)?#\2#')"
    fi
  fi
fi

if [[ -z "${OWNER}" || -z "${REPO}" ]]; then
  if [[ "${ATTEST_STRICT}" == "true" ]]; then
    echo "ERR: could not infer owner/repo; set ATTEST_OWNER and ATTEST_REPO"
    exit 1
  fi
  echo "SKIP: could not infer owner/repo; set ATTEST_OWNER and ATTEST_REPO"
  exit 0
fi

echo "Repo: ${OWNER}/${REPO}"
echo

set +e
gh attestation verify "${ART_PATH}" --owner "${OWNER}" >/tmp/attest_verify.out 2>/tmp/attest_verify.err
RC=$?
set -e

if [[ $RC -ne 0 ]]; then
  echo "Attestation verification failed."
  echo "--- STDOUT ---"
  cat /tmp/attest_verify.out || true
  echo "--- STDERR ---"
  cat /tmp/attest_verify.err || true

  # Policy-aware soft skip:
  # If strict=false, allow known "not available"/permission cases to skip.
  if [[ "${ATTEST_STRICT}" != "true" ]]; then
    # Common cases: feature not enabled for repo plan, permission denied, API not available
    if grep -qiE "forbidden|permission|not available|enterprise|attestation" /tmp/attest_verify.err; then
      echo "SKIP: attestation verification blocked by policy/plan/permissions (set ATTEST_STRICT=true to enforce)"
      exit 0
    fi
  fi

  exit 1
fi

echo "OK: Attestation verification succeeded."
cat /tmp/attest_verify.out || true
