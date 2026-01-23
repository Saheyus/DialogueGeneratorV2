---
stepsCompleted: [1, 2, 3, 4, 5]
inputDocuments:
  - _bmad-output/analysis/brainstorming-session-2026-01-13T190613.md
  - _bmad-output/planning-artifacts/research/technical-les-meilleures-pratiques-pour-éditeurs-de-dialogues-narratifs-research-2026-01-13T222012.md
  - docs/project-overview.md
  - docs/Spécification technique.md
  - docs/architecture-frontend.md
  - docs/architecture-api.md
  - README.md
  - docs/integration-architecture.md
  - docs/technology-stack.md
date: 2026-01-13
author: Marc
---

# Product Brief: DialogueGenerator

## Executive Summary

DialogueGenerator est un outil de génération assistée par IA de dialogues arborescents pour jeux vidéo narratifs. Conçu spécifiquement pour des univers riches (comme Alteir), l'outil permet aux auteurs de dialogue de générer en **1 heure** des dialogues complets (centaines de nœuds, milliers de lignes) avec un contrôle fin sur le contexte et les paramètres de génération.

**Vision clé** : L'auteur humain agit comme un **narrative director** qui pilote un **script writer (dialoguiste) augmenté** par IA. L'humain dirige, l'IA exécute avec intelligence en exploitant un contexte riche (GDD).

L'outil se distingue des solutions existantes (DSU, IA native Unity) par sa gestion sophistiquée de contexte, ses prompts multi-couches, et son contrôle fin des paramètres de génération, le tout optimisé pour des univers narratifs denses.

---

## Core Vision

### Problem Statement

Les auteurs de dialogues pour jeux narratifs (type Disco Elysium) doivent générer des quantités massives de contenu (potentiellement des millions de lignes) avec des dialogues arborescents complexes (centaines de nœuds, milliers de lignes par PNJ). Les solutions existantes souffrent de limitations critiques :

- **Solutions jeu vidéo (DSU, IA native Unity)** : Prompts d'une seule ligne, aucune gestion de contexte riche, interfaces peu maintenables. Impossibles à utiliser avec des GDD riches (fiches de milliers de tokens).
- **Solutions linéaires (Sudowrite)** : Conçues pour l'écriture linéaire (livres, nouvelles), inadaptées aux dialogues arborescents avec choix multiples et variables de jeu.

Le résultat : soit l'écriture manuelle (projet pour une équipe entière de scénaristes), soit des solutions inadaptées qui ne permettent pas d'exploiter la richesse narrative des univers développés.

### Problem Impact

Pour un CRPG narratif lourd comme Alteir, le dialogue est **le cœur du jeu**. Sans outil adapté, les auteurs ne peuvent pas :
- Générer efficacement des dialogues arborescents complexes
- Exploiter la richesse narrative des univers développés (GDD riches)
- Maintenir un contrôle fin sur la qualité et la cohérence narrative
- Atteindre les objectifs de production (1H par dialogue complet)

**Si ce problème n'est pas résolu, le jeu sera mauvais.** Le dialogue est le pilier narratif, et sans outil adapté, la production devient impossible à l'échelle requise.

### Why Existing Solutions Fall Short

