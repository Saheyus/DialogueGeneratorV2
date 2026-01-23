# Script pour activer manuellement le venv
# Usage: .\scripts\activate-venv.ps1

$projectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

Write-Host "=== Activation du venv Python ===" -ForegroundColor Cyan
Write-Host ""

# Vérifier si le venv existe
$venvPath = Join-Path $projectRoot ".venv"
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"

if (-not (Test-Path $venvPath)) {
    Write-Host "❌ Le venv n'existe pas encore" -ForegroundColor Red
    Write-Host ""
    Write-Host "Créez-le avec la commande:" -ForegroundColor Yellow
    Write-Host "  npm run setup" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Ou manuellement:" -ForegroundColor Yellow
    Write-Host "  python -m venv .venv" -ForegroundColor Cyan
    Write-Host "  .\.venv\Scripts\Activate.ps1" -ForegroundColor Cyan
    Write-Host "  pip install -r requirements.txt" -ForegroundColor Cyan
    exit 1
}

if (-not (Test-Path $activateScript)) {
    Write-Host "❌ Script d'activation non trouvé: $activateScript" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Venv trouvé: $venvPath" -ForegroundColor Green
Write-Host ""
Write-Host "Pour activer le venv dans cette session PowerShell:" -ForegroundColor Yellow
Write-Host "  .\.venv\Scripts\Activate.ps1" -ForegroundColor Cyan
Write-Host ""
Write-Host "Pour activer le venv dans un nouveau terminal:" -ForegroundColor Yellow
Write-Host "  1. Ouvrez un nouveau PowerShell" -ForegroundColor Gray
Write-Host "  2. Naviguez vers: $projectRoot" -ForegroundColor Gray
Write-Host "  3. Exécutez: .\.venv\Scripts\Activate.ps1" -ForegroundColor Gray
Write-Host ""
Write-Host "Note: Les scripts npm utilisent automatiquement le venv." -ForegroundColor Green
Write-Host "      Vous n'avez besoin d'activer manuellement que si vous" -ForegroundColor Gray
Write-Host "      exécutez des commandes Python directement." -ForegroundColor Gray
Write-Host ""

# Vérifier si déjà activé
if ($env:VIRTUAL_ENV) {
    Write-Host "ℹ️  Un venv est déjà activé dans cette session:" -ForegroundColor Cyan
    Write-Host "   $env:VIRTUAL_ENV" -ForegroundColor Gray
    Write-Host ""
    $response = Read-Host "Voulez-vous activer le venv du projet ? (o/N)"
    if ($response -ne "o" -and $response -ne "O") {
        Write-Host "Activation annulée." -ForegroundColor Yellow
        exit 0
    }
}

# Activer le venv
Write-Host "Activation du venv..." -ForegroundColor Cyan
& $activateScript

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Venv activé avec succès !" -ForegroundColor Green
    Write-Host ""
    Write-Host "Pour désactiver: deactivate" -ForegroundColor Gray
} else {
    Write-Host ""
    Write-Host "❌ Erreur lors de l'activation du venv" -ForegroundColor Red
    exit 1
}
