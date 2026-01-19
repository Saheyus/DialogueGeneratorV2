# Story 0.9: Preset validation (ID-005)

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **utilisateur chargeant un preset**,
I want **être averti si le preset référence des personnages/lieux qui n'existent plus dans le GDD**,
So that **je peux décider de charger le preset quand même ou le mettre à jour**.

## Acceptance Criteria

1. **Given** un preset sauvegardé référence le personnage "Akthar" et le lieu "Port de Valdris"
   **When** je charge le preset après que "Akthar" ait été supprimé du GDD
   **Then** un warning modal s'affiche "Références obsolètes détectées : Personnage 'Akthar'"
   **And** le lieu "Port de Valdris" est chargé normalement (référence valide)
   **And** j'ai deux options : "Charger quand même" ou "Annuler"

2. **Given** je clique sur "Charger quand même"
   **When** le preset est chargé
   **Then** les références obsolètes sont ignorées (champs vides)
   **And** les références valides sont chargées (personnages/lieux existants)
   **And** un message "Preset chargé avec 1 référence obsolète ignorée" s'affiche

3. **Given** je clique sur "Annuler"
   **When** je ferme le warning
   **Then** le preset n'est pas chargé
   **And** je reste sur l'écran de sélection de preset

4. **Given** un preset avec toutes les références valides
   **When** je charge le preset
   **Then** aucun warning n'est affiché
   **And** le preset est chargé immédiatement

5. **Given** je modifie un preset avec références obsolètes
   **When** je sauvegarde le preset
   **Then** les références obsolètes sont supprimées automatiquement du preset
   **And** un message "Preset mis à jour - références obsolètes supprimées" s'affiche

## Tasks / Subtasks

