#!/usr/bin/env bash
set -euo pipefail

# bundle_policy_receipts.sh
#
# Creates policy-receipts-<TAG>.zip containing:
#   - policy-receipts-index.json
#   - canonical/*.canonical.json
#   - canonical/*.canonical.json.sigstore.json
#
# Usage:
#   ./bundle_policy_receipts.sh <TAG> <REPO>
#
# Output: dist/policy-receipts-<TAG>.zip

TAG="${1:-}"
REPO="${2:-}"

if [[ -z "$TAG" ]]; then
  echo "ERR: TAG required"
  exit 2
fi

cd "$(dirname "$0")/../.."

if [[ ! -d dist/receipts/canonical ]]; then
  echo "ERR: dist/receipts/canonical not found"
  exit 2
fi

# Write tag/repo for index generator
echo "$TAG" > .tag
echo "$REPO" > .repo

# Generate index
python scripts/release/generate_policy_receipts_index.py

# Create staging directory
rm -rf dist/policy-receipts
mkdir -p dist/policy-receipts/canonical

# Copy index
cp dist/receipts/policy-receipts-index.json dist/policy-receipts/

# Copy canonical receipts + sigstore bundles
cp dist/receipts/canonical/*.canonical.json dist/policy-receipts/canonical/ || true
cp dist/receipts/canonical/*.canonical.json.sigstore.json dist/policy-receipts/canonical/ || true

# Create zip
cd dist
ZIP_NAME="policy-receipts-${TAG}.zip"
rm -f "$ZIP_NAME"
zip -r "$ZIP_NAME" policy-receipts/

echo "Created: dist/$ZIP_NAME"

# Cleanup staging
rm -rf policy-receipts

cd ..
rm -f .tag .repo
