# Optimisations - Panneau Modal de Génération

## Analyse des phases et goulots d'étranglement

### Phase 1: Initialisation du panneau (montage)

**Appels API identifiés:**
- `configAPI.listLLMModels()` - Ligne 172 `GenerationPanel.tsx`
- `contextAPI.listCharacters()` - Ligne 61 `useSceneSelection.ts`
- `contextAPI.listRegions()` - Ligne 73 `useSceneSelection.ts`

**Problèmes:**
- ❌ Pas de cache - appels répétés à chaque montage
- ❌ Appels séquentiels dans `useSceneSelection` (Promise.all mais pas de cache)
- ❌ `loadModels()` s'exécute à chaque montage même si les modèles n'ont pas changé

**Optimisations proposées:**

1. **Cache des modèles LLM** (Impact: ⭐⭐⭐)
   - Créer un store Zustand dédié avec TTL (ex: 5 minutes)
   - Invalider uniquement si backend signale un changement
   - Réduit ~200-500ms par ouverture de panneau

2. **Cache des personnages/régions** (Impact: ⭐⭐⭐⭐)
   - Ces données changent rarement
   - Cache dans `contextStore` avec invalidation manuelle ou TTL long (30 min)
   - Réduit ~300-800ms par ouverture

3. **Chargement parallèle optimisé** (Impact: ⭐⭐)
   - Déjà en `Promise.all` mais ajouter cache avant
   - Précharger au démarrage de l'app (Dashboard mount)

### Phase 2: Sélection de scène

**Appels API identifiés:**
- `contextAPI.getSubLocations(regionName)` - Ligne 90 `useSceneSelection.ts`
- Appelé à chaque changement de région

**Problèmes:**
- ❌ Pas de cache - même région = même appel
- ❌ Appel synchrone bloque l'UI

**Optimisations proposées:**

4. **Cache des sous-lieux par région** (Impact: ⭐⭐⭐⭐)
   - Map `Map<regionName, subLocations[]>` dans le store
   - Cache persistant (localStorage) avec version
   - Réduit ~200-400ms par changement de région

5. **Chargement optimiste** (Impact: ⭐⭐)
   - Afficher immédiatement les sous-lieux du cache
   - Rafraîchir en arrière-plan si nécessaire

### Phase 3: Estimation des tokens

**Appels API identifiés:**
- `dialoguesAPI.previewPrompt()` - Ligne 131 `useTokenEstimation.ts`
- Déclenché avec debounce 500ms à chaque changement

**Problèmes:**
- ❌ Pas de cache basé sur hash
- ❌ Debounce 500ms peut être réduit
- ❌ Appel même si prompt identique (hash check existe mais après appel)

**Optimisations proposées:**

6. **Cache par hash de prompt** (Impact: ⭐⭐⭐⭐⭐)
   - Vérifier `promptHash` AVANT l'appel API
   - Si hash identique → skip l'appel
   - Réduit ~80% des appels redondants (500-2000ms économisés)

7. **Debounce adaptatif** (Impact: ⭐⭐)
   - Debounce court (200ms) pour modifications mineures
   - Debounce long (800ms) pour modifications majeures (instructions)
   - Améliore la réactivité perçue

8. **Estimation locale rapide** (Impact: ⭐⭐⭐)
   - Estimation approximative côté client (tokens ≈ length/4)
   - Afficher immédiatement, rafraîchir avec API
   - Améliore la réactivité perçue

### Phase 4: Création du job (avant génération)

**Appels API identifiés:**
- `dialoguesAPI.createGenerationJob()` - Ligne 204 `useGenerationHandlers.ts`
- `checkBudget()` - Ligne 160 `useGenerationHandlers.ts`

**Problèmes:**
- ❌ Vérification budget séquentielle (bloque la génération)
- ❌ Pas de pré-validation côté client

**Optimisations proposées:**

9. **Vérification budget en parallèle** (Impact: ⭐⭐)
   - Lancer `checkBudget()` en parallèle avec la construction de la requête
   - Réduit ~100-300ms si budget check est lent

10. **Pré-validation côté client** (Impact: ⭐⭐⭐)
    - Valider les champs requis avant l'appel API
    - Évite les appels inutiles (400 Bad Request)
    - Réduit ~200-500ms pour erreurs évitables

### Phase 5: Streaming SSE (pendant génération)

**Problèmes identifiés:**
- ⚠️ Délai de 500ms avant fermeture EventSource après 'complete' (ligne 169)
- ⚠️ Pas de compression des chunks
- ⚠️ Buffer de réordonnancement peut être optimisé

**Optimisations proposées:**

11. **Réduction délai fermeture SSE** (Impact: ⭐)
    - Réduire de 500ms à 100ms (suffisant pour événements en transit)
    - Gain marginal mais améliore la réactivité

12. **Compression SSE** (Impact: ⭐⭐⭐)
    - Backend: compresser les chunks JSON
    - Frontend: décompresser côté client
    - Réduit la latence réseau pour gros prompts

