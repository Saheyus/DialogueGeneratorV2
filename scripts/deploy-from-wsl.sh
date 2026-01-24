#!/bin/bash
# Script de déploiement depuis WSL (utilise les clés SSH configurées)
# Usage: bash scripts/deploy-from-wsl.sh

set -e

# Configuration
SERVER_HOST="137.74.115.203"
SERVER_USER="ubuntu"
SERVER_PATH="/opt/DialogueGeneratorV2"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

cd "$PROJECT_ROOT"

# Étape 1: Build du frontend
log_info "=== Étape 1: Build du frontend ==="
cd frontend
npm install --silent
npm run build
cd ..
log_success "Build terminé"

# Étape 2: Upload du build
log_info "=== Étape 2: Upload du build ==="
log_info "Upload vers ${SERVER_USER}@${SERVER_HOST}:${SERVER_PATH}/frontend/dist/..."
scp -r frontend/dist/* ${SERVER_USER}@${SERVER_HOST}:${SERVER_PATH}/frontend/dist/

# Corriger les permissions après upload
log_info "Correction des permissions..."
ssh ${SERVER_USER}@${SERVER_HOST} "sudo chown -R ubuntu:ubuntu ${SERVER_PATH}/frontend/dist && sudo chmod -R 755 ${SERVER_PATH}/frontend/dist && sudo find ${SERVER_PATH}/frontend/dist -type f -exec chmod 644 {} \;"
log_success "Upload terminé"

# Étape 3: Git pull sur le serveur
log_info "=== Étape 3: Mise à jour du code (git pull) ==="
ssh ${SERVER_USER}@${SERVER_HOST} "cd ${SERVER_PATH} && git pull"
log_success "Code mis à jour"

# Étape 4: Mise à jour de la config Nginx
log_info "=== Étape 4: Mise à jour de la config Nginx ==="

# Vérifier si la config a déjà les paramètres SSE
if ssh ${SERVER_USER}@${SERVER_HOST} "grep -q 'proxy_buffering off' /etc/nginx/sites-available/dialogue-generator 2>/dev/null"; then
    log_success "Config Nginx déjà à jour (SSE support présent)"
else
    log_warning "Config Nginx nécessite une mise à jour pour le support SSE"
    
    # Créer un script temporaire pour mettre à jour Nginx
    cat > /tmp/update-nginx.sh << 'NGINX_SCRIPT'
#!/bin/bash
set -e

NGINX_CONFIG="/etc/nginx/sites-available/dialogue-generator"
BACKUP_CONFIG="${NGINX_CONFIG}.backup.$(date +%Y%m%d-%H%M%S)"

# Backup
sudo cp "${NGINX_CONFIG}" "${BACKUP_CONFIG}"
echo "Backup créé: ${BACKUP_CONFIG}"

# Vérifier si la section location /api existe
if ! grep -q "location /api" "${NGINX_CONFIG}"; then
    echo "ERREUR: Section location /api introuvable"
    exit 1
fi

    # Ajouter les paramètres SSE si absents
    if ! grep -q "proxy_buffering off" "${NGINX_CONFIG}"; then
        TMP_FILE=$(mktemp)
        sudo awk '
    /Connection "upgrade";/ {
        print
        print ""
        print "        # Server-Sent Events (SSE) support"
        print "        proxy_buffering off;"
        print "        proxy_cache off;"
        print "        proxy_read_timeout 300s;"
        print "        proxy_connect_timeout 60s;"
        print "        proxy_send_timeout 300s;"
        print ""
        print "        # Headers pour SSE"
        print "        add_header Cache-Control \"no-cache\";"
        print "        add_header X-Accel-Buffering \"no\";"
        next
    }
    { print }
    ' "${NGINX_CONFIG}" > "${TMP_FILE}" && sudo mv "${TMP_FILE}" "${NGINX_CONFIG}"
    echo "Paramètres SSE ajoutés"
else
    echo "Paramètres SSE déjà présents"
fi

# Tester et recharger
if sudo nginx -t; then
    sudo systemctl reload nginx
    echo "Nginx rechargé avec succès"
else
    echo "ERREUR: Config invalide, restauration du backup"
    sudo cp "${BACKUP_CONFIG}" "${NGINX_CONFIG}"
    exit 1
fi
NGINX_SCRIPT

    # Upload et exécuter le script
    scp /tmp/update-nginx.sh ${SERVER_USER}@${SERVER_HOST}:/tmp/update-nginx.sh
    ssh ${SERVER_USER}@${SERVER_HOST} "chmod +x /tmp/update-nginx.sh && bash /tmp/update-nginx.sh && rm /tmp/update-nginx.sh"
    rm /tmp/update-nginx.sh
    
    log_success "Config Nginx mise à jour"
fi

# Étape 5: Redémarrer le service
log_info "=== Étape 5: Redémarrage du service ==="
ssh ${SERVER_USER}@${SERVER_HOST} "sudo systemctl restart dialogue-generator"
sleep 2
log_success "Service redémarré"

# Étape 6: Vérification
log_info "=== Étape 6: Vérification ==="
if ssh ${SERVER_USER}@${SERVER_HOST} "curl -s http://localhost:4242/health | grep -q healthy"; then
    log_success "Health check: OK"
else
    log_warning "Health check: Échec (peut nécessiter quelques secondes)"
fi

log_success "=== Déploiement terminé ==="
log_info "Application disponible sur: http://${SERVER_HOST}"
