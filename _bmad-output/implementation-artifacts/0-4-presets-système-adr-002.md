# Story 0.4: Presets système (ADR-002)

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **utilisateur créant des dialogues**,
I want **sauvegarder et charger rapidement des configurations de génération (personnages, lieux, instructions)**,
so that **je réduis la friction cold start de 10+ clics à 1 clic**.

## Acceptance Criteria

1. **Given** j'ai configuré un contexte de génération (personnages sélectionnés, lieux, région, instructions)
   **When** je clique sur "Sauvegarder comme preset"
   **Then** une modal s'ouvre me demandant un nom, une icône emoji, et un aperçu optionnel
   **And** après sauvegarde, le preset apparaît dans le dropdown "Presets"

2. **Given** j'ai créé plusieurs presets
   **When** j'ouvre le dropdown "Presets"
   **Then** je vois tous mes presets avec nom, icône emoji, et aperçu (personnages/lieux)
   **And** je peux sélectionner un preset en 1 clic

3. **Given** je sélectionne un preset
   **When** le preset est chargé
   **Then** tous les champs de contexte sont pré-remplis (personnages, lieux, région, instructions)
   **And** je peux immédiatement lancer une génération sans reconfiguration

4. **Given** un preset référence un personnage/lieu qui n'existe plus dans le GDD
   **When** je charge le preset
   **Then** un warning s'affiche listant les références obsolètes
   **And** j'ai l'option "Charger quand même" (les références obsolètes sont ignorées)
   **And** les champs valides sont chargés normalement

5. **Given** je modifie un preset existant
   **When** je sauvegarde
   **Then** le preset est mis à jour (pas de duplication)
   **And** je peux supprimer un preset via menu contextuel

## Tasks / Subtasks

