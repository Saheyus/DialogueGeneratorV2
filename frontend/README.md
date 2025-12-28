# DialogueGenerator Frontend

Application React TypeScript pour l'interface web de DialogueGenerator.

✅ **Interface principale du projet** — Utiliser cette interface pour le développement et la production.

## Installation

```bash
npm install
```

## Développement

```bash
npm run dev
```

L'application sera accessible sur http://localhost:3000

## Build de production

```bash
npm run build
```

Les fichiers de production seront dans le dossier `dist/`.

## Configuration

Créer un fichier `.env` à la racine du projet frontend :

```
VITE_API_BASE_URL=http://localhost:4242
```

## Structure

- `src/api/` - Client API et endpoints
- `src/components/` - Composants React
- `src/store/` - State management (Zustand)
- `src/types/` - Types TypeScript
- `src/hooks/` - React hooks personnalisés

