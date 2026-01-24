# Production Environment - DialogueGenerator

**Document de référence centralisé pour l'environnement de production**

## 📍 Informations du Serveur

### Serveur de Production

- **Type** : VPS OVH
- **IP** : `137.74.115.203`
- **Utilisateur** : `ubuntu`
- **Répertoire de l'application** : `/opt/DialogueGeneratorV2`
- **Port API** : `4242` (interne, non exposé directement)
- **Port HTTP** : `80` (Nginx reverse proxy)

### Connexion SSH

```bash
ssh ubuntu@137.74.115.203
```

## 🌐 URLs d'Accès

### Frontend (Interface Web)
- **URL principale** : http://137.74.115.203
- **Interface utilisateur** : Application React complète

### API Backend

- **Base URL** : http://137.74.115.203/api
- **API v1** : http://137.74.115.203/api/v1
- **Documentation Swagger** : http://137.74.115.203/api/docs
- **Documentation ReDoc** : http://137.74.115.203/api/redoc

### Health Checks

- **Health check basique** : http://137.74.115.203/health
- **Health check détaillé** : http://137.74.115.203/health/detailed
- **Health check API v1 (alias)** : http://137.74.115.203/api/v1/healthcheck

**Note** : Les endpoints `/health` et `/api/v1/healthcheck` sont équivalents (le second est un alias pour compatibilité avec les outils de monitoring).

## 🔍 Comment Interroger la Production

### Health Check Basique

Vérifie que l'API est accessible et fonctionnelle :

```bash
# Depuis Windows (PowerShell)
Invoke-WebRequest -Uri "http://137.74.115.203/health" | ConvertFrom-Json

# Depuis Linux/Mac
curl http://137.74.115.203/health | jq

# Depuis le serveur lui-même
curl http://localhost:4242/health
# Ou via l'alias pour monitoring
curl http://localhost:4242/api/v1/healthcheck
```

**Réponse attendue** :
```json
{
  "status": "healthy",
  "service": "DialogueGenerator API",
  "timestamp": "2026-01-24T18:30:00Z"
}
```

### Health Check Détaillé

Vérifie tous les composants (GDD, Vision.json, etc.) :

```bash
curl http://137.74.115.203/health/detailed | jq
```

**Réponse attendue** :
```json
{
  "status": "healthy",
  "service": "DialogueGenerator API",
  "timestamp": "2026-01-24T18:30:00Z",
  "checks": [
    {
      "name": "config",
      "status": "healthy"
    },
    {
      "name": "storage",
      "status": "healthy"
    },
    {
      "name": "gdd_files",
      "status": "healthy",
      "details": {
        "count": 144,
        "path": "/opt/DialogueGeneratorV2/data/GDD_categories"
      }
    },
    {
      "name": "vision_file",
      "status": "healthy",
      "details": {
        "path": "/opt/DialogueGeneratorV2/data/Vision.json"
      }
    },
    {
      "name": "llm_connectivity",
      "status": "healthy"
    }
  ]
}
```

**Statuts possibles** :
- `healthy` : Tout fonctionne correctement
- `degraded` : L'application fonctionne mais avec des limitations (ex: certains fichiers GDD manquants)
- `unhealthy` : Problème critique, l'application ne peut pas fonctionner correctement

### Test des Endpoints API

#### Test d'authentification

```bash
# Login
curl -X POST http://137.74.115.203/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}'
```

#### Test de génération de dialogue

```bash
# Nécessite un token JWT valide
curl -X POST http://137.74.115.203/api/v1/dialogues/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{...}'
```

### Script de Vérification Automatique

Depuis Windows, utilisez le script de vérification :

```powershell
.\scripts\verify_deployment.ps1 -BaseUrl "http://137.74.115.203"
```

## 🛠️ Commandes Utiles

### Gestion du Service

```bash
# Vérifier le statut du service
sudo systemctl status dialogue-generator

# Démarrer le service
sudo systemctl start dialogue-generator

# Arrêter le service
sudo systemctl stop dialogue-generator

# Redémarrer le service
sudo systemctl restart dialogue-generator

# Recharger la configuration (sans interruption)
sudo systemctl reload dialogue-generator

# Activer le démarrage automatique
sudo systemctl enable dialogue-generator

# Désactiver le démarrage automatique
sudo systemctl disable dialogue-generator
```

### Consultation des Logs

```bash
# Logs du service (dernières 50 lignes)
sudo journalctl -u dialogue-generator -n 50

# Logs en temps réel (suivre)
sudo journalctl -u dialogue-generator -f

# Logs depuis une date spécifique
sudo journalctl -u dialogue-generator --since "2026-01-24 10:00:00"

# Logs Nginx (accès)
sudo tail -f /var/log/nginx/dialogue-generator-access.log

# Logs Nginx (erreurs)
sudo tail -f /var/log/nginx/dialogue-generator-error.log

# Logs de l'application (si configurés)
tail -f /opt/DialogueGeneratorV2/data/logs/*.log
```

