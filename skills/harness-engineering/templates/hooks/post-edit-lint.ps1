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
