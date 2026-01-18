# Sprint Plan - DialogueGenerator V1.0 MVP

**Date de création :** 2026-01-15  
**Sprint :** Sprint 1 - Infrastructure & Setup  
**Durée :** 2-3 semaines (estimation)  
**Objectif principal :** Corriger bugs critiques et établir base technique solide pour production

---

## 🎯 Objectifs du Sprint

### Objectif Principal
Établir une base technique fiable en corrigeant les bugs critiques et en implémentant les améliorations infrastructure prioritaires identifiées dans l'Architecture Document.

### Objectifs Spécifiques
1. **Corriger bug critique** : Graph Editor stableID (ADR-003) - **PRIORITÉ 1**
2. **Améliorer UX critique** : Progress Feedback Modal avec SSE (ADR-001)
3. **Renforcer robustesse** : Auto-save, validation cycles, cost governance
4. **Ajouter flexibilité** : Multi-Provider LLM (Mistral) - ADR-004
5. **Réduire friction** : Presets système (ADR-002)

---

## 📋 Stories Sélectionnées pour ce Sprint

### Epic 0: Infrastructure & Setup (Brownfield Adjustments)

**Statut Epic :** `in-progress`  
**Valeur utilisateur :** Base technique fiable pour débloquer production narrative

#### Stories Prioritaires (Must-Have)

1. **Story 0.1: Fix Graph Editor stableID (ADR-003)** ✅ `ready-for-dev`
   - **Priorité :** 🔴 CRITIQUE (bug bloquant corruption graphe)
   - **Effort estimé :** Moyen (3-5 jours)
   - **Dépendances :** Aucune
   - **Acceptance Criteria :** 4 critères BDD
   - **Fichier story :** `0-1-fix-graph-editor-stableid-adr-003.md`

2. **Story 0.2: Progress Feedback Modal avec SSE Streaming (ADR-001)**
   - **Priorité :** 🟠 HAUTE (UX critique - UI "gel" pendant génération)
   - **Effort estimé :** Moyen (4-6 jours)
   - **Dépendances :** Aucune (peut être fait en parallèle de 0.1)
   - **Acceptance Criteria :** 4 critères BDD

3. **Story 0.4: Presets système (ADR-002)**
   - **Priorité :** 🟡 MOYENNE (réduit friction cold start)
   - **Effort estimé :** Moyen (3-5 jours)
   - **Dépendances :** Aucune
   - **Acceptance Criteria :** 5 critères BDD

4. **Story 0.3: Multi-Provider LLM avec abstraction Mistral (ADR-004)**
   - **Priorité :** 🟡 MOYENNE (flexibilité + réduction dépendance)
   - **Effort estimé :** Moyen-Élevé (5-7 jours)
   - **Dépendances :** Aucune (peut être fait en parallèle)
   - **Acceptance Criteria :** 4 critères BDD

#### Stories de Robustesse (Should-Have)

5. **Story 0.5: Auto-save dialogues (ID-001)**
   - **Priorité :** 🟢 BASSE (amélioration robustesse)
   - **Effort estimé :** Faible-Moyen (2-4 jours)
   - **Dépendances :** Aucune
   - **Acceptance Criteria :** 5 critères BDD

6. **Story 0.6: Validation cycles graphe (ID-002)**
   - **Priorité :** 🟢 BASSE (amélioration validation)
   - **Effort estimé :** Faible (2-3 jours)
   - **Dépendances :** Aucune
   - **Acceptance Criteria :** 4 critères BDD

7. **Story 0.7: Cost governance (ID-003)**
   - **Priorité :** 🟢 BASSE (protection financière)
   - **Effort estimé :** Moyen (4-5 jours)
   - **Dépendances :** Aucune
   - **Acceptance Criteria :** 4 critères BDD

8. **Story 0.8: Streaming cleanup (ID-004)**
   - **Priorité :** 🟢 BASSE (amélioration robustesse)
   - **Effort estimé :** Faible (1-2 jours)
   - **Dépendances :** Story 0.2 (Progress Modal)
   - **Acceptance Criteria :** 4 critères BDD

