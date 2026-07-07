# loop-engineering スキル実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** ゴールを検証可能な終了条件に変換し、最適なループ方式を選定・設計・設置・点火する汎用ループエンジニアリングスキルを skills-lab に構築する。

**Architecture:** `skills/loop-engineering/` 配下に SKILL.md(6フェーズ: ゴール検証可能化→実行可能性チェック→方式選定→設計書承認→設置→点火・監視引き渡し)+ references/(知見・方式マトリクス・R1〜R7チェック・質問バンク)+ templates/(設計書・Ralphプロンプト・外部ループスクリプト・kill-switch・監視手順)を作る。メインスレッド中心で、実行可能性調査のみExploreサブエージェントに軽量委譲。

**Tech Stack:** Markdown(スキル本体)、Bash + PowerShell(kill-switch・外部ループ)、Claude Code組み込み(/goal, /loop, schedule, Stopフック)。

**Spec:** `docs/superpowers/specs/2026-07-07-loop-engineering-skill-design.md`(判断に迷ったらこれが正)

## Global Constraints

- 置換マーカーは `{{MARKER}}` 形式で統一。SKILL.md は「マーカーを残したまま設置することを禁止」と明記する
- **R1(機械検証可能な終了条件)と R7(緊急停止手段)がFAILのままでは点火しない** — SKILL.md・readiness-check.md 両方に明記
- **反復上限・予算・緊急停止手段の3点が埋まっていない設計書では点火しない** — SKILL.md Phase 4 に明記
- `.sh` は `jq` 等の外部依存なしで動くこと
- kill-switch は `.sh`(POSIX)と `.ps1`(Windows)の両方を用意する
- SKILL.md frontmatter: `name: loop-engineering`、三人称・"Use when"開始・トリガー条件付き description(1024字以内)
- コミットメッセージ末尾に `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>` を付ける

## ファイル構造(最終形)

```
skills/loop-engineering/
├── SKILL.md                    # Task 7
├── references/
│   ├── loop-knowledge.md       # Task 1
│   ├── decision-matrix.md      # Task 2
│   ├── readiness-check.md      # Task 2
│   └── interview.md            # Task 3
└── templates/
    ├── loop-spec.md            # Task 4
    ├── monitoring.md           # Task 4
    ├── ralph-prompt.md         # Task 5
    ├── external-loop.sh        # Task 6
    ├── kill-switch.sh          # Task 6
    └── kill-switch.ps1         # Task 6
```

---

### Task 1: references/loop-knowledge.md(ループ設計の知見集)

**Files:**
- Create: `skills/loop-engineering/references/loop-knowledge.md`

**Interfaces:**
- Produces: Phase 3(方式選定)・Phase 4(設計書作成)の根拠知識。SKILL.md(Task 7)が `references/loop-knowledge.md` のパスで参照する

- [ ] **Step 1: loop-knowledge.md を作成(全文)**

````markdown
# ループエンジニアリング知見集

方式選定と設計書作成の根拠。Phase 3〜4 の前に必ず読む。

## 定義と位置づけ

ループエンジニアリング = 人が毎回プロンプトを打つ代わりに、
「行動 → 観察 → 検証 → 回復 → 再実行」を自動反復するシステムを設計する実践。
プロンプト → コンテキスト → ハーネス → ループ という積み重ねの最上層で、
ハーネス(環境・検証・権限)の上に成立する。ループはハーネスを置き換えない。

## ループの5要素(全てが揃わないループは設計不備)

1. **検証可能な終了条件を持つ目標** — コマンド1つで真偽判定できること
2. **環境と対話するツール** — テスト実行・ファイル操作・git
3. **コンテキスト管理** — 外部メモリ(状態ファイル)が「ループの脊椎」。
   各反復は git log + 進捗ファイルから状況を再構築する
4. **終了ロジック** — 成功条件 / 反復上限 / 無進捗検出(同一メトリクスがN反復不変)
5. **エラー分別** — 回復可能(次反復で再試行)と致命的(人間へエスカレーション)を区別

## 主要パターン

- **メーカー・チェッカー分離(最重要)**: 成功判定を実装エージェントの自己申告に
  させない。決定論的検証(コマンド)か、新規コンテキストの独立evaluatorを使う