**Dialogue System for Unity (DSU) OpenAI Add-on :**
- Interface avec prompts d'une seule ligne (inadapté pour contexte riche)
- Aucune fonctionnalité de gestion de contexte (impossible d'exploiter des fiches de milliers de tokens)
- Add-on obscur difficile à maintenir (problématique pour projets développés avec IA)

**IA Native Unity :**
- Même limitations que DSU (prompts d'une ligne, pas de contexte)
- Encore moins de contrôles
- Tests décevants pour production professionnelle

**Solutions linéaires (Sudowrite) :**
- Conçues pour l'écriture linéaire (livres, nouvelles)
- Inadaptées aux dialogues arborescents avec choix multiples, variables de jeu, conditions
- Aucune intégration avec pipelines de production de jeux

**Promesses de dialogues runtime :**
- Fausses promesses : même les ordinateurs les plus puissants peinent à faire tourner des LLM performants
- Perte de temps à ce stade : nous voulons des dialogues de qualité professionnelle, co-écrits en amont du jeu

### Proposed Solution

DialogueGenerator est un outil production-ready qui transforme l'auteur humain en **narrative director** pilotant un **script writer (dialoguiste) augmenté** par IA.

**Architecture clé :**
- **Gestion de contexte par couches** : Sélection intelligente de fiches GDD (personnages, lieux, objets, etc.) et agencement en prompts multi-couches pour guider le LLM
- **Contrôle fin augmenté** : Tous les paramètres LLM + code intelligent pour optimiser la génération
- **Optimisé pour univers riches** : Conçu spécifiquement pour exploiter la richesse narrative des GDD denses (fiches de milliers de tokens)
- **Génération pré-production** : Focus sur dialogues de qualité professionnelle co-écrits en amont, pas de runtime

**Objectif de production :** Générer en **1 heure** un dialogue complet pour un PNJ (centaines de nœuds, milliers de lignes) avec équilibrage gameplay/agentivité optimal.

### Key Differentiators

1. **Intégration profonde avec GDD riche** : Unique capacité à exploiter des fiches de milliers de tokens pour enrichir le contexte de génération (personnages, lieux, objets, lore) - impossible avec solutions existantes (DSU = prompts une ligne)

2. **Prompts multi-couches avec sélection intelligente** : Architecture permettant d'agencer intelligemment le contexte GDD en couches pour guider le LLM sans le submerger (évite le "lore dropping") - avantage technique durable

3. **Contrôle fin augmenté par code intelligent** : Tous les paramètres LLM accessibles + code intelligent pour optimiser la génération selon le contexte - expérience utilisateur clé

4. **Outil production-ready maintenable** : Application web moderne (React + FastAPI) développée avec IA, contrairement aux add-ons obscurs difficiles à maintenir

5. **Vision narrative director / script writer augmenté** : Philosophie claire : l'humain dirige, l'IA exécute avec intelligence, optimisé pour des dialogues arborescents complexes - positionnement différenciant

6. **Focus production professionnelle** : Optimisé pour génération pré-production de qualité, pas de fausses promesses de runtime - objectif de valeur : 1H par dialogue complet

---

## Target Users

### Primary Users

#### Author-Writer (Auteur de dialogues)

**Marc et Mathieu** - Auteurs de dialogues pour le projet Alteir

**Rôle et contexte :**
- Auteurs professionnels travaillant sur un CRPG narratif lourd (type Disco Elysium)
- Écrivent des dialogues littéraires, caractérisés (voix du personnage), sans verbosité inutile
- Visent une réelle agentivité : dialogues comme cœur de gameplay (type jeu de rôle sur table)
- Le dialogue est une forme de jeu combinant choix cruciaux, tests, conséquences
- Acceptent volontairement l'explosion combinatoire pour créer des dialogues riches

**Besoins spécifiques :**
- **Marc** : 40h+ par semaine, développe aussi l'application et le code Unity - besoin d'efficacité maximale
- **Mathieu** : Quelques heures par semaine - besoin d'efficacité optimale dans un temps limité

**Objectif de production :** Générer en **1 heure** un dialogue complet pour un PNJ (centaines de nœuds, milliers de lignes) avec équilibrage gameplay/agentivité optimal

**Expérience du problème :**
- Solutions existantes (DSU, IA native Unity) avec prompts d'une ligne - inexploitables pour GDD riches
- Solutions linéaires (Sudowrite) inadaptées aux dialogues arborescents avec choix multiples
- Écriture manuelle trop lente pour atteindre les objectifs de production

**Vision du succès :**
- Pouvoir générer efficacement des dialogues complexes avec contexte riche (GDD denses)
- Maintenir un contrôle fin sur la qualité et la cohérence narrative
- Atteindre l'objectif de production : 1H par dialogue complet
- Sentir qu'ils agissent comme des "narrative directors" pilotant un "script writer augmenté"

#### Admin (Gestion des limites)

**Marc** - Développeur principal et administrateur

**Rôle :**
- Gestion des limites de dépenses (budget LLM, quotas, etc.)
- Contrôle des coûts de génération
- Configuration des paramètres système

**Besoins :**
- Visibilité sur les coûts de génération
- Contrôle des budgets et quotas
- Transparence sur l'utilisation des ressources LLM

### Secondary Users

#### Viewer (Consultation)

**Rest of the team, or anyone Marc wants to show the tool to**

**Rôle :**
- Consultation des dialogues générés
- Feedback et inspiration
- Partage du travail (Marc ne cache pas son travail)

**Besoins :**
- Accès en lecture seule (pas de modification)
- Consultation des dialogues et du contexte
- Potentiel accès universel (open viewing)

### User Journey

**Journey Type : Author-Writer (Marc & Mathieu)**

**Discovery :**
- Marc découvre l'outil en le développant (propriétaire-développeur)
- Mathieu découvre l'outil via Marc (démonstration, documentation, onboarding)

**Onboarding :**
- Configuration initiale : sélection du contexte GDD (personnages, lieux, objets)
- Premier dialogue : génération d'un dialogue simple pour comprendre le workflow
- Familiarisation avec l'interface et les contrôles

**Core Usage :**
- Sélection du contexte GDD pour le dialogue à générer
- Configuration des paramètres de génération (instructions, variantes, etc.)
- Génération assistée par IA avec variantes multiples
- Édition et affinage des dialogues générés
- Export vers Unity (format JSON)
- Répétition pour générer des dialogues complets (centaines de nœuds)

**Success Moment :**
- **Moment d'émerveillement** : Quand ils génèrent leur premier dialogue complet en 1H (centaines de nœuds, milliers de lignes) avec qualité professionnelle
- Réalisation que l'outil permet d'exploiter efficacement la richesse du GDD
- Sentiment de "narrative director" pilotant un "script writer augmenté"

**Long-term :**
- Intégration dans le workflow de production quotidien
- Génération de dialogues complexes de manière systématique
- Collaboration efficace entre auteurs (Marc et Mathieu)
- Partage avec l'équipe via viewer

---

## Success Metrics

### User Success Metrics

#### Primary Metric: Dialogue Node Quality (Priorité #1)

**Objectif :** Mesurer la qualité des nœuds de dialogue générés (plus petite unité du dialogue) et de leurs choix de réponses.

**Indicateurs de qualité :**

**Comportements positifs (bon signe) :**
- **Enregistrement d'un dialogue** : L'utilisateur sauvegarde un dialogue généré (indicateur d'acceptation de la qualité)
- **Utilisation en production** : Le dialogue est exporté vers Unity et intégré dans le jeu
- **Feedback positif** : Retours utilisateurs favorables sur la qualité

**Comportements négatifs (mauvais signe) :**
- **Re-génération** : L'utilisateur demande une nouvelle génération pour le même nœud (indicateur d'insatisfaction)
- **Suppression** : L'utilisateur supprime un dialogue généré (indicateur de rejet)
- **Feedback négatif** : Retours utilisateurs défavorables sur la qualité

**Méthodes de mesure :**
- **Retours utilisateurs** : Feedback direct sur la qualité des dialogues générés
- **Jugement par LLM** : Évaluation automatique de la qualité par LLM (cohérence, caractérisation, agentivité)
- **Taux d'acceptation** : Ratio dialogues enregistrés / dialogues générés
- **Taux de re-génération** : Ratio re-générations / dialogues générés (indicateur inverse)

**Métrique clé :**
- **Taux d'acceptation de qualité** : % de dialogues générés qui sont enregistrés (objectif : >80% en production)
- **Taux de re-génération** : % de dialogues qui nécessitent une re-génération (objectif : <20% en production)

#### Secondary Metric: Production Efficiency (Priorité #2)

**Objectif :** Mesurer l'efficacité de production (atteinte de l'objectif de 1H par dialogue complet).

**Indicateurs d'efficacité :**
- **Temps moyen de génération** : Temps réel pour générer un dialogue complet (objectif : ≤1H)
- **Ratio temps réel / objectif** : Efficacité par rapport à l'objectif de 1H
- **Réduction du temps d'écriture** : Comparaison avec écriture manuelle (objectif : réduction significative)
- **Nombre de dialogues générés** : Volume de production réalisé
- **Utilisation régulière** : Fréquence d'utilisation (quotidienne pour Marc, hebdomadaire pour Mathieu)

**Métrique clé :**
- **Temps moyen de génération** : Temps réel pour générer un dialogue complet (cible : ≤1H)
- **Volume de production** : Nombre de dialogues complets générés par période

#### Tertiary Metric: LLM Cost Management (Priorité #3)

**Objectif :** Surveiller et optimiser les coûts LLM sans compromettre la qualité.

**Indicateurs de coûts :**
- **Coût moyen par dialogue** : Coût LLM pour générer un dialogue complet
- **Coût total par période** : Budget LLM consommé
- **Efficacité token** : Ratio tokens utilisés / tokens générés (optimisation)
- **Taux d'utilisation** : Utilisation effective des ressources LLM

**Métrique clé :**
- **Coût par dialogue complet** : Coût LLM moyen pour générer un dialogue complet
- **Budget respecté** : Respect des limites de dépenses définies par l'admin

### Business Objectives

**Objectif principal :** Rendre DialogueGenerator production-ready pour permettre la production efficace de dialogues pour Alteir.

**Objectifs à 3 mois :**
- Outil production-ready utilisé quotidiennement par les auteurs
- Taux d'acceptation de qualité >80% (dialogues enregistrés / générés)
- Objectif de production atteint : génération de dialogues complets en ≤1H
- Coûts LLM maîtrisés dans les limites budgétaires

**Objectifs à 12 mois :**
- Production systématique de dialogues pour Alteir
- Qualité professionnelle maintenue à grande échelle
- Efficacité de production optimisée
- Potentiel open-source évalué (horizon futur)

### Key Performance Indicators

**KPIs Prioritaires :**

1. **Taux d'acceptation de qualité** (Priorité #1)
   - **Définition :** % de dialogues générés qui sont enregistrés (non re-générés, non supprimés)
   - **Méthode :** (Dialogues enregistrés / Dialogues générés) × 100
   - **Cible :** >80% en production
   - **Fréquence :** Suivi continu, rapport hebdomadaire

2. **Temps moyen de génération** (Priorité #2)
   - **Définition :** Temps réel moyen pour générer un dialogue complet
   - **Méthode :** Mesure du temps entre début et fin de génération d'un dialogue complet
   - **Cible :** ≤1H par dialogue complet
   - **Fréquence :** Suivi continu, rapport hebdomadaire

3. **Coût par dialogue complet** (Priorité #3)
   - **Définition :** Coût LLM moyen pour générer un dialogue complet
   - **Méthode :** (Coût total LLM / Nombre de dialogues générés)
   - **Cible :** Optimisé selon budget disponible
   - **Fréquence :** Suivi continu, rapport hebdomadaire

**KPIs Secondaires :**

4. **Taux de re-génération**
   - **Définition :** % de dialogues qui nécessitent une re-génération
   - **Méthode :** (Re-générations / Dialogues générés) × 100
   - **Cible :** <20% en production
   - **Fréquence :** Suivi continu

5. **Volume de production**
   - **Définition :** Nombre de dialogues complets générés par période
   - **Méthode :** Comptage des dialogues enregistrés
   - **Cible :** Selon besoins de production
   - **Fréquence :** Rapport hebdomadaire

6. **Jugement LLM de qualité**
   - **Définition :** Score de qualité automatique par LLM (cohérence, caractérisation, agentivité)
   - **Méthode :** Évaluation automatique par LLM sur échantillon de dialogues
   - **Cible :** Score moyen >8/10
   - **Fréquence :** Évaluation hebdomadaire

### Strategic Alignment

**Connexion aux objectifs :**
- **Qualité** : Aligné avec la vision "narrative director / script writer augmenté" - l'outil doit produire des dialogues de qualité professionnelle
- **Efficacité** : Aligné avec l'objectif de production (1H par dialogue complet) - permet d'atteindre les objectifs de production
- **Coûts** : Aligné avec la gestion des ressources - permet de maintenir la viabilité économique de l'outil

**Métriques de valeur utilisateur :**
- Les métriques de qualité mesurent directement la valeur créée pour les utilisateurs (dialogues utilisables)
- Les métriques d'efficacité mesurent l'amélioration du workflow utilisateur (gain de temps)
- Les métriques de coûts mesurent la viabilité économique (durabilité de l'outil)

**Métriques de succès business :**
- Production efficace de dialogues pour Alteir
- Outil production-ready maintenable
- Qualité professionnelle à grande échelle
- Potentiel open-source évalué (horizon futur)

---

## MVP Scope

### Core Features (MVP - Production-Ready)

**Objectif MVP :** Permettre aux auteurs (Marc & Mathieu) de produire un dialogue arborescent complet en ≤1H via une boucle d'écriture fiable : **structurer → générer → contrôler → valider → exporter**.

#### 1. Writer Loop (Must-have)

**1. Graph Editor Fonctionnel (Fix du blocage)**
- Visualisation et édition du graphe (zoom/pan, sélection, édition basique d'un nœud)
- **Connexion des nœuds** (création/édition des liens parent/enfant)
- Correction des bugs actuels (DisplayName vs stableID) pour garantir la stabilité

**2. Intégrité & Validation Structurelle du Graphe (Non-LLM)**
- Validation rapide : références cassées, nœuds vides, START manquant, orphans/unreachable, cycles signalés
- Erreurs actionnables (cliquables) pour corriger rapidement

**3. Génération "Continue" (Cohérence + Auto-link)**
- Générer une suite cohérente **à partir d'un nœud / d'un choix**, avec **auto-connexion** dans le graphe
- Capacité à générer en quantité sans perdre la structure (itération rapide)
- (Option MVP) Variantes contrôlées sur un point (N variantes), sans explosion combinatoire multi-niveaux

**4. Export Unity Fiable**
- Sauvegarde/chargement du dialogue
- Export Unity JSON reproductible (pipeline de prod)

#### 2. Prompt & Contexte (Must-have, mais minimal)

**5. Gestion des Couches du Prompt (Compréhensible et prévisible)**
- Contrôle clair inclusion/exclusion des couches (personnages/lieux/objets/etc.)
- Aperçu du prompt final + estimation tokens/coût avant génération (transparence)

**6. Sélection de Contexte (Déjà OK, amélioration ciblée)**
- Améliorations UX/ergonomie et règles simples de pertinence
- Pas de RAG/embeddings avancés dans le MVP

#### 3. Aide à l'Évaluation (Must-have, scope réduit)

**7. Aide à l'Évaluation "À la Demande"**
- Feedback utilisateur (save/regenerate/delete) instrumenté
- Option d'évaluation LLM **sur un nœud / sous-arbre**, quand l'auteur en a besoin (pas QA globale systématique)

#### 4. Coûts (Must-have, minimal)

**8. Cost Governance Minimal**
- Estimation coût avant run + logs de coût par génération
- Plafond budget configurable (soft/hard) pour éviter les dérives

#### Features Existantes (Déjà Implémentées)

- ✅ Chargement GDD (personnages, lieux, objets, etc.)
- ✅ Génération d'un nœud de dialogue
- ✅ Visualisation liste linéaire
- ✅ Export Unity JSON
- ✅ Sélection contexte (améliorable mais fonctionnelle)

### Out of Scope for MVP (Post-MVP)

**Explicitement hors scope MVP :**

1. **Template Marketplace Complet** (Version 2.0)
   - Version complète avec curation admin, marketplace interne
   - A/B testing LLM, scoring de performance
   - Version simplifiée OK pour MVP si nécessaire

2. **Context Intelligence Avancé** (Amélioration Future)
   - RAG avec embeddings (système hybride avancé)
   - Extraction contextuelle intelligente multi-techniques
   - Amélioration basique OK pour MVP

3. **Navigation Editor Avancée** (Amélioration Future)
   - Jump-to-node, recherche, breadcrumbs avancés
   - Variable Inspector complet (live evaluation, coverage)
   - Simulation Coverage avancée
   - Navigation basique OK pour MVP

4. **Localization** (Préparation Future)
   - Important pour sortie internationale mais pas prioritaire (phase écriture)
   - À préparer pour plus tard

5. **Voice-Over** (Mise de Côté)
   - À voir si Unity gère
   - Pas prioritaire pour MVP

6. **Événements Notables** (Fonctionnalité Avancée)
   - Génération combinatoire de variantes basée sur événements narratifs
   - Complexité élevée, peut attendre version 2.0

7. **Multi-LLM Providers** (Amélioration Future)
   - Support multi-providers (au-delà d'OpenAI)
   - Abstraction multi-provider complète
   - MVP : OpenAI uniquement

8. **RBAC Complet** (Nice-to-Have)
   - MVP peut se contenter d'un partage simple (Marc + Mathieu)
   - RBAC durci (admin/writer/viewer) en Post-MVP si nécessaire

9. **GitService** (Nice-to-Have)
   - Intégration Git pour commit automatique
   - Peut être fait manuellement pour MVP
   - À implémenter si temps disponible

### MVP Success Criteria (Go / No-Go)

**Critères de succès MVP :**

1. **Graph Editor + Connexions Opérationnels**
   - Éditeur de graphe fonctionnel sans bugs bloquants
   - Connexion des nœuds fonctionnelle
   - Génération continue auto-link opérationnelle

2. **Objectif de Production Atteint**
   - Génération de dialogues complets en ≤1H (objectif principal)
   - Taux d'acceptation de qualité >80% (dialogues enregistrés / générés)
   - Outil utilisé quotidiennement par les auteurs (Marc et Mathieu)

3. **Cost Governance Opérationnel**
   - Budget/crédits admin fonctionnels
   - Transparence prompt opérationnelle
   - Coûts LLM maîtrisés dans les limites budgétaires

4. **Aide à l'Évaluation Opérationnelle**
   - Feedback utilisateur opérationnel
   - Option d'évaluation LLM "à la demande" fonctionnelle
   - Système de feedback pour améliorer la génération

**Decision Gates (Go/No-Go) :**

- ✅ **Go si :** Graph editor fonctionnel + connexion nœuds opérationnelle + objectif 1H atteint
- ❌ **No-Go si :** Bugs bloquants persistants + objectif 1H non atteint + coûts non maîtrisés

### Future Vision

**Horizon 2.0 (Post-MVP) :**

1. **Template Marketplace Complet**
   - Marketplace interne avec curation admin
   - A/B testing LLM, scoring de performance
   - Templates personnalisables par utilisateur

2. **Context Intelligence Avancé**
   - RAG avec embeddings + extraction contextuelle intelligente
   - Système hybride multi-techniques
   - Sélection intelligente optimisée (tokens, pertinence)

3. **Navigation Editor Avancée**
   - Jump-to-node, recherche, breadcrumbs avancés
   - Variable Inspector complet (live evaluation, coverage)
   - Simulation Coverage avancée

4. **Localization**
   - Support multi-langues
   - Export/import pour traduction
   - Préparation pour sortie internationale

5. **Événements Notables**
   - Génération combinatoire de variantes basée sur événements narratifs
   - Gestion des états d'événements
   - UI pour sélection événements et états

6. **Multi-LLM Providers**
   - Support multi-providers (Anthropic, local, etc.)
   - Abstraction multi-provider complète
   - Comparaison multi-LLM

**Horizon Open-Source (Long Terme) :**

- Portabilité/réutilisabilité pour d'autres GDD
- Adaptation à d'autres univers narratifs
- Communauté d'auteurs utilisant l'outil
- Contributions externes
- Marketplace de templates communautaire

**Vision 3.0+ (Long Terme) :**

- Collaboration temps réel (WebSockets)
- Versioning narratif (Git-like pour dialogues)
- Intégration avec pipelines de production multiples
- Plateforme complète pour production narrative professionnelle

