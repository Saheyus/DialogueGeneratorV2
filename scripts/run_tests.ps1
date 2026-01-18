# Script PowerShell pour exécuter les tests (Windows)
# Usage: .\scripts\run_tests.ps1

# Importer la fonction Get-VenvPython
$projectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
. (Join-Path $projectRoot "scripts\Get-VenvPython.ps1")

Write-Host "Exécution des tests..." -ForegroundColor Cyan

# Obtenir le chemin Python du venv
$pythonPath = Get-VenvPython -ProjectRoot $projectRoot -Quiet

# Exécuter pytest avec options
& $pythonPath -m pytest tests/ -v --tb=short

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ Les tests ont échoué." -ForegroundColor Red
    exit 1
}

Write-Host "`n✅ Tous les tests passent." -ForegroundColor Green
exit 0



