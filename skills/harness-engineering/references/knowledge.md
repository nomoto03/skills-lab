# ハーネスエンジニアリング知見集

診断と提案の根拠。Phase 3(診断+設計)のサブエージェントに必ず読ませる。

## 大原則

1. **最小構成から始め、必要時のみ複雑化する**(Anthropic)。ハーネスの各部品は
   「モデルが単独でできないことを補う」仮説を持つ。不要になった部品は削る。
   過剰な先回り最適化をしない — 問題が実際に起きてから部品を足す。
2. **プロンプトではなく仕組みで強制する**。「テストを書いて」と頼むのではなく、
   フックでテスト未合格なら完了できなくする。
3. **成功宣言を自己申告にさせない**。default-FAILの機能リスト、独立evaluator、
   証拠(テスト出力・スクリーンショット)の必須化で構造的に防ぐ。

## 3層責任分離

| 層 | 手段 | 役割 |
|---|---|---|
| Intent | CLAUDE.md | 助言のみ。ブロック能力なし |
| Harness | permissions / hooks | 実行前ゲート。deny → ask → allow の順に評価 |
| Environment | sandbox / OSユーザー / ネットワーク | 最終防御線 |

ブロックしたいものをCLAUDE.mdに書くのは層違い。permissions.denyかhookで実装する。

## フィードバック速度の階層

PostToolUseフック(ミリ秒) → pre-commit(秒) → CI(分) → 人間レビュー(時間)。
検査は可能な限り速い層に寄せる。前提として高速なリンタが必要:
TypeScript→oxlint/Biome、Python→ruff、Go→golangci-lint。
遅い検査(数十秒超)をPostToolUseに入れると逆効果(全編集が遅くなる)。

## CLAUDE.md の設計

- 50行以下。150行を超えると命令が埋もれる
- ポインタ形式(「設計判断は docs/adr/ を見よ」)。ポインタの腐りは参照エラーで
  検出できるが、説明文の腐りは静かに蓄積する
- 削除テスト: 「この行を消すとエージェントが失敗するか?」Noなら削除
- 書くべき内容: ビルド/テスト/リンタの実コマンド、命名・ブランチ規約、
  ファイル配置、詳細へのポインタ
- 書くべきでない内容: アーキテクチャの長文解説(→ADR)、禁止事項(→deny/hook)

## 知識の置き場所

腐りやすい説明文書(アーキテクチャ解説、API仕様書)より、実行可能な成果物
(テスト、型、スキーマ)と ADR(追記専用の決定記録)で表現する。
テストは実行すれば真偽が自動判定されるが、文書の正しさは誰も検証しない。

## 長時間実行の基本形(Anthropic公式パターン)

- 初期化(初回のみ): 起動スクリプト、PROGRESS.md、機能リスト(JSON,
  全項目 `"passes": false`)、git初期コミット
- 各セッション: git log + PROGRESS.md + 機能リストを読む → 1機能だけ実装 →
  実際に動かして検証 → コミット + 進捗更新して終了
- 評価は実装者と分離: 読み取り専用のevaluatorサブエージェントが
  新規コンテキストで判定する(実装者は自分の仕事を甘く採点するため)

## アンチパターン

- CLAUDE.mdのみでガード(deny規則なし)
- ホストOS上での `--dangerously-skip-permissions`(完全自動はサンドボックス内のみ)
- `Bash(*)` 全許可とMCP書き込みスコープの組み合わせ
- CLAUDE.md / AGENTS.md の肥大化
- エージェント専用インフラの構築(人間用の優れたインフラを共有するのが正解)
- エージェントがリンタ設定・フック定義を書き換えてルールを回避できる状態

## 出典

- https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
- https://www.anthropic.com/engineering/harness-design-long-running-apps
- https://github.com/anthropics/cwc-long-running-agents
- https://www.humanlayer.dev/blog/skill-issue-harness-engineering-for-coding-agents
- https://hidekazu-konishi.com/entry/claude_code_harness_and_environment_engineering_guide.html
- https://nyosegawa.com/en/posts/harness-engineering-best-practices-2026/
