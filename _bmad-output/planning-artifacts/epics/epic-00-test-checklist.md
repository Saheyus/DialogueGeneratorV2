# Checklist Tests Interface - Epic 0 (Fonctionnalités Existantes)

**Date création :** 2026-01-23  
**Objectif :** Valider toutes les fonctionnalités implémentées dans Epic 0  
**Environnement :** Interface web React (`npm run dev`)
---

## 📋 Story 0.1: Fix Graph Editor stableID (ADR-003)

### Test 0.1.1 : Renommer dialogue ne casse pas connexions
- [ ] Renommer un dialogue avec nodes connectés
- [ ] Vérifier que toutes les connexions restent intactes
- [ ] Recharger le dialogue → connexions toujours présentes
- **Notes :** 

### Test 0.1.2 : Génération stableID pour données legacy
- [ ] Charger un dialogue sans stableID
- [ ] Vérifier qu'un UUID est généré automatiquement
- [ ] Sauvegarder → stableID présent dans JSON
- **Notes :** 

### Test 0.1.3 : Connexions utilisent stableID
- [ ] Créer une connexion entre deux nodes
- [ ] Sauvegarder et recharger
- [ ] Vérifier que la connexion persiste (utilise stableID, pas displayName)
- **Notes :** 

### Test 0.1.4 : DisplayName dupliqué ne cause pas conflit
- [ ] Créer deux dialogues avec même displayName
- [ ] Vérifier que tous les nodes sont visibles et éditables
- [ ] Aucun conflit d'ID
- **Notes :** 

---

## 📋 Story 0.2: Progress Feedback Modal avec SSE Streaming (ADR-001)

### Test 0.2.1 : Modal progression s'affiche
- [ ] Lancer une génération (single ou batch)
- [ ] Vérifier que la modal "Génération en cours..." s'affiche
- [ ] Vérifier que le texte s'affiche en streaming (caractère par caractère)
- **Notes :** 

### Test 0.2.2 : Barre de progression fonctionne
- [ ] Observer les étapes : Prompting → Generating → Validating → Complete
- [ ] Vérifier que la progression est visible
- **Notes :** 

### Test 0.2.3 : Interrompre génération
- [ ] Cliquer sur "Interrompre" pendant génération
- [ ] Vérifier que la génération s'arrête (timeout 10s max)
- [ ] Modal se ferme avec message "Génération interrompue"
- [ ] Aucun dialogue partiel sauvegardé
- **Notes :** 

### Test 0.2.4 : Réduire modal
- [ ] Cliquer sur "Réduire" (icône minimize)
- [ ] Vérifier que la modal se réduit en badge compact
- [ ] Vérifier que je peux continuer à travailler sur le graphe
- [ ] Badge affiche toujours la progression
- **Notes :** 

### Test 0.2.5 : Génération terminée
- [ ] Attendre fin de génération (succès)
- [ ] Vérifier message "Génération terminée" avec bouton "Fermer"
- [ ] Vérifier que les nodes générés sont ajoutés au graphe automatiquement
- [ ] Modal se ferme après 3 secondes ou clic utilisateur
- **Notes :** 

---

## 📋 Story 0.3: Multi-Provider LLM avec abstraction Mistral (ADR-004)

### Test 0.3.1 : Sélecteur de modèle affiche providers
- [ ] Ouvrir sélecteur de modèle
- [ ] Vérifier présence de "OpenAI" et "Mistral"
- [ ] Chaque provider affiche son modèle avec icône distincte
- **Notes :** 

### Test 0.3.2 : Génération avec Mistral
- [ ] Sélectionner "Mistral Small Creative"
- [ ] Lancer une génération
- [ ] Vérifier que la génération fonctionne (même format Unity JSON)
- [ ] Vérifier que le streaming SSE fonctionne
- **Notes :** 

### Test 0.3.3 : Préférence provider sauvegardée
- [ ] Changer de provider (OpenAI → Mistral)
- [ ] Recharger la page
- [ ] Vérifier que la sélection est conservée (localStorage)
- **Notes :** 