9. **Story 0.9: Preset validation (ID-005)**
   - **Priorité :** 🟢 BASSE (amélioration presets)
   - **Effort estimé :** Faible (1-2 jours)
   - **Dépendances :** Story 0.4 (Presets système)
   - **Acceptance Criteria :** 5 critères BDD

---

## 📊 Capacité & Effort Estimé

### Effort Total Estimé
- **Must-Have (Stories 0.1, 0.2, 0.3, 0.4) :** 15-23 jours
- **Should-Have (Stories 0.5-0.9) :** 10-16 jours
- **Total :** 25-39 jours (5-8 semaines pour 1 développeur)

### Recommandation Sprint
**Sprint 1 (2-3 semaines) :** Focus sur Must-Have
- Story 0.1 (CRITIQUE) : 3-5 jours
- Story 0.2 (HAUTE) : 4-6 jours
- Story 0.4 (MOYENNE) : 3-5 jours
- Story 0.3 (MOYENNE) : 5-7 jours (peut être reporté Sprint 2 si nécessaire)

**Sprint 2 (2-3 semaines) :** Should-Have + Stories Epic 1
- Stories 0.5-0.9 : 10-16 jours
- Début Epic 1 (génération dialogues) selon capacité

---

## 🔗 Dépendances

### Dépendances Identifiées
- **Story 0.8** dépend de **Story 0.2** (Streaming cleanup nécessite Progress Modal)
- **Story 0.9** dépend de **Story 0.4** (Preset validation nécessite Presets système)
- **Aucune autre dépendance** - Stories peuvent être travaillées en parallèle

### Ordre Recommandé
1. **Story 0.1** (CRITIQUE) - Commencer immédiatement
2. **Stories 0.2, 0.3, 0.4** - Peuvent être faites en parallèle après 0.1
3. **Story 0.8** - Après 0.2
4. **Story 0.9** - Après 0.4
5. **Stories 0.5, 0.6, 0.7** - Peuvent être faites en parallèle à tout moment

---

## ✅ Definition of Done

Une story est considérée "done" quand :
- [ ] Tous les Acceptance Criteria sont satisfaits
- [ ] Code implémenté et testé (unit + integration + E2E si applicable)
- [ ] Tests passent (>80% coverage pour code critique)
- [ ] Code review effectué (workflow `code-review`)
- [ ] Documentation mise à jour si nécessaire
- [ ] Story marquée `done` dans `sprint-status.yaml`

---

## 📈 Métriques de Succès

### Métriques Techniques
- **Zero Blocking Bugs** : Story 0.1 résout bug critique corruption graphe
- **UX Améliorée** : Story 0.2 élimine UI "gel" pendant génération
- **Robustesse** : Stories 0.5-0.9 renforcent stabilité système
- **Flexibilité** : Story 0.3 ajoute support multi-provider LLM

### Métriques Business
- **Production Readiness** : Base technique fiable pour débloquer Epic 1 (génération dialogues)
- **Friction Réduite** : Story 0.4 réduit cold start de 10+ clics à 1 clic
- **Protection Financière** : Story 0.7 protège contre dépassement budget LLM

---

## 🚀 Prochaines Étapes

1. **Immédiat :** Commencer Story 0.1 (CRITIQUE) - `ready-for-dev`
2. **En parallèle :** Créer stories 0.2, 0.3, 0.4 avec workflow `create-story`
3. **Après 0.1 :** Démarrer stories 0.2, 0.3, 0.4 selon priorités
4. **Sprint 2 :** Stories 0.5-0.9 + début Epic 1

---

## 📝 Notes

- **Brownfield Project** : Architecture existante React + FastAPI, pas de refonte
- **Windows-first** : Tous les scripts et chemins doivent fonctionner sur Windows
- **18 Cursor Rules** : Respecter les patterns et conventions définies
- **Tests Requis** : >80% coverage pour code critique (services, API, composants)

---

**Document généré le :** 2026-01-15  
**Dernière mise à jour :** 2026-01-15  
**Statut :** ✅ Plan validé, prêt pour implémentation
