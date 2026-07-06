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
| B3 | 完了の強制 | テスト合格がフック/CIで強制(プロンプト依存でない) | Stopフック提案 or CI(Phase 7) |
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
