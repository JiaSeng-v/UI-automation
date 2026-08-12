<#
.SYNOPSIS
    Uninstall a self-hosted DevBox runner and strip its label from the
    fork's workflow file.

.DESCRIPTION
    Run this on the DevBox in an Administrator PowerShell to fully
    decommission a runner:

        .\scripts\remove-runner.ps1 -Label <YourLabel> -Token <RemoveToken>

    What it does:
      1. Stop and unregister the Scheduled Task 'GHRunner-<Label>'.
      2. Kill any live 'run.cmd'/'Runner.Listener' process for that runner.
      3. Run 'C:\actions-runner\config.cmd remove --token <Token>' to
         deregister the runner on GitHub.
      4. Edit .github/workflows/run-ui-tests.yml on your fork to strip
         '- <Label>' from target_devbox.options and push to origin/main.

.PARAMETER Label
    The runner label (e.g. '12082026-devbox-1').

.PARAMETER Token
    Runner *removal* token. Get one from:
        gh api -X POST repos/<your-handle>/UI-automation/actions/runners/remove-token
    Or (browser): fork -> Settings -> Actions -> Runners -> click your
    runner -> Remove -> copy the token from the shown './config.cmd
    remove --token ...' line.

.PARAMETER Repo
    GitHub 'owner/name' of your fork. Auto-detected from RepoPath origin
    if omitted.

.PARAMETER RepoPath
    Local clone path (default: $HOME\UI-automation).

.PARAMETER RunnerRoot
    Runner install dir (default: C:\actions-runner).

.PARAMETER LocalOnly
    If set, only clean local state (Scheduled Task + config.cmd --local).
    Skips the GitHub-side deregistration; use when the runner is already
    gone from Settings -> Runners or the token endpoint 404s.
#>

param(
    [Parameter(Mandatory=$true)]
    [ValidatePattern('^([A-Z]{2}-)?\d{8}(-[A-Za-z0-9]+)*-\d+$')]
    [string]$Label,

    [string]$Token,

    [string]$Repo,

    [string]$RepoPath = "$HOME\UI-automation",

    [string]$RunnerRoot = 'C:\actions-runner',

    [switch]$LocalOnly
)

$ErrorActionPreference = 'Stop'

function Write-Step($msg) { Write-Host ""; Write-Host "==> $msg" -ForegroundColor Cyan }
function Write-Ok($msg)   { Write-Host "    $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "    $msg" -ForegroundColor Yellow }

# --- Admin check --------------------------------------------------------
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) { throw "This script must be run in an Administrator PowerShell." }

# --- Resolve Repo -------------------------------------------------------
if (-not $Repo) {
    if (-not (Test-Path (Join-Path $RepoPath '.git'))) {
        throw "RepoPath '$RepoPath' is not a git checkout; pass -Repo <owner/name>."
    }
    Push-Location $RepoPath
    try {
        $originUrl = (git remote get-url origin 2>$null).Trim()
    } finally { Pop-Location }
    if ($originUrl -match 'github\.com[:/](?<owner>[^/]+)/(?<repo>[^/.]+)') {
        $Repo = "$($Matches.owner)/$($Matches.repo)"
    } else {
        throw "Could not parse GitHub owner/repo from '$originUrl'. Pass -Repo <owner/name>."
    }
}
Write-Ok "Target fork: $Repo"

# --- Stop and remove Scheduled Task ------------------------------------
$taskName = "GHRunner-$Label"
Write-Step "Stopping Scheduled Task '$taskName'..."
$task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($task) {
    try { Stop-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue } catch {}
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    Write-Ok "Scheduled Task removed."
} else {
    Write-Warn "Scheduled Task '$taskName' not found; skipping."
}

# --- Kill live listener processes --------------------------------------
Write-Step "Stopping any live listener processes..."
$killed = 0
Get-Process -Name 'Runner.Listener','run' -ErrorAction SilentlyContinue | ForEach-Object {
    try { Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue; $killed++ } catch {}
}
if ($killed -gt 0) { Write-Ok "$killed listener process(es) terminated." } else { Write-Warn "No live listener processes found." }

# --- Deregister on GitHub ----------------------------------------------
Write-Step "Removing runner registration..."
if (-not (Test-Path (Join-Path $RunnerRoot 'config.cmd'))) {
    Write-Warn "No runner install found at $RunnerRoot; skipping config.cmd remove."
} else {
    Push-Location $RunnerRoot
    try {
        if ($LocalOnly) {
            .\config.cmd remove --token dummy --local | Out-Host
        } elseif ($Token) {
            .\config.cmd remove --token $Token | Out-Host
        } else {
            Write-Warn "No -Token supplied; falling back to --local removal."
            Write-Warn "The runner may still appear (offline) on GitHub -- delete it manually from Settings -> Actions -> Runners."
            .\config.cmd remove --token dummy --local | Out-Host
        }
        if ($LASTEXITCODE -ne 0) { throw "config.cmd remove failed with exit code $LASTEXITCODE." }
        Write-Ok "Runner unregistered."
    } finally { Pop-Location }
}

# --- Strip label from workflow file ------------------------------------
Write-Step "Removing '$Label' from workflow file on '$RepoPath'..."
if (-not (Test-Path (Join-Path $RepoPath '.git'))) {
    Write-Warn "No local clone at $RepoPath; skipping workflow edit."
} else {
    $workflow = Join-Path $RepoPath '.github/workflows/run-ui-tests.yml'
    if (-not (Test-Path $workflow)) {
        Write-Warn "Workflow file not found at $workflow; skipping."
    } else {
        Push-Location $RepoPath
        try {
            git fetch origin main | Out-Host
            git checkout main | Out-Host
            git reset --hard origin/main | Out-Host

            $content = Get-Content -Path $workflow -Raw
            # Match one full line whose bullet value equals the label, with optional trailing comment.
            $linePattern = "(?m)^[ ]{10}-[ ]+$([regex]::Escape($Label))([ \t]+#[^\r\n]*)?\r?\n"
            if ($content -notmatch $linePattern) {
                Write-Warn "Label '$Label' not found in $workflow; nothing to strip."
            } else {
                $updated = [regex]::Replace($content, $linePattern, '')
                Set-Content -Path $workflow -Value $updated -NoNewline
                Write-Ok "Label line removed from workflow."

                Write-Step "Committing and pushing to origin/main..."
                git add .github/workflows/run-ui-tests.yml
                git commit -m "Decommission DevBox runner: $Label" | Out-Host
                git push origin main | Out-Host
                Write-Ok "Workflow updated on origin/main."
            }
        } catch {
            Write-Warn "Workflow edit/push failed: $_"
        } finally { Pop-Location }
    }
}

Write-Host ""
Write-Host "DONE." -ForegroundColor Green
Write-Host "Verify: https://github.com/$Repo/settings/actions/runners (label should be gone)."