- **Ralphループ**: Stopフックで終了を遮断し同一プロンプトを再投入。
  各反復は「単体では愚直」だが、ファイルとgit履歴の継承で全体として前進する。
  completion promise は正確な文字列一致のみ → **max-iterations が主安全装置**
- **計画・実行・検証ループ**: 順序依存の複数ステップに。各ステップ検証後に進行
- **人間参加ループ**: 曖昧さ・重要判断がある場合、承認ゲートで中断する縮退形

## トークン経済とレビュー帯域(設計書に必ず見積りを書く)

- ループの実コスト = 反復数 × 1反復トークン。無進捗の空回りが最大の浪費
- もう1つの上限は「人間がレビューできる diff 量」(オーケストレーション税)。
  1晩のループが生む差分をレビューする時間も予算である
- ループは責任を削除しない。理解債務が急速に蓄積するため、
  完走後のレビュー計画まで含めて1つのループ設計とする

## 失敗モードと対策

| 失敗モード | 対策 |
|---|---|
| 無限ループ | 反復上限 + 無進捗検出を必須化 |
| 同じ失敗の空回り | 試行ログ(何を試して何が失敗したか)を状態ファイルに構造化記録 |
| コンテキスト溢れ | 反復ごとに文脈リセット(Ralph/外部スクリプト)+外部メモリ |
| 自己申告成功 | 決定論的検証コマンド or 独立evaluatorゲート |
| ゴール誤指定 | Phase 1 の検証可能化で曖昧なゴールを拒否 |
| 暴走・危険操作 | kill-switch(AGENT_STOP)+ deny基盤 + サンドボックス推奨 |

## 出典

- https://tosea.ai/blog/loop-engineering-ai-agents-complete-guide-2026
- https://www.mindstudio.ai/blog/what-is-loop-engineering-ai-coding-agents
- https://www.bestblogs.dev/en/explore/topics/loop-engineering-guide
- https://ghuntley.com/ralph/
- https://github.com/anthropics/claude-code/tree/main/plugins/ralph-wiggum
- https://github.com/anthropics/cwc-long-running-agents
````

- [ ] **Step 2: 検証**

Run: `grep -c 'https://' skills/loop-engineering/references/loop-knowledge.md`
Expected: `6`

Run: `grep -c '^## ' skills/loop-engineering/references/loop-knowledge.md`
Expected: `6`(定義/5要素/パターン/トークン経済/失敗モード/出典)

- [ ] **Step 3: コミット**

