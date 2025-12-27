# Script PowerShell pour exécuter les tests (Windows)
# Usage: .\scripts\run_tests.ps1

Write-Host "Exécution des tests..." -ForegroundColor Cyan

# Exécuter pytest avec options
pytest tests/ -v --tb=short

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ Les tests ont échoué." -ForegroundColor Red
    exit 1
}

Write-Host "`n✅ Tous les tests passent." -ForegroundColor Green
exit 0



