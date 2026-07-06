#!/usr/bin/env bash
# Stop: セッション終了時、未コミット変更があれば自動チェックポイントコミット(セッション間ハンドオフ用)
set -u
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 0
if ! git diff --quiet || ! git diff --cached --quiet || [ -n "$(git ls-files --others --exclude-standard)" ]; then
  git add -A
  git commit -m "wip: session checkpoint (auto-commit by Stop hook)" >/dev/null
fi
exit 0
