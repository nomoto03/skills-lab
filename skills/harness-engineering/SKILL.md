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
各選択肢の説明には「選ぶと何が設置され、日常の何が変わるか」を1行で含める
(interview.md の文言は雛形。対象リポジトリの実物・実コマンドで具体化する)。

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
採用項目を選ばせる。各選択肢の説明には「採用すると何が入り・いつから効くか」と
「見送ると何が起きるか」(提案書の同名欄を転記)を具体的に書く。全採用・全却下も可能。
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
- 最終レポートには設置物ごとに「何が変わるか」を体験ベースで書く:
  ①いつから効くか(セッション再起動の要否) ②日常の変化(例: 「.md を保存する
  たびに検査が走り、違反はその場でエージェントに差し戻される」「rm -rf は確認
  なしで拒否されるようになる」) ③ユーザー自身で試せる確認コマンド

## Phase 7: 改善バックログ(実装しない)

診断・実装で見つかった「ハーネスの前提となるリポジトリ側の不足」を提示する。例:

- テストが無い/遅い → 品質ループの完了強制が組めない
- リンタが遅い → 高速リンタ(oxlint/ruff 等)移行で PostToolUse 化が可能になる
- 腐った説明文書 → 削除してテスト/型/ADR へ置き換え
- CI が無い → フックの次の防衛線が欠けている

各項目に「解消すると、次回このスキルを再実行したとき何が可能になるか」を付記する。
実装は通常の開発作業として別途行う(このスキルのスコープ外)。