### Gestion de Nginx

```bash
# Tester la configuration Nginx
sudo nginx -t

# Recharger Nginx (sans interruption)
sudo systemctl reload nginx

# Redémarrer Nginx
sudo systemctl restart nginx

# Vérifier le statut
sudo systemctl status nginx
```

### Accès au Projet

```bash
# Se connecter au serveur
ssh ubuntu@137.74.115.203

# Aller dans le répertoire du projet
cd /opt/DialogueGeneratorV2

# Activer l'environnement virtuel Python
source .venv/bin/activate

# Vérifier la version Python
python --version

# Vérifier les dépendances installées
pip list
```

### Mise à Jour du Code

```bash
# Se connecter au serveur
ssh ubuntu@137.74.115.203
cd /opt/DialogueGeneratorV2

# Récupérer les dernières modifications
git pull origin main

# Mettre à jour les dépendances Python (si nécessaire)
source .venv/bin/activate
pip install -r requirements.txt

# Rebuild le frontend (si nécessaire)
cd frontend
npm install
npm run build
cd ..

# Redémarrer le service
sudo systemctl restart dialogue-generator

# Vérifier que tout fonctionne
curl http://localhost:4242/health
```

### Gestion des Fichiers GDD

```bash
# Vérifier les fichiers GDD
ls -la /opt/DialogueGeneratorV2/data/GDD_categories/

# Vérifier Vision.json
ls -la /opt/DialogueGeneratorV2/data/Vision.json

# Uploader des fichiers depuis Windows (PowerShell)
scp data/GDD_categories/*.json ubuntu@137.74.115.203:/opt/DialogueGeneratorV2/data/GDD_categories/
scp data/Vision.json ubuntu@137.74.115.203:/opt/DialogueGeneratorV2/data/
```

### Configuration

```bash
# Éditer le fichier .env
nano /opt/DialogueGeneratorV2/.env

# Vérifier les variables d'environnement
cat /opt/DialogueGeneratorV2/.env | grep -v "^#"

# Vérifier la configuration Nginx
cat /etc/nginx/sites-available/dialogue-generator

# Vérifier la configuration Gunicorn
cat /opt/DialogueGeneratorV2/gunicorn.conf.py
```

## 📦 Structure des Fichiers sur le Serveur

```
/opt/DialogueGeneratorV2/
├── api/                    # Code API FastAPI
├── core/                   # Modules core (context, prompt, llm)
├── services/               # Services métier
├── frontend/
│   └── dist/              # Frontend build (servi par Nginx)
├── data/
│   ├── GDD_categories/    # Fichiers JSON GDD
│   │   ├── personnages.json
│   │   ├── lieux.json
│   │   └── ...
│   └── Vision.json        # Fichier Vision principal
├── .venv/                 # Environnement virtuel Python
├── .env                   # Variables d'environnement (NE PAS COMMITER)
├── gunicorn.conf.py       # Configuration Gunicorn
└── requirements.txt       # Dépendances Python
```

## 🔧 Configuration

### Variables d'Environnement

Le fichier `.env` doit contenir (minimum) :

```bash
ENVIRONMENT=production
JWT_SECRET_KEY=<clé-secrète-générée>
OPENAI_API_KEY=<votre-clé-openai>
NOTION_API_KEY=<votre-clé-notion>  # Optionnel, requis pour vocabulaire/guides
CORS_ORIGINS=http://137.74.115.203
API_PORT=4242

# Variables optionnelles (voir env.example pour la liste complète)
# LOG_LEVEL=INFO
# SENTRY_DSN=<votre-dsn-sentry>  # Si Sentry est configuré
# AUTH_RATE_LIMIT_ENABLED=true
```

### Service Systemd

Le service est configuré dans `/etc/systemd/system/dialogue-generator.service`

### Configuration Nginx

La configuration est dans `/etc/nginx/sites-available/dialogue-generator`

## 🚀 Déploiement Initial

Pour un déploiement initial complet, utiliser le script automatisé :

### Depuis Windows

```powershell
# Uploader le script
scp scripts/deploy-production.sh ubuntu@137.74.115.203:/tmp/

# Se connecter au serveur
ssh ubuntu@137.74.115.203

# Rendre exécutable et lancer
chmod +x /tmp/deploy-production.sh
bash /tmp/deploy-production.sh
```

Le script effectue automatiquement :
1. ✅ Vérifications préalables
2. ✅ Installation des dépendances système
3. ✅ Configuration de l'environnement Python
4. ✅ Build du frontend
5. ✅ Configuration .env
6. ✅ Création des dossiers GDD
7. ✅ Configuration Gunicorn
8. ✅ Configuration systemd
9. ✅ Configuration Nginx
10. ✅ Configuration firewall
11. ✅ Démarrage des services
12. ✅ Vérification

