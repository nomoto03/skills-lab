#!/usr/bin/env bash
# 外部スクリプト型ループ: builder(claude -p)→ 独立evaluatorゲート → 検証
# 置換: {{REPO_DIR}} {{MAX_ITER}} {{MAX_STALL}} {{VERIFY_CMD}} {{BUILDER_PROMPT}} {{PROGRESS_CMD}}
# 注意: 無人実行を bypassPermissions で行うのはサンドボックス/コンテナ内のみ。
#       ホストOSでは acceptEdits + permissions.deny 基盤までに留めること。
set -u
cd "{{REPO_DIR}}" || exit 1
ITER=0
STALL=0
LAST_PROGRESS=""
while [ "$ITER" -lt "{{MAX_ITER}}" ]; do
  if [ -f AGENT_STOP ]; then
    echo "AGENT_STOP detected — emergency stop."
    exit 1
  fi
  if {{VERIFY_CMD}}; then
    echo "GOAL REACHED after $ITER iterations."
    exit 0
  fi
  ITER=$((ITER + 1))
  echo "=== iteration $ITER / {{MAX_ITER}} ==="
  claude -p "{{BUILDER_PROMPT}}" --permission-mode acceptEdits || echo "builder exited nonzero (continuing)"
  VERDICT=$(claude --agent evaluator -p "Review the most recent commit against PROGRESS.md and feature-list.json. First line of your reply must be PASS or NEEDS_WORK.")
  FIRST_LINE=$(printf '%s' "$VERDICT" | head -1)
  echo "evaluator: $FIRST_LINE"
  if [ "$FIRST_LINE" != "PASS" ]; then
    printf '%s\n' "$VERDICT" > NEXT_FINDINGS.md
  fi
  PROGRESS=$({{PROGRESS_CMD}})
  if [ "$PROGRESS" = "$LAST_PROGRESS" ]; then
    STALL=$((STALL + 1))
  else
    STALL=0
  fi
  LAST_PROGRESS="$PROGRESS"
  if [ "$STALL" -ge "{{MAX_STALL}}" ]; then
    echo "No progress for {{MAX_STALL}} iterations — stopping. See NEXT_FINDINGS.md"
    exit 1
  fi
done
echo "MAX_ITER ({{MAX_ITER}}) reached without goal. See NEXT_FINDINGS.md"
exit 1
