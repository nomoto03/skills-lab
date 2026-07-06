# harness-engineering スキル実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** リポジトリを調査→質問→診断→提案→実装→検証→バックログ提案する汎用ハーネスエンジニアリングスキルを skills-lab に構築する。

**Architecture:** `skills/harness-engineering/` 配下に SKILL.md(7フェーズのオーケストレーション)+ references/(知見・ルーブリック・質問バンク)+ templates/(CLAUDE.md雛形・permissions・hooks・進捗管理・evaluator)を作る。調査と設計はサブエージェントに委譲し、対話と実装はメインスレッドで行う設計。

**Tech Stack:** Markdown(スキル本体)、Bash + PowerShell(hooksテンプレート)、JSON(permissions・機能リスト)。

**Spec:** `docs/superpowers/specs/2026-07-07-harness-engineering-skill-design.md`(判断に迷ったらこれが正)

## Global Constraints

- スキルが生成する CLAUDE.md は **50行以下**
- テンプレート内の置換マーカーは `{{MARKER}}` 形式で統一。SKILL.md は「マーカーを残したまま設置することを禁止」と明記する
- スキル実行時の中間ファイル(harness-survey.md / harness-proposal.md)はセッションのスクラッチパッドに置く(対象リポジトリを汚さない)
- hooks テンプレートは `.sh`(POSIX)と `.ps1`(Windows)の両方を用意する
- `.sh` は `jq` 等の外部依存なし(sed/grep のみ)で動くこと
- SKILL.md の frontmatter は `name: harness-engineering` と、三人称・トリガー条件付きの `description`(1024字以内)を持つこと
- コミットメッセージ末尾に `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>` を付ける

## ファイル構造(最終形)

```
skills-lab/
├── docs/superpowers/
│   ├── specs/2026-07-07-harness-engineering-skill-design.md   (既存)
│   └── plans/2026-07-07-harness-engineering-skill.md          (この文書)
└── skills/harness-engineering/
    ├── SKILL.md                        # Task 8
    ├── references/
    │   ├── knowledge.md                # Task 2
    │   ├── rubric.md                   # Task 3
    │   └── interview.md                # Task 4
    └── templates/
        ├── claude-md-skeleton.md       # Task 5
        ├── settings-permissions.json   # Task 5
        ├── hooks/
        │   ├── wiring.md               # Task 6
        │   ├── post-edit-lint.sh       # Task 6
        │   ├── post-edit-lint.ps1      # Task 6
        │   ├── protect-config.sh       # Task 6
        │   ├── protect-config.ps1      # Task 6
        │   ├── commit-on-stop.sh       # Task 6
        │   └── commit-on-stop.ps1      # Task 6
        ├── progress/
        │   ├── PROGRESS.md             # Task 7
        │   └── feature-list.json       # Task 7
        └── agents/
            └── evaluator.md            # Task 7
```

---

### Task 1: git初期化とスペックのコミット

**Files:**
- Create: `.gitignore`
- Commit: `docs/superpowers/specs/2026-07-07-harness-engineering-skill-design.md`, `docs/superpowers/plans/2026-07-07-harness-engineering-skill.md`

**Interfaces:**
- Produces: git管理されたskills-labリポジトリ(以降の全タスクがコミット可能になる)

- [ ] **Step 1: git初期化の確認と実行**

Run: `git -C "C:/Users/nomok/Documents/GitHub/skills-lab" rev-parse --is-inside-work-tree` → エラー(not a git repository)を確認してから:

```bash
git init
```

Expected: `Initialized empty Git repository`

- [ ] **Step 2: .gitignore 作成**

`.gitignore` の内容(全文):

```
*.tmp
.DS_Store
Thumbs.db
```

- [ ] **Step 3: 初回コミット**

```bash
git add .gitignore docs/
git commit -m "chore: init skills-lab with harness-engineering spec and plan

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

Run: `git log --oneline` / Expected: 1コミット存在

---

### Task 2: references/knowledge.md(ハーネス設計の知見集)

**Files:**
- Create: `skills/harness-engineering/references/knowledge.md`

**Interfaces:**
- Produces: Phase 3 で architect サブエージェントに読ませる知見集。SKILL.md(Task 8)が `references/knowledge.md` のパスで参照する

- [ ] **Step 1: knowledge.md を作成(全文)**

````markdown
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
````

- [ ] **Step 2: 検証**

Run: `wc -l skills/harness-engineering/references/knowledge.md`
Expected: 80行前後(±20行は許容)。出典URLが6件あること: `grep -c 'https://' skills/harness-engineering/references/knowledge.md` → 6

- [ ] **Step 3: コミット**

```bash
git add skills/harness-engineering/references/knowledge.md
git commit -m "feat: add harness engineering knowledge reference

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 3: references/rubric.md(診断ルーブリック)

**Files:**
- Create: `skills/harness-engineering/references/rubric.md`

