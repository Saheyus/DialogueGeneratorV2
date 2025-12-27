# DialogueGenerator API REST

API REST FastAPI pour la génération de dialogues IA pour jeux de rôle.

⚠️ **IMPORTANT** : Cette API est utilisée par l'**interface web React** (interface principale). L'ancienne interface desktop PySide6 est **dépréciée** et ne doit plus être utilisée.

## Démarrage rapide

### Installation

```bash
pip install -r requirements.txt
```

### Configuration

1. **Créer le fichier `.env`** :
   ```bash
   cp .env.example .env
   ```

2. **Modifier `.env`** et définir les variables d'environnement :
   - `OPENAI_API_KEY`: Clé API OpenAI (requis)
   - `JWT_SECRET_KEY`: Clé secrète pour JWT (requis en production, valeur par défaut acceptée en dev)
   - `ENVIRONMENT`: Environnement (`development` ou `production`)
   - `AUTH_RATE_LIMIT_ENABLED`: Activer le rate limiting (par défaut: `true`)
   - `AUTH_RATE_LIMIT_REQUESTS`: Nombre de requêtes par fenêtre (par défaut: `5`)
   - `AUTH_RATE_LIMIT_WINDOW`: Fenêtre en secondes (par défaut: `60`)

   **Note** : Voir `.env.example` pour la liste complète des variables. En production, `JWT_SECRET_KEY` **doit** être changée et ne peut pas être la valeur par défaut.

3. **Générer une clé secrète JWT sécurisée** (recommandé) :
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

Pour plus de détails sur la sécurité, voir [docs/SECURITY.md](docs/SECURITY.md).

### Lancer l'API

```bash
# Méthode 1: Via Python
python -m api.main

# Méthode 2: Via uvicorn directement
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

L'API sera accessible sur :
- API: http://localhost:8000
- Documentation Swagger: http://localhost:8000/api/docs
- Documentation ReDoc: http://localhost:8000/api/redoc

## Endpoints principaux

### Authentification

- `POST /api/v1/auth/login` - Connexion
- `GET /api/v1/auth/me` - Utilisateur courant
- `POST /api/v1/auth/logout` - Déconnexion
- `POST /api/v1/auth/refresh` - Rafraîchir token

### Génération de dialogues

- `POST /api/v1/dialogues/generate/variants` - Générer variantes texte
- `POST /api/v1/dialogues/generate/interactions` - Générer interactions structurées (supporte `previous_interaction_id` pour la continuité)
- `POST /api/v1/dialogues/estimate-tokens` - Estimer tokens

### Interactions

- `GET /api/v1/interactions` - Liste interactions
- `GET /api/v1/interactions/{id}` - Détails interaction
- `GET /api/v1/interactions/{id}/parents` - Interactions parentes
- `GET /api/v1/interactions/{id}/children` - Interactions enfants
- `GET /api/v1/interactions/{id}/context-path` - Chemin complet de contexte (parents jusqu'à la racine)
- `POST /api/v1/interactions` - Créer interaction
- `PUT /api/v1/interactions/{id}` - Mettre à jour
- `DELETE /api/v1/interactions/{id}` - Supprimer

### Contexte GDD

- `GET /api/v1/context/characters` - Liste personnages
- `GET /api/v1/context/characters/{name}` - Détails d'un personnage
- `GET /api/v1/context/locations` - Liste lieux
- `GET /api/v1/context/locations/{name}` - Détails d'un lieu
- `GET /api/v1/context/items` - Liste objets
- `GET /api/v1/context/species` - Liste espèces
- `GET /api/v1/context/species/{name}` - Détails d'une espèce
- `GET /api/v1/context/communities` - Liste communautés
- `GET /api/v1/context/communities/{name}` - Détails d'une communauté
- `GET /api/v1/context/locations/regions` - Liste régions
- `GET /api/v1/context/locations/regions/{name}/sub-locations` - Sous-lieux d'une région
- `POST /api/v1/context/linked-elements` - Suggère des éléments liés
- `POST /api/v1/context/build` - Construire contexte

### Configuration

- `GET /api/v1/config/llm` - Configuration LLM
- `GET /api/v1/config/llm/models` - Modèles disponibles
- `GET /api/v1/config/context` - Configuration contexte
- `GET /api/v1/config/unity-dialogues-path` - Chemin configuré des dialogues Unity
- `PUT /api/v1/config/unity-dialogues-path` - Configurer le chemin des dialogues Unity

## Authentification

L'API utilise JWT (JSON Web Tokens) pour l'authentification.

1. Se connecter via `POST /api/v1/auth/login` avec `username` et `password`
2. Récupérer le `access_token` dans la réponse
3. Inclure le token dans les requêtes suivantes : `Authorization: Bearer <token>`

**Note**: Pour le développement, un utilisateur par défaut existe :
- Username: `admin`
- Password: `admin123`

⚠️ **À changer en production !**

## Documentation

La documentation interactive est disponible via Swagger UI à `/api/docs` une fois l'API démarrée.

## Tests

```bash
pytest tests/api/
```

## Architecture

L'API suit les principes SOLID et RESTful :

- **Routers**: Gestion des routes HTTP uniquement
- **Services**: Logique métier (réutilise les services existants)
- **Schemas**: DTOs Pydantic pour validation
- **Dependencies**: Injection de dépendances FastAPI
- **Exceptions**: Gestion centralisée des erreurs

## Frontend

Le frontend React est dans le dossier `frontend/`. **C'est l'interface principale du projet.** Voir `frontend/README.md` pour plus d'informations.

⚠️ **Note** : L'ancienne interface desktop PySide6 (`ui/`, `main_app.py`) est dépréciée et ne doit plus être utilisée.

