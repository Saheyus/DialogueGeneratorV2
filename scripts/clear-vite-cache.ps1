# Script de nettoyage du cache Vite
# Supprime le cache Vite et les fichiers de build pour garantir un rafraîchissement propre
# Usage: .\scripts\clear-vite-cache.ps1
# Ou via npm: npm run dev:clean

Write-Host "=== Nettoyage du cache Vite ===" -ForegroundColor Cyan

# Vérifier que nous sommes dans le bon répertoire
$projectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $projectRoot

Write-Host "Répertoire projet: $projectRoot" -ForegroundColor Gray

# Chemin vers le cache Vite
$viteCachePath = Join-Path $projectRoot "frontend" "node_modules" ".vite"
$distPath = Join-Path $projectRoot "frontend" "dist"

# Supprimer le cache Vite
if (Test-Path $viteCachePath) {
    Write-Host "`nSuppression du cache Vite: $viteCachePath" -ForegroundColor Yellow
    try {
        Remove-Item -Path $viteCachePath -Recurse -Force -ErrorAction Stop
        Write-Host "✅ Cache Vite supprimé" -ForegroundColor Green
    } catch {
        Write-Host "⚠️  Erreur lors de la suppression du cache Vite: $_" -ForegroundColor Red
    }
} else {
    Write-Host "ℹ️  Cache Vite introuvable (déjà propre)" -ForegroundColor Gray
}

# Supprimer le dossier dist si présent
if (Test-Path $distPath) {
    Write-Host "`nSuppression du dossier dist: $distPath" -ForegroundColor Yellow
    try {
        Remove-Item -Path $distPath -Recurse -Force -ErrorAction Stop
        Write-Host "✅ Dossier dist supprimé" -ForegroundColor Green
    } catch {
        Write-Host "⚠️  Erreur lors de la suppression du dossier dist: $_" -ForegroundColor Red
    }
} else {
    Write-Host "ℹ️  Dossier dist introuvable (déjà propre)" -ForegroundColor Gray
}

# Optionnel: Nettoyer le cache npm (décommenter si nécessaire)
# Write-Host "`nNettoyage du cache npm..." -ForegroundColor Yellow
# npm cache clean --force
# Write-Host "✅ Cache npm nettoyé" -ForegroundColor Green

Write-Host "`n✅ Nettoyage terminé" -ForegroundColor Green
Write-Host "Vous pouvez maintenant lancer 'npm run dev' pour un démarrage propre" -ForegroundColor Gray