- [ ] Task 1: Améliorer chargement preset avec filtrage références obsolètes (AC: #2)
  - [ ] Modifier `handleValidationConfirm` dans `GenerationPanel.tsx` pour filtrer références obsolètes avant `applyPreset()` (ligne 936-944)
  - [ ] Créer fonction `filterObsoleteReferences(preset, obsoleteRefs)` qui supprime références obsolètes de `preset.configuration`
  - [ ] Filtrer personnages obsolètes : `preset.configuration.characters = preset.configuration.characters.filter(c => !obsoleteRefs.includes(c))`
  - [ ] Filtrer lieux obsolètes : `preset.configuration.locations = preset.configuration.locations.filter(l => !obsoleteRefs.includes(l))`
  - [ ] Appliquer preset filtré avec `applyPreset(presetFiltered)` au lieu de `pendingPreset` direct
  - [ ] Améliorer toast : "Preset chargé avec {count} référence(s) obsolète(s) ignorée(s)" au lieu de "Preset chargé (avec warnings)"
  - [ ] Utiliser `validationResult.obsoleteRefs.length` pour compter références obsolètes
  - [ ] Tests E2E : Charger preset avec obsolètes, références obsolètes ignorées, toast affiché

- [ ] Task 2: Implémenter auto-cleanup références obsolètes lors sauvegarde (AC: #5)
  - [ ] Modifier `PresetService.create_preset()` pour valider et nettoyer références avant sauvegarde
  - [ ] Appeler `validate_preset_references()` avant sauvegarde
  - [ ] Si références obsolètes détectées : Filtrer automatiquement (supprimer obsolètes de `preset.configuration`)
  - [ ] Sauvegarder preset nettoyé (sans références obsolètes)
  - [ ] Logger : "Preset créé avec {count} référence(s) obsolète(s) supprimée(s)"
  - [ ] Modifier `PresetService.update_preset()` pour même logique auto-cleanup
  - [ ] Retourner message dans réponse API : "Preset mis à jour - {count} référence(s) obsolète(s) supprimée(s)"
  - [ ] Tests unitaires : Auto-cleanup lors création, auto-cleanup lors mise à jour

- [ ] Task 3: Améliorer messages frontend après chargement/sauvegarde (AC: #2, #5)
  - [ ] Modifier `handleValidationConfirm` pour afficher toast avec nombre références obsolètes ignorées (déjà fait dans Task 1)
  - [ ] Modifier `handleCreatePreset` dans `PresetSelector.tsx` pour afficher toast si références obsolètes supprimées (après réponse API)
  - [ ] Vérifier réponse API backend : Si message auto-cleanup présent, afficher toast "Preset mis à jour - X référence(s) obsolète(s) supprimée(s)"
  - [ ] Utiliser `useToast` existant pour messages : "Preset chargé avec X référence(s) obsolète(s) ignorée(s)"
  - [ ] Tests E2E : Messages affichés correctement après chargement/sauvegarde

- [ ] Task 4: Vérifier intégration validation dans workflow chargement (AC: #1, #3, #4)
  - [ ] Vérifier que `handlePresetLoaded` appelle bien validation avant chargement (ligne 869 `GenerationPanel.tsx`) - ✅ DÉJÀ FAIT
  - [ ] Vérifier que `PresetValidationModal` s'affiche correctement si `!validationResult.valid` (ligne 872-876) - ✅ DÉJÀ FAIT
  - [ ] Vérifier que preset valide charge directement sans modal (ligne 877-881) - ✅ DÉJÀ FAIT
  - [ ] Vérifier que "Annuler" ferme modal sans charger preset via `handleValidationClose` (ligne 946-950) - ✅ DÉJÀ FAIT
  - [ ] Tests E2E : Workflow complet validation (valide charge direct, invalide affiche modal, annuler ne charge pas)

- [ ] Task 5: Améliorer messages validation modal (AC: #1)
  - [ ] Vérifier que messages warnings sont clairs : "Personnage 'Akthar' not found in GDD" (ligne 217 `preset_service.py`)
  - [ ] Vérifier que modal affiche bien toutes les références obsolètes (ligne 125-140 `PresetValidationModal.tsx`)
  - [ ] S'assurer que format message est cohérent : "Character '{name}' not found" vs "Location '{name}' not found"
  - [ ] Tests E2E : Messages validation clairs et complets

- [ ] Task 6: Validation et tests (AC: #1, #2, #3, #4, #5)
  - [ ] Tests unitaires : `filterObsoleteReferences()` filtre correctement, auto-cleanup sauvegarde
  - [ ] Tests intégration : Endpoint validation retourne obsolètes, auto-cleanup sauvegarde fonctionne
  - [ ] Tests E2E : Workflow complet validation (charger avec obsolètes, "Charger quand même", auto-cleanup sauvegarde)

## Dev Notes

### Architecture Patterns (Extension Story 0.4)

**Réutilisation existante :**
- ✅ **Service validation existant** : `PresetService.validate_preset_references()` existe déjà (ligne 187-235 `services/preset_service.py`)
  - **DÉCISION** : Réutiliser pour validation, étendre pour auto-cleanup sauvegarde
  - **COMMENT** : Appeler `validate_preset_references()` avant sauvegarde, filtrer obsolètes automatiquement
- ✅ **Endpoint validation existant** : `/api/v1/presets/{id}/validate` existe déjà (ligne 183-223 `api/routers/presets.py`)
  - **DÉCISION** : Réutiliser pour validation au chargement
  - **COMMENT** : Déjà appelé dans `handlePresetLoaded` (ligne 869 `GenerationPanel.tsx`)
- ✅ **Modal validation existante** : `PresetValidationModal.tsx` existe déjà (ligne 1-178)
  - **DÉCISION** : Réutiliser pour affichage warnings
  - **COMMENT** : Déjà intégrée dans `GenerationPanel.tsx` (ligne 1567-1575)
- ✅ **Workflow validation existant** : `handlePresetLoaded` appelle déjà validation (ligne 866-886 `GenerationPanel.tsx`)
  - **DÉCISION** : Améliorer pour filtrer obsolètes après "Charger quand même"
  - **COMMENT** : Ajouter filtrage références obsolètes avant `applyPreset()`

**Filtrage références obsolètes :**
- **Fonction helper** : `filterObsoleteReferences(preset, obsoleteRefs)` dans `GenerationPanel.tsx` ou utilitaire
- **Filtrage personnages** : `preset.configuration.characters = preset.configuration.characters.filter(c => !obsoleteRefs.includes(c))`
- **Filtrage lieux** : `preset.configuration.locations = preset.configuration.locations.filter(l => !obsoleteRefs.includes(l))`
- **Préserver autres champs** : Ne pas modifier `region`, `subLocation`, `instructions`, etc.

**Auto-cleanup sauvegarde :**
- **Avant sauvegarde** : Appeler `validate_preset_references()` dans `create_preset()` et `update_preset()`
- **Si obsolètes** : Filtrer automatiquement avant sauvegarde (supprimer obsolètes de `preset.configuration`)
- **Logger** : "Preset créé/mis à jour avec {count} référence(s) obsolète(s) supprimée(s)"
- **Retourner info** : Optionnel : retourner message dans réponse API pour affichage frontend

**Messages utilisateur :**
- **Chargement avec obsolètes** : Toast "Preset chargé avec {count} référence(s) obsolète(s) ignorée(s)"
- **Sauvegarde avec obsolètes** : Toast "Preset mis à jour - {count} référence(s) obsolète(s) supprimée(s)"
- **Format** : Utiliser `useToast` existant avec type 'info' ou 'warning'

### Fichiers existants à vérifier et étendre

**Backend :**
- ✅ `services/preset_service.py` : Service validation existe (ligne 187-235)
  - **DÉCISION** : Étendre `create_preset()` et `update_preset()` pour auto-cleanup
  - **COMMENT** : Appeler `validate_preset_references()` avant sauvegarde, filtrer obsolètes automatiquement
- ✅ `api/routers/presets.py` : Endpoint validation existe (ligne 183-223)
  - **DÉCISION** : Réutiliser tel quel (déjà fonctionnel)
  - **COMMENT** : Pas de modification nécessaire, déjà utilisé par frontend

**Frontend :**
- ✅ `frontend/src/components/generation/GenerationPanel.tsx` : Handlers existent (ligne 866-950)
  - **DÉCISION** : Améliorer `handleValidationConfirm` pour filtrer obsolètes avant `applyPreset()`
  - **COMMENT** : Ajouter fonction `filterObsoleteReferences()`, appeler dans `handleValidationConfirm`, améliorer toast
- ✅ `frontend/src/components/generation/PresetSelector.tsx` : Handler `handleCreatePreset` existe (ligne 57-71)
  - **DÉCISION** : Améliorer pour afficher toast si références obsolètes supprimées
  - **COMMENT** : Vérifier réponse API pour message auto-cleanup, afficher toast si présent
- ✅ `frontend/src/components/generation/PresetValidationModal.tsx` : Modal existe (ligne 1-178)
  - **DÉCISION** : Réutiliser tel quel (déjà fonctionnel)
  - **COMMENT** : Pas de modification nécessaire, déjà intégrée correctement

### Patterns existants à respecter

**FastAPI routers :**
- Namespace `/api/v1/presets/*` (cohérent)
- Pattern endpoint : `@router.post("", response_model=Preset)`
- Gestion erreurs : `HTTPException` avec status_code approprié
- Logging : Utiliser `logger.info()` avec métadonnées

**React composants :**
- Pattern modal : `PresetValidationModal` existant (utiliser pour warnings)
- Pattern toast : `useToast` existant (utiliser pour messages après chargement/sauvegarde)
- Pattern filtrage : `Array.filter()` pour supprimer références obsolètes

**Zustand stores :**
- Immutable updates : `set((state) => ({ ...state, newValue }))`
- Pattern preset : `usePresetStore` existant (utiliser pour chargement/sauvegarde)

**Service patterns :**
- Validation lazy : Validation au chargement, pas à la sauvegarde (déjà implémenté)
- Auto-cleanup : Nettoyage automatique lors sauvegarde (à ajouter)

### Filtrage références obsolètes

**Fonction helper :**
```typescript
function filterObsoleteReferences(preset: Preset, obsoleteRefs: string[]): Preset {
  const filteredPreset = { ...preset }
  filteredPreset.configuration = {
    ...preset.configuration,
    characters: preset.configuration.characters.filter(c => !obsoleteRefs.includes(c)),
    locations: preset.configuration.locations.filter(l => !obsoleteRefs.includes(l))
  }
  return filteredPreset
}
```

**Intégration dans workflow :**
- Après confirmation modal "Charger quand même" : Appeler `filterObsoleteReferences()`
- Appliquer preset filtré : `applyPreset(filteredPreset)`
- Afficher toast : "Preset chargé avec {count} référence(s) obsolète(s) ignorée(s)"

### Auto-cleanup sauvegarde

**Backend logique :**
```python
def create_preset(self, preset_data: Dict[str, Any]) -> Preset:
    # Créer preset
    preset = Preset(...)
    
    # Valider références
    validation = self.validate_preset_references(preset)
    
    # Auto-cleanup si obsolètes
    if not validation.valid:
        preset.configuration.characters = [
            c for c in preset.configuration.characters 
            if c not in validation.obsoleteRefs
        ]
        preset.configuration.locations = [
            l for l in preset.configuration.locations 
            if l not in validation.obsoleteRefs
        ]
        logger.info(f"Preset créé avec {len(validation.obsoleteRefs)} référence(s) obsolète(s) supprimée(s)")
    
    # Sauvegarder preset nettoyé
    self._save_preset_to_disk(preset)
    return preset
```

**Même logique pour `update_preset()`**

### Références techniques

**Source: `_bmad-output/planning-artifacts/prd/epic-00.md#Story-0.9`**
- Story complète avec acceptance criteria et technical requirements

**Source: `services/preset_service.py#validate_preset_references` (ligne 187-235)**
- Méthode validation existante à réutiliser

**Source: `services/preset_service.py#create_preset` (ligne 52-82)**
- Méthode création existante à étendre pour auto-cleanup

**Source: `services/preset_service.py#update_preset` (ligne 137-168)**
- Méthode mise à jour existante à étendre pour auto-cleanup

**Source: `frontend/src/components/generation/GenerationPanel.tsx#handleValidationConfirm` (ligne 936-944)**
- Handler confirmation existant à améliorer pour filtrage obsolètes

**Source: `frontend/src/components/generation/PresetSelector.tsx#handleCreatePreset` (ligne 57-71)**
- Handler création existant à améliorer pour message auto-cleanup

**Source: `frontend/src/components/generation/PresetValidationModal.tsx` (ligne 1-178)**
- Modal validation existante (réutiliser tel quel)

**Source: ID-005 (Architecture Document)**
- Décision architecture : Preset validation (warning + "Charger quand même")

**Source: Story 0.4 (Presets système)**
- Système presets existant (référence pour intégration)

### Project Structure Notes

**Alignment avec structure unifiée :**
- ✅ Backend services : `services/preset_service.py` (cohérent)
- ✅ Backend API : `api/routers/presets.py` (cohérent)
- ✅ Frontend components : `frontend/src/components/generation/` (cohérent)
- ✅ Frontend stores : `frontend/src/store/presetStore.ts` (cohérent)

**Détecté conflits ou variances :**
- Aucun conflit détecté, extension cohérente avec architecture existante

### References

- [Source: `_bmad-output/planning-artifacts/prd/epic-00.md#Story-0.9`] Story complète avec requirements
- [Source: ID-005] Architecture Decision : Preset validation (warning + "Charger quand même")
- [Source: `services/preset_service.py#validate_preset_references`] Méthode validation existante à réutiliser
- [Source: `services/preset_service.py#create_preset`] Méthode création existante à étendre
- [Source: `frontend/src/components/generation/GenerationPanel.tsx#handlePresetLoaded`] Handler chargement existant à améliorer
- [Source: `frontend/src/components/generation/PresetValidationModal.tsx`] Modal validation existante (réutiliser)
- [Source: Story 0.4] Presets système (système presets existant)

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
