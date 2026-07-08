---
name: loop-engineering
description: Use when the user wants to achieve a goal by running an agent in an autonomous loop — triggers include "ループで達成して", "夜間に自律実行させたい", "終わるまで回して", "set up a loop for this goal", "run until tests pass". Converts the goal into a machine-verifiable termination condition, checks loop readiness (R1-R7), selects the best loop type (/goal, /loop, Ralph-style, external script, schedule), gets the loop spec approved, installs the parts, ignites the loop, and hands over monitoring/stop procedures. Never ignites without max-iterations, budget, and a kill switch.
---

# Loop Engineering

「このゴールをループで達成したい」に応える。以下の6フェーズを順に実行する。

## 原則(全フェーズ共通)

- **安全装置なしに点火しない**: 反復上限・予算・緊急停止手段の3点が埋まっていない
  設計書では Phase 6 に進まない。R1(機械検証可能な終了条件)と R7(緊急停止手段)が
  FAIL のままでも点火しない
- **成功判定を実装エージェントの自己申告にさせない**(決定論的コマンド or 独立evaluator)
- テンプレートの `{{MARKER}}` は必ず実値に置換する。残したままの設置を禁止
- 中間ファイル(loop-readiness.md)はセッションのスクラッチパッドに置く
- 完全自動権限(bypassPermissions)はサンドボックス/コンテナ内のみ。
  ホストOSでは acceptEdits + deny 基盤までに留める
- リポジトリを見れば分かることをユーザーに聞かない

## Phase 1: ゴールの検証可能化(メインスレッド)

- ゴールを「コマンド1つで真偽判定できる終了条件」に変換する。
  例: 「APIを完成させる」→「feature-list.json の全項目 passes:true かつ npm test 緑」
- 変換できないゴール(「良い感じにする」等)は理由を示して停止し、
  人間参加型ループ(承認ゲート付きで人が各反復を確認する形)への縮退を提案する
- ゴールが「独立に検証可能なサブゴール3個以上」に分解できる複合機能(エピック級)の
  場合は、単一ループにせず **Planner分解型アウターループ**をオプションとして提案する:
  ①計画分解→人間承認(writing-plans 等の計画スキルがあればそれを使い、なければ
  計画ファイルを書く) ②サブゴールごとに本スキルで単一ループを設計・点火
  ③統合ブランチへマージ+全体レビュー。
  ユーザーが「単一の大きなループで行く」を選べばそのまま Phase 2 へ進む
- `references/interview.md` の Q1〜Q4 を1回の AskUserQuestion で聞く
  (無人時間帯 / 予算・反復上限 / エスカレーション先 / 並列worktree)

## Phase 2: 実行可能性チェック(Explore サブエージェント、軽量)

- `references/readiness-check.md` の R1〜R7 を判定させる(検証コマンドとテストは
  実際に実行して所要時間を計測)。結果はメインスレッドが
  `<scratchpad>/loop-readiness.md` に保存する
- R1・R7 が FAIL なら解消するまで先に進まない(R7 は kill-switch 設置で解消可)
- 不足が2項目以上なら harness-engineering スキルの実行を提案(依存はしない)
- サブエージェント失敗時はメインスレッドで縮退チェック(R1・R3・R7 のみ)

## Phase 3: 方式選定(メインスレッド)

`references/loop-knowledge.md`(5要素・失敗モード・トークン経済)を読んだ上で、
`references/decision-matrix.md` に基づき1方式を推奨し、
採らなかった方式にも1行ずつ理由を付してユーザーに示す。

## Phase 4: ループ設計書の承認(メインスレッド)

`templates/loop-spec.md` の全マーカーを実値に置換して提示し、
AskUserQuestion で承認を得る。選択肢の説明には「承認すると何が起き、
どこまで自動で進むか」(点火直後の動き・止まる条件)を具体的に書く。
修正要求があれば反映し、方式ごと変える場合は
Phase 3 に戻る。**反復上限・予算・緊急停止の3点が空欄の設計書では点火しない。**

## Phase 5: 設置

方式に応じた部品を生成する(すべて差分提示→適用の順):

| 方式 | 設置物 |
|---|---|
| `/goal`・`/loop` | kill-switch(推奨)のみ。コマンドは Phase 6 で発行 |
| Ralph型 | `templates/ralph-prompt.md` → PROMPT.md、状態ファイル(PROGRESS.md /
  feature-list.json は harness-engineering の templates/progress/ と同型)、kill-switch(必須) |
| 外部スクリプト型 | `templates/external-loop.sh` → ループスクリプト、evaluator
  (harness-engineering の templates/agents/evaluator.md と同型)、状態ファイル、kill-switch(必須)(Windows では Git Bash で実行) |
| schedule型 | 実行プロンプトと登録内容の下書き、削除コマンドの控え |

- kill-switch の配線は `templates/monitoring.md` の JSON スニペットに従う
  (Windows は `.ps1` + `-NoProfile -ExecutionPolicy Bypass`)
- 並列なしでもループ用ブランチを切る(Q4 で並列ありなら worktree も作る)— ループの成果物を隔離し、完走後レビューを diff 可能にする(R3)
- 設置後 `grep -r '{{' <設置先>` でマーカー残りゼロを確認する

## Phase 6: 点火 + 監視引き渡し

承認済み設計書の通りに起動し、方式別の初回観察を行う:

| 方式 | 初回観察 |
|---|---|
| `/goal`・`/loop` | **必須**: 1反復目の完了まで観察し異常がないことを確認 |
| 外部スクリプト型 | **必須**: builder + evaluator 各1回の完了まで観察 |
| Ralph型 | **起動確認のみ**: ループ開始と状態ファイルへの初回書き込みを確認(完走は待たない) |
| schedule型 | **省略可**: 登録内容の確認のみ。初回実行後の確認手順を監視手順に含める |

- 1反復目でエラーが連発する場合は即停止(AGENT_STOP)し、原因と修正案を提示する。
  自動リトライしない
- 最後に `templates/monitoring.md` を実値化してユーザーに渡して終了する
  (進捗の見方・介入方法・停止方法・完走後レビュー)。冒頭に「点火後に何が
  どう動き、あなたは何を見ていればよいか」を体験ベースの1段落で添える
