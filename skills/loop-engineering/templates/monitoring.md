# 監視手順: {{GOAL_SUMMARY}}

<!-- テンプレート: Phase 6 でマーカーを実値に置換してユーザーに渡す -->

## 進捗の見方

- `{{WATCH_CMD}}` を {{INTERVAL}} ごとに確認
- 成功判定はいつでも手動で実行できる: `{{VERIFY_CMD}}`

## 介入(指示の追加・軌道修正)

- {{STEER_METHOD}}

## 停止方法

- **緊急停止(全方式共通)**: リポジトリルートに `AGENT_STOP` ファイルを作成する
  (解除は削除)。kill-switch フックが次のツール呼び出しをブロックする
- 方式別:
  - `/goal`・`/loop`: セッションで Esc、または AGENT_STOP
  - Ralph型: AGENT_STOP(次のツール呼び出しで停止)
  - 外部スクリプト型: AGENT_STOP または Ctrl-C
  - schedule型: 登録を削除する — `{{SCHEDULE_REMOVE_CMD}}`

## kill-switch の配線(settings.json に追記済みであること)

```json
{
  "hooks": {
    "PreToolUse": [
      { "hooks": [ { "type": "command", "command": "bash .claude/hooks/kill-switch.sh" } ] }
    ]
  }
}
```

(Windows は `powershell -NoProfile -ExecutionPolicy Bypass -File .claude/hooks/kill-switch.ps1`)

## 完走後レビュー

- `{{REVIEW_CMD}}`(例: `git log --oneline` と `git diff <開始タグ>..HEAD`)で全差分をレビューする
- 失敗終了時は {{FINDINGS_FILE}} を読み、次のループ設計に反映する
