# ループ設計書: {{GOAL_SUMMARY}}

<!-- テンプレート: Phase 4 で全マーカーを実値に置換してユーザーに提示し、承認を得る。
     反復上限・予算・緊急停止の3点が埋まっていない設計書では点火しない -->

## 終了条件

- 成功: `{{VERIFY_CMD}}` が {{EXPECTED}} を返す
- 失敗: 反復 {{MAX_ITER}} 回到達、または {{MAX_STALL}} 反復連続で進捗なし
  (進捗メトリクス = {{PROGRESS_METRIC}})

## 方式

- 採用: {{LOOP_TYPE}}
- 却下案: {{REJECTED}} — {{WHY}}

## 予算

- 最大 {{TOKEN_BUDGET}} トークン相当 / 想定 {{HOURS}} 時間
- 完走後レビュー帯域: {{REVIEW_BUDGET}}(diffを読む時間もこのループのコスト)

## 検証の独立性

- {{EVALUATOR}}(実装エージェントの自己申告は成功判定に使わない)
- 検証軸: {{EVAL_AXES}}(デフォルト1軸。追加条件は decision-matrix.md「検証の多軸化」)
- モデル割当: {{MODEL_ASSIGNMENT}}(目安は decision-matrix.md「役割別モデル割当」)

## 失敗時のエスカレーション

- {{ESCALATION}}。課題は {{FINDINGS_FILE}} に記録して終了する

## 緊急停止と監視

- 緊急停止: `{{KILL_SWITCH_PATH}}` を作成すると次のツール呼び出しで停止
- 監視: `{{WATCH_CMD}}` を {{INTERVAL}} ごとに確認(詳細は monitoring.md)
