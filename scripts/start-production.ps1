# Script pour lancer ngrok + API automatiquement (production)
# Gere les conflits si l'API est deja lancee
# Usage: .\scripts\start-production.ps1
#
# PORTS UTILISES:
# - Production (ce script): 4242
# - Dev (npm run dev): 4243
# - Debug (start-debug.ps1): 4243

param(
    [string]$ProjectPath = $PSScriptRoot,
    [int]$ApiPort = 4242,  # Port production (dev utilise 4243)
    [string]$NgrokPath = ""
)

# Determiner le chemin du projet (parent du dossier scripts)
if ($ProjectPath -eq $PSScriptRoot) {
    $ProjectPath = Split-Path -Parent $PSScriptRoot
}

# Importer la fonction Get-VenvPython
. (Join-Path $ProjectPath "scripts\Get-VenvPython.ps1")

Write-Host "[*] Demarrage du frontend DialogueGenerator (Production)" -ForegroundColor Cyan
Write-Host "[*] Repertoire projet: $ProjectPath" -ForegroundColor Gray

# Fonction pour trouver ngrok
function Find-Ngrok {
    # D'abord, essayer de trouver dans le PATH (Microsoft Store, installation systeme, etc.)
    $ngrokInPath = Get-Command ngrok -ErrorAction SilentlyContinue
    if ($ngrokInPath) {
        return $ngrokInPath.Source
    }
    
    # Chercher dans les emplacements possibles
    $possiblePaths = @(
        "$env:LOCALAPPDATA\Microsoft\WindowsApps\ngrok.exe",  # Microsoft Store
        "$env:LOCALAPPDATA\ngrok\ngrok.exe",
        "$env:USERPROFILE\ngrok\ngrok.exe",
        "E:\CloudFlareTunnel\ngrok.exe",  # Ancien emplacement (au cas où)
        ".\ngrok.exe"
    )
    
    foreach ($path in $possiblePaths) {
        if (Test-Path $path) {
            return Resolve-Path $path
        }
    }
    
    return $null
}

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
    Write-Host "[*] Si vous voulez redemarrer, arretez d'abord l'instance existante" -ForegroundColor Yellow
    Write-Host "[*] Ngrok va quand meme se connecter a l'API existante" -ForegroundColor Gray
    $startApi = $false
} else {
    Write-Host "[+] Port $ApiPort libre, l'API sera demarree" -ForegroundColor Green
    $startApi = $true
}

# Verifier si ngrok tourne deja
$ngrokRunning = Test-Port -Port 4040
$ngrokUrl = $null

if ($ngrokRunning) {
    Write-Host "[!] Ngrok semble deja tourner (port 4040 utilise)" -ForegroundColor Yellow
    Write-Host "[*] Verifiez http://localhost:4040 pour voir l'interface ngrok" -ForegroundColor Gray
    $ngrokJob = $null
    
    # Recuperer l'URL ngrok existante
    try {
        $tunnels = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels" -ErrorAction Stop
        $ngrokUrl = $tunnels.tunnels[0].public_url
        Write-Host "[+] Frontend accessible via : $ngrokUrl" -ForegroundColor Green
    } catch {
        Write-Host "[!] Impossible de recuperer l'URL ngrok" -ForegroundColor Yellow
        $ngrokUrl = $null
    }
} else {
    Write-Host "[*] Demarrage de ngrok..." -ForegroundColor Cyan
    
    # Trouver ngrok
    if ($NgrokPath) {
        $ngrokPath = Resolve-Path $NgrokPath -ErrorAction SilentlyContinue
    } else {
        $ngrokPath = Find-Ngrok
    }
    
    if (-not $ngrokPath) {
        Write-Host "[!] ngrok.exe non trouve" -ForegroundColor Red
        Write-Host "[*] Cherche dans: PATH (Microsoft Store), %LOCALAPPDATA%\\Microsoft\\WindowsApps, %LOCALAPPDATA%\\ngrok" -ForegroundColor Yellow
        Write-Host "[*] Si ngrok est installe via Microsoft Store, il devrait etre dans le PATH" -ForegroundColor Yellow
        Write-Host "[*] Vous pouvez specifier le chemin avec -NgrokPath" -ForegroundColor Yellow
        exit 1
    }
    
    Write-Host "[*] Ngrok trouve: $ngrokPath" -ForegroundColor Gray
    
    $ngrokJob = Start-Job -ScriptBlock {
        param($ngrokPath, $port)
        Set-Location (Split-Path $ngrokPath)
        & $ngrokPath http $port
    } -ArgumentList $ngrokPath, $ApiPort
    
    Start-Sleep -Seconds 3
    
    # Recuperer l'URL ngrok
    try {
        $tunnels = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels" -ErrorAction Stop
        $ngrokUrl = $tunnels.tunnels[0].public_url
        Write-Host "[+] Frontend accessible via : $ngrokUrl" -ForegroundColor Green
    } catch {
        Write-Host "[!] Ngrok demarre mais impossible de recuperer l'URL (verifiez http://localhost:4040)" -ForegroundColor Yellow
        $ngrokUrl = $null
    }
}