### Test 0.3.4 : Erreur provider indisponible
- [ ] Simuler erreur Mistral API (ou clé API invalide)
- [ ] Vérifier message d'erreur clair ("Mistral API unavailable")
- [ ] Vérifier possibilité de basculer vers OpenAI manuellement
- **Notes :** 

---

## 📋 Story 0.10: Multi-Provider LLM avec OpenRouter (Extension ADR-004)

### Test 0.10.1 : Sélecteur affiche OpenRouter
- [ ] Ouvrir sélecteur de modèle
- [ ] Vérifier présence de "OpenRouter" (si clé API configurée)
- [ ] Vérifier modèles OpenRouter affichés (Claude, GPT-4, etc.)
- **Notes :** 

### Test 0.10.2 : Génération avec OpenRouter
- [ ] Sélectionner un modèle OpenRouter (ex: "openai/gpt-4-turbo")
- [ ] Lancer une génération
- [ ] Vérifier que la génération fonctionne
- [ ] Vérifier que le streaming SSE fonctionne
- **Notes :** 

### Test 0.10.3 : OpenRouter sans clé API
- [ ] Supprimer `OPENROUTER_API_KEY` de l'environnement
- [ ] Recharger l'application
- [ ] Vérifier que OpenRouter n'apparaît pas dans le sélecteur (pas d'erreur)
- **Notes :** 

---

## 📋 Story 0.4: Presets système (ADR-002)

### Test 0.4.1 : Créer preset
- [ ] Configurer contexte (personnages, lieux, région, instructions)
- [ ] Cliquer "Sauvegarder comme preset"
- [ ] Remplir nom, icône emoji, aperçu
- [ ] Vérifier que le preset apparaît dans le dropdown
- **Notes :** 

### Test 0.4.2 : Charger preset
- [ ] Ouvrir dropdown "Presets"
- [ ] Sélectionner un preset
- [ ] Vérifier que tous les champs sont pré-remplis
- [ ] Vérifier possibilité de lancer génération immédiatement
- **Notes :** 

### Test 0.4.3 : Preset avec références obsolètes
- [ ] Créer preset avec personnage "X"
- [ ] Supprimer "X" du GDD
- [ ] Charger le preset
- [ ] Vérifier warning "Références obsolètes détectées"
- [ ] Vérifier options "Charger quand même" / "Annuler"
- **Notes :** 

### Test 0.4.4 : Modifier preset
- [ ] Modifier un preset existant
- [ ] Sauvegarder
- [ ] Vérifier que le preset est mis à jour (pas de duplication)
- **Notes :** 

### Test 0.4.5 : Supprimer preset
- [ ] Supprimer un preset via menu contextuel
- [ ] Vérifier que le preset disparaît du dropdown
- **Notes :** 

---

## 📋 Story 0.5: Auto-save dialogues (ID-001)

### Test 0.5.1 : Auto-save déclenché
- [ ] Modifier un dialogue (ajout node, édition texte, connexion)
- [ ] Attendre 2 minutes
- [ ] Vérifier que le dialogue est sauvegardé automatiquement
- [ ] Vérifier indicateur "Sauvegardé il y a Xs"
- **Notes :** 

### Test 0.5.2 : Auto-save suspendu pendant génération
- [ ] Lancer une génération LLM
- [ ] Attendre 2 minutes pendant génération
- [ ] Vérifier que l'auto-save ne se déclenche pas
- [ ] Vérifier que l'auto-save reprend après fin de génération
- **Notes :** 

### Test 0.5.3 : Sauvegarde manuelle réinitialise timer
- [ ] Modifier dialogue
- [ ] Sauvegarder manuellement (Ctrl+S)
- [ ] Vérifier que le timer auto-save est réinitialisé
- [ ] Vérifier indicateur mis à jour
- **Notes :** 

### Test 0.5.4 : Session recovery
- [ ] Modifier dialogue sans sauvegarder
- [ ] Fermer l'application
- [ ] Rouvrir l'application
- [ ] Vérifier message "Modifications non sauvegardées récupérées"
- [ ] Vérifier que les modifications sont récupérées
- **Notes :** 

---

## 📋 Story 0.5.5: Génération next node avec gestion automatique des connexions

