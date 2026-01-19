# ⚠️ GARDE-FOUS - Vérification de l'Existant (Scrum Master)

**OBLIGATOIRE avant création de chaque story :**

Avant de créer une story, le Scrum Master DOIT vérifier l'existant pour éviter les doublons et documenter les décisions de remplacement.

### Checklist de Vérification

1. **Fichiers à créer/modifier :**
   - [ ] Vérifier si les fichiers mentionnés dans "New Files" existent déjà
   - [ ] Vérifier si les fichiers mentionnés dans "Modified Files" existent et correspondent
   - [ ] Rechercher dans le codebase : `grep`, `codebase_search`, `glob_file_search`
   - [ ] Si fichier existe déjà : **DÉCISION REQUISE** - Étendre ou remplacer ?

2. **Composants/Stores/Services :**
   - [ ] Vérifier si composants React similaires existent (`frontend/src/components/`)
   - [ ] Vérifier si stores Zustand similaires existent (`frontend/src/store/`)
   - [ ] Vérifier si services Python similaires existent (`services/`, `core/`)
   - [ ] Si similaire existe : **DÉCISION REQUISE** - Réutiliser ou créer nouveau ?

3. **Endpoints API :**
   - [ ] Vérifier si endpoints similaires existent (`api/routers/`)
   - [ ] Vérifier cohérence namespace (`/api/v1/dialogues/` vs `/api/v1/generate/`)
   - [ ] Si endpoint similaire existe : **DÉCISION REQUISE** - Étendre ou créer nouveau ?

4. **Patterns et Conventions :**
   - [ ] Vérifier patterns existants (Zustand, FastAPI, React)
   - [ ] Vérifier conventions de nommage (fichiers, fonctions, variables)
   - [ ] Vérifier structure de dossiers (cohérence avec existant)

5. **Documentation des Décisions :**
   - Si remplacement : Documenter **POURQUOI** dans la story (section "Dev Notes")
   - Si extension : Documenter **COMMENT** (quels champs/méthodes ajouter)
   - Si nouveau : Documenter **POURQUOI** pas de réutilisation

### Exemples de Problèmes Détectés

**❌ MAUVAIS (Story 0.2 initiale) :**
- Story dit "Créer `generationStore.ts`" → **EXISTE DÉJÀ** avec rôle différent
- Story dit `/api/v1/generate/stream` → **INCOHÉRENT** avec `/api/v1/dialogues/*`
- Story dit `services/llm/llm_client.py` → **MAUVAIS CHEMIN** (devrait être `core/llm/llm_client.py`)

**✅ BON (Story 0.2 corrigée) :**
- Story dit "Étendre `generationStore.ts` existant" → **CORRECT**
- Story dit `/api/v1/dialogues/generate/stream` → **COHÉRENT**
- Story dit `core/llm/llm_client.py` → **CORRECT**

### Workflow de Vérification

1. **Avant création story :** Exécuter checklist complète
2. **Pendant création story :** Documenter toutes les décisions dans "Dev Notes"
3. **Après création story :** Vérifier que les corrections sont appliquées

---
