# PostToolUse (Write|Edit): run the repo structure check after markdown edits
# and feed violations back to the agent (exit 2 = block + stderr to agent).
# Installed from skills/harness-engineering/templates/hooks/post-edit-lint.ps1
# (EXT=md, LINT_CMD=scripts/check-structure.ps1, called in-process because the
# hook already runs under powershell - avoids nested powershell startup cost).
$json = [Console]::In.ReadToEnd() | ConvertFrom-Json
$file = $json.tool_input.file_path
if (-not $file) { exit 0 }
if ($file -notmatch '\.md$') { exit 0 }
& .\scripts\check-structure.ps1 $file
if ($LASTEXITCODE -ne 0) {
    [Console]::Error.WriteLine("Structure check failed after editing $file - fix the violations above before proceeding.")
    exit 2
}
exit 0
