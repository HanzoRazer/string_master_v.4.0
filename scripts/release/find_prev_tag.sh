#!/usr/bin/env bash
set -euo pipefail

# find_prev_tag.sh
# Finds the previous tag before CURRENT_TAG, using tag creatordate ordering.
#
# Usage:
#   ./find_prev_tag.sh v1.2.3
#
# Output: previous tag on stdout, empty if none

CUR="${1:-}"
if [[ -z "$CUR" ]]; then
  echo "ERR: missing current tag" >&2
  exit 2
fi

# Ensure tags available
git fetch --tags --force >/dev/null 2>&1 || true

TAGS="$(git tag --sort=-creatordate)"
PREV=""
FOUND=0
while IFS= read -r t; do
  if [[ "$FOUND" -eq 1 ]]; then
    PREV="$t"
    break
  fi
  if [[ "$t" == "$CUR" ]]; then
    FOUND=1
  fi
done <<< "$TAGS"

echo "$PREV"
