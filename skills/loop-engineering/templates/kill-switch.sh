#!/usr/bin/env bash
# PreToolUse(全ツール): AGENT_STOP ファイルが存在したら全ツール呼び出しをブロック(緊急停止)
# 配線は templates/monitoring.md 参照。解除は AGENT_STOP を削除する
set -u
if [ -f "AGENT_STOP" ]; then
  echo "EMERGENCY STOP: AGENT_STOP file present. Stop all work now and end the session." >&2
  exit 2
fi
exit 0
