# skills-lab

Claude Code 用スキル(Markdown)を開発するリポジトリ。

## コマンド

- テスト(構造チェック): `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check-structure.ps1`

## 構成

- ソース: `skills/`(1スキル = SKILL.md + references/ + templates/)
- テスト: `scripts/check-structure.ps1`(frontmatter・マーカー規約・リンク整合・hooks両OSペア)
- `fixtures/` は診断練習用サンプル。**sample-py は意図的にテスト・git 無し — 直さないこと**

## 規約

- ブランチ: `feature/<topic>`
- `{{MARKER}}` を含むファイルは `templates/` 配下のみ。地の文での言及はバッククォートで囲む
- SKILL.md frontmatter の `name` はディレクトリ名と一致させる
- 計画(`docs/superpowers/plans/`)と成果物は常に同期させる

## 詳細ポインタ

- 設計仕様: `docs/superpowers/specs/` / 実装計画: `docs/superpowers/plans/`
- 進捗台帳: `.superpowers/sdd/progress.md`(git 管理外)