```bash
git add skills/loop-engineering/references/loop-knowledge.md
git commit -m "feat: add loop engineering knowledge reference

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: references/decision-matrix.md と readiness-check.md

**Files:**
- Create: `skills/loop-engineering/references/decision-matrix.md`
- Create: `skills/loop-engineering/references/readiness-check.md`

**Interfaces:**
- Produces: Phase 2 の判定基準(R1〜R7、R1/R7=点火ブロッカー)と Phase 3 の選定基準。テンプレートファイル名(`templates/...`)は Task 4〜6 の実ファイルと一致させる

- [ ] **Step 1: decision-matrix.md を作成(全文)**

````markdown
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
````

- [ ] **Step 2: readiness-check.md を作成(全文)**

````markdown
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
````

- [ ] **Step 3: 検証**

Run: `grep -Eo '\| R[0-9] \|' skills/loop-engineering/references/readiness-check.md | sort -u | wc -l`
Expected: `7`

Run: `grep -c '点火不可' skills/loop-engineering/references/readiness-check.md`
Expected: `2`(R1とR7)

Run: `grep -o 'templates/[a-z.-]*' skills/loop-engineering/references/*.md | sort -u`
Expected: external-loop.sh / kill-switch(.sh/.ps1) / progress(R5がharness-engineering側のtemplates/progress/を指すため。loop-engineering自身のテンプレとしてはTask 6の実ファイルと一致)

- [ ] **Step 4: コミット**

```bash
git add skills/loop-engineering/references/decision-matrix.md skills/loop-engineering/references/readiness-check.md
git commit -m "feat: add loop decision matrix and R1-R7 readiness check

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 3: references/interview.md(質問バンク)

**Files:**
- Create: `skills/loop-engineering/references/interview.md`

**Interfaces:**
- Produces: Q1〜Q4。SKILL.md Phase 1 から参照される。Q2 の回答は loop-spec.md の必須欄(予算・反復上限)へ流れる

- [ ] **Step 1: interview.md を作成(全文)**

````markdown
# 質問バンク(Phase 1)

ゴールの検証可能化と同時に、以下4問を1回の AskUserQuestion で聞く。
**鉄則: リポジトリを見れば分かること(テストコマンド等)は聞かない。**

## Q1 無人時間帯と監視可否(常に聞く)

「このループはどの程度放置しますか?」
- 画面の前で見ている(数十分〜数時間)
- ときどき確認する(半日)
- 完全放置(夜間・終日)

→ 使い道: 方式選定(見ている→/goal、完全放置→Ralph/外部スクリプト/schedule)と
Phase 6 の観察要件。完全放置なら R4(deny基盤)・R7 を厳格化。

## Q2 予算と反復上限(常に聞く)

「トークン予算と反復上限の希望は?」
- 小(〜20反復 / 数時間相当)
- 中(〜50反復 / 一晩相当)
- 大(それ以上。要サンドボックス+レビュー計画)

→ 使い道: loop-spec.md の {{MAX_ITER}} と {{TOKEN_BUDGET}}。
「大」の場合はレビュー帯域(完走後にdiffを読む時間)の確認を追加で行う。

## Q3 失敗時のエスカレーション先(常に聞く)

「反復上限や無進捗で失敗終了したとき、どう知らせますか?」
- 課題ファイル(NEXT_FINDINGS.md)に書き残すだけでよい
- 通知が欲しい(通知手段があれば設定)

→ 使い道: loop-spec.md の {{ESCALATION}}。

## Q4 並列実行の要否(常に聞く)

「他の作業と並行しますか?」
- しない(現在のブランチ/リポジトリを占有してよい)
- する(worktree で隔離する)

→ 使い道: R3 の判定と設置時のworktree作成。

## 追加質問の裁量

ゴールの検証可能化(Phase 1 本体)で曖昧さが残る場合のみ、自由形式で追加質問してよい。
ただし「コマンドで判定できる終了条件」が確定するまで Phase 2 に進まないこと。
````

- [ ] **Step 2: 検証**

Run: `grep -c '^## Q' skills/loop-engineering/references/interview.md`
Expected: `4`

- [ ] **Step 3: コミット**

```bash
git add skills/loop-engineering/references/interview.md
git commit -m "feat: add loop interview question bank (Q1-Q4)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 4: templates/loop-spec.md と monitoring.md

**Files:**
- Create: `skills/loop-engineering/templates/loop-spec.md`
- Create: `skills/loop-engineering/templates/monitoring.md`

**Interfaces:**
- Produces: マーカー群 `{{GOAL_SUMMARY}}` `{{VERIFY_CMD}}` `{{EXPECTED}}` `{{MAX_ITER}}` `{{MAX_STALL}}` `{{PROGRESS_METRIC}}` `{{LOOP_TYPE}}` `{{REJECTED}}` `{{WHY}}` `{{TOKEN_BUDGET}}` `{{HOURS}}` `{{EVALUATOR}}` `{{ESCALATION}}` `{{FINDINGS_FILE}}` `{{KILL_SWITCH_PATH}}` `{{WATCH_CMD}}` `{{INTERVAL}}` `{{STEER_METHOD}}` `{{SCHEDULE_REMOVE_CMD}}` `{{REVIEW_CMD}}` `{{REVIEW_BUDGET}}`。SKILL.md Phase 4〜6 が使用

- [ ] **Step 1: loop-spec.md を作成(全文)**

````markdown
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

## 失敗時のエスカレーション

- {{ESCALATION}}。課題は {{FINDINGS_FILE}} に記録して終了する

## 緊急停止と監視

- 緊急停止: `{{KILL_SWITCH_PATH}}` を作成すると次のツール呼び出しで停止
- 監視: `{{WATCH_CMD}}` を {{INTERVAL}} ごとに確認(詳細は monitoring.md)
````

- [ ] **Step 2: monitoring.md を作成(全文)**

````markdown
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
````

- [ ] **Step 3: 検証**

Run: `grep -c '{{' skills/loop-engineering/templates/loop-spec.md`
Expected: 15行以上(マーカーが揃っている)

Run: `grep -c 'AGENT_STOP' skills/loop-engineering/templates/monitoring.md`
Expected: 4以上

- [ ] **Step 4: コミット**

```bash
git add skills/loop-engineering/templates/loop-spec.md skills/loop-engineering/templates/monitoring.md
git commit -m "feat: add loop-spec and monitoring templates

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 5: templates/ralph-prompt.md

**Files:**
- Create: `skills/loop-engineering/templates/ralph-prompt.md`

**Interfaces:**
- Consumes: `{{GOAL_SUMMARY}}` `{{VERIFY_CMD}}` `{{MAX_STALL}}` `{{FINDINGS_FILE}}`(Task 4 と同一マーカー)。新規: `{{PROMISE}}` `{{PHASE_LIST}}`
- Produces: Ralph型で使う PROMPT.md 雛形

- [ ] **Step 1: ralph-prompt.md を作成(全文)**

````markdown
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
````

- [ ] **Step 2: 検証**

Run: `grep -c 'promise' skills/loop-engineering/templates/ralph-prompt.md`
Expected: 3以上(promiseの扱いが明記されている)

Run: `grep -c '禁止' skills/loop-engineering/templates/ralph-prompt.md`
Expected: 1以上

- [ ] **Step 3: コミット**

```bash
git add skills/loop-engineering/templates/ralph-prompt.md
git commit -m "feat: add Ralph loop prompt template

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 6: templates/external-loop.sh と kill-switch.sh / .ps1

**Files:**
- Create: `skills/loop-engineering/templates/external-loop.sh`
- Create: `skills/loop-engineering/templates/kill-switch.sh`
- Create: `skills/loop-engineering/templates/kill-switch.ps1`

**Interfaces:**
- Consumes: `{{MAX_ITER}}` `{{MAX_STALL}}` `{{VERIFY_CMD}}`(Task 4 と同一)。新規: `{{REPO_DIR}}` `{{BUILDER_PROMPT}}` `{{PROGRESS_CMD}}`
- Produces: 外部スクリプト型ループ本体と、全方式共通の緊急停止フック

- [ ] **Step 1: external-loop.sh を作成(全文)**

```bash
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
```

- [ ] **Step 2: kill-switch.sh を作成(全文)**

```bash
#!/usr/bin/env bash
# PreToolUse(全ツール): AGENT_STOP ファイルが存在したら全ツール呼び出しをブロック(緊急停止)
# 配線は templates/monitoring.md 参照。解除は AGENT_STOP を削除する
set -u
if [ -f "AGENT_STOP" ]; then
  echo "EMERGENCY STOP: AGENT_STOP file present. Stop all work now and end the session." >&2
  exit 2
fi
exit 0
```

- [ ] **Step 3: kill-switch.ps1 を作成(全文)**

```powershell
# PreToolUse(全ツール): AGENT_STOP ファイルが存在したら全ツール呼び出しをブロック(緊急停止)
# 配線は templates/monitoring.md 参照。解除は AGENT_STOP を削除する
if (Test-Path "AGENT_STOP") {
    [Console]::Error.WriteLine("EMERGENCY STOP: AGENT_STOP file present. Stop all work now and end the session.")
    exit 2
}
exit 0
```

- [ ] **Step 4: 構文検証**

Run: `bash -n skills/loop-engineering/templates/external-loop.sh && bash -n skills/loop-engineering/templates/kill-switch.sh && echo SH-OK`
Expected: `SH-OK`(`{{MARKER}}` は literal word として構文上有効)

Run (PowerShell): `$errs = $null; [System.Management.Automation.PSParser]::Tokenize((Get-Content skills/loop-engineering/templates/kill-switch.ps1 -Raw), [ref]$errs) | Out-Null; if ($errs.Count -eq 0) { Write-Output "PS-OK" } else { Write-Output "PS-FAIL" }`
Expected: `PS-OK`

- [ ] **Step 5: コミット**

```bash
git add skills/loop-engineering/templates/external-loop.sh skills/loop-engineering/templates/kill-switch.sh skills/loop-engineering/templates/kill-switch.ps1
git commit -m "feat: add external loop script and kill-switch hooks

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 7: SKILL.md(オーケストレーション本体)

**Files:**
- Create: `skills/loop-engineering/SKILL.md`

**Interfaces:**
- Consumes: references/ 4ファイル、templates/ 6ファイル(Task 1〜6 の全成果物。パス・マーカー名は各タスクの定義と一致させること)
- Produces: スキルのエントリポイント

- [ ] **Step 1: SKILL.md を作成(全文)**

````markdown
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
AskUserQuestion で承認を得る。修正要求があれば反映し、方式ごと変える場合は
Phase 3 に戻る。**反復上限・予算・緊急停止の3点が空欄の設計書では点火しない。**

## Phase 5: 設置

方式に応じた部品を生成する(すべて差分提示→適用の順):

| 方式 | 設置物 |
|---|---|
| `/goal`・`/loop` | kill-switch(推奨)のみ。コマンドは Phase 6 で発行 |
| Ralph型 | `templates/ralph-prompt.md` → PROMPT.md、状態ファイル(PROGRESS.md /
  feature-list.json は harness-engineering の templates/progress/ と同型)、kill-switch(必須) |
| 外部スクリプト型 | `templates/external-loop.sh` → ループスクリプト、evaluator
  (harness-engineering の templates/agents/evaluator.md と同型)、状態ファイル、kill-switch(必須) |
| schedule型 | 実行プロンプトと登録内容の下書き、削除コマンドの控え |

- kill-switch の配線は `templates/monitoring.md` の JSON スニペットに従う
  (Windows は `.ps1` + `-NoProfile -ExecutionPolicy Bypass`)
- Q4 で並列ありなら、ループ用ブランチ/worktree を先に作る
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
  (進捗の見方・介入方法・停止方法・完走後レビュー)
````

- [ ] **Step 2: 検証**

Run: `head -4 skills/loop-engineering/SKILL.md`
Expected: frontmatter に `name: loop-engineering`、description が "Use when" で始まる

Run: `grep -c '^## Phase' skills/loop-engineering/SKILL.md`
Expected: `6`

Run: `grep -o 'references/[a-z-]*\.md\|templates/[a-z.-]*' skills/loop-engineering/SKILL.md | sort -u` → 出力された全パスが `ls skills/loop-engineering/...` で実在することを確認

Run: `grep -c '点火しない' skills/loop-engineering/SKILL.md`
Expected: 2以上(原則とPhase 4)

- [ ] **Step 3: コミット**

```bash
git add skills/loop-engineering/SKILL.md
git commit -m "feat: add loop-engineering SKILL.md orchestrating 6 phases

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 8: 手動E2E検証(ユーザー参加)

**Files:**
- なし(既存の fixtures/sample-ts と fixtures/sample-py を再利用)

**Interfaces:**
- Consumes: 完成したスキル一式 + 既存フィクスチャ

- [ ] **Step 1: 手動E2E検証(ユーザーと実施)**

スキルを `~/.claude/skills/loop-engineering/` にコピーし、以下の3シナリオを実施:

シナリオ1 — /goal完走(fixtures/sample-ts を git 管理外へコピーして使用):
- [ ] ゴール「add に subtract/multiply/divide を追加し全テスト緑」で起動
- [ ] Phase 1 で終了条件が `npm test` ベースに検証可能化される
- [ ] Phase 3 で /goal が推奨される(短時間・条件明確のため)
- [ ] 設計書に反復上限・予算・停止手段が埋まってから点火される
- [ ] 完走後に monitoring.md 相当の引き渡しがある

シナリオ2 — R2縮退(fixtures/sample-py を git 管理外へコピーして使用):
- [ ] テスト無しのため R2 FAIL となり、harness-engineering 提案 or リンタ縮退が提示される

シナリオ3 — 点火拒否:
- [ ] 「コードを良い感じにして」という曖昧ゴールで、検証可能化不能→点火拒否+
      人間参加型ループへの縮退提案が出る

結果を記録し、問題があれば SKILL.md / references / templates を修正して再検証する。

- [ ] **Step 2: 検証結果の反映をコミット**

```bash
git add -A
git commit -m "fix: adjust loop-engineering skill based on manual E2E findings

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

(修正が無ければこのステップはスキップ)
