# Stop: セッション終了時、未コミット変更があれば自動チェックポイントコミット(セッション間ハンドオフ用)
git rev-parse --is-inside-work-tree 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) { exit 0 }
$dirty = (git status --porcelain)
if ($dirty) {
    git add -A
    git commit -m "wip: session checkpoint (auto-commit by Stop hook)" | Out-Null
}
exit 0
