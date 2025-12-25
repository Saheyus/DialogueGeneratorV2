# Guide de Déploiement - DialogueGenerator API

## Déploiement sur SmarterASP.net

### Prérequis

1. Compte SmarterASP.net avec support Python
2. Accès FTP/SFTP ou contrôle de panel
3. Variables d'environnement configurées

### Étapes de déploiement

#### 1. Préparation du code

```bash
# Installer les dépendances
pip install -r requirements.txt

# Vérifier que l'API démarre localement
python -m api.main
```

#### 2. Configuration des variables d'environnement

Sur SmarterASP.net, configurer les variables suivantes :

- `OPENAI_API_KEY`: Clé API OpenAI
- `JWT_SECRET_KEY`: Clé secrète pour JWT (générer une clé forte)
- `ENVIRONMENT`: `production` ou `development`

#### 3. Déploiement du backend

1. Uploader tous les fichiers Python dans le répertoire de l'application
2. Créer un fichier `web.config` ou `startup.py` selon la configuration SmarterASP.net
3. Configurer le point d'entrée : `api.main:app`

#### 4. Configuration du serveur

- **Port**: Configurer selon les spécifications SmarterASP.net (généralement automatique)
- **Worker processes**: 1-2 workers selon les ressources
- **Timeout**: Augmenter pour les requêtes LLM longues (60-120 secondes)

#### 5. Déploiement du frontend

1. Build de production :
```bash
cd frontend
npm install
npm run build
```

2. Uploader le contenu du dossier `dist/` vers le répertoire statique
3. Configurer le serveur pour servir les fichiers statiques et rediriger `/api/*` vers le backend

### Configuration Nginx (si applicable)

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        root /path/to/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### Vérification

1. Tester le health check : `https://your-domain.com/health`
2. Tester l'API : `https://your-domain.com/api/docs`
3. Tester le frontend : `https://your-domain.com`

### Maintenance

- **Logs**: Vérifier les logs SmarterASP.net pour les erreurs
- **Monitoring**: Surveiller l'utilisation des ressources
- **Backups**: Sauvegarder régulièrement les interactions dans `data/interactions/`

## Développement local

### Démarrer le backend

```bash
# Terminal 1
python -m api.main
# Ou avec uvicorn directement
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### Démarrer le frontend

```bash
# Terminal 2
cd frontend
npm install
npm run dev
```

L'application sera accessible sur :
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/api/docs

