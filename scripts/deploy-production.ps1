# Script de déploiement en production
# Build le frontend et upload sur le serveur
# Usage: .\scripts\deploy-production.ps1 [-SkipBuild] [-SkipRestart] [-ServerHost "137.74.115.203"] [-ServerUser "ubuntu"]

param(
    [switch]$SkipBuild = $false,
    [switch]$SkipRestart = $false,
    [string]$ServerHost = "137.74.115.203",
    [string]$ServerUser = "ubuntu",
    [string]$ServerPath = "/opt/DialogueGeneratorV2"
)

$ErrorActionPreference = "Stop"

# Couleurs pour la sortie
function Write-Info { Write-Host "[INFO] $args" -ForegroundColor Cyan }
function Write-Success { Write-Host "[SUCCESS] $args" -ForegroundColor Green }
function Write-Warning { Write-Host "[WARNING] $args" -ForegroundColor Yellow }
function Write-Error { Write-Host "[ERROR] $args" -ForegroundColor Red }

Write-Host "`n=== Déploiement en Production ===" -ForegroundColor Cyan
Write-Info "Serveur: ${ServerUser}@${ServerHost}"
Write-Info "Chemin serveur: $ServerPath"
Write-Host ""

# Vérifier que nous sommes dans le bon répertoire
$projectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $projectRoot
Write-Info "Répertoire projet: $projectRoot"

# Vérifier que SCP est disponible (OpenSSH)
$scpAvailable = Get-Command scp -ErrorAction SilentlyContinue
if (-not $scpAvailable) {
    Write-Error "SCP n'est pas disponible. Installez OpenSSH Client (Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0)"
    exit 1
}

# Vérifier que SSH est disponible
$sshAvailable = Get-Command ssh -ErrorAction SilentlyContinue
if (-not $sshAvailable) {
    Write-Error "SSH n'est pas disponible. Installez OpenSSH Client"
    exit 1
}

# Étape 1: Build du frontend
if (-not $SkipBuild) {
    Write-Host "`n=== Étape 1: Build du frontend ===" -ForegroundColor Cyan
    
    # Vérifier que Node.js est installé
    $nodeVersion = node --version 2>$null
    if (-not $nodeVersion) {
        Write-Error "Node.js n'est pas installé ou pas dans le PATH"
        exit 1
    }
    Write-Info "Node.js version: $nodeVersion"
    
    # Aller dans le dossier frontend
    $frontendPath = Join-Path $projectRoot "frontend"
    if (-not (Test-Path $frontendPath)) {
        Write-Error "Le dossier frontend n'existe pas"
        exit 1
    }
    
    Set-Location $frontendPath
    
    # Installer les dépendances si nécessaire
    Write-Info "Vérification des dépendances..."
    npm install --silent
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Échec de l'installation des dépendances"
        exit 1
    }
    
    # Build
    Write-Info "Build du frontend en cours..."
    npm run build
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Échec du build"
        exit 1
    }
    
    # Vérifier que le dossier dist existe
    $distPath = Join-Path $frontendPath "dist"
    if (-not (Test-Path $distPath)) {
        Write-Error "Le dossier dist n'a pas été créé"
        exit 1
    }
    
    Write-Success "Build terminé avec succès"
    Write-Info "Fichiers dans: $distPath"
} else {
    Write-Warning "Build ignoré (--SkipBuild)"
    $frontendPath = Join-Path $projectRoot "frontend"
    $distPath = Join-Path $frontendPath "dist"
    
    if (-not (Test-Path $distPath)) {
        Write-Error "Le dossier dist n'existe pas. Lancez le build d'abord."
        exit 1
    }
}

# Étape 2: Upload du build sur le serveur
Write-Host "`n=== Étape 2: Upload du build sur le serveur ===" -ForegroundColor Cyan

# Créer un dossier temporaire pour l'upload
$tempDir = Join-Path $env:TEMP "dialogue-generator-deploy-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
Write-Info "Dossier temporaire: $tempDir"

# Copier le contenu de dist dans le dossier temporaire
Write-Info "Préparation des fichiers pour l'upload..."
Copy-Item -Path "$distPath\*" -Destination $tempDir -Recurse -Force

# Compter les fichiers
$fileCount = (Get-ChildItem -Path $tempDir -Recurse -File).Count
Write-Info "$fileCount fichiers à uploader"

# Upload via SCP
Write-Info "Upload en cours sur ${ServerUser}@${ServerHost}:${ServerPath}/frontend/dist/..."
Write-Warning "Cela peut prendre quelques minutes..."

$scpCommand = "scp -r `"$tempDir\*`" ${ServerUser}@${ServerHost}:${ServerPath}/frontend/dist/"
Invoke-Expression $scpCommand

if ($LASTEXITCODE -ne 0) {
    Write-Error "Échec de l'upload"
    Remove-Item -Path $tempDir -Recurse -Force -ErrorAction SilentlyContinue
    exit 1
}

Write-Success "Upload terminé avec succès"

# Nettoyer le dossier temporaire
Remove-Item -Path $tempDir -Recurse -Force -ErrorAction SilentlyContinue

# Étape 3: Redémarrer le service (optionnel)
if (-not $SkipRestart) {
    Write-Host "`n=== Étape 3: Redémarrage du service ===" -ForegroundColor Cyan
    
    Write-Info "Redémarrage du service dialogue-generator..."
    $sshCommand = "ssh ${ServerUser}@${ServerHost} 'sudo systemctl restart dialogue-generator'"
    Invoke-Expression $sshCommand
    
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Échec du redémarrage du service (peut nécessiter une intervention manuelle)"
    } else {
        Write-Success "Service redémarré avec succès"
        
        # Attendre un peu pour que le service démarre
        Start-Sleep -Seconds 2
        
        # Vérifier le statut
        Write-Info "Vérification du statut du service..."
        $statusCommand = "ssh ${ServerUser}@${ServerHost} 'sudo systemctl status dialogue-generator --no-pager -l'"
        Invoke-Expression $statusCommand
    }
} else {
    Write-Warning "Redémarrage ignoré (--SkipRestart)"
    Write-Info "N'oubliez pas de redémarrer le service manuellement:"
    Write-Info "  ssh ${ServerUser}@${ServerHost}"
    Write-Info "  sudo systemctl restart dialogue-generator"
}

# Étape 4: Vérification
Write-Host "`n=== Étape 4: Vérification ===" -ForegroundColor Cyan

Write-Info "Vérification du health check..."
$healthUrl = "http://${ServerHost}/health"
try {
    $response = Invoke-WebRequest -Uri $healthUrl -Method Get -TimeoutSec 10 -UseBasicParsing -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        $health = $response.Content | ConvertFrom-Json
        if ($health.status -eq "healthy") {
            Write-Success "Health check: OK (status: $($health.status))"
        } else {
            Write-Warning "Health check: Degraded (status: $($health.status))"
        }
    }
} catch {
    Write-Warning "Impossible de vérifier le health check: $($_.Exception.Message)"
}

# Résumé
Write-Host "`n=== Déploiement terminé ===" -ForegroundColor Green
Write-Info "Frontend déployé sur: http://${ServerHost}"
Write-Info "API disponible sur: http://${ServerHost}/api"
Write-Info "Documentation API: http://${ServerHost}/api/docs"
Write-Host ""
