# Script to create and configure the project's Python venv
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts/setup-venv.ps1
# Options:
#   -Force       Recreate venv (deletes existing .venv)
#   -SkipInstall Create venv but do not install requirements

param(
    [switch]$Force = $false,
    [switch]$SkipInstall = $false
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$venvDir = Join-Path $projectRoot ".venv"
$venvPython = Join-Path $venvDir "Scripts\python.exe"
$requirementsFile = Join-Path $projectRoot "requirements.txt"

function Get-PythonCandidate {
    <#
    .SYNOPSIS
    Resolve a usable Python command on Windows.

    .DESCRIPTION
    Tries "python" first, then the Windows launcher "py" for 3.12/3.11/3.10.
    Returns a PSCustomObject with Exe, Args, VersionText, Major, Minor.
    Returns $null if nothing works.
    #>
    param()

    $candidates = @(
        @{ Exe = "python"; Args = @() },
        @{ Exe = "py"; Args = @("-3.12") },
        @{ Exe = "py"; Args = @("-3.11") },
        @{ Exe = "py"; Args = @("-3.10") },
        @{ Exe = "py"; Args = @("-3") }
    )

    foreach ($c in $candidates) {
        try {
            $versionText = & $c.Exe @($c.Args) --version 2>&1
            if ($LASTEXITCODE -ne 0) { continue }

            if ($versionText -match "Python (\d+)\.(\d+)\.(\d+)") {
                return [pscustomobject]@{
                    Exe         = $c.Exe
                    Args        = $c.Args
                    VersionText = $versionText
                    Major       = [int]$matches[1]
                    Minor       = [int]$matches[2]
                }
            }
        } catch {
            continue
        }
    }

    return $null
}

Write-Host ""
Write-Host "=== Python venv setup ===" -ForegroundColor Cyan
Write-Host ("Project: {0}" -f $projectRoot) -ForegroundColor Gray
Write-Host ""

Write-Host "[1/4] Checking Python..." -ForegroundColor Cyan
$python = Get-PythonCandidate
if (-not $python) {
    Write-Host "  ERROR: Python was not found on PATH." -ForegroundColor Red
    Write-Host "  Install Python 3.10+ from https://www.python.org/downloads/ (recommended)." -ForegroundColor Yellow
    Write-Host "  Tip: if typing 'python' opens the Microsoft Store, install Python from python.org (includes 'py')." -ForegroundColor Gray
    exit 1
}

if ($python.Major -lt 3 -or ($python.Major -eq 3 -and $python.Minor -lt 10)) {
    Write-Host ("  ERROR: Unsupported Python version: {0}" -f $python.VersionText) -ForegroundColor Red
    Write-Host "  Required: Python 3.10+" -ForegroundColor Yellow
    exit 1
}

Write-Host ("  OK: {0}" -f $python.VersionText) -ForegroundColor Green

Write-Host ""
Write-Host "[2/4] Creating venv..." -ForegroundColor Cyan

if (Test-Path -LiteralPath $venvDir) {
    if ($Force) {
        Write-Host ("  Removing existing venv: {0}" -f $venvDir) -ForegroundColor Yellow
        Remove-Item -LiteralPath $venvDir -Recurse -Force
    } elseif (-not (Test-Path -LiteralPath $venvPython)) {
        Write-Host "  Existing venv looks corrupted (python.exe missing). Recreating it." -ForegroundColor Yellow
        Remove-Item -LiteralPath $venvDir -Recurse -Force
    } else {
        Write-Host ("  Venv already exists: {0}" -f $venvDir) -ForegroundColor Gray
    }
}

if (-not (Test-Path -LiteralPath $venvDir)) {
    & $python.Exe @($python.Args) -m venv $venvDir
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ERROR: Failed to create venv." -ForegroundColor Red
        exit 1
    }
}

if (-not (Test-Path -LiteralPath $venvPython)) {
    Write-Host ("  ERROR: venv python was not created: {0}" -f $venvPython) -ForegroundColor Red
    exit 1
}

Write-Host ("  OK: {0}" -f $venvPython) -ForegroundColor Green

Write-Host ""
Write-Host "[3/4] Upgrading pip..." -ForegroundColor Cyan
try {
    & $venvPython -m pip install --upgrade pip | Out-Null
    $pipVersion = & $venvPython -m pip --version 2>&1
    Write-Host ("  OK: {0}" -f $pipVersion) -ForegroundColor Green
} catch {
    Write-Host "  WARN: pip upgrade failed; continuing." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[4/4] Installing dependencies..." -ForegroundColor Cyan

if ($SkipInstall) {
    Write-Host "  Skipped (SkipInstall)." -ForegroundColor Yellow
} elseif (-not (Test-Path -LiteralPath $requirementsFile)) {
    Write-Host ("  WARN: requirements.txt not found: {0}" -f $requirementsFile) -ForegroundColor Yellow
} else {
    & $venvPython -m pip install -r $requirementsFile
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ERROR: pip install -r requirements.txt failed." -ForegroundColor Red
        Write-Host "  Try:" -ForegroundColor Yellow
        Write-Host ("    {0} -m pip install -r requirements.txt" -f $venvPython) -ForegroundColor Cyan
        exit 1
    }
    Write-Host "  OK: requirements installed." -ForegroundColor Green
}

$packagesToCheck = @("fastapi", "uvicorn", "pytest", "pytest-asyncio", "openai", "pydantic")
$missing = @()

foreach ($pkg in $packagesToCheck) {
    & $venvPython -m pip show $pkg | Out-Null
    if ($LASTEXITCODE -ne 0) {
        $missing += $pkg
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Venv:   $venvDir" -ForegroundColor Gray
Write-Host "Python: $venvPython" -ForegroundColor Gray

if ($missing.Count -eq 0) {
    Write-Host "Status: OK" -ForegroundColor Green
} else {
    Write-Host "Status: WARN (missing packages detected)" -ForegroundColor Yellow
    Write-Host ("Missing: {0}" -f ($missing -join ", ")) -ForegroundColor Yellow
    Write-Host "Fix: run npm run setup (or rerun this script without SkipInstall)." -ForegroundColor Gray
}

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  - npm scripts automatically use the venv" -ForegroundColor Gray
Write-Host "  - Manual activation: .\\scripts\\activate-venv.ps1" -ForegroundColor Gray
Write-Host "  - Verify: npm run verify:venv" -ForegroundColor Gray
Write-Host "  - Dev: npm run dev" -ForegroundColor Gray
Write-Host ""
