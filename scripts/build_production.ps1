# Script de build pour production
# Build le frontend React et prépare les fichiers pour déploiement
# Usage: .\scripts\build_production.ps1
# Ou via npm: npm run deploy:build

Write-Host "=== Build Production ===" -ForegroundColor Cyan

# Vérifier que nous sommes dans le bon répertoire
$projectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $projectRoot

Write-Host "Répertoire projet: $projectRoot" -ForegroundColor Gray

# Vérifier que Node.js est installé
$nodeVersion = node --version 2>$null
if (-not $nodeVersion) {
    Write-Host "ERREUR: Node.js n'est pas installé ou pas dans le PATH" -ForegroundColor Red
    exit 1
}
Write-Host "Node.js version: $nodeVersion" -ForegroundColor Gray

# Vérifier que npm est installé
$npmVersion = npm --version 2>$null
if (-not $npmVersion) {
    Write-Host "ERREUR: npm n'est pas installé ou pas dans le PATH" -ForegroundColor Red
    exit 1
}
Write-Host "npm version: $npmVersion" -ForegroundColor Gray

# Aller dans le dossier frontend
$frontendPath = Join-Path $projectRoot "frontend"
if (-not (Test-Path $frontendPath)) {
    Write-Host "ERREUR: Le dossier frontend n'existe pas" -ForegroundColor Red
    exit 1
}

Set-Location $frontendPath
Write-Host "`n=== Installation des dépendances ===" -ForegroundColor Cyan
npm install

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERREUR: Échec de l'installation des dépendances" -ForegroundColor Red
    exit 1
}

Write-Host "`n=== Build du frontend ===" -ForegroundColor Cyan
npm run build

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERREUR: Échec du build" -ForegroundColor Red
    exit 1
}

# Vérifier que le dossier dist existe
$distPath = Join-Path $frontendPath "dist"
if (-not (Test-Path $distPath)) {
    Write-Host "ERREUR: Le dossier dist n'a pas été créé" -ForegroundColor Red
    exit 1
}

Write-Host "`n=== Build terminé avec succès ===" -ForegroundColor Green
Write-Host "Fichiers de production dans: $distPath" -ForegroundColor Gray

# Lister quelques fichiers pour vérification
$files = Get-ChildItem -Path $distPath -File -Recurse | Select-Object -First 5
Write-Host "`nPremiers fichiers générés:" -ForegroundColor Gray
foreach ($file in $files) {
    Write-Host "  - $($file.Name)" -ForegroundColor Gray
}

Write-Host "`n=== Build production terminé ===" -ForegroundColor Green

