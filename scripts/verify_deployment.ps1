# Script de vérification post-déploiement
# Vérifie que l'application déployée fonctionne correctement
# Usage: .\scripts\verify_deployment.ps1 [-BaseUrl "https://votre-domaine.com"]

param(
    [string]$BaseUrl = "http://localhost:4242"
)

Write-Host "=== Vérification de déploiement ===" -ForegroundColor Cyan
Write-Host "URL de base: $BaseUrl" -ForegroundColor Gray
Write-Host ""

$errors = @()
$warnings = @()
$success = @()

# Fonction pour faire une requête HTTP
function Invoke-HealthCheck {
    param(
        [string]$Url,
        [string]$Description
    )
    
    try {
        $response = Invoke-WebRequest -Uri $Url -Method Get -TimeoutSec 10 -UseBasicParsing -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            $content = $response.Content | ConvertFrom-Json
            return @{
                Success = $true
                StatusCode = $response.StatusCode
                Content = $content
            }
        } else {
            return @{
                Success = $false
                StatusCode = $response.StatusCode
                Content = $null
            }
        }
    } catch {
        return @{
            Success = $false
            StatusCode = $null
            Error = $_.Exception.Message
            Content = $null
        }
    }
}

# 1. Vérifier le health check basique
Write-Host "1. Vérification du health check basique..." -ForegroundColor Cyan
$healthUrl = "$BaseUrl/health"
$healthResult = Invoke-HealthCheck -Url $healthUrl -Description "Health check basique"

if ($healthResult.Success) {
    if ($healthResult.Content.status -eq "healthy") {
        Write-Host "  ✓ Health check: OK (status: $($healthResult.Content.status))" -ForegroundColor Green
        $success += "Health check basique"
    } else {
        Write-Host "  ⚠ Health check: Degraded (status: $($healthResult.Content.status))" -ForegroundColor Yellow
        $warnings += "Health check retourne un statut dégradé"
    }
} else {
    Write-Host "  ✗ Health check: ÉCHEC" -ForegroundColor Red
    if ($healthResult.Error) {
        Write-Host "    Erreur: $($healthResult.Error)" -ForegroundColor Red
    }
    $errors += "Health check basique inaccessible: $($healthResult.Error)"
}

# 2. Vérifier le health check détaillé
Write-Host "`n2. Vérification du health check détaillé..." -ForegroundColor Cyan
$detailedHealthUrl = "$BaseUrl/health/detailed"
$detailedResult = Invoke-HealthCheck -Url $detailedHealthUrl -Description "Health check détaillé"

if ($detailedResult.Success) {
    Write-Host "  ✓ Health check détaillé: OK" -ForegroundColor Green
    $success += "Health check détaillé"
    
    # Vérifier les dépendances
    if ($detailedResult.Content.checks) {
        Write-Host "  Vérification des dépendances:" -ForegroundColor Gray
        foreach ($check in $detailedResult.Content.checks) {
            $statusIcon = if ($check.status -eq "healthy") { "✓" } elseif ($check.status -eq "degraded") { "⚠" } else { "✗" }
            $statusColor = if ($check.status -eq "healthy") { "Green" } elseif ($check.status -eq "degraded") { "Yellow" } else { "Red" }
            Write-Host "    $statusIcon $($check.name): $($check.status)" -ForegroundColor $statusColor
            
            if ($check.status -ne "healthy") {
                if ($check.details) {
                    Write-Host "      Détails: $($check.details | ConvertTo-Json -Compress)" -ForegroundColor Gray
                }
                if ($check.status -eq "unhealthy") {
                    $errors += "$($check.name): $($check.message)"
                } else {
                    $warnings += "$($check.name): $($check.message)"
                }
            }
        }
    }
} else {
    Write-Host "  ✗ Health check détaillé: ÉCHEC" -ForegroundColor Red
    if ($detailedResult.Error) {
        Write-Host "    Erreur: $($detailedResult.Error)" -ForegroundColor Red
    }
    $errors += "Health check détaillé inaccessible: $($detailedResult.Error)"
}

# 3. Vérifier l'endpoint de documentation API
Write-Host "`n3. Vérification de la documentation API..." -ForegroundColor Cyan
$docsUrl = "$BaseUrl/api/docs"
try {
    $docsResponse = Invoke-WebRequest -Uri $docsUrl -Method Get -TimeoutSec 10 -UseBasicParsing -ErrorAction Stop
    if ($docsResponse.StatusCode -eq 200) {
        Write-Host "  ✓ Documentation API accessible" -ForegroundColor Green
        $success += "Documentation API"
    } else {
        Write-Host "  ⚠ Documentation API: Status $($docsResponse.StatusCode)" -ForegroundColor Yellow
        $warnings += "Documentation API retourne un statut inattendu"
    }
} catch {
    Write-Host "  ⚠ Documentation API: Non accessible (peut être normal si désactivée)" -ForegroundColor Yellow
    $warnings += "Documentation API non accessible: $($_.Exception.Message)"
}

# 4. Vérifier le frontend (si sur le même domaine)
Write-Host "`n4. Vérification du frontend..." -ForegroundColor Cyan
$frontendUrl = $BaseUrl
try {
    $frontendResponse = Invoke-WebRequest -Uri $frontendUrl -Method Get -TimeoutSec 10 -UseBasicParsing -ErrorAction Stop
    if ($frontendResponse.StatusCode -eq 200) {
        # Vérifier que c'est bien du HTML (frontend) et pas une erreur API
        if ($frontendResponse.Content -match "<!DOCTYPE html>" -or $frontendResponse.Content -match "<html") {
            Write-Host "  ✓ Frontend accessible" -ForegroundColor Green
            $success += "Frontend"
        } else {
            Write-Host "  ⚠ Frontend: Réponse inattendue (pas de HTML)" -ForegroundColor Yellow
            $warnings += "Frontend ne retourne pas de HTML valide"
        }
    } else {
        Write-Host "  ⚠ Frontend: Status $($frontendResponse.StatusCode)" -ForegroundColor Yellow
        $warnings += "Frontend retourne un statut inattendu"
    }
} catch {
    Write-Host "  ⚠ Frontend: Non accessible (peut être normal si déployé séparément)" -ForegroundColor Yellow
    $warnings += "Frontend non accessible: $($_.Exception.Message)"
}

# Résumé
Write-Host "`n=== Résumé ===" -ForegroundColor Cyan

if ($success.Count -gt 0) {
    Write-Host "`n✓ Succès ($($success.Count)):" -ForegroundColor Green
    foreach ($item in $success) {
        Write-Host "  - $item" -ForegroundColor Green
    }
}

if ($warnings.Count -gt 0) {
    Write-Host "`n⚠ Avertissements ($($warnings.Count)):" -ForegroundColor Yellow
    foreach ($warning in $warnings) {
        Write-Host "  - $warning" -ForegroundColor Yellow
    }
}

if ($errors.Count -gt 0) {
    Write-Host "`n✗ Erreurs ($($errors.Count)):" -ForegroundColor Red
    foreach ($error in $errors) {
        Write-Host "  - $error" -ForegroundColor Red
    }
    Write-Host "`n✗ Le déploiement présente des erreurs critiques." -ForegroundColor Red
    exit 1
} elseif ($warnings.Count -gt 0) {
    Write-Host "`n⚠ Le déploiement fonctionne mais présente des avertissements." -ForegroundColor Yellow
    exit 0
} else {
    Write-Host "`n✓ Toutes les vérifications ont réussi. Le déploiement est opérationnel!" -ForegroundColor Green
    exit 0
}


