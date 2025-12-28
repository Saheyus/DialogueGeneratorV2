# Script pour lancer l'API en mode debug (sans ngrok)
# Verifie si ngrok tourne deja et vous avertit
# Usage: .\scripts\start-debug.ps1

param(
    [string]$ProjectPath = $PSScriptRoot,
    [int]$ApiPort = 4243  # Port debug (different du port production)
)

# Determiner le chemin du projet (parent du dossier scripts)
if ($ProjectPath -eq $PSScriptRoot) {
    $ProjectPath = Split-Path -Parent $PSScriptRoot
}

Write-Host "[*] Mode DEBUG - Demarrage de l'API uniquement" -ForegroundColor Cyan
Write-Host "[*] Port debug : $ApiPort (production utilise 4242)" -ForegroundColor Gray
Write-Host "[*] Repertoire projet: $ProjectPath" -ForegroundColor Gray

# Fonction pour verifier si un port est utilise
function Test-Port {
    param([int]$Port)
    try {
        $connection = Test-NetConnection -ComputerName localhost -Port $Port -InformationLevel Quiet -WarningAction SilentlyContinue
        return $connection
    } catch {
        return $false
    }
}

# Verifier si l'API tourne deja
$apiRunning = Test-Port -Port $ApiPort

if ($apiRunning) {
    Write-Host "[!] L'API tourne deja sur le port $ApiPort" -ForegroundColor Yellow
    Write-Host "[*] Voulez-vous vraiment redemarrer ? (O/N)" -ForegroundColor Yellow
    $response = Read-Host
    if ($response -ne "O" -and $response -ne "o") {
        Write-Host "[*] Annule" -ForegroundColor Red
        exit 0
    }
    
    # Trouver et arreter le processus
    Write-Host "[*] Arret de l'instance existante..." -ForegroundColor Yellow
    $processes = Get-NetTCPConnection -LocalPort $ApiPort -ErrorAction SilentlyContinue | 
        Select-Object -ExpandProperty OwningProcess -Unique
    
    foreach ($pid in $processes) {
        try {
            Stop-Process -Id $pid -Force -ErrorAction Stop
            Write-Host "[+] Processus $pid arrete" -ForegroundColor Green
        } catch {
            Write-Host "[!] Impossible d'arreter le processus $pid" -ForegroundColor Yellow
        }
    }
    
    Start-Sleep -Seconds 2
}

# Verifier si ngrok tourne
$ngrokRunning = Test-Port -Port 4040

if ($ngrokRunning) {
    Write-Host "[*] Ngrok semble tourner (port 4040 utilise)" -ForegroundColor Cyan
    Write-Host "[*] L'API sera accessible via ngrok ET en local" -ForegroundColor Gray
    Write-Host "[*] Interface ngrok : http://localhost:4040" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "[*] Demarrage de l'API en mode debug..." -ForegroundColor Green
Write-Host "[*] L'API sera accessible sur : http://localhost:$ApiPort" -ForegroundColor Cyan
Write-Host "[*] Appuyez sur Ctrl+C pour arreter" -ForegroundColor Gray
Write-Host ""

# Lancer l'API (en avant-plan pour voir les logs)
if (-not (Test-Path $ProjectPath)) {
    Write-Host "[!] Repertoire projet non trouve : $ProjectPath" -ForegroundColor Red
    exit 1
}

Set-Location $ProjectPath
$env:API_PORT = $ApiPort
Write-Host "[*] Port API defini a : $ApiPort (mode debug)" -ForegroundColor Gray
python -m api.main