# Builder le frontend si necessaire
if ($ngrokUrl) {
    Write-Host ""
    Write-Host "[*] Verification du build du frontend..." -ForegroundColor Cyan
    $buildScript = Join-Path $ProjectPath "scripts\build-frontend-if-needed.ps1"
    if (Test-Path $buildScript) {
        & $buildScript -ProjectPath $ProjectPath -NgrokUrl $ngrokUrl
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[!] Erreur lors du build du frontend, continuons quand meme..." -ForegroundColor Yellow
        }
    } else {
        Write-Host "[!] Script build-frontend-if-needed.ps1 non trouve, build manuel necessaire" -ForegroundColor Yellow
    }
} else {
    Write-Host "[!] URL ngrok non disponible, build du frontend ignore" -ForegroundColor Yellow
    Write-Host "[*] Le frontend utilisera des URLs relatives" -ForegroundColor Gray
}

Write-Host ""

# Demarrer l'API si necessaire
if ($startApi) {
    Write-Host "[*] Demarrage de l'API..." -ForegroundColor Cyan
    
    if (-not (Test-Path $ProjectPath)) {
        Write-Host "[!] Repertoire projet non trouve : $ProjectPath" -ForegroundColor Red
        exit 1
    }
    
    $apiJob = Start-Job -ScriptBlock {
        param($projectPath, $port, $pythonPath)
        $env:API_PORT = $port
        Set-Location $projectPath
        & $pythonPath -m api.main
    } -ArgumentList $ProjectPath, $ApiPort, (Get-VenvPython -ProjectRoot $ProjectPath -Quiet)
    
    Write-Host "[+] API demarree (job ID: $($apiJob.Id))" -ForegroundColor Green
    Write-Host "[*] Pour voir les logs de l'API, utilisez: Receive-Job -Id $($apiJob.Id) -Keep" -ForegroundColor Gray
} else {
    Write-Host "[*] API non demarree (deja en cours d'execution)" -ForegroundColor Yellow
    $apiJob = $null
}

Write-Host ""
Write-Host "[+] Tout est pret !" -ForegroundColor Green
Write-Host ""
if ($ngrokUrl) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  FRONTEND ACCESSIBLE A :" -ForegroundColor Green
    Write-Host "  $ngrokUrl" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "[*] C'est l'URL ou vous travaillez (frontend)" -ForegroundColor Gray
    Write-Host "[*] Interface ngrok (debug) : http://localhost:4040" -ForegroundColor Gray
} else {
    Write-Host "[!] URL ngrok non disponible" -ForegroundColor Yellow
    Write-Host "[*] Frontend local : http://localhost:$ApiPort" -ForegroundColor Cyan
}
Write-Host ""
Write-Host "[*] Pour arreter : Ctrl+C ou fermer cette fenetre" -ForegroundColor Gray
Write-Host ""

# Attendre et afficher les logs
try {
    while ($true) {
        Start-Sleep -Seconds 5
        
        # Verifier que ngrok tourne toujours
        if ($ngrokJob -and (Get-Job -Id $ngrokJob.Id -ErrorAction SilentlyContinue).State -eq "Failed") {
            Write-Host "[!] Ngrok s'est arrete" -ForegroundColor Red
            break
        }
        
        # Verifier que l'API tourne toujours (si on l'a demarree)
        if ($startApi -and $apiJob -and (Get-Job -Id $apiJob.Id -ErrorAction SilentlyContinue).State -eq "Failed") {
            Write-Host "[!] L'API s'est arretee" -ForegroundColor Red
            break
        }
    }
} catch {
    Write-Host ""
    Write-Host "[*] Arret..." -ForegroundColor Yellow
} finally {
    # Nettoyage
    if ($ngrokJob) {
        Stop-Job $ngrokJob -ErrorAction SilentlyContinue
        Remove-Job $ngrokJob -ErrorAction SilentlyContinue
    }
    if ($apiJob) {
        Stop-Job $apiJob -ErrorAction SilentlyContinue
        Remove-Job $apiJob -ErrorAction SilentlyContinue
    }
}