**Interfaces:**
- Consumes: FAIL時の提案候補列が Task 5-7 のテンプレートファイル名を指す(`templates/...`)
- Produces: Phase 3 の判定基準。項目ID(A1〜D5)は harness-proposal.md 内で参照される

- [ ] **Step 1: rubric.md を作成(全文)**

````markdown
# 診断ルーブリック

Phase 3 で全項目を判定する。判定は **現状OK / 要改善 / 対象外** の3値。
「対象外」には理由を必ず書く(例: 用途がバグ修正中心のためD領域は対象外)。

## A. コンテキスト整備

| ID | 項目 | PASS基準 | FAIL時の提案候補 |
|---|---|---|---|
| A1 | CLAUDE.mdの存在と規模 | 存在し50行以下 | `templates/claude-md-skeleton.md` から新規作成、または縮小差分案 |
| A2 | 実コマンドの記載 | ビルド/テスト/リンタのコマンドが正確に書かれ、実際に動く | Phase 1 で確認済みコマンドを記載 |
| A3 | ポインタ形式 | 長文説明がなく、詳細はdocs/ADR等へのポインタ | 長文をADRへ移しポインタ化 |
| A4 | 鮮度 | 記載内容が現状のリポジトリと一致 | 腐った行の削除(削除テスト適用) |
| A5 | 反復作業のスキル化 | 定型作業(リリース手順等)がプロジェクトskillsにある(該当時のみ) | スキル化候補の提示のみ(実装はPhase 7) |

## B. 品質フィードバックループ

| ID | 項目 | PASS基準 | FAIL時の提案候補 |
|---|---|---|---|
| B1 | 高速リンタ | 1〜2秒以内に完了するリンタがある | 高速リンタ移行は Phase 7 バックログへ |
| B2 | 編集時自動検査 | PostToolUseフックでリンタ/型チェックが自動実行 | `templates/hooks/post-edit-lint.*` |
| B3 | 完了の強制 | テスト合格がフック/CIで強制(プロンプト依存でない) | Stopフック(汎用テンプレなし・対象リポジトリごとに書き起こす) or CI(Phase 7) |
| B4 | ハーネス設定の保護 | リンタ設定・フック定義をエージェントが改変できない | `templates/hooks/protect-config.*` |
| B5 | テスト実行速度 | テストスイートが数分以内に完了 | 分割/高速化は Phase 7 バックログへ |

注意: B2 は B1 が PASS であることが前提(遅いリンタのフック化は逆効果)。

## C. 権限・安全性

| ID | 項目 | PASS基準 | FAIL時の提案候補 |
|---|---|---|---|
| C1 | deny基盤 | 破壊的コマンド(rm -rf, sudo, force push)とシークレット(.env, 鍵)がdeny済み | `templates/settings-permissions.json` |
| C2 | 自律度との整合 | permissions がユーザーの望む自律度(Q2回答)と一致 | ask/allow の調整 |
| C3 | 設定の共有 | チーム共有なら .claude/settings.json がgit管理 | git追加の提案 |
| C4 | サンドボックス | 完全自動運転はコンテナ/sandbox内のみ | 推奨として提示のみ(Environment層はスコープ外) |

## D. 長時間実行・状態管理

| ID | 項目 | PASS基準 | FAIL時の提案候補 |
|---|---|---|---|
| D1 | git管理 | リポジトリがgit管理下にある | git init を最優先で提案(全ハーネスの前提) |
| D2 | 状態引き継ぎ | PROGRESS.md等 + git履歴で新セッションが状況を再構築できる | `templates/progress/PROGRESS.md` |
| D3 | default-FAIL | 機能リストが `"passes": false` 初期値で管理されている | `templates/progress/feature-list.json` |
| D4 | 自己評価の分離 | 成功判定が独立evaluator/テストにある | `templates/agents/evaluator.md` |
| D5 | 起動ルーチン | セッション開始時に読むべきものがCLAUDE.mdに明記 | CLAUDE.mdへ起動手順追記 |

## 適用条件

- **D2〜D5** は用途(Q1)に「長時間自律実行」が含まれる場合のみ診断する。
  それ以外は D1 のみ診断し、D2〜D5 は「対象外(用途に含まれない)」とする。
- **D1(git管理)だけは常に診断する。** FAILなら他の全提案より優先。
````

- [ ] **Step 2: 検証**

Run: `grep -Eo '\| [A-D][0-9] \|' skills/harness-engineering/references/rubric.md | sort -u | wc -l`
Expected: `19`(A1-A5, B1-B5, C1-C4, D1-D5)

Run: `grep -o 'templates/[a-z/-]*' skills/harness-engineering/references/rubric.md | sort -u`
Expected: 後続タスクで作る実ファイル群と一致(claude-md-skeleton / settings-permissions / hooks/post-edit-lint / hooks/protect-config / progress/ / agents/evaluator)

- [ ] **Step 3: コミット**