### Test 0.5.5.1 : Générer suite pour choix spécifique (graphe)
- [ ] Sélectionner node avec plusieurs choix
- [ ] Sélectionner un choix spécifique
- [ ] Lancer "Générer la suite pour ce choix"
- [ ] Vérifier que `targetNode` est rempli automatiquement
- [ ] Vérifier que connexion visuelle (edge) est créée
- **Notes :** 

### Test 0.5.5.2 : Générer suite pour choix spécifique (éditeur dialogue)
- [ ] Dans éditeur de dialogue, sélectionner node avec choix
- [ ] Sélectionner choix dans panneau édition
- [ ] Lancer "Générer la suite pour ce choix"
- [ ] Vérifier que `targetNode` est rempli
- [ ] Vérifier focus automatique vers nouveau node
- **Notes :** 

### Test 0.5.5.3 : Générer suite pour tous les choix (graphe)
- [ ] Sélectionner node avec plusieurs choix sans `targetNode`
- [ ] Lancer "Générer la suite pour tous les choix"
- [ ] Vérifier qu'un node est généré pour chaque choix
- [ ] Vérifier que tous les `targetNode` sont remplis
- [ ] Vérifier que toutes les connexions visuelles sont créées
- **Notes :** 

### Test 0.5.5.4 : Générer suite pour tous les choix (éditeur dialogue)
- [ ] Dans éditeur de dialogue, sélectionner node avec choix
- [ ] Lancer "Générer la suite pour tous les choix"
- [ ] Vérifier que tous les `targetNode` sont remplis
- [ ] Vérifier focus automatique vers premier nouveau node
- **Notes :** 

### Test 0.5.5.5 : Générer nextNode (navigation linéaire)
- [ ] Sélectionner node sans choix
- [ ] Lancer "Générer la suite (nextNode)"
- [ ] Vérifier que `nextNode` est rempli automatiquement
- [ ] Vérifier que connexion visuelle est créée
- **Notes :** 

### Test 0.5.5.6 : Générer avec choix déjà connectés
- [ ] Sélectionner node avec certains choix déjà connectés
- [ ] Lancer "Générer la suite pour tous les choix"
- [ ] Vérifier que seuls les choix sans `targetNode` génèrent des nodes
- [ ] Vérifier message "X choix(s) déjà connecté(s), Y nouveau(x) node(s) généré(s)"
- **Notes :** 

---

## 📋 Story 0.6: Validation cycles graphe (ID-002)

### Test 0.6.1 : Détection cycle
- [ ] Créer un cycle (node A → B → C → A)
- [ ] Sauvegarder ou lancer validation
- [ ] Vérifier warning "Cycle détecté : A → B → C → A"
- [ ] Vérifier que les nodes du cycle sont surlignés (orange)
- **Notes :** 

### Test 0.6.2 : Plusieurs cycles
- [ ] Créer plusieurs cycles
- [ ] Lancer validation
- [ ] Vérifier que tous les cycles sont listés
- [ ] Vérifier que chaque cycle est cliquable pour zoomer
- **Notes :** 

### Test 0.6.3 : Cycle intentionnel
- [ ] Marquer un cycle comme "intentionnel" (checkbox)
- [ ] Vérifier que le warning ne réapparaît plus pour ce cycle
- [ ] Vérifier que le cycle est toujours validé structurellement
- **Notes :** 

### Test 0.6.4 : Graphe sans cycles
- [ ] Créer graphe sans cycles
- [ ] Lancer validation
- [ ] Vérifier qu'aucun warning cycle n'est affiché
- **Notes :** 

---

## 📋 Story 0.7: Cost governance (ID-003)

### Test 0.7.1 : Warning budget 90%
- [ ] Configurer budget LLM (ex: 100€/mois)
- [ ] Atteindre 90% du budget (90€ dépensés)
- [ ] Vérifier warning "Budget atteint à 90% - 10€ restants"
- [ ] Vérifier possibilité de continuer à générer
- **Notes :** 

### Test 0.7.2 : Blocage budget 100%
- [ ] Atteindre 100% du budget
- [ ] Tenter de lancer une génération
- [ ] Vérifier message "Budget dépassé"
- [ ] Vérifier qu'aucun appel LLM n'est effectué
- **Notes :** 

