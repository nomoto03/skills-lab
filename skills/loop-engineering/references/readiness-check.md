# ループ実行可能性チェック(R1〜R7)

Phase 2 で判定する。**R1・R7 は点火ブロッカー: FAILのままでは Phase 6 に進まない。**

| ID | 項目 | 判定方法 | FAIL時 |
|---|---|---|---|
| R1 | 終了条件がコマンドで機械検証可能 | Phase 1 で定義した検証コマンドを実際に実行し、真偽が返ることを確認 | **点火不可**。Phase 1 に戻る |
| R2 | 検証手段(テスト等)が存在し1反復あたり数分以内 | テストを実行し所要時間を計測 | harness-engineering提案 or 縮退(リンタのみ+終了条件を目視レビューに変更) |
| R3 | git管理+専用ブランチ/worktreeで隔離可能 | `git rev-parse --is-inside-work-tree`、作業中の変更の有無 | git init / ループ用ブランチ・worktree作成を先行 |
| R4 | 無人実行に見合うpermissions(deny基盤) | `.claude/settings*.json` の deny を確認 | 設置に含める(harness-engineeringのsettings-permissions.jsonを案内) |
| R5 | 状態外部化の場所(PROGRESS.md/feature-list) | ファイルの有無 | harness-engineeringのtemplates/progress/を設置 |
| R6 | トークン予算とレビュー帯域が見積もられている | Phase 1 の回答(Q2)から算出済みか | 見積りを設計書に明記してから進む |
| R7 | 緊急停止手段 | kill-switchフック設置済みか、または方式固有の停止手順が確立しているか | **点火不可**。`templates/kill-switch.*` 設置で解消 |

## 運用ルール

- 不足が2項目以上ある場合は harness-engineering スキルの実行を提案する(依存はしない —
  R4/R5 は harness のテンプレートを、R7 はこのスキルの kill-switch を使えば単独でも解消できる)
- 判定結果は `<scratchpad>/loop-readiness.md` に R1〜R7 の PASS/FAIL と根拠を記録する
- サブエージェント失敗時はメインスレッドで縮退チェック(R1・R3・R7 のみ)にフォールバック
