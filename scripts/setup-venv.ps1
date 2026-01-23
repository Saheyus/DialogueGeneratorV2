# Script pour créer et configurer le venv Python
# Usage: .\scripts\setup-venv.ps1

param(
    [switch]$Force = $false,
    [switch]$SkipInstall = $false
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$venvPath = Join-Path $projectRoot ".venv"
$requirementsFile = Join-Path $projectRoot "requirements.txt"

Write-Host ""
Write-Host "=== Configuration du venv Python ===" -ForegroundColor Cyan
Write-Host "Projet: $projectRoot" -ForegroundColor Gray
Write-Host ""

# Vérifier que Python est installé
Write-Host "[1/5] Vérification de Python..." -ForegroundColor Cyan
try {
    $pythonVersion = & python --version 2>&1
    Write-Host "  ✅ Python trouvé: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Python n'est pas installé ou pas dans le PATH" -ForegroundColor Red
    Write-Host ""
    Write-Host "Installez Python 3.10+ depuis: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

# Vérifier si le venv existe déjà
if (Test-Path $venvPath) {
    if ($Force) {
        Write-Host ""
        Write-Host "⚠️  Le venv existe déjà et sera supprimé (-Force)" -ForegroundColor Yellow
        Remove-Item -Recurse -Force $venvPath
        Write-Host "  ✅ Ancien venv supprimé" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "ℹ️  Le venv existe déjà: $venvPath" -ForegroundColor Cyan
        Write-Host ""
        $response = Read-Host "Voulez-vous le recréer ? Cela supprimera tous les packages installés (o/N)"
        if ($response -eq "o" -or $response -eq "O") {
            Remove-Item -Recurse -Force $venvPath
            Write-Host "  ✅ Ancien venv supprimé" -ForegroundColor Green
        } else {
            Write-Host ""
            Write-Host "✅ Venv existant conservé" -ForegroundColor Green
            
            if (-not $SkipInstall) {
                Write-Host ""
                Write-Host "[5/5] Mise à jour des dépendances..." -ForegroundColor Cyan
                $pythonExe = Join-Path $venvPath "Scripts\python.exe"
                & $pythonExe -m pip install --upgrade pip
                & $pythonExe -m pip install -r $requirementsFile
                
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "  ✅ Dépendances mises à jour" -ForegroundColor Green
                } else {
                    Write-Host "  ❌ Erreur lors de la mise à jour des dépendances" -ForegroundColor Red
                    exit 1
                }
            }
            
            Write-Host ""
            Write-Host "✅ Configuration terminée !" -ForegroundColor Green
            Write-Host ""
            Write-Host "Les scripts npm utilisent automatiquement le venv." -ForegroundColor Gray
            Write-Host "Pour activer manuellement: .\scripts\activate-venv.ps1" -ForegroundColor Gray
            exit 0
        }
    }
}

# Créer le venv
Write-Host ""
Write-Host "[2/5] Création du venv..." -ForegroundColor Cyan
try {
    & python -m venv $venvPath
    if ($LASTEXITCODE -ne 0) {
        throw "Erreur lors de la création du venv"
    }
    Write-Host "  ✅ Venv créé: $venvPath" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Erreur: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Assurez-vous que le module venv est installé:" -ForegroundColor Yellow
    Write-Host "  python -m pip install --upgrade pip" -ForegroundColor Cyan
    exit 1
}

# Vérifier que le venv a été créé correctement
$pythonExe = Join-Path $venvPath "Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    Write-Host "  ❌ L'exécutable Python n'a pas été créé: $pythonExe" -ForegroundColor Red
    exit 1
}

# Mettre à jour pip
Write-Host ""
Write-Host "[3/5] Mise à jour de pip..." -ForegroundColor Cyan
try {
    & $pythonExe -m pip install --upgrade pip --quiet
    if ($LASTEXITCODE -ne 0) {
        throw "Erreur lors de la mise à jour de pip"
    }
    $pipVersion = & $pythonExe -m pip --version
    Write-Host "  ✅ pip mis à jour: $pipVersion" -ForegroundColor Green
} catch {
    Write-Host "  ⚠️  Avertissement: Erreur lors de la mise à jour de pip" -ForegroundColor Yellow
    Write-Host "  Continuons quand même..." -ForegroundColor Gray
}

# Installer les dépendances
if (-not $SkipInstall) {
    Write-Host ""
    Write-Host "[4/5] Installation des dépendances..." -ForegroundColor Cyan
    
    if (-not (Test-Path $requirementsFile)) {
        Write-Host "  ⚠️  Fichier requirements.txt non trouvé" -ForegroundColor Yellow
        Write-Host "  Les dépendances devront être installées manuellement" -ForegroundColor Gray
    } else {
        Write-Host "  Installation depuis: requirements.txt" -ForegroundColor Gray
        Write-Host "  Cela peut prendre quelques minutes..." -ForegroundColor Gray
        Write-Host ""
        
        try {
            & $pythonExe -m pip install -r $requirementsFile
            if ($LASTEXITCODE -ne 0) {
                throw "Erreur lors de l'installation des dépendances"
            }
            Write-Host ""
            Write-Host "  ✅ Dépendances installées avec succès" -ForegroundColor Green
        } catch {
            Write-Host ""
            Write-Host "  ❌ Erreur lors de l'installation des dépendances" -ForegroundColor Red
            Write-Host "  Vous pouvez réessayer avec:" -ForegroundColor Yellow
            Write-Host "    .\.venv\Scripts\python.exe -m pip install -r requirements.txt" -ForegroundColor Cyan
            exit 1
        }
    }
} else {
    Write-Host ""
    Write-Host "[4/5] Installation des dépendances ignorée (-SkipInstall)" -ForegroundColor Yellow
}

# Vérification finale
Write-Host ""
Write-Host "[5/5] Vérification de l'installation..." -ForegroundColor Cyan

$packagesToCheck = @("fastapi", "pytest", "openai", "pydantic")
$allInstalled = $true

foreach ($package in $packagesToCheck) {
    try {
        $result = & $pythonExe -m pip show $package 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✅ $package installé" -ForegroundColor Green
        } else {
            Write-Host "  ⚠️  $package non installé" -ForegroundColor Yellow
            $allInstalled = $false
        }
    } catch {
        Write-Host "  ⚠️  $package non installé" -ForegroundColor Yellow
        $allInstalled = $false
    }
}

# Résumé final
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
if ($allInstalled) {
    Write-Host "  ✅ Configuration terminée avec succès !" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  Configuration terminée avec avertissements" -ForegroundColor Yellow
}
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Chemin du venv: $venvPath" -ForegroundColor Gray
Write-Host "Python: $pythonExe" -ForegroundColor Gray
Write-Host ""
Write-Host "Prochaines etapes:" -ForegroundColor Yellow
Write-Host "  * Les scripts npm utilisent automatiquement le venv" -ForegroundColor Gray
Write-Host "  * Pour activer manuellement: .\scripts\activate-venv.ps1" -ForegroundColor Gray
Write-Host "  * Pour verifier l'installation: npm run verify:venv" -ForegroundColor Gray
Write-Host "  * Pour demarrer le developpement: npm run dev" -ForegroundColor Gray
Write-Host ""
