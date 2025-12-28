# Script pour tester le frontend de manière automatisée
# Vérifie build, lint, tests unitaires, et optionnellement E2E

param(
    [switch]$E2E = $false,
    [switch]$Browser = $false
)

Write-Host "=== Tests Frontend ===" -ForegroundColor Cyan

$projectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $projectRoot

$errors = @()

# 1. Build check
Write-Host "`n1. Vérification du build..." -ForegroundColor Cyan
Set-Location frontend
npm run build 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    $errors += "Build échoué"
    Write-Host "  ✗ Build échoué" -ForegroundColor Red
} else {
    Write-Host "  ✓ Build réussi" -ForegroundColor Green
}

# 2. Lint check
Write-Host "`n2. Vérification du lint..." -ForegroundColor Cyan
npm run lint 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    $errors += "Lint échoué"
    Write-Host "  ✗ Lint échoué" -ForegroundColor Red
} else {
    Write-Host "  ✓ Lint OK" -ForegroundColor Green
}

# 3. Tests unitaires
Write-Host "`n3. Tests unitaires (Vitest)..." -ForegroundColor Cyan
npm test -- --run 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    $errors += "Tests unitaires échoués"
    Write-Host "  ✗ Tests unitaires échoués" -ForegroundColor Red
} else {
    Write-Host "  ✓ Tests unitaires passés" -ForegroundColor Green
}

# 4. Tests E2E (optionnel)
if ($E2E) {
    Write-Host "`n4. Tests E2E (Playwright)..." -ForegroundColor Cyan
    Set-Location $projectRoot
    npx playwright test 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        $errors += "Tests E2E échoués"
        Write-Host "  ✗ Tests E2E échoués" -ForegroundColor Red
    } else {
        Write-Host "  ✓ Tests E2E passés" -ForegroundColor Green
    }
}

# Résumé
Write-Host "`n=== Résumé ===" -ForegroundColor Cyan
if ($errors.Count -eq 0) {
    Write-Host "✓ Tous les tests frontend ont réussi!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "✗ Erreurs détectées:" -ForegroundColor Red
    foreach ($err in $errors) {
        Write-Host "  - $err" -ForegroundColor Red
    }
    exit 1
}