```bash
git add skills/harness-engineering/references/rubric.md
git commit -m "feat: add diagnostic rubric (19 items across 4 areas)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 4: references/interview.md(質問バンク)

**Files:**
- Create: `skills/harness-engineering/references/interview.md`

**Interfaces:**
- Produces: Q1〜Q6 の質問定義。Q番号は rubric.md(C2がQ2を参照)と SKILL.md Phase 2 から参照される

- [ ] **Step 1: interview.md を作成(全文)**

````markdown
# 質問バンク

Phase 2 でメインスレッドが AskUserQuestion で使う。4〜6問。
**鉄則: harness-survey.md で判明していることは絶対に聞かない。**

## Q1 用途(常に聞く / multiSelect)

「このリポジトリでエージェントに主に任せたい作業は?」
- バグ修正・小さな変更
- 機能開発
- リファクタリング・保守
- 長時間の自律実行(夜間バッチ的な開発など)

→ 使い道: D領域(D2〜D5)を診断対象に含めるか、提案の重心を決める。

## Q2 自律度(常に聞く)

「どこまで自動で動かしたいですか?」
- 全操作を承認したい(承認優先)
- 安全な操作は自動、危険な操作のみ確認(許可リスト)
- サンドボックス内で完全自動

→ 使い道: settings-permissions.json の ask/allow の広さと C2 の判定基準。
「完全自動」の場合はサンドボックス環境の有無を追加で確認し、
無ければ許可リスト運用を推奨する(C4)。

## Q3 痛みポイント(常に聞く / multiSelect)

「エージェント利用で現状いちばん困っていることは?」
- 同じ指示を毎回繰り返している → A領域を優先
- 「できた」と言うのに動かない/検証が甘い → B3・D4 を優先
- 危険な操作をしないか不安 → C領域を優先
- 長い作業の途中で文脈を失う → D領域を優先

→ 使い道: 提案の優先度付けの重み。

## Q4 共有範囲(常に聞く)

「この設定は個人用ですか、チームでgit共有しますか?」
- 個人用 → .claude/settings.local.json に設置
- チーム共有 → .claude/settings.json に設置し git 管理(C3)

## Q5 テスト投資(テストが無い/壊れている場合のみ)

「品質フィードバックループの前提となるテスト整備から始める意思はありますか?」
- ある → Phase 7 バックログの筆頭に「最初の1本」の具体案を書く
- 今はない → B3 の提案を縮退(リンタのみ)し、理由を提案書に明記

## Q6 既存設定の扱い(既存 .claude/ や CLAUDE.md がある場合のみ)

「既存のハーネス設定があります。どう扱いますか?」
- 尊重して差分提案のみ(推奨)
- 作り直してよい

→ 「尊重」の場合、既存ファイルの変更は必ず差分提示→承認の手順を踏む。

## 選択ルール

- Q1〜Q4 は常に出す(1回の AskUserQuestion にまとめる。最大4問制限に一致)
- Q5・Q6 は該当条件を満たす場合のみ、2回目の AskUserQuestion で出す
````

- [ ] **Step 2: 検証**

Run: `grep -c '^## Q' skills/harness-engineering/references/interview.md`
Expected: `6`

- [ ] **Step 3: コミット**

```bash
git add skills/harness-engineering/references/interview.md
git commit -m "feat: add interview question bank (Q1-Q6 with selection rules)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 5: templates/claude-md-skeleton.md と settings-permissions.json

**Files:**
- Create: `skills/harness-engineering/templates/claude-md-skeleton.md`
- Create: `skills/harness-engineering/templates/settings-permissions.json`

**Interfaces:**
- Produces: `{{PROJECT_NAME}}` `{{BUILD_CMD}}` `{{TEST_CMD}}` `{{LINT_CMD}}` `{{TYPECHECK_CMD}}` `{{SRC_DIR}}` `{{TEST_DIR}}` `{{PKG_INSTALL_CMD}}` `{{BRANCH_CONVENTION}}` `{{NAMING_CONVENTION}}` `{{ADR_PATH}}` の置換マーカー群。SKILL.md Phase 5 が置換ルールを規定する

- [ ] **Step 1: claude-md-skeleton.md を作成(全文)**

````markdown
<!-- テンプレート: 設置時に全 {{MARKER}} を実値へ置換し、このコメントと不要セクションを削除。50行以下厳守 -->
# {{PROJECT_NAME}}

## コマンド

- ビルド: `{{BUILD_CMD}}`
- テスト: `{{TEST_CMD}}`
- リンタ: `{{LINT_CMD}}`
- 型チェック: `{{TYPECHECK_CMD}}`

## 構成

- ソース: `{{SRC_DIR}}`
- テスト: `{{TEST_DIR}}`

## 規約

- ブランチ: `{{BRANCH_CONVENTION}}`
- {{NAMING_CONVENTION}}

## セッション開始時(長時間実行構成の場合のみ残す)

1. `git log --oneline -10` と `PROGRESS.md` を読む
2. `feature-list.json` から `"passes": false` の機能を1つ選ぶ

## 詳細ポインタ

- 設計判断: `{{ADR_PATH}}`
````

