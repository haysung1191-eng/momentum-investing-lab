param(
    [double]$TotalCapital = 100000000,
    [switch]$RefreshShadow,
    [switch]$RefreshReference,
    [switch]$StatusOnly,
    [switch]$Json,
    [switch]$FailOnNotGo,
    [switch]$NoDashboard
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$python = (Get-Command python -ErrorAction Stop).Source

$args = @("tools/pipelines/run_split_models_operator_handoff.py", "--total-capital", $TotalCapital.ToString())
if ($RefreshShadow) {
    $args += "--refresh-shadow"
}
if ($RefreshReference) {
    $args += "--refresh-reference"
}
if ($StatusOnly) {
    $args += "--status-only"
}
if ($Json) {
    $args += "--json"
}
if ($FailOnNotGo) {
    $args += "--fail-on-not-go"
}

Write-Host "[ops] running operator handoff" -ForegroundColor Cyan
& $python @args

if ((-not $NoDashboard) -and (-not $StatusOnly)) {
    Write-Host "[ops] opening split-model shadow dashboard" -ForegroundColor Cyan
  Start-Process $python -ArgumentList "-m", "streamlit", "run", ".\tools\dashboards\split_models_shadow_dashboard.py"
}

Write-Host "[ops] done" -ForegroundColor Green
