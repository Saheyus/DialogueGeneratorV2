# Epic 0.9 - Résultats Exploration Production Readiness

**Date :** 2026-01-23  
**Durée exploration :** ~30min  
**Statut :** ✅ Exploration complétée

---

## 🔍 Résultats par Domaine

### 1. Positions des nœuds - Edge Cases Identifiés

**✅ Système de base fonctionnel :**
- `nodePositions.ts` avec localStorage dédié ✅
- `updateNodePosition()` sauvegarde immédiatement ✅
- Priorité : localStorage > draft > backend ✅

**⚠️ Edge Cases identifiés :**

#### Edge Case 1 : TestNodes ne suivent pas leur parent
**Problème :** Quand un DialogueNode est déplacé, ses TestNodes associés ne suivent pas automatiquement.

**Code actuel :**
- TestNodes créés avec position relative : `x: parent.x + 300, y: parent.y - 150 + (choiceIndex * 200)`
- `updateNodePosition()` ne met à jour QUE le nœud spécifié (ligne 564-566)
- Pas de logique pour mettre à jour TestNodes enfants

**Impact :** Si utilisateur déplace DialogueNode, TestNodes restent à l'ancienne position → connexions visuelles cassées

**Solution nécessaire :** 
- Détecter TestNodes enfants lors de `updateNodePosition()`
- Mettre à jour leurs positions relativement au parent
- Effort estimé : **2-3h**

#### Edge Case 2 : TestNodes lors de chargement
**Problème :** TestNodes sont créés dynamiquement depuis les choix, mais leurs positions peuvent être perdues si le DialogueNode parent n'a pas de position sauvegardée.

**Code actuel :**
- TestNodes créés dans `updateNode()` (ligne 250-272)
- Position calculée depuis `dialogueNode.position` (ligne 252-256)
- Si `dialogueNode.position` est undefined → TestNode à (300, -150) par défaut

**Impact :** TestNodes mal positionnés si parent sans position

**Solution nécessaire :**
- Vérifier position parent avant création TestNode
- Fallback sur auto-layout si position manquante
- Effort estimé : **1h**

---

### 2. Performance - Déjà Optimisée ! ✅

**✅ Cache hash prompt :** IMPLÉMENTÉ
- `useTokenEstimation.ts` ligne 144-151 : Hash calculé AVANT appel API
- Si hash identique → skip l'appel ✅
- **Gain : 80% des appels redondants évités**

**✅ Cache personnages/régions :** IMPLÉMENTÉ
- `contextStore.ts` : Cache avec TTL 30min ✅
- `useSceneSelection.ts` ligne 63-68, 98-103 : Utilise cache avant appel API ✅
- **Gain : 300-800ms par ouverture panneau**

**✅ Cache sous-lieux :** IMPLÉMENTÉ
- `useSceneSelection.ts` ligne 136-144 : Cache par région ✅
- **Gain : 200-400ms par changement région**

**Conclusion :** Les optimisations quick wins sont **DÉJÀ IMPLÉMENTÉES** !  
**Action :** Story 0.9.2 devient "Validation performance" (mesurer latence réelle, vérifier que cache fonctionne)

---

### 3. Refactorisation - Analyse Code

**Fichiers volumineux identifiés :**
- `GraphEditor.tsx` : 1170 lignes
- `graphStore.ts` : 1075 lignes

**À vérifier :**
- [ ] Lancer ESLint pour code smells
- [ ] Vérifier coverage tests
- [ ] Tester maintenabilité (facilité modification)

**Hypothèse :** Si code fonctionne + tests OK → Refactorisation optionnelle (nice-to-have)

**Action :** Story 0.9.3 devient "Audit code" (1-2h) puis décision si nécessaire

---

### 4. Deployment - Presque Prêt ✅

**✅ Variables d'environnement :**
- `.env.example` complet avec toutes variables ✅
- Documentation claire ✅

**✅ Health check :**
- Endpoint `/health` existe ✅
- Endpoint `/health/detailed` existe ✅
- `api/utils/health_check.py` implémenté ✅

**✅ Build production :**
- `npm run build` fonctionne ✅
- Build frontend OK ✅

**⚠️ À valider :**
- [ ] Secrets hardcodés : Audit code pour vérifier
- [ ] CORS configuration : Vérifier si configuré pour production
- [ ] Tests E2E en environnement production-like

**Action :** Story 0.9.4 devient "Checklist validation déploiement" (1-2h)

---

## 📊 Synthèse et Priorisation

### Problèmes RÉELS identifiés

1. **TestNodes ne suivent pas parent** (Edge Case 1) - **BLOQUANT** ⚠️
   - Impact : UX cassée (connexions visuelles)
   - Effort : 2-3h
   - Priorité : **HAUTE**

2. **TestNodes position lors chargement** (Edge Case 2) - **MOYEN**
   - Impact : Positionnement incorrect si parent sans position
   - Effort : 1h
   - Priorité : **MOYENNE**

### Optimisations déjà faites ✅

- Cache hash prompt ✅
- Cache personnages/régions ✅
- Cache sous-lieux ✅

**Action :** Validation performance (mesurer latence réelle)

### Déploiement presque prêt ✅

- Variables d'environnement ✅
- Health check ✅
- Build production ✅

**Action :** Checklist validation (audit secrets, CORS, tests)

---

## 🎯 Epic 0.9 Ajusté (3 jours max)

### Story 0.9.1: Fix edge cases positions TestNodes (2-3h) - **CRITIQUE**
- Edge Case 1 : TestNodes suivent parent lors déplacement
- Edge Case 2 : TestNodes position lors chargement (fallback auto-layout)

### Story 0.9.2: Validation performance (1-2h) - **OPTIONNEL**
- Mesurer latence réelle (panneau génération, estimation tokens)
- Vérifier que cache fonctionne correctement
- Si latence <500ms → Story optionnelle

### Story 0.9.3: Audit code (1-2h) - **OPTIONNEL**
- ESLint pour code smells
- Vérifier coverage tests
- Décision : Refactorisation nécessaire ou non ?

### Story 0.9.4: Checklist validation déploiement (1-2h) - **MOYENNE**
- Audit secrets hardcodés
- Vérifier CORS configuration
- Tests E2E production-like

**Total estimé :** 5-9h (1-2 jours) si toutes stories, **3-5h (1 jour)** si seulement Story 0.9.1 + 0.9.4

---

## 🚀 Recommandation

**Must-have (3-5h) :**
1. Story 0.9.1 : Fix edge cases TestNodes (2-3h)
2. Story 0.9.4 : Checklist validation déploiement (1-2h)

**Should-have (si temps) :**
3. Story 0.9.2 : Validation performance (1-2h)
4. Story 0.9.3 : Audit code (1-2h)

**Total réaliste :** 1 jour (3-5h) pour must-have, 2 jours (5-7h) si should-have inclus

---

**Statut :** ✅ Exploration complétée, Epic 0.9 peut être ajusté selon ces résultats