### Phase 6: Chargement du graphe (après génération)

**Appels API identifiés:**
- `graphAPI.loadGraph()` - Ligne 146 `graphStore.ts`
- Appelé dans `onComplete` callback SSE

**Problèmes:**
- ❌ Appel séquentiel après réception du JSON
- ❌ Parsing JSON peut être optimisé

**Optimisations proposées:**

13. **Parsing JSON optimisé** (Impact: ⭐⭐)
    - Utiliser `JSON.parse()` avec streaming si possible
    - Worker thread pour parsing si JSON > 1MB
    - Réduit ~50-200ms pour gros graphes

14. **Chargement asynchrone du graphe** (Impact: ⭐⭐⭐)
    - Ne pas bloquer l'UI pendant le chargement
    - Afficher un indicateur de progression
    - Améliore la réactivité perçue

## Priorisation des optimisations

### Quick wins (implémentation rapide, impact élevé)

1. **Cache par hash de prompt** (#6) - ⭐⭐⭐⭐⭐
   - Impact: Réduit 80% des appels redondants
   - Effort: 2-3h
   - Fichiers: `useTokenEstimation.ts`, `generationStore.ts`

2. **Cache personnages/régions** (#2) - ⭐⭐⭐⭐
   - Impact: Réduit 300-800ms par ouverture
   - Effort: 3-4h
   - Fichiers: `useSceneSelection.ts`, `contextStore.ts`

3. **Cache sous-lieux par région** (#4) - ⭐⭐⭐⭐
   - Impact: Réduit 200-400ms par changement région
   - Effort: 2h
   - Fichiers: `useSceneSelection.ts`, `contextStore.ts`

### Moyen terme (impact moyen, effort modéré)

4. **Cache modèles LLM** (#1) - ⭐⭐⭐
   - Impact: Réduit 200-500ms par ouverture
   - Effort: 2h
   - Fichiers: Nouveau store ou `llmStore.ts`

5. **Estimation locale rapide** (#8) - ⭐⭐⭐
   - Impact: Améliore réactivité perçue
   - Effort: 3h
   - Fichiers: `useTokenEstimation.ts`

6. **Pré-validation côté client** (#10) - ⭐⭐⭐
   - Impact: Évite appels inutiles
   - Effort: 2h
   - Fichiers: `useGenerationHandlers.ts`

### Long terme (optimisations avancées)

7. **Compression SSE** (#12) - ⭐⭐⭐
   - Impact: Réduit latence réseau
   - Effort: 4-6h (backend + frontend)
   - Fichiers: Backend SSE endpoint, `useSSEStreaming.ts`

8. **Worker thread pour parsing JSON** (#13) - ⭐⭐
   - Impact: Réduit 50-200ms pour gros graphes
   - Effort: 4h
   - Fichiers: `graphStore.ts`, nouveau worker

## Estimation gains totaux

**Scénario typique (génération complète):**
- Avant: ~3-5s d'attente totale (initialisation + estimation + génération)
- Après optimisations quick wins: ~1.5-2.5s
- **Gain: 40-50% de réduction du temps d'attente**

**Scénario répétitif (changements mineurs):**
- Avant: ~2-3s par changement
- Après cache hash: ~0.3-0.5s
- **Gain: 80-85% de réduction**

## Notes d'implémentation

### Cache par hash (priorité #1)

```typescript
// Dans useTokenEstimation.ts
const estimateTokens = useCallback(async () => {
  // ... validation ...
  
  // Calculer hash AVANT l'appel API
  const contextSelections = buildContextSelections()
  const stateHash = computeStateHash({
    userInstructions,
    contextSelections,
    maxContextTokens,
    // ... autres paramètres ...
  })
  
  // Vérifier cache AVANT appel
  if (stateHash === promptHash && tokenCount !== null) {
    return // Skip l'appel API
  }
  
  // Appel API seulement si hash différent
  const response = await dialoguesAPI.previewPrompt({...})
  // ...
}, [...])
```

### Cache personnages/régions (priorité #2)

```typescript
// Nouveau store ou extension contextStore
interface ContextCache {
  characters: { data: string[], timestamp: number }
  regions: { data: string[], timestamp: number }
  subLocations: Map<string, { data: string[], timestamp: number }>
}

const CACHE_TTL = 30 * 60 * 1000 // 30 minutes

// Dans useSceneSelection.ts
const loadCharacters = useCallback(async () => {
  const cached = contextStore.getState().cachedCharacters
  if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
    setData(prev => ({ ...prev, characters: cached.data }))
    return
  }
  
  const response = await contextAPI.listCharacters()
  contextStore.getState().setCachedCharacters(response.characters)
  // ...
}, [])
```

## Conclusion

Les optimisations prioritaires (#1, #2, #4) peuvent réduire de **40-50%** le temps d'attente total, avec un effort modéré (6-9h de développement). Les optimisations de cache sont particulièrement efficaces car elles éliminent les appels redondants, qui représentent la majorité des latences perçues.
