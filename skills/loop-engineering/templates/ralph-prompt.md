<!-- テンプレート: Ralph型ループの PROMPT.md。全マーカーを実値に置換して
     対象リポジトリに設置し、/ralph-loop または Stopフック再投入で使う。
     completion promise は正確な文字列一致のみ。max-iterations を必ず併用する -->

# ゴール

{{GOAL_SUMMARY}}

完了の定義: `{{VERIFY_CMD}}` が成功すること。

# 段階的フェーズ

{{PHASE_LIST}}

# 毎反復の手順

1. `git log --oneline -10` と PROGRESS.md と feature-list.json を読み、現在地を把握する
2. `"passes": false` の項目から**1つだけ**選ぶ(フェーズ順)
3. 実装し、その項目の verification に書かれた検証を実際に実行する
4. 検証が通った場合のみ passes を true にし、evidence に実行コマンドと結果を書く
5. コミットし、PROGRESS.md に「やったこと・テスト結果・次への注意」を追記して終了する

# 禁止事項

- 検証の実行なしに passes を true にすること
- 1反復で複数項目に手を出すこと
- テスト・リンタ設定の書き換えによる「合格」

# 完了と脱出

- 全項目が passes: true かつ `{{VERIFY_CMD}}` 成功 → 最終行に
  <promise>{{PROMISE}}</promise> とだけ出力する(完了していない限り絶対に出力しない)
- 同じ項目で {{MAX_STALL}} 反復進捗がない → 課題と試行ログを {{FINDINGS_FILE}} に
  書き出し、「BLOCKED: 人間の判断が必要」と PROGRESS.md に記録する(promiseは出力しない)
