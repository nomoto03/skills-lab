#!/usr/bin/env bash
# PreToolUse (Write|Edit): ハーネス設定・シークレットの改変をブロック
# 設置時の置換: {{LINT_CONFIG}} = リンタ設定ファイル名の正規表現(例: \.oxlintrc\.json)
set -u
INPUT=$(cat)
FILE=$(printf '%s' "$INPUT" | sed -n 's/.*"file_path"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
[ -z "$FILE" ] && exit 0
PROTECTED='(\.env($|\.)|\.claude/settings.*\.json|\.claude/hooks/|{{LINT_CONFIG}})'
if printf '%s' "$FILE" | grep -Eq "$PROTECTED"; then
  echo "BLOCKED: $FILE is protected harness configuration. Ask the user to change it manually." >&2
  exit 2
fi
exit 0
