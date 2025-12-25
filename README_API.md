# DialogueGenerator API REST

API REST FastAPI pour la génération de dialogues IA pour jeux de rôle.

## Démarrage rapide

### Installation

```bash
pip install -r requirements.txt
```

### Configuration

1. Créer un fichier `.env` (optionnel) ou configurer les variables d'environnement :
   - `OPENAI_API_KEY`: Clé API OpenAI
   - `JWT_SECRET_KEY`: Clé secrète pour JWT (par défaut: "your-secret-key-change-in-production")

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
- `POST /api/v1/dialogues/generate/interactions` - Générer interactions structurées
- `POST /api/v1/dialogues/estimate-tokens` - Estimer tokens

### Interactions

- `GET /api/v1/interactions` - Liste interactions
- `GET /api/v1/interactions/{id}` - Détails interaction
- `POST /api/v1/interactions` - Créer interaction
- `PUT /api/v1/interactions/{id}` - Mettre à jour
- `DELETE /api/v1/interactions/{id}` - Supprimer

### Contexte GDD

- `GET /api/v1/context/characters` - Liste personnages
- `GET /api/v1/context/locations` - Liste lieux
- `GET /api/v1/context/items` - Liste objets
- `POST /api/v1/context/build` - Construire contexte

### Configuration

- `GET /api/v1/config/llm` - Configuration LLM
- `GET /api/v1/config/llm/models` - Modèles disponibles
- `GET /api/v1/config/context` - Configuration contexte

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

Le frontend React est dans le dossier `frontend/`. Voir `frontend/README.md` pour plus d'informations.

