#!/usr/bin/env bash
# Fail if any tracked file leaks a home directory path or a credential-shaped
# string. This is the check CI runs, and it is the reason .github/ and this
# script are excluded from the scan: they are where the patterns are written
# down. Binary files (the atlases and the preview GIFs) are scanned too, since
# an embedded path or key would sit in them as plain bytes.

set -uo pipefail
cd "$(dirname "$0")/.."

patterns=(
  '/Users/[A-Za-z0-9._-]+'          # macOS home directory
  '/home/[A-Za-z0-9._-]+'           # Linux home directory
  'C:\\Users\\'                     # Windows home directory
  'AKIA[0-9A-Z]{16}'                # AWS access key id
  'gh[pousr]_[A-Za-z0-9]{36,}'      # GitHub token
  'sk-[A-Za-z0-9_-]{20,}'           # generic secret key
  'xox[baprs]-'                     # Slack token
  '-----BEGIN [A-Z ]*PRIVATE KEY-----'
  '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'   # email address
)

fail=0
for pattern in "${patterns[@]}"; do
  hits="$(grep -rnaE \
            --exclude-dir=.git \
            --exclude-dir=.github \
            --exclude='sanitize-check.sh' \
            -e "$pattern" . || true)"
  if [ -n "$hits" ]; then
    printf 'pattern %s matched:\n%s\n\n' "$pattern" "$hits"
    fail=1
  fi
done

if [ "$fail" -ne 0 ]; then
  echo "sanitize-check: FAILED" >&2
  exit 1
fi
echo "sanitize-check: clean"