- [ ] **Step 2: settings-permissions.json を作成(全文)**

```json
{
  "_comment": "テンプレート: {{MARKER}} を実コマンドに置換。自律度(Q2)が「承認優先」なら allow を空に、「許可リスト」ならこのまま。設置先は共有なら .claude/settings.json、個人なら .claude/settings.local.json。設置時は `_comment` と `_limitations` キーを削除する(内容はユーザーへの説明に使ってから消す。不明キーが設定エラーになり得るため)",
  "_limitations": [
    "Bashルールはプレフィックス一致(prefix:*)。連結コマンド(cmd; 別コマンド)が allow を素通りし得るため、allow は利便性の層と割り切り、危険操作の防止は deny + hooks(protect-config)+ Environment層で行う(3層責任分離)",
    "deny は文字列一致であり表記ゆれ(rm -fr, rm -r -f 等)で回避され得る。文字列denyで網羅を目指さず、最終防御線はサンドボックス/コンテナに置く",
    "シークレットは Read ルールだけでは守れない(Bash 経由の cat .env 等)。機密を扱うリポジトリでは環境分離を優先する"
  ],
  "permissions": {
    "deny": [
      "Bash(rm -rf:*)",
      "Bash(rm -fr:*)",
      "Bash(sudo:*)",
      "Bash(git push --force:*)",
      "Bash(git push -f:*)",
      "Bash(git reset --hard:*)",
      "Read(./.env)",
      "Read(./.env.*)",
      "Read(**/*.pem)",
      "Read(**/id_rsa*)",
      "Read(**/credentials*)"
    ],
    "ask": [
      "Bash(git push:*)",
      "Bash({{PKG_INSTALL_CMD}}:*)"
    ],
    "allow": [
      "Bash({{TEST_CMD}}:*)",
      "Bash({{LINT_CMD}}:*)",
      "Bash({{BUILD_CMD}}:*)",
      "Bash(git status)",
      "Bash(git diff:*)",
      "Bash(git log:*)",
      "Bash(git add:*)",
      "Bash(git commit:*)"
    ]
  }
}
```

- [ ] **Step 3: 検証**

Run: `wc -l skills/harness-engineering/templates/claude-md-skeleton.md` → 30行前後(50行以下必須)

Run (PowerShell): `Get-Content skills/harness-engineering/templates/settings-permissions.json -Raw -Encoding UTF8 | ConvertFrom-Json | Out-Null; echo OK`
Expected: `OK`(JSONとして妥当。`{{MARKER}}` は文字列内なのでパース可能。`-Encoding UTF8` 必須 — PS5.1は既定でCP932読みし日本語で偽エラーになる)

- [ ] **Step 4: コミット**

```bash
git add skills/harness-engineering/templates/claude-md-skeleton.md skills/harness-engineering/templates/settings-permissions.json
git commit -m "feat: add CLAUDE.md skeleton and permissions template

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 6: templates/hooks/(sh + ps1 + 配線ガイド)

**Files:**
- Create: `skills/harness-engineering/templates/hooks/post-edit-lint.sh`
- Create: `skills/harness-engineering/templates/hooks/post-edit-lint.ps1`
- Create: `skills/harness-engineering/templates/hooks/protect-config.sh`
- Create: `skills/harness-engineering/templates/hooks/protect-config.ps1`
- Create: `skills/harness-engineering/templates/hooks/commit-on-stop.sh`
- Create: `skills/harness-engineering/templates/hooks/commit-on-stop.ps1`
- Create: `skills/harness-engineering/templates/hooks/wiring.md`

**Interfaces:**
- Consumes: `{{LINT_CMD}}` `{{EXT}}` `{{LINT_CONFIG}}` マーカー(Task 5 と同じ規則)
- Produces: `.claude/hooks/` に設置されるスクリプト群と、settings.json への配線スニペット(wiring.md)

- [ ] **Step 1: post-edit-lint.sh を作成(全文)**

```bash
#!/usr/bin/env bash
# PostToolUse (Write|Edit): 編集されたファイルにリンタを実行し、違反をエージェントに差し戻す
# 設置時の置換: {{LINT_CMD}} = リンタコマンド(例: npx oxlint)、{{EXT}} = 対象拡張子(例: ts)
set -u
INPUT=$(cat)
FILE=$(printf '%s' "$INPUT" | sed -n 's/.*"file_path"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
[ -z "$FILE" ] && exit 0
case "$FILE" in
  *.{{EXT}}) ;;
  *) exit 0 ;;
esac
if ! OUTPUT=$({{LINT_CMD}} "$FILE" 2>&1); then
  echo "Lint failed for $FILE — fix these before proceeding:" >&2
  echo "$OUTPUT" >&2
  exit 2
