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
