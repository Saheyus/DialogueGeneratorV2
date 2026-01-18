# Script pour vérifier que le venv est correctement configuré
# Usage: .\scripts\verify-venv.ps1
# Ou via npm: npm run verify:venv

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

Write-Host ""
Write-Host "=== Vérification du venv Python ===" -ForegroundColor Cyan
Write-Host "Projet: $projectRoot" -ForegroundColor Gray
Write-Host ""

# Importer la fonction Get-VenvPython
. (Join-Path $projectRoot "scripts\Get-VenvPython.ps1")

$allChecks = $true

# 1. Vérifier que le venv existe
Write-Host "[1/5] Vérification de l'existence du venv..." -ForegroundColor Cyan
$venvPath = Join-Path $projectRoot ".venv"
if (Test-Path $venvPath) {
    Write-Host "  ✅ Venv trouvé: $venvPath" -ForegroundColor Green
} else {
    Write-Host "  ❌ Venv non trouvé" -ForegroundColor Red
    Write-Host "     Créez-le avec: npm run setup" -ForegroundColor Yellow
    $allChecks = $false
    exit 1
}

# 2. Vérifier que Python existe dans le venv
Write-Host ""
Write-Host "[2/5] Vérification de l'exécutable Python..." -ForegroundColor Cyan
$pythonExe = Get-VenvPython -ProjectRoot $projectRoot -Quiet
if (Test-Path $pythonExe) {
    Write-Host "  ✅ Python trouvé: $pythonExe" -ForegroundColor Green
} else {
    Write-Host "  ❌ Python non trouvé dans le venv" -ForegroundColor Red
    $allChecks = $false
}

# 3. Vérifier la version Python
Write-Host ""
Write-Host "[3/5] Vérification de la version Python..." -ForegroundColor Cyan
try {
    $pythonVersion = & $pythonExe --version 2>&1
    Write-Host "  ✅ $pythonVersion" -ForegroundColor Green
    
    # Vérifier que c'est Python 3.10+
    if ($pythonVersion -match "Python (\d+)\.(\d+)") {
        $major = [int]$matches[1]
        $minor = [int]$matches[2]
        if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 10)) {
            Write-Host "  ⚠️  Version Python < 3.10 (recommandé: 3.10+)" -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host "  ❌ Impossible de vérifier la version Python" -ForegroundColor Red
    $allChecks = $false
}

# 4. Vérifier pip
Write-Host ""
Write-Host "[4/5] Vérification de pip..." -ForegroundColor Cyan
try {
    $pipVersion = & $pythonExe -m pip --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ pip disponible: $pipVersion" -ForegroundColor Green
    } else {
        Write-Host "  ❌ pip non disponible dans le venv" -ForegroundColor Red
        $allChecks = $false
    }
} catch {
    Write-Host "  ❌ Erreur lors de la vérification de pip" -ForegroundColor Red
    $allChecks = $false
}

# 5. Vérifier les dépendances principales
Write-Host ""
Write-Host "[5/5] Vérification des dépendances principales..." -ForegroundColor Cyan

$requiredPackages = @(
    "fastapi",
    "uvicorn",
    "pytest",
    "openai",
    "pydantic",
    "pytest-asyncio"
)

$missingPackages = @()
$installedPackages = @()

foreach ($package in $requiredPackages) {
    try {
        $result = & $pythonExe -m pip show $package 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✅ $package installé" -ForegroundColor Green
            $installedPackages += $package
        } else {
            Write-Host "  ❌ $package non installé" -ForegroundColor Red
            $missingPackages += $package
            $allChecks = $false
        }
    } catch {
        Write-Host "  ❌ $package non installé" -ForegroundColor Red
        $missingPackages += $package
        $allChecks = $false
    }
}

# Résumé final
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
if ($allChecks) {
    Write-Host "  ✅ Toutes les vérifications ont réussi !" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Le venv est correctement configuré." -ForegroundColor Green
    Write-Host "Vous pouvez démarrer le développement avec: npm run dev" -ForegroundColor Gray
    Write-Host ""
    exit 0
} else {
    Write-Host "  ⚠️  Certaines vérifications ont échoué" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    
    if ($missingPackages.Count -gt 0) {
        Write-Host "Packages manquants:" -ForegroundColor Yellow
        foreach ($pkg in $missingPackages) {
            Write-Host "  - $pkg" -ForegroundColor Gray
        }
        Write-Host ""
        Write-Host "Pour installer les dépendances manquantes:" -ForegroundColor Yellow
        Write-Host "  & $pythonExe -m pip install -r requirements.txt" -ForegroundColor Cyan
        Write-Host ""
    }
    
    Write-Host "Pour recréer le venv complètement:" -ForegroundColor Yellow
    Write-Host "  npm run setup" -ForegroundColor Cyan
    Write-Host ""
    exit 1
}
