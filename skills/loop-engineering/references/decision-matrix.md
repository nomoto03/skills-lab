# ループ方式選定マトリクス

Phase 3 で1方式を推奨する。採らなかった方式にも1行ずつ理由を付す。

## 選定表

| タスク特性 | 推奨方式 | 理由 |
|---|---|---|
| 数十分〜数時間で終わる見込み、条件明確 | `/goal` | 部品追加ゼロ。条件チェックは別の高速モデルが毎ターン実施 |
| 外部状態のポーリング(CI待ち、定期チェック) | `/loop` | 間隔駆動が自然。回数/間隔を指定できる |
| 複数セッション級の大型構築、夜間無人 | Ralph型 | Stopフック再投入で文脈リセット+ファイル継承。max-iterations必須 |
| 検証の独立性を強制したい(自己採点を許さない) | 外部スクリプト型 | evaluatorゲートを通らないと次反復に進めない構造(`templates/external-loop.sh`) |
| 定期メンテ(依存更新、レポート生成)、ローカル不要 | schedule(cloud) | cron的定期実行、マシン不要 |

## 方式別の安全装置対応表(設計書に転記する)

| 方式 | 反復上限の実装 | 緊急停止 | 初回観察(Phase 6) |
|---|---|---|---|
| `/goal` | 目安時間で人間が確認(上限は運用) | AGENT_STOP または Esc | 必須(1反復完了まで) |
| `/loop` | 回数指定 | AGENT_STOP または Esc | 必須(1反復完了まで) |
| Ralph型 | `--max-iterations`(必須) | AGENT_STOP(次ツール呼び出しで停止) | 起動確認のみ(状態ファイル初回書き込みまで) |
| 外部スクリプト型 | whileカウンタ({{MAX_ITER}}) | AGENT_STOP または Ctrl-C | 必須(builder+evaluator各1回完了まで) |
| schedule | 実行回数・期限 | 登録削除 | 省略可(登録内容の確認のみ) |

## 組み合わせの指針

- Ralph型・外部スクリプト型には必ず状態ファイル(PROGRESS.md / feature-list.json)を併設する
- どの方式でも kill-switch(`templates/kill-switch.sh` / `.ps1`)の設置を推奨。
  無人実行(Ralph/外部/schedule)では必須(R7)
- 完全自動権限(bypassPermissions)はサンドボックス/コンテナ内のみ。
  ホストOSでは acceptEdits + deny基盤までに留める
