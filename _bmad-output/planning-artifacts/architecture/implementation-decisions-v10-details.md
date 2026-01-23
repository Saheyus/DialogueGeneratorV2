# Implementation Decisions (V1.0 Details)

Les décisions suivantes clarifient les détails d'implémentation pour les features V1.0. Ces décisions sont pragmatiques, testables, et cohérentes avec l'architecture baseline.

### ID-001: Auto-save Conflict Resolution

**Decision:** Last Write Wins (LWW)

**Context:**  
MVP mono-utilisateur sans collaboration temps réel. Besoin d'une stratégie simple et prévisible.

**Rationale:**
- Simple à implémenter et à tester
- Prévisible pour l'utilisateur (pas de merge surprenant)
- Suffisant pour MVP mono-utilisateur
- V2.0 : Migration vers CRDT/OT si collaboration multi-utilisateurs

**Behavior:**
- Auto-save toutes les **2 minutes** (intervalle configurable)
- Aucun merge intelligent (écrase sauvegarde précédente)
- Indicateur visuel "Sauvegardé il y a Xs" dans UI
- Manual save disponible via Ctrl+S (immediate)

**Implementation:**
- Frontend : `setInterval()` dans `useAutoSave()` hook
- Backend : `/api/v1/interactions/{id}` PUT endpoint
- State : Zustand `lastSaveTimestamp` pour indicateur UI

**Tests Required:**
- Unit : Hook auto-save timer
- Integration : PUT endpoint écrase données existantes
- E2E : Indicateur "Sauvegardé il y a Xs" se met à jour

---

### ID-002: Validation Structurelle (Cycles)

**Decision:** Warning non-bloquant

**Context:**  
Authoring tool créatif où cycles peuvent être intentionnels (boucles narratives, retours en arrière).

**Rationale:**
- Authoring tool privilégie créativité sur strictness
- Cycles peuvent être intentionnels (gameplay loops)
- Export Unity peut ajouter validation stricte optionnelle
- Warning informe sans bloquer workflow

**Behavior:**
- Badge warning orange sur graphe : "⚠️ 3 cycles détectés"
- Panneau Détails liste cycles avec navigation (clic → highlight nœuds)
- **Pas de blocage** génération/sauvegarde/export
- Export Unity : Option "Valider cycles" (optionnelle, désactivée par défaut)

**Implementation:**
- Frontend : Cycle detection algorithm (DFS) dans `useGraphValidation()`
- UI : Badge component avec tooltip
- Panneau Détails : Section "Validation" avec liste cycles

**Tests Required:**
- Unit : Cycle detection algorithm (cas simples + complexes)
- Integration : Badge affiché correctement
- E2E : Navigation cycles fonctionne

---

### ID-003: Cost Governance Plafonds

**Decision:** Soft warning (90%) + Hard blocking (100%)

**Context:**  
Protection financière nécessaire avec workflow fluide. Pattern industrie standard (AWS, Azure).

**Rationale:**
- **Soft warning (90%)** : Alerte précoce, laisse marge manœuvre
- **Hard blocking (100%)** : Protection absolue contre dépassement
- Pattern éprouvé (cloud providers)
- Balance protection vs UX

**Behavior:**

**90% Soft Warning:**
- Toast warning orange : "⚠️ Quota à 90%, XX€ restants sur YY€"
- Génération autorisée
- Toast répété à chaque génération jusqu'à reset ou augmentation quota

**100% Hard Blocking:**
- Modal bloquante : "🚫 Quota mensuel atteint (XX€/XX€)"
- Message : "Impossible de générer. Options : Attendre reset mensuel ou contacter admin"
- Bouton "Fermer" uniquement (pas de génération possible)

**Reset & Bypass:**
- Reset : Mensuel automatique (1er du mois 00:00 UTC)
- Bypass : Admin peut augmenter temporairement quota (settings panel)
- Logs : Toutes tentatives après 100% loguées (audit)

**Implementation:**
- Backend : Middleware cost tracking (avant LLM call)
- Database : `cost_usage` table (user_id, month, amount, quota)
- Frontend : `useCostGovernance()` hook (fetch quota status)

**Tests Required:**
- Unit : Cost tracking calculation
- Integration : Middleware bloque à 100%
- E2E : Toast 90% + Modal 100% affichés correctement

---

### ID-004: Streaming Interruption Cleanup

**Decision:** 10s timeout graceful shutdown

**Context:**  
Utilisateur peut interrompre génération LLM. Besoin cleanup propre (logs, stats) sans bloquer UX.

**Rationale:**
- **10s** suffisant pour cleanup LLM + écriture logs finaux
- Pas trop long pour UX (user attend confirmation)
- Graceful > brutal (préserve cohérence logs)

**Behavior:**

**Frontend (Immediate):**
1. Clic "Interrompre" → `AbortController.abort()`
2. EventSource SSE fermé immédiatement
3. UI change : Bouton → Spinner "Nettoyage..."
4. Après confirmation backend : "Interrompu ✓" + fermeture modal (2s delay)

**Backend (Graceful):**
1. LLM stream interrompu (OpenAI SDK gère AbortSignal)
2. `try/finally` block écrit logs finaux :
   - Tokens consommés (partial)
   - Durée génération
   - Statut "interrupted"
3. **Timeout 10s** : Si cleanup dépasse, force close connection
4. Return SSE event final : `{"type": "interrupted", "reason": "user_abort"}`

**Implementation:**
- Frontend : AbortController dans `useGenerationStream()`
- Backend : `asyncio.timeout(10)` dans cleanup handler
- Logs : Status field `"interrupted"` vs `"completed"`

**Tests Required:**
- Unit : AbortController signal propagation
- Integration : Backend cleanup sous 10s
- E2E : UI "Nettoyage..." → "Interrompu" workflow

---

### ID-005: Preset Validation Strictness

**Decision:** Warning avec option "Charger quand même"

**Context:**  
GDD externe peut changer (personnages supprimés, renommés). Presets peuvent devenir partiellement obsolètes.

**Rationale:**
- Authoring tool : Ne pas bloquer workflow créatif
- GDD externe → références obsolètes normales
- User reste responsable (informed choice)
- Meilleure UX qu'erreur bloquante

**Behavior:**

**Validation au Chargement:**
1. Preset chargé → validation références (personnages, lieux, objets)
2. Si références invalides détectées → Modal warning

**Modal Warning:**
- **Titre** : "⚠️ Preset partiellement obsolète"
- **Message** : "Ce preset contient des références introuvables dans le GDD actuel :"
- **Liste** :
  - "❌ Personnage 'Akthar' (ID: abc123) introuvable"
  - "❌ Lieu 'Ancienne Forge' (ID: xyz789) introuvable"
- **Note** : "Ces références seront ignorées si vous continuez."
- **Actions** :
  - "Annuler" (primaire) → Ferme modal, pas de chargement
  - "Charger quand même" (secondaire, warning style) → Charge preset

**Après "Charger quand même":**
- Références invalides ignorées (pas sélectionnées dans UI)
- Toast confirmation : "Preset chargé (2 références ignorées)"
- User peut modifier manuellement sélection

**Implementation:**
- Backend : `/api/v1/presets/{id}/validate` endpoint (validation pre-load)
- Frontend : `usePresetValidation()` hook
- Modal : `PresetValidationWarningModal.tsx` component

**Tests Required:**
- Unit : Validation logic détecte références invalides
- Integration : API `/validate` retourne liste références invalides
- E2E : Workflow "Annuler" vs "Charger quand même"

---
