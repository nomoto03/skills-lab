# Structure check for skills-lab ("the test" of this repository).
# Compatible with Windows PowerShell 5.1 and pwsh (used as-is in CI).
# Checks:
#   1. every skills/*/ has SKILL.md with frontmatter name/description, name == dir name
#   2. no bare {{MARKER}} outside templates/ in skills/ markdown
#      (mentions inside backticks or fenced code blocks are allowed)
#   3. references/... and templates/... paths mentioned in SKILL.md and
#      references/*.md resolve to real files in some skills/*/ directory
#   4. every skills/*/templates/hooks/ script exists as a .ps1/.sh pair
# Accepts an optional file path argument (from the PostToolUse hook) but always
# runs the full scan - the whole check completes in well under a second.
param([string]$Path)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$skillsRoot = Join-Path $repoRoot 'skills'
$violations = @()

function Read-Utf8Lines([string]$file) {
    return [System.IO.File]::ReadAllLines($file, [System.Text.Encoding]::UTF8)
}

$skillDirs = @(Get-ChildItem -Path $skillsRoot -Directory)

# --- Check 1: SKILL.md frontmatter ---
foreach ($dir in $skillDirs) {
    $skillMd = Join-Path $dir.FullName 'SKILL.md'
    if (-not (Test-Path $skillMd)) {
        $violations += "[frontmatter] skills/$($dir.Name)/SKILL.md is missing"
        continue
    }
    $lines = Read-Utf8Lines $skillMd
    if ($lines.Count -lt 3 -or $lines[0].Trim() -ne '---') {
        $violations += "[frontmatter] skills/$($dir.Name)/SKILL.md has no frontmatter block"
        continue
    }
    $end = -1
    for ($i = 1; $i -lt $lines.Count; $i++) {
        if ($lines[$i].Trim() -eq '---') { $end = $i; break }
    }
    if ($end -lt 0) {
        $violations += "[frontmatter] skills/$($dir.Name)/SKILL.md frontmatter is not closed"
        continue
    }
    $fm = $lines[1..($end - 1)]
    $nameLine = @($fm | Where-Object { $_ -match '^name:\s*(\S+)' })
    $descLine = @($fm | Where-Object { $_ -match '^description:\s*\S' })
    if ($nameLine.Count -eq 0) {
        $violations += "[frontmatter] skills/$($dir.Name)/SKILL.md: 'name:' key missing"
    } else {
        $null = $nameLine[0] -match '^name:\s*(\S+)'
        if ($Matches[1] -ne $dir.Name) {
            $violations += "[frontmatter] skills/$($dir.Name)/SKILL.md: name '$($Matches[1])' != directory name '$($dir.Name)'"
        }
    }
    if ($descLine.Count -eq 0) {
        $violations += "[frontmatter] skills/$($dir.Name)/SKILL.md: 'description:' key missing"
    }
}

# --- Check 2: bare {{MARKER}} outside templates/ ---
$mdFiles = Get-ChildItem -Path $skillsRoot -Recurse -Filter '*.md' |
    Where-Object { $_.FullName -notmatch '[\\/]templates[\\/]' }
foreach ($f in $mdFiles) {
    $rel = $f.FullName.Substring($repoRoot.Length + 1) -replace '\\', '/'
    $inFence = $false
    $lineNo = 0
    foreach ($line in (Read-Utf8Lines $f.FullName)) {
        $lineNo++
        if ($line -match '^\s*```') { $inFence = -not $inFence; continue }
        if ($inFence) { continue }
        $stripped = $line -replace '`[^`]*`', ''
        if ($stripped -match '\{\{[A-Z][A-Z_]*\}\}') {
            $violations += "[marker] ${rel}:${lineNo}: bare {{MARKER}} outside templates/ (wrap in backticks if it is a mention)"
        }
    }
}

# --- Check 3: referenced paths resolve ---
foreach ($dir in $skillDirs) {
    $targets = @(Join-Path $dir.FullName 'SKILL.md')
    $refDir = Join-Path $dir.FullName 'references'
    if (Test-Path $refDir) {
        $targets += (Get-ChildItem -Path $refDir -Filter '*.md' | ForEach-Object { $_.FullName })
    }
    foreach ($t in $targets) {
        if (-not (Test-Path $t)) { continue }
        $rel = $t.Substring($repoRoot.Length + 1) -replace '\\', '/'
        $text = [System.IO.File]::ReadAllText($t, [System.Text.Encoding]::UTF8)
        $refs = [regex]::Matches($text, '(?:references|templates)/[A-Za-z0-9._/\-]+') |
            ForEach-Object { $_.Value.TrimEnd('.', '/') } | Sort-Object -Unique
        foreach ($r in $refs) {
            $found = $false
            foreach ($base in $skillDirs) {
                $cand = Join-Path $base.FullName ($r -replace '/', [IO.Path]::DirectorySeparatorChar)
                if ((Test-Path $cand) -or (@(Get-Item -Path "$cand*" -ErrorAction SilentlyContinue).Count -gt 0)) {
                    $found = $true; break
                }
            }
            if (-not $found) {
                $violations += "[link] ${rel}: referenced path '$r' not found in any skills/*/ directory"
            }
        }
    }
}

# --- Check 4: templates/hooks/ .ps1/.sh pairs ---
foreach ($dir in $skillDirs) {
    $hooksDir = Join-Path $dir.FullName 'templates\hooks'
    if (-not (Test-Path $hooksDir)) { continue }
    $scripts = Get-ChildItem -Path $hooksDir | Where-Object { $_.Extension -in '.ps1', '.sh' }
    $names = $scripts | ForEach-Object { $_.BaseName } | Sort-Object -Unique
    foreach ($n in $names) {
        foreach ($ext in '.ps1', '.sh') {
            if (-not (Test-Path (Join-Path $hooksDir "$n$ext"))) {
                $violations += "[hooks-pair] skills/$($dir.Name)/templates/hooks/${n}${ext} is missing (both OS variants required)"
            }
        }
    }
}

if ($violations.Count -gt 0) {
    foreach ($v in $violations) { [Console]::Error.WriteLine($v) }
    [Console]::Error.WriteLine("check-structure: $($violations.Count) violation(s) found")
    exit 1
}
Write-Output 'check-structure: OK'
exit 0