**Voir** : `scripts/deploy-production.sh` pour les détails complets.

## 🔄 Mise à Jour (Update)

Pour mettre à jour le code sans tout reconfigurer :

```bash
# Sur le serveur
cd /opt/DialogueGeneratorV2
git pull origin main

# Si dépendances Python changées
source .venv/bin/activate
pip install -r requirements.txt

# Si frontend changé
cd frontend
npm install
npm run build
cd ..

# Redémarrer
sudo systemctl restart dialogue-generator

# Vérifier
curl http://localhost:4242/health
```

## 🐛 Troubleshooting

### Le service ne démarre pas

```bash
# Vérifier les logs d'erreur
sudo journalctl -u dialogue-generator -n 100 --no-pager

# Vérifier la configuration
sudo systemctl status dialogue-generator

# Tester manuellement
cd /opt/DialogueGeneratorV2
source .venv/bin/activate
python -m api.main
```

### L'API ne répond pas

```bash
# Vérifier que le service tourne
sudo systemctl status dialogue-generator

# Vérifier le port
sudo netstat -tlnp | grep 4242

# Tester localement
curl http://localhost:4242/health

# Vérifier Nginx
sudo nginx -t
sudo systemctl status nginx
```

### Les fichiers GDD ne sont pas trouvés

```bash
# Vérifier les chemins
curl http://localhost:4242/health/detailed | jq

# Vérifier les permissions
ls -la /opt/DialogueGeneratorV2/data/GDD_categories/
ls -la /opt/DialogueGeneratorV2/data/Vision.json

# Vérifier les variables d'environnement
grep GDD /opt/DialogueGeneratorV2/.env
```

### Le frontend ne charge pas

```bash
# Vérifier que le build existe
ls -la /opt/DialogueGeneratorV2/frontend/dist/

# Vérifier Nginx
sudo nginx -t
sudo tail -f /var/log/nginx/dialogue-generator-error.log

# Vérifier les permissions
ls -la /opt/DialogueGeneratorV2/frontend/dist/index.html
```

## 📊 Monitoring

### Health Checks Réguliers

Mettre en place un monitoring qui vérifie régulièrement :

```bash
# Health check basique (toutes les 5 minutes)
# Note: Nécessite que mailx ou un service de notification soit configuré
*/5 * * * * curl -f http://localhost:4242/health > /dev/null 2>&1 || echo "API down" | mail -s "Alert" admin@example.com
```

### Métriques à Surveiller

- ✅ Status du service (`systemctl status`)
- ✅ Health checks (`/health` et `/health/detailed`)
- ✅ Logs d'erreur (Nginx et application)
- ✅ Utilisation CPU/RAM
- ✅ Espace disque
- ✅ Coûts API OpenAI (via logs)

## 🔐 Sécurité

### Firewall

Le firewall (UFW) est configuré pour autoriser uniquement :
- Port 22 (SSH)
- Port 80 (HTTP)
- Port 443 (HTTPS, si configuré)

### Recommandations

- ✅ Utiliser HTTPS (certificat Let's Encrypt via Certbot)
  ```bash
  # Installation Certbot
  sudo apt install certbot python3-certbot-nginx
  
  # Obtenir un certificat
  sudo certbot --nginx -d votre-domaine.com
  
  # Renouvellement automatique (configuré par défaut)
  sudo certbot renew --dry-run
  ```
- ✅ Changer le port SSH par défaut (modifier `/etc/ssh/sshd_config`)
- ✅ Désactiver l'authentification par mot de passe SSH (utiliser uniquement les clés)
- ✅ Mettre à jour régulièrement le système (`sudo apt update && sudo apt upgrade`)
- ✅ Surveiller les logs pour détecter les intrusions
- ✅ Ne jamais commiter le fichier `.env`
- ✅ Configurer un backup automatique des données GDD et Vision.json

## 📚 Documentation Complémentaire

- **Guide de déploiement complet** : `docs/guides/DEPLOYMENT.md`
- **Script de déploiement** : `scripts/deploy-production.sh`
- **Configuration Nginx** : `docs/deployment/nginx.conf.example`
- **Configuration Gunicorn** : `docs/deployment/gunicorn.conf.example`
- **Maintenance des données GDD** : `docs/deployment/DATA_MAINTENANCE.md`

## 📝 Notes Importantes

- ⚠️ Le port 4242 n'est **pas exposé publiquement**, seul Nginx y accède
- ⚠️ Le fichier `.env` contient des secrets, **ne jamais le commiter**
- ⚠️ Les fichiers GDD doivent être uploadés manuellement après le déploiement
- ⚠️ Le service systemd s'appelle `dialogue-generator` (pas `dialogue-generator.service` dans les commandes)
- ⚠️ Après modification de `.env`, redémarrer le service : `sudo systemctl restart dialogue-generator`

---

**Dernière mise à jour** : 2026-01-24  
**Maintenu par** : Équipe DialogueGenerator
