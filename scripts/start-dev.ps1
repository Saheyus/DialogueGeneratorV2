# Script PowerShell simplifié pour démarrer le développement
# Lance backend + frontend ensemble

Write-Host "=== Démarrage DialogueGenerator (Dev) ===" -ForegroundColor Cyan

$projectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $projectRoot

# Vérifier Node.js
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "ERREUR: Node.js n'est pas installé" -ForegroundColor Red
    exit 1
}

# Vérifier Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "ERREUR: Python n'est pas installé" -ForegroundColor Red
    exit 1
}

# Installer les dépendances frontend si nécessaire
$frontendNodeModules = Join-Path $projectRoot "frontend" "node_modules"
if (-not (Test-Path $frontendNodeModules)) {
    Write-Host "Installation des dépendances frontend..." -ForegroundColor Yellow
    Set-Location (Join-Path $projectRoot "frontend")
    npm install
    Set-Location $projectRoot
}

$apiPort = if ($env:API_PORT) { $env:API_PORT } else { "4242" }
Write-Host "`nDémarrage des serveurs..." -ForegroundColor Green
Write-Host "  Backend API:  http://localhost:$apiPort" -ForegroundColor Gray
Write-Host "  Frontend:     http://localhost:3000" -ForegroundColor Gray
Write-Host "  API Docs:     http://localhost:$apiPort/api/docs" -ForegroundColor Gray
Write-Host "`nAppuyez sur Ctrl+C pour arrêter`n" -ForegroundColor Yellow

# Lancer backend et frontend en parallèle
$backendJob = Start-Job -ScriptBlock {
    Set-Location $using:projectRoot
    python -m api.main
}

$frontendJob = Start-Job -ScriptBlock {
    Set-Location (Join-Path $using:projectRoot "frontend")
    npm run dev
}

# Attendre et afficher les logs
try {
    while ($true) {
        Receive-Job -Job $backendJob, $frontendJob -ErrorAction SilentlyContinue | ForEach-Object {
            Write-Host $_
        }
        Start-Sleep -Milliseconds 500
        
        if ($backendJob.State -eq "Failed" -or $frontendJob.State -eq "Failed") {
            break
        }
    }
} finally {
    Write-Host "`nArrêt des serveurs..." -ForegroundColor Yellow
    Stop-Job -Job $backendJob, $frontendJob -ErrorAction SilentlyContinue
    Remove-Job -Job $backendJob, $frontendJob -ErrorAction SilentlyContinue
}