### Test 0.7.3 : Dashboard coûts
- [ ] Ouvrir section "Usage LLM"
- [ ] Vérifier budget total, montant dépensé, pourcentage utilisé
- [ ] Vérifier graphique évolution coûts sur le mois
- **Notes :** 

### Test 0.7.4 : Coûts multi-provider
- [ ] Changer provider (OpenAI → Mistral)
- [ ] Vérifier que les coûts sont trackés séparément
- [ ] Vérifier que le budget global s'applique à tous les providers
- **Notes :** 

---

## 📋 Story 0.8: Streaming cleanup (ID-004)

### Test 0.8.1 : Interruption propre
- [ ] Lancer génération
- [ ] Cliquer "Interrompre"
- [ ] Vérifier que le streaming s'arrête (timeout 10s max)
- [ ] Vérifier que la modal se ferme
- [ ] Vérifier qu'aucun dialogue partiel n'est sauvegardé
- **Notes :** 

### Test 0.8.2 : Timeout interruption
- [ ] Simuler backend qui ne répond pas à l'annulation
- [ ] Attendre 10 secondes
- [ ] Vérifier que la connexion SSE est fermée (force close)
- [ ] Vérifier message "Interruption terminée"
- [ ] Vérifier que l'UI reste réactive
- **Notes :** 

### Test 0.8.3 : Cleanup automatique
- [ ] Lancer génération qui se termine normalement
- [ ] Vérifier que toutes les ressources sont nettoyées
- [ ] Vérifier que la modal affiche "Génération terminée"
- **Notes :** 

---

## 📋 Story 0.9: Preset validation (ID-005)

### Test 0.9.1 : Warning références obsolètes
- [ ] Charger preset avec personnage supprimé du GDD
- [ ] Vérifier warning modal "Références obsolètes détectées"
- [ ] Vérifier options "Charger quand même" / "Annuler"
- **Notes :** 

### Test 0.9.2 : Charger preset avec obsolètes
- [ ] Cliquer "Charger quand même"
- [ ] Vérifier que références obsolètes sont ignorées
- [ ] Vérifier que références valides sont chargées
- [ ] Vérifier message "Preset chargé avec X référence(s) obsolète(s) ignorée(s)"
- **Notes :** 

### Test 0.9.3 : Preset valide
- [ ] Charger preset avec toutes références valides
- [ ] Vérifier qu'aucun warning n'est affiché
- [ ] Vérifier que le preset est chargé immédiatement
- **Notes :** 

### Test 0.9.4 : Auto-cleanup références obsolètes
- [ ] Modifier preset avec références obsolètes
- [ ] Sauvegarder le preset
- [ ] Vérifier que références obsolètes sont supprimées automatiquement
- [ ] Vérifier message "Preset mis à jour - références obsolètes supprimées"
- **Notes :** 

---

## 📊 Résumé Tests

| Story | Tests | Complétés | Notes |
|-------|-------|-----------|-------|
| 0.1 - stableID | 4 | 0/4 | |
| 0.2 - Progress Modal SSE | 5 | 0/5 | |
| 0.3 - Multi-Provider Mistral | 4 | 0/4 | |
| 0.10 - Multi-Provider OpenRouter | 3 | 0/3 | |
| 0.4 - Presets système | 5 | 0/5 | |
| 0.5 - Auto-save | 4 | 0/4 | |
| 0.5.5 - Génération next node | 6 | 0/6 | |
| 0.6 - Validation cycles | 4 | 0/4 | |
| 0.7 - Cost governance | 4 | 0/4 | |
| 0.8 - Streaming cleanup | 3 | 0/3 | |
| 0.9 - Preset validation | 4 | 0/4 | |
| **TOTAL** | **46** | **0/46** | |

---

## 📝 Notes Globales

**Date début tests :**  
**Date fin tests :**  
**Environnement testé :**  
**Version testée :**  

**Bugs identifiés :**
- 

**Améliorations suggérées :**
- 

**Tests non applicables (raison) :**
- 

---

**Dernière mise à jour :** 2026-01-23
