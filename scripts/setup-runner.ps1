<#
.SYNOPSIS
    Register the current DevBox as a self-hosted GitHub Actions runner
    for the UI-automation repository.

.DESCRIPTION
    One-time bootstrap. Run this ON YOUR DEVBOX (RDP'd, unlocked) once,
    then never again for that DevBox. After it completes, your DevBox
    is a runner reachable from the Actions tab, and any tester can
    trigger a workflow against it from a browser.

    What it does:
      1. Prompts for (or accepts) your DevBox label.
      2. Verifies uv, python, git are present (installs via winget if not).
      3. Downloads the latest actions/runner release.
      4. Configures it against the repo with your chosen label.
      5. Installs and starts it as a Windows service that survives reboots.

    You will need a runner registration token from the repo's
    Settings -> Actions -> Runners -> New self-hosted runner page.
    (Or pass -Token to skip the interactive prompt.)

.PARAMETER Label
    The label to register this runner under. Must follow the convention:
      <INITIALS>-<DDMMYYYY>-<N>
    e.g. ZY-24072026-1

.PARAMETER Repo
    The GitHub repo to register against. Default: zunyangc/UI-automation
    Change to the upstream slug once we move there.

.PARAMETER Token
    Registration token from GitHub. If omitted, you'll be prompted with
    the URL to fetch it from.

.PARAMETER InstallRoot
    Directory to install the runner into. Default: C:\actions-runner

.EXAMPLE
    .\scripts\setup-runner.ps1 -Label ZY-24072026-1

.EXAMPLE
    .\scripts\setup-runner.ps1 -Label WN-24072026-1 -Token ABCXYZ...

.NOTES
    Must be run in an Administrator PowerShell (installing a Windows
    service requires elevation).
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[A-Z]{2}-\d{8}-\d+$')]
    [string]$Label,

    [string]$Repo = 'zunyangc/UI-automation',

    [string]$Token,

    [string]$InstallRoot = 'C:\actions-runner'
)

$ErrorActionPreference = 'Stop'

function Write-Step($msg) { Write-Host "==> $msg" -ForegroundColor Cyan }
function Write-Ok($msg)   { Write-Host "    $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "    $msg" -ForegroundColor Yellow }

# --- Admin check ----------------------------------------------------------
$isAdmin = ([Security.Principal.WindowsPrincipal] `
    [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    throw "This script must be run in an Administrator PowerShell."
}

# --- Prereqs: uv, git, python --------------------------------------------
Write-Step "Checking prerequisites (uv, git, python)..."

function Ensure-Winget {
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        throw "winget is not available. Install App Installer from the Microsoft Store, then re-run."
    }
}

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Ensure-Winget
    Write-Warn "git missing; installing via winget..."
    winget install -e --id Git.Git --accept-source-agreements --accept-package-agreements | Out-Null
    $env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' +
                [Environment]::GetEnvironmentVariable('Path','User')
}
Write-Ok "git: $(git --version)"

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Warn "uv missing; installing from astral.sh..."
    irm https://astral.sh/uv/install.ps1 | iex
    $env:Path = "$HOME\.local\bin;$env:Path"
}
Write-Ok "uv: $(uv --version)"

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    # uv will fetch python on first `uv sync`; nothing to install here.
    Write-Warn "python not on PATH — uv will provision one on first sync."
} else {
    Write-Ok "python: $(python --version)"
}

# --- Token ---------------------------------------------------------------
if (-not $Token) {
    Write-Host ""
    Write-Host "A runner registration token is required." -ForegroundColor Yellow
    Write-Host "Get one from:" -ForegroundColor Yellow
    Write-Host "  https://github.com/$Repo/settings/actions/runners/new?arch=x64&os=win" -ForegroundColor Cyan
    Write-Host "Copy the token shown next to './config.cmd --token ...' and paste it here:"
    $Token = Read-Host -Prompt "Token" -AsSecureString |
        ForEach-Object { [Runtime.InteropServices.Marshal]::PtrToStringAuto(
            [Runtime.InteropServices.Marshal]::SecureStringToBSTR($_)) }
}
if (-not $Token) { throw "No token provided." }

# --- Download runner ------------------------------------------------------
Write-Step "Downloading latest actions/runner..."
New-Item -ItemType Directory -Force -Path $InstallRoot | Out-Null
Set-Location $InstallRoot

$latest = Invoke-RestMethod https://api.github.com/repos/actions/runner/releases/latest
$asset  = $latest.assets | Where-Object { $_.name -like 'actions-runner-win-x64-*.zip' } | Select-Object -First 1
if (-not $asset) { throw "Could not find a Windows x64 runner asset in the latest release." }

$zip = Join-Path $InstallRoot $asset.name
if (-not (Test-Path $zip)) {
    Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $zip
}

if (-not (Test-Path (Join-Path $InstallRoot 'config.cmd'))) {
    Write-Step "Extracting runner..."
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [System.IO.Compression.ZipFile]::ExtractToDirectory($zip, $InstallRoot)
}

# --- Configure -----------------------------------------------------------
Write-Step "Configuring runner as '$Label' against $Repo..."
$runnerUrl = "https://github.com/$Repo"
& .\config.cmd `
    --url $runnerUrl `
    --token $Token `
    --name $Label `
    --labels $Label `
    --work "_work" `
    --unattended `
    --replace
if ($LASTEXITCODE -ne 0) { throw "config.cmd failed with exit code $LASTEXITCODE" }

# --- Install as Windows service ------------------------------------------
Write-Step "Installing runner as a Windows service..."
& .\svc.cmd install
& .\svc.cmd start
if ($LASTEXITCODE -ne 0) { throw "svc.cmd start failed with exit code $LASTEXITCODE" }

Write-Ok "Runner '$Label' installed and started as a Windows service."
Write-Host ""
Write-Host "NEXT STEPS:" -ForegroundColor Yellow
Write-Host "  1. Verify at: https://github.com/$Repo/settings/actions/runners"
Write-Host "     Your runner '$Label' should show status = Idle."
Write-Host "  2. Add '$Label' to .github/workflows/run-ui-tests.yml"
Write-Host "     under target_devbox.options and open a PR."
Write-Host "  3. Trigger a run from the Actions tab: pick a CSV + your label."
Write-Host ""
