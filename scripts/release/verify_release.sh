#!/usr/bin/env bash
set -euo pipefail

# verify_release.sh
# Verifies:
#  1) SHA256 matches *.sha256 file
#  2) cosign verifies blob using *.sigstore.json bundle
#  3) (optional) GitHub attestations presence via gh (best-effort)
#
# Usage:
#   ./verify_release.sh [--repo OWNER/REPO] [--tag TAG] [--no-gh]
#
# Notes:
# - Does not download assets; run in a directory containing the release files.

REPO=""
TAG=""
USE_GH="yes"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo) REPO="$2"; shift 2 ;;
    --tag)  TAG="$2"; shift 2 ;;
    --no-gh) USE_GH="no"; shift ;;
    *) echo "Unknown arg: $1"; exit 2 ;;
  esac
done

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