fi
exit 0
```

- [ ] **Step 2: post-edit-lint.ps1 を作成(全文)**

```powershell
# PostToolUse (Write|Edit): 編集されたファイルにリンタを実行し、違反をエージェントに差し戻す
# 設置時の置換: {{LINT_CMD}} = リンタコマンド、{{EXT}} = 対象拡張子(例: ts)
$json = [Console]::In.ReadToEnd() | ConvertFrom-Json
$file = $json.tool_input.file_path
if (-not $file) { exit 0 }
if ($file -notmatch '\.{{EXT}}$') { exit 0 }
$output = & {{LINT_CMD}} $file 2>&1
if ($LASTEXITCODE -ne 0) {
    [Console]::Error.WriteLine("Lint failed for $file — fix these before proceeding:")
    [Console]::Error.WriteLine(($output | Out-String))
    exit 2
}
exit 0
```

- [ ] **Step 3: protect-config.sh を作成(全文)**

```bash
#!/usr/bin/env bash
# PreToolUse (Write|Edit): ハーネス設定・シークレットの改変をブロック
# 設置時の置換: {{LINT_CONFIG}} = リンタ設定ファイル名の正規表現(例: \.oxlintrc\.json)
set -u
INPUT=$(cat)
FILE=$(printf '%s' "$INPUT" | sed -n 's/.*"file_path"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
[ -z "$FILE" ] && exit 0
PROTECTED='(\.env($|\.)|\.claude/settings.*\.json|\.claude/hooks/|{{LINT_CONFIG}})'
if printf '%s' "$FILE" | grep -Eq "$PROTECTED"; then
  echo "BLOCKED: $FILE is protected harness configuration. Ask the user to change it manually." >&2
  exit 2
fi
exit 0
```

- [ ] **Step 4: protect-config.ps1 を作成(全文)**

```powershell
# PreToolUse (Write|Edit): ハーネス設定・シークレットの改変をブロック
# 設置時の置換: {{LINT_CONFIG}} = リンタ設定ファイル名の正規表現(例: \.oxlintrc\.json)
$json = [Console]::In.ReadToEnd() | ConvertFrom-Json
$file = $json.tool_input.file_path
if (-not $file) { exit 0 }
$protected = '(\.env($|\.)|\.claude[/\\]settings.*\.json|\.claude[/\\]hooks[/\\]|{{LINT_CONFIG}})'
if ($file -match $protected) {
    [Console]::Error.WriteLine("BLOCKED: $file is protected harness configuration. Ask the user to change it manually.")
    exit 2
}
exit 0
```

- [ ] **Step 5: commit-on-stop.sh を作成(全文)**

```bash
#!/usr/bin/env bash
# Stop: セッション終了時、未コミット変更があれば自動チェックポイントコミット(セッション間ハンドオフ用)
set -u
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 0
if ! git diff --quiet || ! git diff --cached --quiet || [ -n "$(git ls-files --others --exclude-standard)" ]; then
  git add -A
  git commit -m "wip: session checkpoint (auto-commit by Stop hook)" >/dev/null
fi
exit 0
```

- [ ] **Step 6: commit-on-stop.ps1 を作成(全文)**

```powershell
# Stop: セッション終了時、未コミット変更があれば自動チェックポイントコミット(セッション間ハンドオフ用)
git rev-parse --is-inside-work-tree 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) { exit 0 }
$dirty = (git status --porcelain)
if ($dirty) {
    git add -A
    git commit -m "wip: session checkpoint (auto-commit by Stop hook)" | Out-Null
}
exit 0
```

- [ ] **Step 7: wiring.md を作成(全文)**

````markdown
# hooks 配線ガイド

スクリプトを対象リポジトリの `.claude/hooks/` にコピーし、マーカーを置換した上で、
settings.json の `hooks` キーに以下を追記する(POSIX例。Windowsは
`bash <script>.sh` を `powershell -NoProfile -ExecutionPolicy Bypass -File <script>.ps1` に読み替える。
既定の Restricted ポリシーでは `-File` が黙って実行拒否され hooks が無効化されるため)。

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
- [ ] protect-config は Write|Edit のみを監視するため、Bash 経由の書き込み(`echo ... > .claude/settings.json` 等)は防げない — Bash 側は permissions.deny と Environment 層で守る
````

- [ ] **Step 8: 構文検証**

Run: `bash -n skills/harness-engineering/templates/hooks/post-edit-lint.sh && bash -n skills/harness-engineering/templates/hooks/protect-config.sh && bash -n skills/harness-engineering/templates/hooks/commit-on-stop.sh && echo SH-OK`
Expected: `SH-OK`

Run (PowerShell): `$errs = $null; foreach ($f in (Get-ChildItem skills/harness-engineering/templates/hooks/*.ps1)) { [System.Management.Automation.PSParser]::Tokenize((Get-Content $f -Raw), [ref]$errs) | Out-Null; if ($errs.Count -gt 0) { Write-Output "FAIL: $f" } }; Write-Output "PS-CHECKED"`
Expected: `PS-CHECKED`(FAIL行なし)

- [ ] **Step 9: コミット**

```bash
git add skills/harness-engineering/templates/hooks/
git commit -m "feat: add hook templates (sh/ps1) with wiring guide

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 7: templates/progress/ と templates/agents/evaluator.md

**Files:**
- Create: `skills/harness-engineering/templates/progress/PROGRESS.md`
- Create: `skills/harness-engineering/templates/progress/feature-list.json`
- Create: `skills/harness-engineering/templates/agents/evaluator.md`

**Interfaces:**
- Produces: 長時間実行構成(rubric D2〜D4 のFAIL時)で設置されるファイル群

- [ ] **Step 1: PROGRESS.md を作成(全文)**

````markdown
# PROGRESS

<!-- テンプレート: 対象リポジトリのルートに設置。エージェントがセッションごとに更新する -->

## 現在の状態

(1〜3行: 何がどこまで動くか。新セッションがこれだけ読めば再開できる粒度で)

## 次にやること

(優先順。1項目 = 1セッションで終わる粒度)

1.

## セッションログ(新しい順)

### YYYY-MM-DD セッションN

- やったこと:
- テスト結果(コマンドと結果を貼る):
- ハマった点・次セッションへの注意:
````

- [ ] **Step 2: feature-list.json を作成(全文)**

```json
{
  "_comment": "default-FAIL契約: 全機能を passes:false で登録し、検証の証拠なしに true へ変えてはならない",
  "features": [
    {
      "id": "F001",
      "description": "(機能の説明。何をもって動作確認とするかも書く)",
      "verification": "(検証方法。例: npm test -- feature.spec.ts が通る)",
      "passes": false,
      "evidence": null
    }
  ]
}
```

- [ ] **Step 3: evaluator.md を作成(全文)**

````markdown
---
name: evaluator
description: 実装とは独立に、直近の変更が要件を満たすかを懐疑的に検証する読み取り専用の評価エージェント。実装者の自己申告を信用せず、テスト実行と成果物の確認のみで判定する。
tools: Read, Grep, Glob, Bash
---

あなたは独立した評価者です。実装者の主張・報告文を根拠にしてはいけません。
証拠(コマンド出力・ファイル内容)のみで判定します。

## 手順

1. `git log -1 -p` で直近の変更を読み、対象機能の要件(feature-list.json の該当項目)を確認する
2. verification に書かれた検証コマンドを実際に実行し、出力を確認する
3. 要件の各観点について、証拠を挙げて判定する

## 出力形式(1行目は必ず判定のみ)

```
PASS または NEEDS_WORK
- 観点1: 判定(証拠: 実行したコマンドと結果)
- 観点2: 判定(証拠: ...)
```

NEEDS_WORK の場合は、修正すべき点を具体的なファイル・行とともに列挙する。

## 禁止事項

- ファイルの作成・編集・削除(Bashは検証コマンドの実行のみに使う)
- 「実装者がそう言っているから」を根拠にすること
- 検証コマンドが実行できなかった項目を PASS にすること(必ず NEEDS_WORK)
````

- [ ] **Step 4: 検証**

Run (PowerShell): `Get-Content skills/harness-engineering/templates/progress/feature-list.json -Raw -Encoding UTF8 | ConvertFrom-Json | Out-Null; echo OK`
Expected: `OK`(`-Encoding UTF8` 必須 — PS5.1の既定読みは日本語で偽エラーになる)

Run: `head -5 skills/harness-engineering/templates/agents/evaluator.md`
Expected: frontmatter に `name: evaluator` と `tools: Read, Grep, Glob, Bash` がある

- [ ] **Step 5: コミット**

```bash
git add skills/harness-engineering/templates/progress/ skills/harness-engineering/templates/agents/
git commit -m "feat: add progress tracking and evaluator agent templates

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 8: SKILL.md(オーケストレーション本体)

**Files:**
- Create: `skills/harness-engineering/SKILL.md`

**Interfaces:**
- Consumes: `references/knowledge.md`, `references/rubric.md`, `references/interview.md`, `templates/`(Task 2〜7 の全成果物。パス・マーカー名は各タスクの定義と一致させること)
- Produces: スキルのエントリポイント

- [ ] **Step 1: SKILL.md を作成(全文)**

````markdown
---
name: harness-engineering
description: Use when the user wants to make a repository agent-ready or set up/improve its agent harness — triggers include "ハーネスを整備/設計して", "エージェントが働きやすい環境にして", "make this repo agent-ready", "set up CLAUDE.md / hooks / permissions for this repo". Surveys the repository, asks 4-6 targeted questions, diagnoses against a rubric, proposes a prioritized minimal harness design, implements only approved items, verifies them, and leaves a follow-up improvement backlog.
---

# Harness Engineering

対象リポジトリを、Claude Code が安定して働ける環境に整える。
以下の7フェーズを順に実行する。各フェーズの成果物を飛ばさないこと。

## 原則(全フェーズ共通)

- **最小構成を提案する。** 必要になってから複雑化する(部品を足すほど良いのではない)
- **調査で分かることをユーザーに聞かない**
- テンプレートは必ず対象リポジトリの実コマンド・実パスに書き換える。
  `{{MARKER}}` を残したまま設置することを禁止する
- 中間ファイルはセッションのスクラッチパッドに置き、対象リポジトリを汚さない
- 検証できなかった項目は「未検証」と正直に報告する
- 既存の `.claude/` や CLAUDE.md がある場合は**差分診断モード**:
  既存物を壊さず、ルーブリック再評価と差分提案のみ行う(Q6 で扱いを確認)

## Phase 1: 調査

Explore サブエージェントを1つ起動し、以下を調査させて結果を
`<scratchpad>/harness-survey.md` に構造化して保存する
(サブエージェントは調査結果を返答で報告し、メインスレッドが harness-survey.md として保存する):

- 言語 / フレームワーク / パッケージマネージャ
- ビルド・テスト・リンタ・型チェックの各コマンド。**実際に実行して**所要時間と成否を記録
- 既存の `.claude/`(settings.json, hooks, skills, agents)と CLAUDE.md / AGENTS.md
  の有無・行数・内容の鮮度(記載コマンドが今も動くか)
- CI 設定、pre-commit フック、テストの実態(存在・通るか・所要時間)
- git 管理の有無、モノレポ構造、生成コード、シークレット(.env 等)の場所
- OS / シェル環境(POSIX か Windows か — hooks テンプレの選択に使う)

サブエージェントが失敗した場合はメインスレッドで縮退調査
(パッケージ定義・CI設定・.claude/ の有無のみ)にフォールバックする。

## Phase 2: 質問

`references/interview.md` を読み、選択ルールに従って質問する。
Q1〜Q4 は常に(1回の AskUserQuestion で)、Q5・Q6 は該当時のみ2回目で。

## Phase 3: 診断 + 設計

Plan サブエージェントに以下をファイルパスで渡し、
`<scratchpad>/harness-proposal.md` を生成させる:

- `<scratchpad>/harness-survey.md`、Phase 2 の回答(プロンプトに含める)
- このスキルの `references/rubric.md` と `references/knowledge.md`

提案書の必須要件:

- ルーブリック全項目に **現状OK / 要改善 / 対象外** の判定と根拠(対象外は理由必須)
- 改善提案は 効果(高/中/低) × 導入コスト(高/中/低) で優先度付け
- 各提案に「これを入れないと何が起きるか」を1行で明記
- 各提案に使用するテンプレートファイルと置換するマーカーの値を明記

## Phase 4: 承認

提案書を領域ごと(A〜D)に提示し、AskUserQuestion(multiSelect)で
採用項目を選ばせる。全採用・全却下も可能。
**全却下の場合は Phase 5・6 をスキップし、Phase 7 のみ実施して終了する。**

## Phase 5: 実装

承認された項目のみ実装する。`templates/` を出発点に:

| テンプレート | 設置先 | 備考 |
|---|---|---|
| claude-md-skeleton.md | `CLAUDE.md` | 50行以下。不要セクション削除 |
| settings-permissions.json | `.claude/settings.json`(共有) or `.claude/settings.local.json`(個人) | Q2・Q4 の回答で決定。`_comment`/`_limitations` キーは設置時に削除 |
| hooks/*.sh または *.ps1 | `.claude/hooks/` | 環境で選択。`hooks/wiring.md` に従い settings.json へ配線。`.sh` は `chmod +x` |
| progress/, agents/evaluator.md | リポジトリルート / `.claude/agents/` | 長時間実行が承認された場合のみ |

- 全マーカーを Phase 1 で確認済みの実値に置換する
- 既存ファイルの変更は差分を提示してから適用する
- コミットはユーザーの指示がある場合のみ

## Phase 6: 検証

- hooks: ダミーファイルの編集で実際に発火するか確認する。
  発火しない場合は実行権限・パス・matcher を疑う
- settings.json: JSON として妥当か、`claude` 起動でエラー・不明キー警告が出ないか確認する
- CLAUDE.md: 50行以下か、各行が削除テスト(消すと失敗するか?)に耐えるか
- `grep -r '{{' <設置先>` でマーカー残りがないか確認する
- 結果を最終レポートとして提示する。**検証できなかった項目は「未検証」と明記する**

## Phase 7: 改善バックログ(実装しない)

診断・実装で見つかった「ハーネスの前提となるリポジトリ側の不足」を提示する。例:

- テストが無い/遅い → 品質ループの完了強制が組めない
- リンタが遅い → 高速リンタ(oxlint/ruff 等)移行で PostToolUse 化が可能になる
- 腐った説明文書 → 削除してテスト/型/ADR へ置き換え
- CI が無い → フックの次の防衛線が欠けている

各項目に「解消すると、次回このスキルを再実行したとき何が可能になるか」を付記する。
実装は通常の開発作業として別途行う(このスキルのスコープ外)。
````

- [ ] **Step 2: 検証**

Run: `head -4 skills/harness-engineering/SKILL.md`
Expected: frontmatter に `name: harness-engineering` があり、description が "Use when" で始まる

Run: `grep -c '^## Phase' skills/harness-engineering/SKILL.md`
Expected: `7`

Run: `grep -o 'references/[a-z]*\.md\|templates/[a-zA-Z/.-]*' skills/harness-engineering/SKILL.md | sort -u` → 出力された全パスが実在することを `ls` で確認

- [ ] **Step 3: コミット**

```bash
git add skills/harness-engineering/SKILL.md
git commit -m "feat: add harness-engineering SKILL.md orchestrating 7 phases

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 9: フィクスチャ作成と手動E2E検証(ユーザー参加)

**Files:**
- Create: `fixtures/sample-py/main.py`, `fixtures/sample-py/README.md`(テスト無しPythonリポジトリのフィクスチャ)
- Create: `fixtures/sample-ts/package.json`, `fixtures/sample-ts/src/add.mjs`, `fixtures/sample-ts/test/add.test.mjs`, `fixtures/sample-ts/README.md`(テスト有りNodeリポジトリのフィクスチャ。依存インストール不要のnode:testを使用)

**Interfaces:**
- Consumes: 完成したスキル一式
- Produces: スペックの「スキル自体の検証方法」チェックリストの実施結果

- [ ] **Step 1: フィクスチャ作成**

`fixtures/sample-py/main.py`(全文):

```python
def add(a, b):
    return a + b


def main():
    print(add(1, 2))


if __name__ == "__main__":
    main()
```

`fixtures/sample-py/README.md`(全文):

```markdown
# sample-py

harness-engineering スキルの動作確認用フィクスチャ。テスト・リンタ・CI・git なし。
期待される診断結果: D1(git管理)FAIL が最優先、テスト無しのため Q5 が発動、
B2(編集時自動検査)は B1 前提のため縮退提案になること。
検証時はこのディレクトリを git 管理外の一時ディレクトリへコピーして実行すること
(skills-lab 自体が git 管理下のため、ここで開くと D1 が PASS してしまう)。
```

- [ ] **Step 2: 2つ目のフィクスチャ作成(テスト有りNodeリポジトリ)**

`fixtures/sample-ts/package.json`(全文):

```json
{
  "name": "sample-ts",
  "private": true,
  "type": "module",
  "scripts": {
    "test": "node --test"
  }
}
```

`fixtures/sample-ts/src/add.mjs`(全文):

```javascript
export function add(a, b) {
  return a + b;
}
```

`fixtures/sample-ts/test/add.test.mjs`(全文):

```javascript
import test from "node:test";
import assert from "node:assert/strict";
import { add } from "../src/add.mjs";

test("add", () => {
  assert.equal(add(1, 2), 3);
});
```

`fixtures/sample-ts/README.md`(全文):

```markdown
# sample-ts

harness-engineering スキルの動作確認用フィクスチャ(テスト有り・リンタ無し・CLAUDE.md無し)。
期待される診断結果: B3(完了の強制)が提案され、B2 はリンタ不在(B1 FAIL)のため
Phase 7 バックログ行きになること。テストは `npm test`(node:test、依存インストール不要)。
```

Run: `cd fixtures/sample-ts && npm test` / Expected: `pass 1`

- [ ] **Step 3: フィクスチャをコミット**

```bash
git add fixtures/
git commit -m "test: add sample-py and sample-ts fixtures for manual skill verification

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

- [ ] **Step 4: 手動E2E検証(ユーザーと実施)**

スキルを `~/.claude/skills/harness-engineering/` にコピーし、各フィクスチャで
新しい Claude Code セッションを開いてスキルを起動する。以下をチェック:

検証時はこのディレクトリを git 管理外の一時ディレクトリへコピーして実行すること
(skills-lab 自体が git 管理下のため、ここで開くと D1 が PASS してしまう)。

sample-py(テスト無し・git無し):
- [ ] Phase 1 の survey に「テスト無し・git 無し・Windows」が記録される
- [ ] Phase 2 で Q1〜Q4 + Q5 が出る(調査で分かること=言語やコマンドを聞いていない)
- [ ] Phase 3 の提案で D1(git init)が最優先になっている
- [ ] Phase 5 で設置されたファイルに `{{` マーカーが残っていない
- [ ] Phase 7 で「テスト整備」がバックログ筆頭に出る

sample-ts(テスト有り・リンタ無し):
- [ ] Phase 3 で B3 が提案され、B2 が「B1前提のため対象外/バックログ行き」になる
- [ ] settings.json の allow に `npm test` 系が入り、JSONとして妥当
- [ ] 実装後にもう一度スキルを実行し、差分診断モードで動く(新規構築をやり直さない)

結果を記録し、問題があれば SKILL.md / references を修正して再検証する。

- [ ] **Step 5: 検証結果の反映をコミット**

```bash
git add -A
git commit -m "fix: adjust skill based on manual E2E verification findings

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

(修正が無ければこのステップはスキップ)
