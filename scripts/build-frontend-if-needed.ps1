# Script pour builder le frontend uniquement si necessaire
# Verifie les dates de modification pour determiner si un rebuild est necessaire
# Usage: .\scripts\build-frontend-if-needed.ps1 -ProjectPath . -NgrokUrl "https://..."

param(
    [string]$ProjectPath = $PSScriptRoot,
    [string]$NgrokUrl = "",
    [switch]$Force = $false
)

# Determiner le chemin du projet (parent du dossier scripts)
if ($ProjectPath -eq $PSScriptRoot) {
    $ProjectPath = Split-Path -Parent $PSScriptRoot
}

$frontendPath = Join-Path $ProjectPath "frontend"
$distPath = Join-Path $frontendPath "dist"
$distIndexPath = Join-Path $distPath "index.html"
$packageJsonPath = Join-Path $frontendPath "package.json"

# Verifier que le repertoire frontend existe
if (-not (Test-Path $frontendPath)) {
    Write-Host "[!] Repertoire frontend non trouve : $frontendPath" -ForegroundColor Red
    exit 1
}

# Si force, builder directement
if ($Force) {
    Write-Host "[*] Build force demande..." -ForegroundColor Yellow
    $shouldBuild = $true
} elseif (-not (Test-Path $distIndexPath)) {
    # Pas de dist/index.html, il faut builder
    Write-Host "[*] frontend/dist/index.html n'existe pas, build necessaire" -ForegroundColor Yellow
    $shouldBuild = $true
} else {
    # Verifier les dates de modification
    $distDate = (Get-Item $distIndexPath).LastWriteTime
    $packageJsonDate = (Get-Item $packageJsonPath).LastWriteTime
    
    # Verifier aussi les fichiers sources (src/)
    $srcPath = Join-Path $frontendPath "src"
    $latestSourceDate = $packageJsonDate
    if (Test-Path $srcPath) {
        $sourceFiles = Get-ChildItem -Path $srcPath -Recurse -File | Where-Object { $_.Extension -match '\.(ts|tsx|js|jsx|css)$' }
        foreach ($file in $sourceFiles) {
            if ($file.LastWriteTime -gt $latestSourceDate) {
                $latestSourceDate = $file.LastWriteTime
            }
        }
    }
    
    # Builder si les sources sont plus recentes que le dist
    if ($latestSourceDate -gt $distDate) {
        Write-Host "[*] Sources plus recentes que le build, rebuild necessaire" -ForegroundColor Yellow
        Write-Host "    Derniere modification source: $latestSourceDate" -ForegroundColor Gray
        Write-Host "    Derniere modification dist: $distDate" -ForegroundColor Gray
        $shouldBuild = $true
    } else {
        Write-Host "[+] Build a jour, pas besoin de rebuilder" -ForegroundColor Green
        Write-Host "    Derniere modification source: $latestSourceDate" -ForegroundColor Gray
        Write-Host "    Derniere modification dist: $distDate" -ForegroundColor Gray
        $shouldBuild = $false
    }
}

if ($shouldBuild) {
    Write-Host "[*] Demarrage du build du frontend..." -ForegroundColor Cyan
    
    # Configurer VITE_API_BASE_URL si URL ngrok fournie
    if ($NgrokUrl) {
        $env:VITE_API_BASE_URL = $NgrokUrl
        Write-Host "[*] Configuration VITE_API_BASE_URL=$NgrokUrl" -ForegroundColor Gray
    }
    
    # Executer le build
    Set-Location $ProjectPath
    
    try {
        # Utiliser le script de build existant
        $buildScript = Join-Path $ProjectPath "scripts\build_production.ps1"
        if (Test-Path $buildScript) {
            & $buildScript
        } else {
            # Fallback: build manuel
            Set-Location $frontendPath
            npm run build
        }
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[+] Build du frontend termine avec succes" -ForegroundColor Green
            exit 0
        } else {
            Write-Host "[!] Erreur lors du build du frontend" -ForegroundColor Red
            exit 1
        }
    } catch {
        Write-Host "[!] Exception lors du build : $_" -ForegroundColor Red
        exit 1
    }
} else {
    exit 0
}


