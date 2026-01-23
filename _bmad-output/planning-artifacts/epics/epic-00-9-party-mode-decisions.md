# Epic 0.9 - Décisions Party Mode (2026-01-23)

**Date :** 2026-01-23  
**Participants :** Bob (Scrum Master), Sally (UX Designer), Winston (Architect), Amelia (Dev), Marc (User)  
**Statut :** ✅ Décisions validées

---

## 🎯 Questions Posées et Décisions

### 1. TestNodes doivent-ils suivre leur parent ?

**Question :** Veut-on que l'enfant suive toujours le parent ?

**Réponse utilisateur :** Oui, les TestNodes doivent suivre leur parent parce qu'elles ne sont qu'une représentation visuelle d'un élément de leur parent, elles ne sont pas vraiment indépendantes.

**Décision :**
- ✅ **TestNodes suivent toujours leur parent** lors du déplacement
- ✅ **Pas de découplage manuel** pour V1.0 (simplicité)

**Impact :**
- Story 0.9.1 : Ajouter logique suivi TestNodes dans `updateNodePosition()` (+2-3h)

---

### 2. Détection de collision lors création nodes

**Question :** À la création de plusieurs nodes (ex: 4 résultats de test), l'UX vérifie-t-elle que les nodes créés soient bien espacés/disposés visuellement ?

**Réponse utilisateur :** Non, actuellement les nodes se chevauchent et je dois les déplacer manuellement.

**Décision :**
- ✅ **Détection de collision avec ajustement automatique**
- ✅ **Toggle on/off** pour activer/désactiver la détection (facilite tests)
- ✅ **Nodes peuvent être déplacés plus loin** si nécessaire pour éviter collision
- ✅ **Espacement minimal garanti : 50px** entre nodes

**Implémentation :**
- Fonction utilitaire `findFreePosition()` pour détection collision
- Intégration dans `generateFromNode()` pour batch nodes et TestNodes
- Toggle dans settings ou UI (à définir)

**Impact :**
- Story 0.9.1 : Ajouter détection collision (+3-4h)
- Story 0.9.1 : Ajouter toggle on/off (+1h)

---

### 3. Feedback visuel pendant génération

**Question :** Préférez-vous un ajustement automatique silencieux, ou un indicateur visuel (ex: ligne pointillée) montrant où le node sera placé avant création ?

**Réponse utilisateur :** Je viens de penser à un truc. Actuellement, pendant la génération de node, on est bloqué. Par contre, si on pouvait voir les nodes avant leur "remplissage", au moins on aurait quelque chose à faire en attendant que ça génère.

**Décision :**
- ✅ **Afficher nodes "squelettes" immédiatement** lors début génération batch
- ✅ **Mettre à jour nodes progressivement** avec contenu généré (SSE streaming)
- ✅ **Permettre interaction graphe** pendant génération (pas de blocage UI)

**Implémentation :**
- Créer nodes avec ID, position, type immédiatement (avant génération contenu)
- Mettre à jour `data` progressivement via SSE
- Permettre zoom/pan/déplacement autres nodes pendant génération

**Impact :**
- Story 0.9.2 : Ajouter feedback visuel nodes squelettes (+4-6h)
- Story 0.9.2 : Permettre interaction pendant génération (+2-3h)

---

### 4. Bug auto-layout

**Question :** L'auto-layout fonctionne-t-il ?

**Réponse utilisateur :** Je crois que l'auto-layout ne marche pas.

**Décision :**
- ⚠️ **Bug auto-layout à investiguer et corriger**
- Code existe (`graphStore.ts::applyAutoLayout()` ligne 924-975)
- Problème potentiel : positions non sauvegardées après layout, ou erreur silencieuse

**Impact :**
- Story 0.9.1 : Investiguer et corriger auto-layout (+2-3h)

---

## 📋 Récapitulatif Décisions

| Décision | Impact Story | Effort | Priorité |
|----------|--------------|--------|----------|
| TestNodes suivent parent | 0.9.1 | 2-3h | HAUTE |
| Détection collision + toggle | 0.9.1 | 4-5h | HAUTE |
| Correction auto-layout | 0.9.1 | 2-3h | HAUTE |
| Feedback visuel nodes squelettes | 0.9.2 | 4-6h | MOYENNE |
| Interaction pendant génération | 0.9.2 | 2-3h | MOYENNE |

**Total Story 0.9.1 :** 8-11h (2-3 jours)  
**Total Story 0.9.2 :** 6-9h (1-2 jours)

---

## 🎯 Scope Ajusté (3 jours max)

**Must-have (2-3 jours) :**
1. Story 0.9.1 : Fix bugs comportement (TestNodes, collision, auto-layout)
2. Story 0.9.2 : Feedback visuel prioritaire (nodes squelettes)

**Should-have (si temps) :**
3. Story 0.9.2 : Interaction pendant génération
4. Story 0.9.3 : Audit code (optionnel)
5. Story 0.9.4 : Checklist déploiement (optionnel)

---

## 📝 Notes Techniques

### TestNodes suivi parent
- Détecter TestNodes enfants : `node.id.startsWith(\`test-node-${nodeId}-choice-\`)`
- Mettre à jour position relative : `x: parent.x + 300, y: parent.y - 150 + (choiceIndex * 200)`
- Référence : `graphStore.ts::updateNodePosition()` ligne 554-583

### Détection collision
- Fonction `findFreePosition()` : Vérifier collision avec nodes existants
- Si collision : Décaler vers le bas (candidateY += nodeHeight + minSpacing)
- Toggle : Settings store ou UI toggle (à définir)
- Référence : `graphStore.ts::generateFromNode()` ligne 704-728

### Auto-layout
- Code existant : `graphStore.ts::applyAutoLayout()` ligne 924-975
- Problème potentiel : Positions non sauvegardées après layout, ou erreur silencieuse
- À investiguer : Console errors, vérifier sauvegarde positions après layout

### Feedback visuel
- Créer nodes immédiatement : `{ id, type, position }` sans `data` complet
- Mettre à jour `data` progressivement via SSE
- Référence : `graphStore.ts::generateFromNode()` ligne 586-777

---

**Statut :** ✅ Décisions documentées, Epic 0.9 mis à jour