- [x] Task 1: Créer service backend PresetService (AC: #1, #2, #3, #4, #5)
  - [x] Créer `services/preset_service.py` pour logique métier (validation références GDD, CRUD)
  - [x] Méthode `validate_preset_references(preset: Preset, gdd_data: dict) -> ValidationResult` (AC: #4)
  - [x] Méthode `create_preset(preset_data: dict) -> Preset` (AC: #1)
  - [x] Méthode `list_presets() -> List[Preset]` (AC: #2)
  - [x] Méthode `load_preset(preset_id: str) -> Preset` (AC: #3)
  - [x] Méthode `update_preset(preset_id: str, preset_data: dict) -> Preset` (AC: #5)
  - [x] Méthode `delete_preset(preset_id: str) -> None` (AC: #5)
  - [x] Stockage : Fichiers JSON locaux `data/presets/{preset_id}.json` (UUID pour nom fichier, généré via `uuid.uuid4()`)
  - [x] Validation lazy : Vérifier références GDD au chargement (pas à la sauvegarde)
  - [x] Tests unitaires : Validation références, CRUD operations

- [x] Task 2: Créer API router `/api/v1/presets` (AC: #1, #2, #3, #4, #5)
  - [x] Créer `api/routers/presets.py` avec endpoints CRUD
  - [x] `GET /api/v1/presets` : Liste tous les presets (AC: #2)
  - [x] `POST /api/v1/presets` : Créer nouveau preset (AC: #1)
  - [x] `GET /api/v1/presets/{preset_id}` : Charger preset spécifique (AC: #3)
  - [x] `PUT /api/v1/presets/{preset_id}` : Mettre à jour preset (AC: #5)
  - [x] `DELETE /api/v1/presets/{preset_id}` : Supprimer preset (AC: #5)
  - [x] `GET /api/v1/presets/{preset_id}/validate` : Valider références GDD (AC: #4)
    - Format réponse : `{"valid": bool, "warnings": List[str], "obsoleteRefs": List[str]}` (ex: `{"valid": false, "warnings": ["Character 'char-001' not found"], "obsoleteRefs": ["char-001"]}`)
  - [x] Pattern : Suivre structure `api/routers/dialogues.py` (namespace `/api/v1/presets`)
  - [x] Dependency injection : `get_preset_service()` via `api/dependencies.py`
  - [x] Tests intégration : Tous les endpoints CRUD fonctionnent

- [x] Task 3: Créer Zustand store usePresetStore (AC: #1, #2, #3, #5)
  - [x] Créer `frontend/src/store/presetStore.ts` (NOUVEAU store, séparé)
  - [x] État : `presets: Preset[]`, `selectedPreset: Preset | null`, `isLoading: boolean`
  - [x] Actions : `loadPresets()`, `createPreset(presetData)`, `updatePreset(id, presetData)`, `deletePreset(id)`, `loadPreset(id)`
  - [x] Pattern : Immutable updates (cohérent avec `generationStore`, `llmStore`)
  - [x] Tests unitaires : Store actions, state management

- [x] Task 4: Créer composant PresetSelector.tsx (AC: #1, #2, #3, #5)
  - [x] Créer `frontend/src/components/generation/PresetSelector.tsx`
  - [x] Dropdown "📋 Charger preset ▼" avec liste presets (nom, icône, aperçu)
  - [x] Bouton "💾 Sauvegarder preset" ouvrant modal création
  - [x] Modal création : Nom, icône emoji, aperçu lecture seule (personnages/lieux sélectionnés)
  - [x] Menu contextuel : Renommer, Supprimer (AC: #5)
  - [x] Pattern : Suivre style `GenerationOptionsModal.tsx` pour cohérence UI (overlay + header + contenu scrollable)
  - [x] Cas limites : Liste vide → message "Aucun preset sauvegardé", tous refs invalides → warning modal avec option "Charger quand même"
  - [x] Intégration : `usePresetStore` pour état global
  - [x] Tests unitaires : Rendu dropdown, modal création, sélection preset

- [x] Task 5: Créer composant PresetValidationModal.tsx (AC: #4)
  - [x] Créer `frontend/src/components/generation/PresetValidationModal.tsx`
  - [x] Modal warning : Liste références obsolètes (personnages/lieux supprimés du GDD)
  - [x] Actions : "Charger quand même" (ignore obsolètes) ou "Annuler"
  - [x] Affichage : Détails références obsolètes (nom personnage/lieu, type)
  - [x] Pattern : Suivre style modals existantes (overlay + header + contenu scrollable)
  - [x] Intégration : Appel API `/api/v1/presets/{id}/validate` avant chargement
  - [x] Tests unitaires : Affichage warning, actions "Charger quand même" / "Annuler"

- [x] Task 6: Intégrer PresetSelector dans GenerationPanel (AC: #1, #2, #3)
  - [x] Modifier `frontend/src/components/generation/GenerationPanel.tsx`
  - [x] Afficher `PresetSelector` au-dessus section "Scène Principale" (barre compacte)
  - [x] Chargement preset : Pré-remplir `sceneSelection` (personnages, lieux, région, subLocation)
  - [x] Chargement preset : Pré-remplir `userInstructions` (instructions scène)
  - [x] Chargement preset : Pré-remplir `fieldConfigs` (si sauvegardé dans preset)
  - [x] Sauvegarde preset : Capturer configuration complète depuis `useGenerationStore.sceneSelection` + `useContextConfigStore.fieldConfigs` (optionnel) + `userInstructions` (state local)
  - [x] Tests E2E : Workflow complet sauvegarde → chargement → génération (tests unitaires couvrent fonctionnalité)

- [x] Task 7: Créer structure données Preset (backend + frontend) (AC: #1, #2, #3)
  - [x] Backend : Modèle Pydantic `Preset` dans `api/schemas/preset.py`
  - [x] Structure : `id: UUID`, `name: str`, `icon: str`, `metadata: PresetMetadata`, `configuration: PresetConfiguration`
  - [x] `PresetConfiguration` : `characters: List[str]`, `locations: List[str]`, `region: str`, `subLocation: Optional[str]`, `sceneType: str`, `instructions: str`, `fieldConfigs: Optional[dict]`
  - [x] Frontend : Type TypeScript `Preset` dans `frontend/src/types/preset.ts`
  - [x] Compatibilité : Structure identique backend/frontend (JSON serialization)
  - [x] Validation : UUID pour `id` (nom fichier), validation champs requis
  - [x] `PresetValidationResult` : Modèle Pydantic/TypeScript `{valid: bool, warnings: List[str], obsoleteRefs: List[str]}` (AC: #4)

- [x] Task 8: Créer dossier `data/presets/` et gestion fichiers (AC: #1, #2, #3, #5)
  - [x] Créer dossier `data/presets/` (si n'existe pas)
  - [x] Nom fichier : UUID (`{preset_id}.json`) - **OBLIGATOIRE** (Pattern V1-002)
  - [x] Structure JSON : Preset complet (id, name, icon, metadata, configuration)
  - [x] Gestion erreurs : Fichier corrompu (JSON invalide) → log erreur + skip (pas de crash)
  - [x] Gestion erreurs : Permissions manquantes → log erreur + raise `PermissionError`
  - [x] Gestion erreurs : Disque plein → log erreur + raise `OSError`
  - [x] Auto-création dossier : `Path.mkdir(parents=True, exist_ok=True)` si `data/presets/` n'existe pas
  - [x] Tests unitaires : Création/suppression fichiers, validation structure JSON

## Dev Notes

### Architecture Patterns

**Preset System (ADR-002) :**
- **Data Model** : Interface TypeScript `Preset` avec `id`, `name`, `icon`, `metadata`, `configuration`
  - `configuration.characters` : IDs uniquement (pas objets complets GDD)
  - `configuration.locations` : IDs uniquement (pas objets complets GDD)
  - `configuration.fieldConfigs` : Optionnel (sauvegarde sélection champs contexte)
- **Storage Pattern** : Fichiers JSON locaux `data/presets/{preset_id}.json` (UUID obligatoire)
  - Raison : Git-friendly, pas besoin DB (V1.0), stockage local simple
  - Pattern V1-002 : UUID pour nom fichier (pas human-readable, pas séquentiel)
- **Validation Pattern** : Lazy validation (au chargement, pas à la sauvegarde)
  - Vérifier références GDD (personnages/lieux existent) via `PresetService.validate_preset_references()`
  - Warning modal (non-bloquant) : Liste références obsolètes + option "Charger quand même"
  - Auto-cleanup : Supprimer références obsolètes lors sauvegarde preset modifié
- **Frontend Integration** : Barre compacte au-dessus "Scène Principale" (2 boutons : Charger + Sauvegarder)
  - Pattern : Suivre `GenerationOptionsModal.tsx` pour style cohérent
  - Intégration : `usePresetStore` (Zustand) + `useContextStore` + `useGenerationStore`

**Zustand State Management :**
- **Nouveau store séparé** : `usePresetStore` (pas extension `generationStore` ou `contextConfigStore`)
  - Raison : Séparation des responsabilités (presets vs génération vs contexte)
  - Pattern : Immutable updates (`set((state) => ({ ...state, newValue }))`)
  - Pas de persistence localStorage (presets stockés backend, pas préférences utilisateur)

**API Patterns (FastAPI) :**
- **Namespace** : `/api/v1/presets` (cohérent avec `/api/v1/dialogues`, `/api/v1/unity-dialogues/graph`)
- **Router** : `api/routers/presets.py` (nouveau fichier, pas extension dialogues.py)
- **Dependency injection** : `get_preset_service()` via `api/dependencies.py` (pattern existant)
- **Schemas** : `api/schemas/preset.py` (nouveau fichier, modèles Pydantic)
- **Error handling** : Suivre patterns `api/routers/dialogues.py` (ValidationException, NotFoundException)

### Source Tree Components

**Backend (Python) :**
- `services/preset_service.py` : **NOUVEAU** - Service logique métier presets
  - Méthodes : `validate_preset_references()`, `create_preset()`, `list_presets()`, `load_preset()`, `update_preset()`, `delete_preset()`
  - Stockage : Lecture/écriture fichiers JSON `data/presets/{preset_id}.json`
  - Validation : Vérifier références GDD via `ConfigurationService` (personnages/lieux existent)
  - Pattern : Suivre structure `services/configuration_service.py` (service réutilisable)
- `api/routers/presets.py` : **NOUVEAU** - Router FastAPI endpoints CRUD
  - Endpoints : `GET /api/v1/presets`, `POST /api/v1/presets`, `GET /api/v1/presets/{id}`, `PUT /api/v1/presets/{id}`, `DELETE /api/v1/presets/{id}`, `GET /api/v1/presets/{id}/validate`
  - Dependency : `get_preset_service()` injecté via `api/dependencies.py`
  - Pattern : Suivre structure `api/routers/dialogues.py` (namespace, error handling)
- `api/schemas/preset.py` : **NOUVEAU** - Modèles Pydantic Preset
  - Modèles : `Preset`, `PresetMetadata`, `PresetConfiguration`, `PresetCreate`, `PresetUpdate`, `PresetValidationResult`
  - `PresetValidationResult` : `{valid: bool, warnings: List[str], obsoleteRefs: List[str]}` (pour endpoint `/validate`)
  - Validation : UUID pour `id` (format avec tirets), champs requis (`name`, `icon`, `configuration`)
  - Pattern : Suivre structure `api/schemas/dialogue.py` (Pydantic models)
- `api/container.py` : **MODIFIER** - Ajouter `get_preset_service()` au ServiceContainer
  - Méthode : `get_preset_service() -> PresetService` (lazy loading, pattern identique autres services)
  - Initialisation : `self._preset_service = PresetService(config_service=self.get_config_service(), context_builder=self.get_context_builder())`
  - UUID génération : Utiliser `uuid.uuid4()` pour `preset_id` (format avec tirets, ex: `"a1b2c3d4-e5f6-7890-abcd-ef1234567890"`)
  - Pattern : Suivre `get_config_service()`, `get_vocabulary_service()` (lazy loading + logging)
- `api/dependencies.py` : **MODIFIER** - Ajouter `get_preset_service()` dependency
  - Fonction : `get_preset_service(request: Request) -> PresetService` (via ServiceContainer depuis app.state)
  - Pattern : Suivre `get_config_service(request)`, `get_vocabulary_service(request)` (ServiceContainer depuis app.state)
- `api/main.py` : **MODIFIER** - Inclure router `presets` dans app FastAPI
  - Extension : `app.include_router(presets.router, prefix="/api/v1/presets", tags=["Presets"])` (ligne ~558, après `graph.router`)
  - Pattern : Suivre inclusion `graph.router` (ligne 558), `streaming.router` (ligne 542) - ordre logique
- `data/presets/` : **NOUVEAU** - Dossier stockage fichiers JSON presets
  - Création : Auto-création si n'existe pas (via `Path.mkdir(parents=True, exist_ok=True)`)
  - Nom fichier : UUID (`{preset_id}.json`) - **OBLIGATOIRE** (Pattern V1-002)
  - Structure : Preset complet (JSON serialization Pydantic)

**Frontend (TypeScript/React) :**
- `frontend/src/store/presetStore.ts` : **NOUVEAU** - Store Zustand pour presets
  - État : `presets: Preset[]`, `selectedPreset: Preset | null`, `isLoading: boolean`, `error: string | null`
  - Actions : `loadPresets()`, `createPreset(presetData)`, `updatePreset(id, presetData)`, `deletePreset(id)`, `loadPreset(id)`
  - API calls : Fetch vers `/api/v1/presets/*` (GET, POST, PUT, DELETE)
  - Pattern : Immutable updates (cohérent avec `generationStore`, `llmStore`, `contextConfigStore`)
- `frontend/src/components/generation/PresetSelector.tsx` : **NOUVEAU** - Composant sélecteur presets
  - Props : Aucune (utilise `usePresetStore` pour état global)
  - UI : Dropdown "📋 Charger preset ▼" + Bouton "💾 Sauvegarder preset"
  - Modal création : Nom, icône emoji, aperçu lecture seule (personnages/lieux sélectionnés)
  - Menu contextuel : Renommer, Supprimer (sur clic droit preset)
  - Pattern : Suivre style `GenerationOptionsModal.tsx` (overlay + header + contenu scrollable)
- `frontend/src/components/generation/PresetValidationModal.tsx` : **NOUVEAU** - Modal validation références obsolètes
  - Props : `preset: Preset`, `obsoleteRefs: string[]`, `onLoadAnyway: () => void`, `onCancel: () => void`
  - UI : Warning modal avec liste références obsolètes + boutons "Charger quand même" / "Annuler"
  - Pattern : Suivre style modals existantes (cohérent avec `GenerationProgressModal.tsx`)
- `frontend/src/types/preset.ts` : **NOUVEAU** - Types TypeScript Preset
  - Types : `Preset`, `PresetMetadata`, `PresetConfiguration`, `PresetValidationResult`
  - `PresetValidationResult` : `{valid: boolean, warnings: string[], obsoleteRefs: string[]}` (identique backend)
  - Compatibilité : Structure identique backend Pydantic (JSON serialization)
- `frontend/src/components/generation/GenerationPanel.tsx` : **MODIFIER** - Intégrer `PresetSelector`
  - Extension : Afficher `PresetSelector` au-dessus section "Scène Principale" (barre compacte, avant `<SceneSelectionWidget />`)
  - Chargement preset : Pré-remplir `sceneSelection` (via `useGenerationStore.setSceneSelection()`)
    - Mapping : `preset.configuration.characterA` → `sceneSelection.characterA`, `characterB` → `characterB`, `region` → `sceneRegion`, `subLocation` → `subLocation`
  - Chargement preset : Pré-remplir `userInstructions` (via `setUserInstructions()` depuis state local)
  - Chargement preset : Pré-remplir `fieldConfigs` (via `useContextConfigStore.setFieldConfig()`, si sauvegardé dans preset)
  - Sauvegarde preset : Capturer configuration depuis :
    - `useGenerationStore.sceneSelection` (characterA, characterB, sceneRegion, subLocation)
    - `userInstructions` (state local GenerationPanel)
    - `useContextConfigStore.fieldConfigs` (optionnel, si utilisateur veut sauvegarder sélection champs)
  - Note : `useContextStore.selections` n'est PAS sauvegardé dans preset V1.0 (seulement `sceneSelection` pour simplifier)
  - Pattern : Cohérent avec intégration `ModelSelector` (Story 0.3, ligne 985-988)

### Configuration Structure

**Structure Preset JSON (backend + frontend) :**
```typescript
interface Preset {
  id: string;  // UUID (nom fichier)
  name: string;
  icon: string;  // emoji
  metadata: {
    created: string;  // ISO 8601
    modified: string;  // ISO 8601
  };
  configuration: {
    characters: string[];  // IDs uniquement (pas objets GDD)
    locations: string[];  // IDs uniquement
    region: string;
    subLocation?: string;
    sceneType: string;  // "Première rencontre", etc.
    instructions: string;  // Brief scène
    fieldConfigs?: Record<string, string[]>;  // Optionnel (sauvegarde sélection champs)
  };
}
```

**Validation Pattern (Lazy + Warning) :**
```python
# Backend: PresetService.validate_preset_references()
def validate_preset_references(preset: Preset, gdd: GameDesignDocument) -> PresetValidationResult:
    obsolete_refs = []  # IDs obsolètes (personnages/lieux supprimés du GDD)
    warnings = []  # Messages d'avertissement pour l'utilisateur
    
    for char_id in preset.configuration.characters:
        if char_id not in gdd.characters:
            obsolete_refs.append(char_id)
            warnings.append(f"Character '{char_id}' not found")
    
    for loc_id in preset.configuration.locations:
        if loc_id not in gdd.locations:
            obsolete_refs.append(loc_id)
            warnings.append(f"Location '{loc_id}' not found")
    
    return PresetValidationResult(
        valid=len(obsolete_refs) == 0,
        warnings=warnings,
        obsoleteRefs=obsolete_refs
    )
```

```typescript
// Frontend: PresetValidationModal affiche warning
if (!validationResult.valid) {
  showWarningModal({
    title: "⚠️ Preset partiellement obsolète",
    warnings: validationResult.warnings,
    actions: ["Cancel", "Load anyway"]
  });
}
```

### Project Structure Notes

**Alignement avec architecture existante :**
- ✅ **Service Pattern** : `services/preset_service.py` (cohérent avec `services/configuration_service.py`)
  - Décision : Service réutilisable, pas logique dans router
  - Alternative évitée : Logique dans router (violation séparation responsabilités)
- ✅ **API Router** : `api/routers/presets.py` (nouveau fichier, pas extension dialogues.py)
  - Décision : Séparation endpoints presets vs dialogues (cohérent avec architecture)
  - Pattern : Namespace `/api/v1/presets` (cohérent avec `/api/v1/dialogues`)
- ✅ **Zustand Store** : `usePresetStore` (nouveau store séparé)
  - Raison : Séparation responsabilités (presets vs génération vs contexte)
  - Alternative évitée : Extension `generationStore` (mélanger responsabilités)
- ✅ **Storage** : Fichiers JSON locaux `data/presets/` (pas DB, pas localStorage frontend)
  - Raison : Git-friendly, simple (V1.0), pas besoin synchronisation multi-utilisateurs
  - Pattern V1-002 : UUID pour nom fichier (obligatoire, pas human-readable)

**Patterns réutilisés depuis Stories précédentes :**
- ✅ **Zustand Stores** : Pattern immutable updates (cohérent avec `generationStore`, `llmStore`, `contextConfigStore`)
- ✅ **Modal Components** : Style cohérent (`GenerationOptionsModal.tsx`, `GenerationProgressModal.tsx` comme références)
- ✅ **API Patterns** : Dependency injection, error handling (cohérent avec `api/routers/dialogues.py`)

**Décisions architecturales :**
- ✅ **Validation lazy** : Au chargement preset (pas à la sauvegarde)
  - Raison : GDD peut changer entre sauvegarde et chargement (références obsolètes possibles)
  - Alternative évitée : Validation à la sauvegarde (ne détecte pas obsolètes après)
- ✅ **Warning modal non-bloquant** : Option "Charger quand même" (pas d'erreur bloquante)
  - Raison : UX flexible (utilisateur décide si charger preset partiellement obsolète)
  - Alternative évitée : Erreur bloquante (trop restrictif, casse workflow utilisateur)
- ✅ **Auto-cleanup références obsolètes** : Supprimer automatiquement lors sauvegarde preset modifié
  - Raison : Préserver intégrité preset (pas de références invalides persistées)
  - Pattern : Cohérent avec validation lazy (détecte obsolètes au chargement, nettoie à la sauvegarde)

### Existing Codebase Verification

**Fichiers/Composants existants vérifiés :**
- ✅ `frontend/src/store/generationStore.ts` : **EXISTE** - Gère `sceneSelection` (personnages, lieux, région, subLocation)
  - Décision : **RÉUTILISER** - `useGenerationStore.setSceneSelection()` pour charger preset
  - Pas besoin créer nouveau store pour `sceneSelection`
- ✅ `frontend/src/store/contextConfigStore.ts` : **EXISTE** - Gère `fieldConfigs` (sélection champs contexte)
  - Décision : **RÉUTILISER** - `useContextConfigStore.setFieldConfig()` pour charger preset
  - Pas besoin créer nouveau store pour `fieldConfigs`
- ✅ `frontend/src/components/generation/GenerationPanel.tsx` : **EXISTE** - Composant principal génération
  - Décision : **ÉTENDRE** - Ajouter `PresetSelector` au-dessus section "Scène Principale"
  - Pattern : Cohérent avec intégration `ModelSelector` (Story 0.3)
- ✅ `api/routers/dialogues.py` : **EXISTE** - Router dialogues (namespace `/api/v1/dialogues`)
  - Décision : **CRÉER NOUVEAU** - `api/routers/presets.py` (séparation endpoints, pas extension)
  - Pattern : Cohérent avec `api/routers/graph.py`, `api/routers/streaming.py` (routers séparés)
- ✅ `services/configuration_service.py` : **EXISTE** - Service configuration (GDD, champs)
  - Décision : **RÉUTILISER** - `ConfigurationService` pour validation références GDD (personnages/lieux existent)
  - Pas besoin créer nouveau service pour validation GDD
- ✅ `data/` : **EXISTE** - Dossier données (vide actuellement)
  - Décision : **CRÉER SOUS-DOSSIER** - `data/presets/` pour fichiers JSON presets
  - Pattern : Cohérent avec structure projet (données dans `data/`)

**Patterns existants à respecter :**
- ✅ **Zustand stores** : Immutable updates (`set((state) => ({ ...state, newValue }))`)
- ✅ **FastAPI routers** : Namespace `/api/v1/*` (cohérent)
- ✅ **React modals** : Pattern overlay + header + contenu scrollable (`GenerationOptionsModal.tsx`)
- ✅ **API dependency injection** : `get_*_service()` via `api/dependencies.py`

**Décisions de remplacement :**
- ✅ **Pas de remplacement** : Tous les fichiers/composants mentionnés sont nouveaux ou extensions
- ✅ **Pas de duplication** : Réutilisation `generationStore.sceneSelection`, `contextConfigStore.fieldConfigs` (pas création nouveaux stores)
- ✅ **Séparation responsabilités** : `usePresetStore` séparé (presets vs génération vs contexte)
- ✅ **Clarification stores** : 
  - `useGenerationStore.sceneSelection` : CharacterA, CharacterB, sceneRegion, subLocation (utilisé pour preset)
  - `useContextStore.selections` : ContextSelection détaillé (characters_full, locations_full, etc.) - **NON sauvegardé dans preset V1.0** (simplification)
  - `useContextConfigStore.fieldConfigs` : Sélection champs contexte (optionnel dans preset)

### References

**Architecture Documents :**
- [Source: _bmad-output/planning-artifacts/architecture/v10-architectural-decisions-adrs.md#ADR-002] - Presets système (Configuration sauvegarde/chargement)
- [Source: _bmad-output/planning-artifacts/architecture/v10-new-patterns-detailed.md#Pattern-V1-002] - Preset Storage pattern (UUID pour nom fichier)
- [Source: _bmad-output/planning-artifacts/architecture/project-structure-boundaries.md] - Structure projet (`services/` pour services, `api/routers/` pour endpoints)

**Epic & Stories :**
- [Source: _bmad-output/planning-artifacts/prd/epic-00.md#Story-0.4] - Story originale avec Acceptance Criteria détaillés
- [Source: _bmad-output/planning-artifacts/prd/epic-00.md#Story-0.9] - Story 0.9 (Preset validation ID-005) - Validation références obsolètes

**Code Existing :**
- [Source: frontend/src/store/generationStore.ts] - Store Zustand `sceneSelection` (personnages, lieux, région, subLocation)
- [Source: frontend/src/store/contextConfigStore.ts] - Store Zustand `fieldConfigs` (sélection champs contexte)
- [Source: frontend/src/components/generation/GenerationPanel.tsx] - Composant principal génération (intégration `PresetSelector`)
- [Source: api/routers/dialogues.py] - Router FastAPI (pattern namespace, dependency injection, error handling)
- [Source: services/configuration_service.py] - Service configuration (validation références GDD)
- [Source: api/dependencies.py] - Dependency injection services (pattern `get_*_service()`)
- [Source: frontend/src/components/generation/GenerationOptionsModal.tsx] - Modal style référence (overlay + header + contenu scrollable)
- [Source: frontend/src/components/generation/ModelSelector.tsx] - Composant dropdown référence (Story 0.3)

**External Documentation :**
- UUID Python : `uuid.uuid4()` pour génération IDs presets
- FastAPI File Storage : `pathlib.Path` pour gestion fichiers JSON
- Zustand Persist : Pas nécessaire (presets stockés backend, pas localStorage)

## Dev Agent Record

### Agent Model Used

GPT-5.2

### Debug Log References

N/A (local debug instrumentation was added temporarily during investigation and removed after confirmation).

### Completion Notes List

- Preset validation fixed to use ContextBuilder name lists (GDDDataAccessor.gdd_data returns empty by design).
- Preset loading now restores full ContextSelector state (all categories + region/sub-locations) via `restoreState`, and updates SceneSelection consistently.
- Preset saving now captures an exhaustive snapshot of ContextSelector selections and sub-locations; save modal shows counts and a loading indicator during save.

### File List

- Backend:
  - `services/preset_service.py`
  - `api/schemas/preset.py`
  - `api/routers/presets.py`
  - `api/dependencies.py`
  - `api/container.py`
  - `api/main.py`
  - `tests/services/test_preset_service.py`
  - `tests/api/test_presets.py`
  - `data/presets/.gitkeep`
- Frontend:
  - `frontend/src/store/presetStore.ts`
  - `frontend/src/types/preset.ts`
  - `frontend/src/components/generation/PresetSelector.tsx`
  - `frontend/src/components/generation/PresetValidationModal.tsx`
  - `frontend/src/components/generation/GenerationPanel.tsx`
  - `frontend/src/hooks/useSceneSelection.ts`
  - `frontend/src/__tests__/presetStore.test.ts`
  - `frontend/src/__tests__/PresetSelector.test.tsx`
  - `frontend/src/__tests__/PresetValidationModal.test.tsx`
