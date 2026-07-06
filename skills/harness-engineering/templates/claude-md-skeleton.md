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
