#!/usr/bin/env bash
# Sign policy receipt with cosign (keyless, Sigstore)
set -eu

RECEIPT_FILE="${1:-}"

if [[ -z "$RECEIPT_FILE" || ! -f "$RECEIPT_FILE" ]]; then
    echo "Usage: $0 <receipt.json>" >&2
    exit 1
fi

echo "Signing policy receipt: $RECEIPT_FILE"

# Keyless sign produces .sigstore.json bundle
COSIGN_EXPERIMENTAL=true cosign sign-blob \
    --bundle "${RECEIPT_FILE}.sigstore.json" \
    "$RECEIPT_FILE"

echo "Receipt signature bundle: ${RECEIPT_FILE}.sigstore.json"
