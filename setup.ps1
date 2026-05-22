# setup.ps1 — Local convenience wrapper. Assumes uv is already installed.
# For a true zero-state install on a fresh machine, use install.ps1 instead:
#   irm https://raw.githubusercontent.com/william051200/UI-automation/main/install.ps1 | iex
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw "uv not found on PATH. Run install.ps1 instead, or: irm https://astral.sh/uv/install.ps1 | iex"
}
uv sync
Write-Host "Done. Run: uv run python run_test.py test_cases\powershell_echo_loop.yaml"
