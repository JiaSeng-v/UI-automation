# run.ps1 — Shortcut for: uv run python run_test.py <spec> [extra args]
# Lets you invoke a scenario directly from the repo root without going
# through an LLM, which is the cheapest way to run the suite.
#
# Examples:
#   .\run.ps1 test_cases\powershell_echo_loop.yaml
#   .\run.ps1 test_cases\powershell_echo_loop.yaml -q
#   .\run.ps1 test_cases\powershell_echo_loop.csv -q   # CSV spec (run directly)
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Spec,
    [Parameter(ValueFromRemainingArguments = $true)]
    $Rest
)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

uv run python run_test.py $Spec @Rest
exit $LASTEXITCODE
