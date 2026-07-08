#!/usr/bin/env bash
# PostToolUse (Write|Edit): run the repo structure check after markdown edits.
# POSIX pair of post-edit-lint.ps1 (kept per this repo's "both OS variants" rule).
# Non-Windows users: wire this variant in settings and install pwsh.
set -u
INPUT=$(cat)
FILE=$(printf '%s' "$INPUT" | sed -n 's/.*"file_path"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
[ -z "$FILE" ] && exit 0
case "$FILE" in
  *.md) ;;
  *) exit 0 ;;
esac
if ! pwsh -NoProfile -File scripts/check-structure.ps1 "$FILE"; then
  echo "Structure check failed after editing $FILE - fix the violations above before proceeding." >&2
  exit 2
fi
exit 0
