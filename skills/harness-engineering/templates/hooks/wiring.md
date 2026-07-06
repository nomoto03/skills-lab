# hooks 配線ガイド

スクリプトを対象リポジトリの `.claude/hooks/` にコピーし、マーカーを置換した上で、
settings.json の `hooks` キーに以下を追記する(POSIX例。Windowsは
`bash <script>.sh` を `powershell -File <script>.ps1` に読み替える)。

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          { "type": "command", "command": "bash .claude/hooks/protect-config.sh" }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          { "type": "command", "command": "bash .claude/hooks/post-edit-lint.sh" }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          { "type": "command", "command": "bash .claude/hooks/commit-on-stop.sh" }
        ]
      }
    ]
  }
}
```

## 設置チェックリスト

- [ ] `{{MARKER}}` が1つも残っていない(`grep -r '{{' .claude/hooks/`)
- [ ] `.sh` に実行権限がある(`chmod +x .claude/hooks/*.sh`)
- [ ] Exit code契約: `exit 2` = ブロック+stderrをエージェントに提示 / `exit 0` = 通過
- [ ] ダミー編集で発火確認(Phase 6)
