#!/usr/bin/env bash
# PostToolUse (Write|Edit): 編集されたファイルにリンタを実行し、違反をエージェントに差し戻す
# 設置時の置換: {{LINT_CMD}} = リンタコマンド(例: npx oxlint)、{{EXT}} = 対象拡張子(例: ts)
set -u
INPUT=$(cat)
FILE=$(printf '%s' "$INPUT" | sed -n 's/.*"file_path"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
[ -z "$FILE" ] && exit 0
case "$FILE" in
  *.{{EXT}}) ;;
  *) exit 0 ;;
esac
if ! OUTPUT=$({{LINT_CMD}} "$FILE" 2>&1); then
  echo "Lint failed for $FILE — fix these before proceeding:" >&2
  echo "$OUTPUT" >&2
  exit 2
fi
exit 0
