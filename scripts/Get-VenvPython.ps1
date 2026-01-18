# Fonction pour obtenir le chemin de l'interpréteur Python du venv
# Usage: $pythonPath = Get-VenvPython
# Usage dans un script: . .\scripts\Get-VenvPython.ps1; $python = Get-VenvPython

function Get-VenvPython {
    <#
    .SYNOPSIS
    Retourne le chemin de l'interpréteur Python du venv.
    
    .DESCRIPTION
    Détecte automatiquement le venv (.venv ou venv) et retourne le chemin
    de l'interpréteur Python. Si le venv n'existe pas, retourne 'python'
    avec un avertissement.
    
    .PARAMETER ProjectRoot
    Chemin racine du projet (optionnel, par défaut: parent du dossier scripts)
    
    .PARAMETER Quiet
    Supprime les avertissements si le venv n'est pas trouvé
    
    .EXAMPLE
    $python = Get-VenvPython
    & $python -m api.main
    
    .EXAMPLE
    . .\scripts\Get-VenvPython.ps1
    $python = Get-VenvPython -Quiet
    & $python -m pytest tests/
    #>
    
    param(
        [string]$ProjectRoot = $null,
        [switch]$Quiet = $false
    )
    
    # Déterminer le chemin racine du projet
    if (-not $ProjectRoot) {
        $ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
    }
    
    # Chemins possibles pour le venv
    $venvPaths = @(
        (Join-Path $ProjectRoot ".venv\Scripts\python.exe"),
        (Join-Path $ProjectRoot "venv\Scripts\python.exe")
    )
    
    # Chercher le premier chemin existant
    foreach ($venvPath in $venvPaths) {
        if (Test-Path $venvPath) {
            return $venvPath
        }
    }
    
    # Fallback: Python global
    if (-not $Quiet) {
        Write-Host "⚠️  Venv non trouvé, utilisation de Python global" -ForegroundColor Yellow
        Write-Host "   Créez le venv avec: npm run setup" -ForegroundColor Gray
    }
    
    return "python"
}

function Test-VenvExists {
    <#
    .SYNOPSIS
    Vérifie si le venv existe.
    
    .PARAMETER ProjectRoot
    Chemin racine du projet (optionnel)
    
    .EXAMPLE
    if (Test-VenvExists) {
        Write-Host "Venv trouvé"
    }
    #>
    
    param(
        [string]$ProjectRoot = $null
    )
    
    if (-not $ProjectRoot) {
        $ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
    }
    
    $venvDirs = @(
        (Join-Path $ProjectRoot ".venv"),
        (Join-Path $ProjectRoot "venv")
    )
    
    foreach ($venvDir in $venvDirs) {
        if (Test-Path $venvDir) {
            return $true
        }
    }
    
    return $false
}

# Si le script est exécuté directement (pas dotsourcé), afficher le chemin
if ($MyInvocation.InvocationName -ne '.') {
    Get-VenvPython
}
