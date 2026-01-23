# Epic 0.9 - Audit Rapide Production Readiness

**Date :** 2026-01-23  
**Objectif :** Identifier les VRAIS problèmes bloquants avant rédaction US  
**Durée estimée :** 2-3h d'exploration

---

## 🔍 Questions à Explorer

### 1. Positions des nœuds - Vraie problématique ?

**État actuel :**
- ✅ Système implémenté dans Story 0.5 (auto-save)
- ✅ `nodePositions.ts` avec localStorage dédié
- ✅ Priorité : localStorage > draft > backend

**À vérifier :**
- [ ] **Test manuel** : Déplacer nœud → sauvegarder → recharger → position conservée ?
- [ ] **Test génération** : Générer nouveau nœud → autres nœuds bougent-ils ?
- [ ] **Test edge case** : Dialogue sans filename → positions perdues ?
- [ ] **Test legacy** : Dialogue ancien sans positions → auto-layout fonctionne ?

**Hypothèses :**
- Si tout fonctionne → Story 0.9.1 devient "Tests E2E pour valider" (1-2h)
- Si bug réel → Story 0.9.1 devient "Fix bug positions" (3-5h)

---

### 2. Performance - Vrais goulots d'étranglement ?

**Analyse existante :** `_bmad-output/analysis/optimisations-generation-panel.md`

**Quick wins identifiés (6-9h) :**
1. Cache par hash de prompt (⭐⭐⭐⭐⭐) - 2-3h
2. Cache personnages/régions (⭐⭐⭐⭐) - 3-4h
3. Cache sous-lieux par région (⭐⭐⭐⭐) - 2h

**À vérifier :**
- [ ] **Test réel** : Ouvrir panneau génération → mesurer temps (objectif <500ms)
- [ ] **Test répétitif** : Changer instructions → mesurer temps estimation tokens
- [ ] **Test graphe large** : Charger dialogue 100+ nœuds → mesurer temps rendu

**Hypothèses :**
- Si latence <500ms → Story 0.9.2 devient optionnelle ou réduite
- Si latence >1s → Story 0.9.2 devient prioritaire (quick wins)

---

### 3. Refactorisation - Vraiment nécessaire ?

**Zones identifiées :**
- `GraphEditor.tsx` : 1170 lignes
- `graphStore.ts` : 1075 lignes

**À vérifier :**
- [ ] **Analyse code** : ESLint/Pylint pour code smells
- [ ] **Couverture tests** : Coverage actuel pour code critique
- [ ] **Maintenabilité** : Est-ce que le code est difficile à modifier ?

**Hypothèses :**
- Si code propre + tests OK → Story 0.9.3 devient optionnelle
- Si code smells + pas de tests → Story 0.9.3 devient prioritaire

---

### 4. Deployment - Vraiment prêt ?

**Documentation existante :** `docs/guides/DEPLOYMENT.md`, `docs/guides/deployment-guide.md`

**À vérifier :**
- [ ] **`.env.example`** : Toutes variables documentées ?
- [ ] **Build production** : `npm run deploy:build` fonctionne ?
- [ ] **Secrets** : Aucun secret hardcodé dans le code ?
- [ ] **Health check** : Endpoint `/api/v1/health` existe ?
- [ ] **CORS** : Configuration production prête ?

**Hypothèses :**
- Si tout OK → Story 0.9.4 devient "Checklist validation" (1-2h)
- Si manquants → Story 0.9.4 devient "Préparation déploiement" (2-3h)

---

## 📋 Plan d'Exploration (2-3h)

### Phase 1 : Tests manuels (30min)
1. **Test positions nœuds** (10min)
   - Ouvrir dialogue existant
   - Déplacer 3-4 nœuds
   - Sauvegarder
   - Recharger → Vérifier positions

2. **Test génération nœud** (10min)
   - Générer nouveau nœud depuis parent
   - Vérifier que autres nœuds ne bougent pas

3. **Test performance** (10min)
   - Ouvrir panneau génération → Mesurer temps
   - Changer instructions → Mesurer temps estimation

### Phase 2 : Analyse code (1h)
1. **ESLint/Pylint** (20min)
   - Lancer analyse code smells
   - Identifier problèmes critiques

2. **Couverture tests** (20min)
   - Vérifier coverage code critique
   - Identifier zones sans tests

3. **Review déploiement** (20min)
   - Vérifier `.env.example`
   - Vérifier build production
   - Vérifier documentation

### Phase 3 : Synthèse et priorisation (30min)
1. **Liste problèmes réels** (15min)
   - Bug réel vs optimisation
   - Bloquant vs nice-to-have

2. **Priorisation** (15min)
   - Must-have pour production
   - Should-have (si temps)
   - Won't-have (reporté)

---

## 🎯 Résultats Attendus

**Document de synthèse avec :**
- ✅ Liste problèmes RÉELS identifiés
- ✅ Priorisation (Must/Should/Won't)
- ✅ Estimation effort réaliste (3 jours max)
- ✅ Stories ajustées selon réalité

---

## 🚀 Prochaines Étapes

**Après audit :**
1. Ajuster Epic 0.9 selon résultats
2. Créer stories détaillées uniquement pour problèmes réels
3. Estimer effort réaliste (3 jours max)

**Si tout est OK :**
- Epic 0.9 devient "Validation production" (checklist + tests)
- Effort : 1-2 jours

**Si problèmes identifiés :**
- Epic 0.9 devient "Fix production blockers"
- Effort : 2-3 jours (selon problèmes)

---

**Statut :** 🔍 À explorer avant rédaction US
