---
stepsCompleted: ["step-01-init", "step-02-discovery", "step-03-success", "step-04-journeys", "step-05-domain", "step-06-innovation", "step-07-project-type", "step-08-scoping", "step-09-functional", "step-10-nonfunctional", "step-10b-quality-framework", "step-11-polish"]
inputDocuments:
  - _bmad-output/planning-artifacts/product-brief-DialogueGenerator-2026-01-13.md
  - _bmad-output/planning-artifacts/research/technical-les-meilleures-pratiques-pour-éditeurs-de-dialogues-narratifs-research-2026-01-13T222012.md
  - _bmad-output/analysis/brainstorming-session-2026-01-13T190613.md
  - docs/index.md
  - README.md
  - docs/Spécification technique.md
  - docs/DEPLOYMENT.md
  - docs/project-overview.md
workflowType: 'prd'
briefCount: 1
researchCount: 1
brainstormingCount: 1
projectDocsCount: 5
date: 2026-01-13
user_name: Marc
project_name: DialogueGenerator
classification:
  projectType: "Developer Tool / Web App"
  domain: "Game Development Tools - Narrative Authoring"
  complexity: "Medium-High"
  projectContext: "Active Development → Production Readiness"
  targetScale: "1M+ dialogue lines by 2028"
  productionGoal: "Disco Elysium+ scale CRPG (Alteir)"
partyModeInsights:
  - "Marc is content producer who learned to code, not dev learning content"
  - "500-page GDD produced in 1 year with LLM, quality guaranteed"
  - "Architecture already scales, no major refactoring needed"
  - "Filesystem + Git sufficient, DB migration = YAGNI for now"
  - "Process > tools - Marc already has efficient mental workflow"
  - "32 ideas structured in 6-phase roadmap (MVP → V3.0)"
journeyInsights:
  - "Two distinct personas: Marc (power user) vs Mathieu (casual user)"
  - "Need for Power Mode (advanced features) and Guided Mode (wizard, templates)"
  - "5 architectural systems revealed: LLM Orchestration, State Management, Validation & Quality, Permission & Auth, Search & Index"
  - "Auto-save upgraded from nice-to-have to should-have (V1.0)"
  - "Debug Console needed: chat LLM intégré for diagnostic (V1.0)"
  - "4th persona added: Unity Dev (Thomas) - Integration & JSON validation critical"
  - "New metrics: Autonomy (>95%), Onboarding (<2H), Integration (100% valid exports)"
architecturalReveals:
  systemsIdentified:
    - "LLM Orchestration Layer: multi-provider, fallback, retry logic"
    - "State Management Layer: auto-save, sync, version control"
    - "Validation & Quality Layer: lore checker, structure validator, LLM judge"
    - "Permission & Auth Layer: RBAC, shared access, audit logs"
    - "Search & Index Layer: fast search, filtering, metadata"
  mvpScope:
    - "LLM Orchestration: base (OpenAI only, retry logic)"
    - "State Management: base (manual save, Git)"
    - "Validation: structure only (nœuds vides, orphans)"
  v1Scope:
    - "LLM Orchestration: multi-provider (Anthropic fallback)"
    - "State Management: auto-save (2min intervals)"
    - "Validation: quality (lore checker, LLM judge)"
    - "Permission & Auth: RBAC (3 roles)"
    - "Search & Index: full (metadata search)"
---

# Product Requirements Document - DialogueGenerator

**Author:** Marc
**Date:** 2026-01-13

## Success Criteria

### User Success

**Le Moment "Aha!" - Progression de Valeur**

**Base (MVP)** : Générer un bon nœud de dialogue avec de bons choix joueur
- 1 nœud NPC de qualité
- 3-8 choix joueur pertinents et caractérisés
- Cohérence narrative avec le contexte GDD
- **Critère de succès** : Marc/Mathieu enregistre le nœud sans re-génération

**Top (V1.0)** : Générer d'un coup TOUS les nœuds répondant aux choix d'un nœud précédent
- Génération batch 3-8 nœuds en une passe
- Tous les nœuds de qualité (cohérence, caractérisation, agentivité)
- Auto-connexion dans le graphe (auto-link)
- **Critère de succès** : 80%+ des nœuds générés sont acceptés sans modification

**Vision (V2.0+)** : Dialogue complet à portée
- Génération itérative rapide (workflow fluide)
- Qualité constante sur centaines de nœuds
- Temps de production : quelques heures → dialogue complet validé
- **Critère de succès** : Production dialogue complet (100+ nœuds) en <4H

**Émotions Utilisateur Ciblées :**
- **Émerveillement** : "L'IA a capturé la voix du personnage !"
- **Confiance** : "Je peux itérer rapidement sans craindre de perdre le contrôle"
- **Efficacité** : "Je produis en 1H ce qui me prenait une semaine"

### Business Success

**Objectif Global :** Produire 1M+ lignes de dialogue (Disco Elysium+ scale) d'ici début 2028 pour le CRPG Alteir.

**Milestone 3 Mois (Avril 2026) - Préprod Ready**
- ✅ **Capacité** : Produire un dialogue complet validé en quelques heures
- ✅ **Usage** : Outil utilisé quotidiennement par Marc + Mathieu
- ✅ **Production** : 10-20 dialogues complets validés (test préprod)
- ✅ **Démarrage préprod** : Alteir narrative production officially starts
- **Success Metric** : Outil prouvé opérationnel pour préprod

**Milestone 12 Mois (Janvier 2027) - Production Industrielle**
- ✅ **Capacité** : Plusieurs dialogues complets par jour (2-3+)
- ✅ **Production** : 100+ dialogues complets produits (échelle validée)
- ✅ **Équipe** : Writer à plein temps opérationnel avec l'outil
- ✅ **Pipeline** : Workflow production → Unity → test gameplay fluide
- **Success Metric** : Production industrielle à l'échelle Disco Elysium

**Timeline Globale (2026-2028) :**
- **2026 Q1-Q2** : Tool MVP + préprod start (quelques dialogues/semaine)
- **2026 Q3-Q4** : Production ramp-up (1-2 dialogues/jour)
- **2027** : Production intensive (2-3+ dialogues/jour)
- **2028 Q1** : 1M+ lignes complétées, Alteir narrative content complete

### Technical Success

**Critère Principal : 0 Bug Bloquant**

DialogueGenerator va évoluer avec beaucoup de fonctionnalités. La métrique technique qui juge la production-readiness : **aucun bug qui empêche la production narrative**.

**Définition "Bug Bloquant" :**
- Éditeur graphe inutilisable (crash, rendering cassé, impossible d'éditer)
- Génération LLM fail >10% du temps (instabilité API)
- Export Unity produit JSON invalides (crash Unity import)
- Data loss (dialogues perdus, corruption fichiers)
- Performance dégradée (génération >5min, UI freeze)

**Critères Techniques Additionnels :**

**Stabilité :**
- Uptime >99% (outil toujours accessible)
- Zero data loss (auto-save, backup, versioning Git)
- Error recovery gracieux (retry LLM failures, validation feedback)

**Performance :**
- Génération 1 nœud : <30s (prompt + LLM + validation)
- Génération batch (3-8 nœuds) : <2min
- UI responsive : interactions <100ms
- Graphe 500+ nœuds : rendering <1s

**Scalabilité Prouvée :**
- 1000+ dialogues stockés sans ralentissement
- Search/navigation fluide sur large base
- Git repo performant (100+ MB dialogues)

**Quality Gates :**
- Tests E2E workflow complet (sélection contexte → génération → export Unity)
- Validation JSON Unity schema (100% conformité)
- Coverage code critique >80%

### Measurable Outcomes

**Primary Metrics (Priorité #1 - Qualité)** :
- **Taux d'acceptation qualité** : >80% dialogues enregistrés sans re-génération
- **Taux de re-génération** : <20% (indicateur qualité inversé)
- **Jugement LLM qualité** : Score moyen >8/10 (cohérence, caractérisation, agentivité)

**Secondary Metrics (Priorité #2 - Efficacité)** :
- **Temps moyen génération 1 nœud** : <30s
- **Temps moyen génération batch (3-8 nœuds)** : <2min
- **Temps production dialogue complet** : <4H (objectif initial), <2H (optimisé)
- **Volume production** : Dialogues complets générés par semaine/mois

**Tertiary Metrics (Priorité #3 - Coûts)** :
- **Coût par nœud généré** : <0.01€ (optimisé)
- **Coût par dialogue complet** : <1€ (100 nœuds)
- **Budget mensuel LLM** : <100€ (phase test), <500€ (production intensive)

**Business Impact Metrics** :
- **Production totale** : Dialogues complets validés (cumulative)
- **Lignes totales** : Progression vers 1M+ lignes (tracking)
- **Adoption utilisateur** : Marc + Mathieu usage quotidien (engagement)

## Product Scope

### MVP - Minimum Viable Product (Sprint 1-2, ~1 semaine)

**Goal :** Débloquer la production immédiate. Atteindre le moment "aha!" Base.

**Must-Have :**
1. ✅ **Éditeur graphe fonctionnel** (fix display bug, connexions nœuds, édition basique)
2. ✅ **Génération continue + auto-link** (générer depuis choix, auto-connexion graphe)
3. ✅ **Validation structurelle** (DisplayName/stableID, nœuds vides, orphans, cycles)
4. ✅ **Export Unity fiable** (batch export, validation JSON schema)

**Success Criteria MVP :**
- Marc/Mathieu génèrent 1 nœud de qualité en <1min
- Génération batch 3-8 nœuds en <2min
- Export Unity sans erreurs (100% conformité schema)
- 0 bugs bloquants identifiés

### V1.0 - Editor Pro Foundation (Sprint 3-5, ~2-3 semaines)

**Goal :** Atteindre le moment "aha!" Top. Éditeur professionnel scalable.

**Should-Have (Pattern "Editor Pro") :**
5. 🟡 **Navigation Editor** (jump-to-node, search texte/acteur, focus auto)
6. 🟡 **Dialogue Database layer** (index/search, renommage/refactor, refs cassées)
7. 🟡 **Variable Inspector** (variables/flags, scénarios presets, simulation basique)
8. 🟡 **Simulation Coverage** (run dialogue, dead ends/unreachable, rapport)

**Success Criteria V1.0 :**
- Navigation fluide dialogues 500+ nœuds
- Refactoring (renommer acteur) propage automatiquement
- Simulation détecte >95% bugs structurels
- Production dialogue complet <4H

### V1.5 - Cost & Collaboration (Sprint 6-8, ~2-3 semaines)

**Goal :** Gouvernance coûts + collaboration équipe.

**Should-Have (Pattern "Cost Governance" + RBAC) :**
9. 🟡 **Cost Governance** (estimation coût, transparence prompt, logs/audit)
10. 🟡 **RBAC + Shared Dialogues** (admin/writer, dialogues partagés)
11. 🟡 **Template System v1** (templates instructions/auteur, personnalisation, validation)

**Success Criteria V1.5 :**
- Coûts LLM <0.01€ par nœud (optimisé)
- Marc + Mathieu collaborent sans friction
- Templates améliorent qualité +20% (LLM judge)

### V2.0 - Context Intelligence (Sprint 9-12, ~4 semaines)

**Goal :** Atteindre le moment "aha!" Vision. Optimisation contextuelle.

**Could-Have (Pattern "Context Intelligence") :**
12. 🟢 **Intelligent Context Selection** (extraction sous-parties pertinentes)
13. 🟢 **Hybrid Context Intelligence** (RAG + embeddings + règles)
14. 🟢 **Contextual Link Exploitation** (auto-suggest via liens JSON GDD)
15. 🟢 **Dialogue History Recommender** (re-utilisation contextes similaires)

**Success Criteria V2.0 :**
- Réduction tokens -50% (5000 → 2500 tokens/prompt)
- Pertinence contexte >90% (validation humaine)
- Workflow accéléré : 4H → 2H par dialogue complet

### V2.5 - Quality & Validation Pro (Sprint 13-15, ~3 semaines)

**Goal :** Industrialisation qualité narrative.

**Could-Have (Pattern "Quality & Validation") :**
16. 🟢 **Template Marketplace complet** (bibliothèque admin, A/B testing, scoring)
17. 🟢 **Template Quality Validation** (tests auto, LLM judge, feedback loop)
18. 🟢 **Multi-LLM Comparison** (génération simultanée, LLM judge, sélection)

**Success Criteria V2.5 :**
- Taux acceptation qualité >90%
- Feedback loop améliore templates automatiquement
- Multi-LLM réduit coûts -30%

### V3.0 - Advanced Features (Sprint 16+, ~6+ semaines)

**Goal :** Features avancées pour scale ultime.

**Nice-to-Have :**
19. ⚪ **Multi-LLM Provider Architecture** (support Anthropic/local)
20. ⚪ **Game System Integration** (conditions stats, effets relations)
21. ⚪ **Conditions/Variables DSL** (langage writer-friendly, validation)
22. ⚪ **Sequencer-lite RPG** (delta influence, unlock traits, hooks Unity)
23. ⚪ **Twine-like Passage Linking** (draft rapide texte, compilation JSON)
24. ⚪ **Git-like Narrative Versioning** (branches narratives, merge assisté)

**Success Criteria V3.0 :**
- Support 3+ LLM providers
- Game systems intégrés (conditions/variables/effets)
- Workflow hybride texte/graphe opérationnel

### Growth Features (Post-MVP)

**Déploiement progressif selon feedback production réelle :**
- DB migration (si filesystem devient douloureux)
- Advanced search (si volume nécessite)
- Dashboard analytics (si métriques critiques)
- Localization prep (si sortie internationale confirmée)

### Vision (Future)

**Long Terme (Post-2028) :**
- Voice-Over metadata integration
- Real-time collaboration (WebSockets)
- Multi-game support (réutilisabilité GDD)
- Community marketplace (templates partagés)
- Open-source release (si pertinent)

## User Journeys

### Journey 1 : Marc - Le Power User / Content Producer

**Persona :** Marc  
*Content producer qui a appris à coder, pas dev qui apprend le contenu*

**Context & Background :**
- Utilise DialogueGenerator 40h/semaine (usage intensif)
- Expert du GDD Alteir (500 pages produites en 1 an avec LLM)
- Responsable qualité narrative finale
- Tolère la friction technique si contrôle total
- Mental workflow déjà efficace, besoin d'outils qui s'adaptent

**Primary Goal :** Produire des dialogues de qualité Disco Elysium scale en maximisant le contrôle créatif et la vitesse de production.

**Opening Scene - Le Problème Subtil :**

Marc génère un dialogue pour **Akthar-Neth** (personnage philosophe) discutant avec le joueur sur **Deimos** (lune-gardienne d'Amatru, monde sans étoiles).

**Génération LLM produit :**
> "Akthar : Oui, les étoiles brillent dans le ciel... Deimos les protège."

**❌ ERREUR DE LORE** : Le monde Amatru n'a PAS d'étoiles (lore établi : ciel vide gardé par Deimos).

**Frustration Marc :** *"Context dropping ENCORE. L'IA a reçu le GDD, mais elle n'a pas intégré la lore subtilement. Elle mentionne 'étoiles' explicitement alors que c'est une révélation narrative tardive que ce monde n'en a pas."*

**Rising Action - Le Workflow Actuel :**

1. **Itération manuelle** : Marc modifie le prompt pour renforcer "absence étoiles"
2. **Re-génération** : Nouveau nœud, meilleur mais encore trop explicite
3. **3ème tentative** : Enfin, un nœud subtil et philosophique :
   > "Akthar : Uresaïr médite sous Deimos... Certains cherchent ce qui n'existe plus. D'autres gardent ce qui demeure."

**✅ SUCCESS** : Le nœud capture la voice d'Uresaïr (calme, philosophique) ET la lore (Deimos gardien, absence étoiles) SANS l'expliquer explicitement.

**Climax - Le Moment "Aha!" :**

Marc sélectionne le nœud parfait. **Mais maintenant il a 8 choix joueur à développer.**

Il clique : **"Générer tous les nœuds suivants"**.

DialogueGenerator génère **batch 8 nœuds en 90 secondes**. Marc les review rapidement :
- **6/8 nœuds** : Qualité parfaite, acceptés immédiatement
- **2/8 nœuds** : Minimes ajustements (reformulation)

**🎯 Moment "Aha!" :** *"C'est ça. Je viens de produire en 2 minutes ce qui me prenait 1H. ET la qualité est là."*

**Resolution - Le Nouveau Workflow :**

Marc continue l'itération. En **3H**, il a :
- 1 dialogue complet (120 nœuds)
- 80% des nœuds générés acceptés sans modification
- Coût total : 0.75€ LLM
- Export Unity : JSON validé, 0 erreurs

**Milestone atteint** : Dialogue complet de qualité professionnelle en quelques heures.

**Emotional Arc :**
- **Frustration** (context dropping, lore explicite) → **Expérimentation** (itération prompts) → **Découverte** (node parfait) → **Émerveillement** (batch generation qualité) → **Confiance** (workflow rapide + contrôle)

**Edge Cases & Pain Points :**

1. **LLM API down** (OpenAI 503) :
   - **Current** : Génération échoue, Marc attend ou retry manuel
   - **Desired (V1.0)** : Fallback automatique Anthropic, 0 friction

2. **Context dropping récurrent** (lore non intégrée) :
   - **Current** : Itération manuelle prompts
   - **Desired (V2.0)** : Template System anti-context-dropping (instructions optimisées)

3. **Debug mystérieux** (génération échoue sans raison) :
   - **Current** : Marc examine logs backend manuellement
   - **Desired (V1.0)** : Debug Console avec chat LLM intégré (diagnostic automatique)

4. **Session loss** (crash navigateur) :
   - **Current** : Perte des modifications non sauvegardées
   - **Desired (V1.0)** : Auto-save toutes les 2min, recovery automatique

**Required Capabilities :**
- ✅ MVP : Génération continue + batch, validation structure, export Unity fiable
- 🟡 V1.0 : Multi-provider LLM (fallback), auto-save, debug console, RBAC
- 🟢 V2.0 : Template System (anti context-dropping), lore checker, LLM judge qualité

**Success Metrics :**
- **Qualité** : >80% nœuds acceptés sans re-génération
- **Efficacité** : <4H par dialogue complet (120 nœuds)
- **Coûts** : <1€ par dialogue complet
- **Stabilité** : 0 bugs bloquants, 0 data loss

---

### Journey 2 : Mathieu - Le Writer Occasionnel

**Persona :** Mathieu  
*Game Designer / Writer occasionnel, temps limité*

**Context & Background :**
- Utilise DialogueGenerator quelques heures/semaine (usage occasionnel)
- Connaît bien le lore Alteir, mais pas expert technique de l'outil
- Temps limité : veut produire rapidement sans friction
- Besoin d'autonomie : préfère ne pas appeler Marc pour chaque question
- Workflow idéal : wizard guidé, automation maximale

**Primary Goal :** Produire un dialogue de qualité rapidement (1-2H max) sans support technique externe.

**Opening Scene - La Découverte :**

Mathieu a une idée narrative : **"Taverne des Poutres Brisées"** (lieu) → Conversation NPC sur **Avili de l'Éternel Retour** (région mythique des Nids-Cités).

Il ouvre DialogueGenerator. **Dashboard intimidant** : nombreux champs, options avancées.

**Hésitation :** *"Par où commencer ? Je veux juste générer un dialogue simple..."*

**Rising Action - Le Workflow Guidé :**

**V1.0 : Wizard Onboarding activé automatiquement (mode Guided détecté).**

1. **Step 1** : "Quel lieu pour ce dialogue ?" → Mathieu tape "Taverne" → Liste filtrée apparaît : "Taverne des Poutres Brisées"
2. **Step 2** : "Quel personnage parle ?" → Mathieu sélectionne "NPC Tavernier"
3. **Step 3** : "Contexte ou thème ?" → Mathieu écrit : "Légende Avili Éternel Retour"
4. **Step 4** : "Instructions spéciales ?" → Template pré-rempli : *"Ton informel, ambiance taverne, révélation progressive lore"*

**Bouton** : **"Générer dialogue"**

**Climax - Le Moment "Connect-the-dots" :**

DialogueGenerator génère le 1er nœud :
> "Tavernier : T'as entendu parler des Nids-Cités ? Y'en a qui disent qu'Avili revient tous les cycles... Moi j'y crois pas, mais les vieux du coin jurent l'avoir vue."

**🎯 Moment "Aha!" :** *"Wow. L'IA a connecté les points : Taverne → Avili → Nids-Cités. Je n'ai pas eu à expliquer les liens, elle a compris le contexte."*

Mathieu génère 4 choix joueur, puis batch 4 nœuds suivants. **Tout fonctionne.**

**Resolution - Autonomie Atteinte :**

En **1H30**, Mathieu a :
- 1 dialogue complet (80 nœuds)
- Qualité validée (cohérence lore, ton approprié)
- Export Unity : prêt pour intégration
- **0 fois** : Besoin d'appeler Marc pour support

**Auto-save** : Mathieu ferme son navigateur pour une réunion. Quand il revient, **tout son travail est restauré automatiquement**.

**Emotional Arc :**
- **Hésitation** (interface intimidante) → **Guidance** (wizard clair) → **Découverte** (connect-the-dots auto) → **Confiance** (autonomie complète) → **Satisfaction** (production rapide sans friction)

**Edge Cases & Pain Points :**

1. **Interface trop complexe** (mode power par défaut) :
   - **Current (MVP)** : Mathieu hésite, appelle Marc
   - **Desired (V1.0)** : Détection automatique skill level → wizard guided activé

2. **Perte de travail** (navigateur fermé accidentellement) :
   - **Current (MVP)** : Modifications perdues
   - **Desired (V1.0)** : Auto-save toutes les 2min + recovery session automatique

3. **Recherche lente** (GDD 500 pages, difficile de trouver contexte pertinent) :
   - **Current (MVP)** : Recherche manuelle
   - **Desired (V1.0)** : Search & Index Layer (metadata search, filtres rapides)

4. **Qualité incertaine** (Mathieu pas sûr si le dialogue est bon) :
   - **Current (MVP)** : Demande validation à Marc
   - **Desired (V1.5)** : LLM judge qualité automatique (score 8/10) + suggestions

**Required Capabilities :**
- 🟡 V1.0 : Wizard Onboarding (guided mode), auto-save, search performante, mode detection
- 🟢 V1.5 : LLM judge qualité, templates pré-remplis, validation automatique
- 🟢 V2.0 : Context Intelligence (connect-the-dots automatique)

**Success Metrics :**
- **Autonomie** : >95% sessions sans support Marc
- **Efficacité** : <2H par dialogue complet (80 nœuds)
- **Onboarding** : <30min pour 1er dialogue complet produit

---

### Journey 3 : Sophie - Le Viewer / Productrice

**Persona :** Sophie  
*Productrice, stakeholder, lecture seule*

**Context & Background :**
- Ne produit pas de dialogues, mais suit la production
- Besoin de visibilité sur l'avancement (combien de dialogues produits, qualité, métriques)
- Consulte DialogueGenerator pour reporting stakeholders
- Utilise le graphe en mode lecture seule pour review narratif

**Primary Goal :** Suivre la production narrative et reporter aux stakeholders (investisseurs, CNC, équipe).

**Opening Scene - Le Besoin de Visibilité :**

Sophie prépare un rapport mensuel pour les investisseurs :
- **Question 1** : Combien de dialogues complets produits ce mois ?
- **Question 2** : Quelle est la qualité moyenne (taux acceptation) ?
- **Question 3** : Sommes-nous on track pour 1M lignes d'ici 2028 ?

**Current (MVP)** : Sophie envoie email à Marc : *"Peux-tu me donner les chiffres ?"*

**Rising Action - Dashboard Viewer :**

**V1.5 : RBAC activé. Sophie a un compte "Viewer".**

Elle se connecte à DialogueGenerator :
- **Dashboard** : Affiche métriques globales
  - **Dialogues produits** : 45 complets (ce mois : +12)
  - **Lignes totales** : 4,500 (progression : +1,200 ce mois)
  - **Taux acceptation qualité** : 82% (target : >80% ✅)
  - **Coût moyen** : 0.75€ par dialogue (target : <1€ ✅)

**Climax - Le Graphe en Lecture Seule :**

Sophie ouvre un dialogue : **"Akthar-Neth_Taverne_LegendeAvili"**.

Le graphe s'affiche en **mode lecture seule** (pas d'édition possible). Elle peut :
- Naviguer les nœuds
- Lire le contenu
- Voir les branches narratives

**🎯 Moment "Aha!" :** *"Je peux montrer ça aux investisseurs. Ils vont voir la complexité des dialogues produits."*

**Resolution - Reporting Autonome :**

Sophie génère un rapport PDF depuis DialogueGenerator (V1.5 feature) :
- Métriques de production (volume, qualité, coûts)
- Screenshots graphes dialogues clés
- Projection 2028 : **On track pour 1M lignes**

**Stakeholders validés.** Sophie n'a pas eu besoin de Marc pour les chiffres.

**Emotional Arc :**
- **Frustration** (dépendance Marc pour chiffres) → **Découverte** (dashboard viewer) → **Confiance** (données fiables) → **Satisfaction** (reporting autonome)

**Edge Cases & Pain Points :**

1. **Accès lecture seule non garanti** (risque édition accidentelle) :
   - **Current (MVP)** : Pas de RBAC, Sophie pourrait modifier par erreur
   - **Desired (V1.5)** : RBAC strict (Viewer = read-only garanti)

2. **Métriques indisponibles** (pas de dashboard analytics) :
   - **Current (MVP)** : Sophie demande à Marc
   - **Desired (V1.5)** : Dashboard analytics complet (métriques temps réel)

**Required Capabilities :**
- 🟡 V1.5 : RBAC (3 roles : Admin/Writer/Viewer), dashboard analytics, export PDF reporting

**Success Metrics :**
- **Autonomie** : >90% reporting sans support Marc
- **Fiabilité** : Métriques temps réel, 0 erreurs données

---

### Journey 4 : Thomas - Le Unity Dev / Intégrateur

**Persona :** Thomas  
*Unity Developer, responsable intégration dialogues in-game*

**Context & Background :**
- Utilise système de dialogue maison (codé en C# dans Unity) pour intégrer les dialogues
- Reçoit les JSON produits par DialogueGenerator (export Unity)
- Ne produit pas de dialogues, mais doit les intégrer sans friction
- Besoin : JSON 100% conformes au schema Unity custom (pas d'erreurs import)
- Edge case critique : Erreur schema → blocage pipeline

**Primary Goal :** Intégrer les dialogues dans Unity sans erreurs, tester in-game rapidement, détecter problèmes avant build production.

**Opening Scene - L'Import Échoue :**

Thomas ouvre DialogueGenerator (compte Viewer). Il voit :
- **"Akthar-Neth_Taverne_LegendeAvili"** - Status: **Exported**

Il télécharge le JSON, l'importe dans Unity via le système de dialogue maison.

**❌ ERREUR Unity :**
```
Invalid JSON schema - missing stableID on node 7
```

**Frustration Thomas :** *"Le JSON ne respecte pas le schema. Je dois demander à Marc de corriger... Encore une itération perdue."*

**Rising Action - Validation Stricte :**

**V1.0 : JSON Validation Unity stricte activée.**

Marc re-génère le dialogue. **Avant export**, DialogueGenerator exécute :
1. **Schema validation** : Vérifie tous les champs requis (stableID, DisplayName, etc.)
2. **Structure validation** : Vérifie cohérence nœuds/liens (pas d'orphans, cycles OK)
3. **Unity compatibility check** : Teste conformité 100% schema custom Unity

**Résultat** : **✅ Validation passed. Export autorisé.**

**Climax - L'Import Réussit :**

Thomas télécharge le nouveau JSON. Import Unity → **✅ Success. 0 erreurs.**

Il teste le dialogue in-game :
- Les choix joueur fonctionnent
- Les branches narratives sont cohérentes
- Les conditions/variables sont correctes

**🎯 Moment "Aha!" :** *"Enfin. DialogueGenerator garantit JSON Unity-ready. Je n'ai plus à debugger les exports."*

**Resolution - Pipeline Smooth :**

Thomas intègre 12 dialogues ce mois. **100% imports réussis, 0 erreurs schema.**

**Nouveau workflow** : DialogueGenerator → Export validé → Unity import → Test in-game → Production.

**Emotional Arc :**
- **Frustration** (import échoue, schema invalide) → **Découverte** (validation stricte activée) → **Confiance** (exports garantis valides) → **Efficacité** (pipeline sans friction)

**Edge Cases & Pain Points :**

1. **Schema Unity change** (système dialogue C# update) :
   - **Current (MVP)** : Exports cassés après update schema Unity
   - **Desired (V1.0)** : Validation schema paramétrable (accord dev Unity/IA pour évolutions)

2. **Test in-game lent** (besoin d'importer → build → tester) :
   - **Current (MVP)** : Workflow lourd
   - **Desired (V2.5)** : Simulation gameplay in-tool (preview branches sans Unity)

3. **Debugging erreurs in-game** (dialogue bugs, conditions incorrectes) :
   - **Current (MVP)** : Difficile de tracer l'origine (Unity logs peu clairs)
   - **Desired (V1.5)** : Export logs enrichis (metadata debug, trace génération)

**Required Capabilities :**
- ✅ MVP : Export Unity basique (JSON valide structure)
- 🟡 V1.0 : Validation JSON Unity stricte (100% conformité schema custom Unity)
- 🟡 V1.5 : Export logs enrichis (metadata debug)
- 🟢 V2.5 : Simulation gameplay in-tool (preview branches)

**Success Metrics :**
- **Integration** : 100% exports Unity sans erreurs schema
- **Efficacité** : <5min par dialogue pour import + test in-game
- **Fiabilité** : 0 bugs schema détectés post-import

---

## Domain-Specific Requirements

### Game Development Tools - Narrative Authoring

**Domain Context :** DialogueGenerator est un outil de production narrative pour CRPGs (Computer Role-Playing Games) à l'échelle Disco Elysium/Planescape Torment/BG3. Ce domaine a des exigences spécifiques en termes de qualité narrative, workflow créatif, et intégration technique.

---

### Standards & Formats

**Système de Dialogue Unity :**
- **Implémentation** : Système de dialogue maison codé en C# dans Unity (pas de plugin tiers)
- **Format** : JSON custom consommé par le système Unity
- **Évolution schema** : Format peut évoluer uniquement avec accord des devs Unity (ou IA dev Unity)
- **Validation** : 100% conformité au schema custom Unity requis (blocage pipeline si échec)

**Contrainte critique :**  
Tout export DialogueGenerator doit être **validé avant export** pour garantir compatibilité Unity. Aucun JSON invalide ne doit atteindre Unity (coût itération élevé).

---

### Workflow Créatif - Risques & Best Practices

**Risques Réels à Éviter :**

1. **Loss of Authorial Control**
   - **Risque** : L'IA prend des décisions narratives sans supervision humaine
   - **Mitigation** : Marc garde contrôle créatif total (LLM = assistant, pas auteur)
   - **Implementation** : Validation humaine requise avant acceptation nœud, édition manuelle toujours possible

2. **"AI Slop" (Contenu Générique/Fade)**
   - **Risque** : Dialogues génériques, prévisibles, sans personnalité
   - **Mitigation** : Templates optimisés, voice consistency checker, LLM judge qualité
   - **Implementation** : Score qualité >8/10 requis, feedback loop amélioration templates

3. **Genericité Narrative**
   - **Risque** : Perte de l'unicité narrative du monde Alteir, dialogues interchangeables
   - **Mitigation** : Lore checker (contradictions GDD), context richness, tone consistency
   - **Implementation** : Validation lore automatique, GDD 500 pages intégré dans contexte

**Best Practices à Garantir :**

1. **Player Agency**
   - **Principe** : Joueur doit avoir choix significatifs qui impactent la narration
   - **Implementation** : 3-8 choix joueur par nœud NPC, agentivité validée par LLM judge
   - **Validation** : Vérifier que choix ont des conséquences différentes (pas juste reformulations)

2. **Branching Coherence**
   - **Principe** : Branches narratives cohérentes entre elles, pas de contradictions
   - **Implementation** : Validation structure (orphans, cycles), simulation coverage
   - **Validation** : Run dialogue complet, détecter dead ends/unreachable >95%

3. **Tone Consistency**
   - **Principe** : Chaque personnage a une voice distinctive, maintenue sur tous ses dialogues
   - **Implementation** : Voice consistency checker, character profile intégré au contexte
   - **Validation** : Tone score par personnage (Uresaïr = calme/philosophique maintenu)

**Note :** Ces best practices sont un **échantillon minimal**. D'autres seront identifiées pendant la production (feedback utilisateur, itérations).

---

### Integration Ecosystem

**Outils Externes :**

1. **Notion (GDD - Game Design Document)**
   - **Usage actuel** : GDD 500 pages stocké sur Notion, exporté JSON via Notion-Scrapper
   - **Intégration potentielle V2.0** : Renforcer lien DialogueGenerator ↔ Notion
   - **Use cases** :
     - Sync automatique GDD (webhook Notion → auto-update DialogueGenerator)
     - Export dialogues vers Notion (documentation narrative, review stakeholders)
     - Bidirectional linking (page Notion personnage ↔ dialogues associés)

2. **Unity (Game Engine)**
   - **Usage actuel** : Import JSON dialogues dans système C# custom
   - **Intégration** : Export JSON validé DialogueGenerator → Unity pipeline
   - **Workflow** : DialogueGenerator → Export → Unity import → Test in-game → Production

**Priorité intégration :**  
- **V1.0** : Validation stricte export Unity (garantir compatibilité)
- **V2.0** : Explorer intégration Notion (si workflow sync GDD devient douloureux)

---

### Quality & Intellectual Property

**Qualité Narrative à l'Échelle 1M Lignes :**

**Challenge :** Maintenir qualité constante sur production massive (1M+ lignes d'ici 2028).

**Stratégie qualité :**
1. **Validation multi-niveaux** :
   - Structure (MVP) : Nœuds vides, orphans, cycles
   - Schema (V1.0) : Conformité JSON Unity
   - Lore (V1.5) : Contradictions GDD, accuracy checker
   - Quality (V1.5) : LLM judge score >8/10, voice consistency

2. **Review Process** :
   - Marc/Mathieu review humain (acceptation/rejet nœuds)
   - Feedback loop amélioration templates (V2.0)
   - A/B testing templates (V2.5) : Identifier patterns qualité optimaux

3. **Consistency Checks** :
   - Voice consistency par personnage (tone score tracking)
   - Lore accuracy (detect contradictions GDD 500 pages)
   - Player agency validation (choix significatifs, pas cosmétiques)

**Propriété Intellectuelle :**

**Position Marc :** Pas de contraintes IP. Open source friendly.

**Implications :**
- ✅ Pas de restrictions sur partage dialogues générés
- ✅ Pas de contraintes sur envoi données à OpenAI/Anthropic (pas de privacy concerns)
- ✅ Open-source release potentielle (Vision future, post-2028)

**Note :** Si open-source, considérer :
- Anonymisation GDD spécifique Alteir (partager outil, pas contenu)
- Documentation workflow production (communauté narrative gaming)
- Marketplace templates (partage patterns anti context-dropping)

---

### Performance & Scale Benchmarks

**Objectifs Scale :**
- **Target** : 1M+ lignes dialogue d'ici début 2028 (équivalent Disco Elysium+)
- **Architecture** : Doit supporter ce scale sans refactoring majeur

**Benchmarks Techniques :**

**Storage & Search :**
- **MVP** : Filesystem + Git (1000+ dialogues, 100+ MB)
- **V1.0** : Search & Index Layer (navigation fluide 1000+ dialogues)
- **V2.0+** : DB migration si filesystem devient douloureux (décision basée feedback production)

**Graph Editor Performance :**
- **Target** : Rendering graphe 500+ nœuds <1s
- **Interaction** : UI responsive <100ms
- **Large dialogues** : Support 100+ nœuds par dialogue (Disco Elysium scale)

**LLM Generation Performance :**
- **1 nœud** : <30s (prompt + LLM + validation)
- **Batch (3-8 nœuds)** : <2min
- **Dialogue complet (100 nœuds)** : <4H (objectif initial), <2H (optimisé V2.0)

**Unity Integration Performance :**
- **Import JSON** : <5s par dialogue (100 nœuds)
- **Schema validation** : 100% conformité (0 erreurs)
- **Test in-game** : <5min par dialogue (import + build + test)

---

### Technical Constraints Summary

**Must-Have (Blockers) :**
- ✅ JSON Unity 100% valid (conformité schema custom C#)
- ✅ Authorial control total (Marc garde décision finale)
- ✅ Lore accuracy (contradictions GDD détectées)
- ✅ Scale-ready architecture (1M+ lignes supportées)

**Should-Have (V1.0+) :**
- 🟡 Quality validation (LLM judge >8/10, voice consistency)
- 🟡 Best practices garanties (player agency, branching coherence, tone)
- 🟡 Integration Notion explorée (si workflow GDD sync critique)

**Could-Have (V2.0+) :**
- 🟢 Template marketplace (patterns anti AI slop)
- 🟢 A/B testing templates (optimisation qualité automatique)
- 🟢 Open-source release (communauté narrative gaming)

---

## Innovation & Novel Patterns

### Detected Innovation Areas

**1. First-Ever LLM-Assisted CRPG Dialogue Production at Disco Elysium+ Scale**

**Innovation :** DialogueGenerator vise à produire **1M+ lignes de dialogue** pour un CRPG de l'envergure de Disco Elysium/Planescape Torment/BG3, avec assistance LLM. **Vous êtes les premiers.**

**Context Market ([EQ-Bench Creative Writing](https://eqbench.com/creative_writing.html)) :**
- Écriture de livres avec LLM existe (inspiration possible)
- Outils game dev AI : Inworld (script assist/prototypage), mais pas production asset complet
- Prototypes recherche : GENEVA (narrative graph from constraints), mais pas packagé outil prod
- Chat-tree interfaces : tldraw branching chat, GitChat (gestion conversations en branches), mais pas pour dialogues ramifiés complexes avec contraintes/flags/conséquences

**Gap identifié :** Pas d'outil pour **production asset éditable** (type Yarn/Ink/Articy) avec contraintes fortes, tests automatiques, export propre, **at CRPG scale**.

**Différenciation clé :**
- **Scale** : 1M+ lignes (Disco Elysium+)
- **Quality** : Pas "AI slop", mais qualité narrative professionnelle
- **Outillage complet** : Génération + Édition graphe + Validation + Export Unity

**Competitive Defensibility :**

**NOT tech stack** (commodité : LLM API + React + FastAPI copiable en 6 mois)

**BUT domain expertise :**
- **Content producer profile** : Marc = rare profile (content producer who learned to code, not dev learning content)
- **Prompting art** : Templates anti context-dropping, accumulated know-how over hundreds of dialogues
- **Process innovation** : Two-phase quality (manual establishment → automated validation)

**First-mover window :** 6-12 mois avant que concurrents (Inworld, studios AA) copient tech.

**Long-term moat :** Si open-source (Vision future), competitive advantage devient **communauté** + **expertise documentée** (process, templates, best practices).

---

**2. Context Intelligence - Règles de Pertinence Explicites**

**Innovation :** La plupart des outils AI writing sont **"generic context-free"**. DialogueGenerator est **"deeply lore-aware"** via **système de règles de pertinence contexte**.

**Mechanism :**
- GDD 500 pages (Alteir) intégré dans contexte génération via Notion-Scrapper
- LLM ne génère pas dans le vide, mais **informé par lore massive**
- "Connect-the-dots" automatique : Taverne → Avili → Nids-Cités (Journey Mathieu)
- Context Intelligence (V2.0) : RAG + embeddings + **règles pertinence** pour extraction sous-parties pertinentes

**Core IP - Règles de Pertinence Contexte (Explicites, Outillées, Évolutives, Mesurables) :**

**Principe :** Pour chaque dialogue, déterminer **quelles parties GDD sont pertinentes** via règles explicites.

**Exemple règles :**
```
Dialogue Taverne_Conversation_Avili :
  → Lieu : Taverne des Poutres Brisées (description complète + ambiance)
  → Région : Nids-Cités (contexte géographique + culture)
  → Personnages présents : Akthar-Neth (profile complet + voice + backstory)
  → Thème discussion : Avili de l'Éternel Retour (légende + implications narratives)
  → Relations : Liens Akthar ↔ Avili, Taverne ↔ Région
  
  EXCLUSIONS :
  → Autres régions (non pertinentes pour ce dialogue)
  → Personnages absents (pas dans la scène)
  → Thèmes non abordés (pas dans instructions)
```

**Architecture système (V2.0) :**

**1. Règles Explicites (Configuration JSON/YAML) :**
```yaml
context_rules:
  dialogue_type: taverne_conversation
  required_entities:
    - type: lieu
      selector: by_name
      value: "Taverne des Poutres Brisées"
    - type: region
      selector: by_location_hierarchy
      value: auto_from_lieu
    - type: personnage
      selector: by_presence_scene
      value: ["Akthar-Neth"]
    - type: theme
      selector: by_keywords
      value: ["Avili", "Éternel Retour", "légende"]
  
  relations:
    - extract_links_between: [personnage, theme]
    - extract_links_between: [lieu, region]
  
  exclusions:
    - exclude_regions: all_except_current
    - exclude_personnages: all_except_present
```

**2. Outillage (Context Selection Service) :**
- **Context Builder** : Construit le contexte basé sur règles
- **Context Validator** : Vérifie pertinence (mesure overlap thème ↔ GDD extrait)
- **Context Optimizer** : Réduit tokens gardant pertinence maximale

**3. Évolutivité (Learning System) :**
- **Feedback loop** : Marc accepte/rejette nœuds → analyse quel contexte a produit qualité
- **Rule refinement** : Ajuste règles pertinence basées sur patterns qualité
- **Template optimization** : Templates évoluent avec règles

**4. Mesurabilité (Metrics) :**
- **Context relevance score** : % GDD extrait utilisé dans dialogue généré (target >80%)
- **Token efficiency** : Tokens contexte / Tokens dialogue généré (optimize ratio)
- **Quality correlation** : Corrélation entre contexte fourni ↔ qualité nœud (LLM judge score)

**Innovation architecturale :**

**Pas juste RAG générique**, mais **"business rules for narrative context selection"**.

**Différenciation :** Generic AI writing tools : RAG blind (embed tout, retrieve top-K). DialogueGenerator : **règles métier narratives** (quoi inclure, quoi exclure, pourquoi).

**Risque mitigé :** Si context windows LLMs explosent (GPT-5 = 10M tokens), RAG devient moins critique MAIS règles pertinence restent valuable (sélection intelligente > brute force full GDD).

---

**3. Anti "AI Slop" Quality System - Two-Phase Strategy**

**Innovation :** Système de qualité multi-layer pour garantir **0 "AI slop"** à l'échelle.

**Phase 1 (MVP-V1.0) : Établissement Style Manuel**
- Travail manuel sur **premières centaines de lignes** (ou premières lignes par personnage)
- Lignes retouchées ou **écrites à la main** si nécessaire
- LLM reçoit ce contexte → **continue dans le même style établi**

**Phase 2 (V1.5-V2.0) : Validation Multi-Layer Automatique**
- **Structure** : Nœuds vides, orphans, cycles
- **Schema** : Conformité JSON Unity custom
- **Lore** : Contradictions GDD, accuracy checker
- **Quality** : LLM judge score >8/10, voice consistency, anti context-dropping templates
- **Feedback loop** : Amélioration templates basée sur patterns qualité

**Référence benchmark :** [EQ-Bench Creative Writing v3](https://eqbench.com/creative_writing.html) - Mesure "Slop Score" (fréquence mots/phrases LLM overused).

**Adaptation DialogueGenerator :** Benchmark **par run** (pas par modèle), critères mesurables adaptés CRPG dialogues.

---

**4. Iterative Generation IN Graph Editor**

**Innovation UX :** La plupart des éditeurs narratifs sont soit consultation (Articy, lourd) soit édition pure (Twine, linéaire). DialogueGenerator combine **génération LLM itérative + édition graphe temps réel**.

**Workflow révolutionnaire :**

1. **Generate** : Depuis nœud existant, générer batch 3-8 nœuds suivants
2. **Review** : Voir nœuds générés **immédiatement dans graphe** (pas liste séparée)
3. **Accept/Reject** : Inline review (clic droit → accept/reject, édition rapide)
4. **Iterate** : Re-générer nœuds rejetés avec instructions ajustées

**User pain point résolu (Journey Marc) :**
> "Marc génère batch 8 nœuds en 90 secondes. Il les review rapidement dans le graphe, 6/8 acceptés immédiatement."

**Différenciation :**
- **NOT** : Génération LLM séparée → import manuel dans éditeur (friction élevée)
- **BUT** : Génération intégrée dans éditeur, workflow fluide, itérations rapides

**Rare combination :**
- Graph editor 500+ nœuds performant (rendering <1s)
- AI batch insertion (3-8 nœuds en <2min)
- Auto-linking (connexions automatiques)
- Inline review (accept/reject dans graphe, pas UI séparée)

---

**5. Prompting as Art - Branching Dialogues Specificity**

**Innovation :** Le prompting pour **dialogues ramifiés CRPG** est un **art largement inexploré**.

**Spécificités techniques :**
- **Player Agency** : 3-8 choix significatifs (pas cosmétiques)
- **Branching Coherence** : Embranchements + reconvergences sans contradictions
- **Flags & Game Systems** : Conditions, variables, conséquences narratives
- **Tone Consistency** : Voice distinctive par personnage sur centaines de nœuds

**Innovation prompting :**
- Templates anti context-dropping (subtilité lore vs explicite)
- Instructions structurées (V1.5) : Situations → Choix → Conséquences
- Multi-LLM comparison (V2.5) : Génération simultanée, LLM judge, sélection best

**Market gap :** Outils existants visent **conversation dynamique temps réel** (NPC), pas **production asset structuré avec contraintes fortes**.

---

### Validation Approach

**Comment prouver que ça marche ?**

**1. Benchmark Adapté (EQ-Bench style)**

Inspiré de [EQ-Bench Creative Writing](https://eqbench.com/creative_writing.html), mais évaluer **runs** (pas modèles) :

**Metrics DialogueGenerator (4 catégories) :**

1. **Structural Quality (automated) :**
   - **Player agency %** : % choix significatifs vs cosmétiques (target >80%)
   - **Branching ratio** : Embranchements / Reconvergences (sweet spot 1.2-1.5)
   - **Coverage %** : % états jeu accessibles via dialogues (target >95%)
   - **Dead ends %** : % nœuds sans sortie (target 0%)

2. **Narrative Quality (LLM judge) :**
   - **Lore accuracy** : % dialogues sans contradictions GDD (target 100%)
   - **Voice consistency** : Tone score par personnage 0-10 (target >8)
   - **Subtilité** : Context dropping score 0-10, 10 = subtil (target >8)
   - **Agentivité** : Choix impact score 0-10 (target >7)

3. **Slop Detection (automated) :**
   - **GPT-isms frequency** : Liste mots/phrases overused ("delve", "tapestry", "multifaceted")
   - **Repetition score** : Bigrams/trigrams répétés (lower = better)
   - **Generic patterns** : "I understand", "Let me explain", "It's important to note"

4. **Production Efficiency (metrics) :**
   - **Time per dialogue** : Target <4H (MVP), <2H (V2.0 optimisé)
   - **Cost per node** : Target <0.01€
   - **Acceptance rate** : Target >80%

**Implementation :**
- Rubric scoring automatique (tests scripts)
- Feedbacks humains (Marc/Mathieu review = ground truth)
- Dashboard metrics temps réel (V1.5)

---

**2. Benchmark vs Disco Elysium Dialogues (Anonymized)**

**Concept :** Tester qualité DialogueGenerator contre dialogues jeux célèbres (leaked data).

**Methodology :**
1. **Scrape dialogues** : Disco Elysium dialogues (leaked, anonymiser termes reconnaissables)
2. **Anonymisation** : Remplacer noms personnages, lieux, concepts → termes génériques (éviter biais LLM)
3. **Génération parallèle** : Run DialogueGenerator sur mêmes scénarios (ex : "Taverne conversation philosophique")
4. **Comparison metrics** : Player agency, branching complexity, tone consistency, slop score
5. **Target** : Atteindre 80%+ qualité Disco Elysium

**Risk mitigation :**
- **Double-blind test** : Reviewer humain ne sait pas quelle source (DialogueGenerator vs Disco)
- **Anonymisation stricte** : LLM ne doit pas reconnaître jeu source (sinon biais)

---

**3. Production Validation (Real-World)**

**MVP-V1.0 :**
- **10-20 dialogues complets** validés (test préprod)
- Marc/Mathieu usage quotidien (engagement)
- Taux acceptation >80% (quality gate)

**V1.5-V2.0 :**
- **100+ dialogues complets** produits (échelle validée)
- Writer à plein temps opérationnel (scalability proof)
- Production industrielle : 2-3+ dialogues/jour

---

### Risk Mitigation

**Risque Principal :** L'innovation ne scale pas. Qualité se dégrade à l'échelle, ou coûts explosent.

**Fallback Strategy :**

**Plan B : Dialogues en Losange Classiques**
- Réduire complexité branching (moins d'embranchements, plus de reconvergences rapides)
- Structure plus linéaire (moins d'agentivité joueur)
- Réduction scope : Moins de lignes totales

**Plan C : Plus de Retouches Humaines**
- Ratio humain/IA inversé : LLM = draft initial, humain = édition lourde
- Workflow : LLM génère → Marc/Mathieu réécrivent 50%+ des nœuds
- Coût : Temps production x2-3, mais qualité garantie

**Plan D : Moins d'IA**
- Réduction usage LLM aux moments critiques uniquement (NPC importants, révélations narratives)
- Dialogues secondaires : écriture manuelle classique ou templates simples
- Coût : Temps production x5-10, mais risque qualité éliminé

---

**Indicateurs Déclencheurs Fallback :**

1. **Quality Degradation** : Taux acceptation <60% (target >80%)
2. **Cost Explosion** : Coût >0.05€ par nœud (target <0.01€)
3. **Time Inefficiency** : Temps dialogue complet >8H (target <4H)
4. **Slop Detection** : Slop Score >30% (detection GPT-isms récurrent)

**Décision Fallback :** Si 2+ indicateurs déclenchés pendant 2 sprints consécutifs → activer Plan B/C/D.

---

### Market Context & Competitive Landscape

**Landscape Analysis :**

**1. Prototypes Recherche**
- **GENEVA** : Génération narrative graph from constraints (le plus proche conceptuellement)
- **Gap** : Pas packagé outil prod, pas d'export asset éditable

**2. Outils Game Dev AI**
- **Inworld** : Script assist, prototypage rapide, accélération écriture
- **Gap** : Pas production asset complet avec contraintes fortes, tests, export

**3. Chat-Tree Interfaces**
- **tldraw branching chat** : Interface conversation en arbre + intégration AI
- **GitChat** : Gestion conversations LLM en branches (nœuds, contexte)
- **Gap** : Pas pour dialogues ramifiés CRPG (flags, conséquences, game systems)

**4. Outils Narratifs Classiques**
- **Articy Draft** : Pro, intimidant, pas d'AI assist
- **Twine/Ink** : Casual, limité scale, pas d'AI assist
- **Gap** : Aucun outil combine AI assist + scale CRPG + dual-mode UX

---

**Positionnement DialogueGenerator :**

**Niche Unique :** Premier outil production asset narratif ramifié, AI-assisted, CRPG scale, deeply lore-aware, anti-slop quality system.

**Market Opportunity :**
- Indie RPG devs (budget limité, besoin scale narrative)
- AA studios (production dialogues intensive, qualité professionnelle)
- Content producers (comme Marc) qui learned to code, pas devs learning content

**Timing :** LLMs (OpenAI, Anthropic) ont atteint qualité suffisante pour narrative authoring (2023-2024). Prompting techniques émergent. **Timing optimal pour innover.**

---

### Business Value & Market Impact

**Problem Solved :**

**Challenge actuel :**
- Produire 1M+ lignes dialogue qualité Disco Elysium = **impossible manuellement**
- Disco Elysium : 4 ans dev, 1M words (~600K dialogue lines estimate), équipe ~20 personnes
- Cost manual : ~50€/H writer professionnel x 10,000H (estimate 1M lines) = **500K€ minimum**
- Timeline manual : 3-5 ans (trop lent pour Alteir roadmap 2028)

**DialogueGenerator Solution :**
- **Cost réduit -90%** : LLM-assisted → 5€/H équivalent (50€/H → 5€/H grâce automation)
- **Timeline réduit -80%** : 5 ans → 1 an pour 1M lines (2026-2028)
- **Rend faisable** : CRPG Disco Elysium scale pour budgets AA/indie (Alteir devient réalisable)

**Business Impact :**
- **Alteir project unlocked** : Sans DialogueGenerator, scope réduit ou projet avorté
- **Market unlock** : Narrative-rich CRPGs accessibles à plus de créateurs (indie devs, AA studios, content producers)

---

**Market Opportunity (Vision Future) :**

**TAM (Total Addressable Market) :**
- **Indie RPG devs** : Milliers projets (Kickstarter, Discord, itch.io)
- **AA studios** : Dizaines studios (besoin production narrative industrielle)
- **Content producers** : Profile Marc (rare mais croissant avec LLMs)

**Business Model Potentiel (Post-Alteir) :**
- **Open-source core** : DialogueGenerator base (community building)
- **SaaS premium** : Hosting, LLM API management, templates marketplace, analytics dashboard
- **Community** : Narrative designers, writers CRPG, partage patterns anti context-dropping

**Competitive Strategy :**
- **First-mover advantage** : 6-12 mois window (documenter process agressivement)
- **Long-term moat** : Communauté + expertise documentée (process, templates, best practices)
- **Open-source friendly** : Marc = pas contraintes IP, vision open-source

---

## Developer Tool / Web App Specific Requirements

### Project-Type Overview

DialogueGenerator est un **hybride Developer Tool + Web App** :
- **Developer Tool** : Outil de production narrative pour game devs / writers / content producers
- **Web App** : Interface React (SPA) consommant API REST FastAPI

**Target Users :**
- Content producers (Marc profile : content producer who learned to code)
- Writers / Narrative designers (Mathieu : game designer, usage occasionnel)
- Unity developers (Thomas : intégration dialogues in-game)
- Future : AA studios, indie RPG devs, narrative gaming community

---

### Technical Architecture Considerations

**1. Deployment Model : Cloud SaaS Hosted**

**Architecture :**
- **Hosting** : Cloud SaaS (URL publique accessible)
- **Backend** : FastAPI (Python) exposant API REST `/api/v1/*`
- **Frontend** : React + Vite + TypeScript (SPA, consomme API)
- **Data** : Filesystem + Git (MVP-V1.0), DB migration potentielle (V2.0+ si douloureux)
- **LLM Integration** : OpenAI API (MVP), multi-provider (Anthropic fallback V1.0)

**Deployment Process :**
- Build production : `npm run deploy:build`
- Deployment checklist : `docs/DEPLOYMENT.md`
- Environment variables : `ENVIRONMENT=production`, `CORS_ORIGINS`, `OPENAI_API_KEY`
- GDD files : Lien symbolique `data/GDD_categories/` (Notion-Scrapper export)

**Scalability :**
- MVP : Single instance (Marc + Mathieu + viewer)
- V1.5 : Support 3-5 concurrent users (RBAC : Admin/Writer/Viewer)
- V2.0+ : Scale 10+ users (si open-source communauté ou AA studios clients)

---

**2. API Surface : Internal API Only (MVP-V1.0)**

**Current Architecture :**
- **API REST interne** : `/api/v1/*` endpoints pour frontend React
- **Pas d'API publique externe** pour MVP/V1.0
- **Export manuel** : Download JSON Unity via UI

**Future API Publique (V2.0+ Potentielle) :**

**Use cases externes :**
- **Unity Plugin** : Import direct dialogues depuis DialogueGenerator (skip manual download)
- **CLI Tools** : Génération batch, export scripts, automation workflows
- **Notion Integration** : Sync bidirectionnel GDD (webhook Notion → auto-update DialogueGenerator)

**Decision Point :** API publique = V2.0+ si demande communauté ou clients AA studios.

---

**3. Documentation Strategy : Internal Team → External Community**

**MVP-V1.0 : Internal Team Documentation**

**Target audience :** Marc, Mathieu, writer futur, Thomas (Unity dev)

**Docs existantes :**
- `README.md` : Overview projet, quick start
- `docs/index.md` : Index documentation (architecture, API, data models)
- `docs/Spécification technique.md` : Specs détaillées (modules, workflow, storage)
- `docs/DEPLOYMENT.md` : Guide déploiement (prerequisites, checklist, troubleshooting)
- `docs/project-overview.md` : High-level overview

**Docs à ajouter (V1.0) :**
- **User Guide** : Workflow complet (sélection contexte → génération → export Unity)
- **Template Guide** : Comment créer/optimiser templates anti context-dropping
- **Troubleshooting** : FAQ, common errors, debug tips

**V1.5-V2.0 : External Community Documentation (si open-source)**

**Docs additionnelles :**
- **Installation Guide** : Self-hosted deployment (Docker, config, GDD setup)
- **API Reference** : Si API publique (endpoints, auth, examples)
- **Tutorial Videos** : Onboarding wizard, graph editor, generation workflow
- **Best Practices** : Prompting art, règles pertinence contexte, anti-slop strategies
- **Contributing Guide** : Si open-source (code style, PR process, community guidelines)

---

**4. Web App Architecture : SPA (Single Page Application)**

**Stack technique :**
- **Frontend** : React 18+ + TypeScript + Vite
- **Routing** : React Router (côté client, navigation fluide)
- **State Management** : React Context + hooks (ou Zustand si complexité croît)
- **UI Components** : Custom components + graph editor (React Flow based)
- **HTTP Client** : Fetch API ou Axios (appels API REST)

**Build & Performance :**
- **Dev mode** : `npm run dev` (Vite HMR, fast refresh)
- **Production** : `npm run deploy:build` (minification, tree-shaking, code splitting)
- **Bundle size target** : <500KB initial (gzip), lazy-load graph editor si >200KB

**Interface Structure :**
- **Layout** : 3 colonnes verticales (Contexte / Génération / Détails)
- **Colonne Contexte** : Sélection ressources GDD (personnages, lieux, objets, etc.) via onglets
- **Colonne Centrale** : Configuration scène (PJ/PNJ, région, instructions, templates)
- **Colonne Détails** : Affichage prompt (token usage, sections dépliables), résultat génération, export Unity
- **Référence complète** : `docs/features/current-ui-structure.md`

---

**5. Browser Support : Modern Browsers Only**

**Supported Browsers :**
- **Chrome** : Latest 2 versions (primary target)
- **Firefox** : Latest 2 versions
- **Edge** : Latest 2 versions (Chromium-based)
- **Safari** : Latest 2 versions (Mac users)

**NOT Supported :**
- IE11 (obsolète, pas de support)
- Legacy browsers (<2 ans)

**Browser Feature Requirements :**
- **ES2020** : Modules, async/await, optional chaining
- **Web APIs** : LocalStorage (auto-save), WebSockets (V2.0+ real-time)
- **Canvas / SVG** : Graph editor rendering (React Flow utilise SVG)

---

**6. Performance Targets**

**Graph Editor :**
- Rendering graphe 500+ nœuds : **<1s**
- UI interactions : **<100ms** (clicks, drag&drop)
- Large dialogues : Support 100+ nœuds par dialogue

**Initial Load Time :**
- **First Contentful Paint (FCP)** : <1.5s
- **Time to Interactive (TTI)** : <3s
- **Largest Contentful Paint (LCP)** : <2.5s

**API Response Times :**
- GET endpoints (list dialogues, GDD) : **<200ms**
- POST generation (1 nœud) : **<30s** (LLM latency dominant)
- Export Unity JSON : **<500ms**

---

**7. SEO & Accessibility**

**SEO : Not Required**
- DialogueGenerator = **outil SaaS privé** (accès authentifié)
- Si open-source : Site documentation séparé (Docusaurus) = SEO-friendly

**Accessibility : Basique MVP → Enhanced V2.0**

**MVP-V1.0 :**
- **Keyboard navigation** : Critique pour graph editor (Tab, Arrow keys, Enter/Space, Escape)
- **Color contrast** : WCAG AA minimum (4.5:1 texte, 3:1 UI)
- **Focus indicators** : Visible focus states

**V2.0+ (si open-source) :**
- **Screen readers** : ARIA labels, roles, live regions
- **Keyboard shortcuts** : Custom shortcuts (Ctrl+G = generate, Ctrl+S = save)
- **High contrast mode** : Theme alternative
- **Reduced motion** : `prefers-reduced-motion` support

---

**8. Real-Time Features : Phased Approach**

**MVP : No Real-Time**
- Save manuel (button "Save")
- Git commits (Marc manual workflow)
- Single-user édition

**V1.0 : Auto-Save Local**
- Auto-save toutes les 2min (LocalStorage + backend sync)
- Session recovery automatique

**V2.0+ : Real-Time Collaboration (Vision)**
- WebSockets (backend → frontend push notifications)
- Multi-user édition simultanée (Operational Transform ou CRDT)
- Conflict resolution (merge assisté)

---

### Implementation Considerations

**1. Security Model**

**Authentication & Authorization :**
- **MVP** : Basic auth (username/password, session tokens)
- **V1.5** : RBAC (Admin/Writer/Viewer roles)
- **V2.0** : OAuth2 / SSO (si clients AA studios)

**Data Security :**
- **Secrets** : Environment variables (jamais hardcodés)
- **API Keys** : LLM API keys stockées backend (jamais exposées frontend)
- **CORS** : Configured `CORS_ORIGINS` (éviter wildcard production)

---

**2. Error Handling & Resilience**

**LLM API Failures :**
- Retry logic (3 tentatives, exponential backoff)
- Fallback multi-provider (OpenAI → Anthropic si 503)
- User feedback (error messages clairs)

**Network Errors :**
- Offline detection (display banner "reconnecting...")
- Request queuing (auto-retry quand connexion restaurée)
- Data loss prevention (auto-save + LocalStorage backup)

---

**3. Testing Strategy**

**Backend (Python) :**
- `pytest tests/` (tous tests)
- Tests API : `pytest tests/api/` (TestClient FastAPI, mocks LLM/GDD)
- Coverage target : >80% code critique

**Frontend (React) :**
- `.\scripts\test-frontend.ps1` (build + lint + tests unitaires)
- Vitest (tests unitaires components)
- Playwright (E2E tests workflows complets)

**Integration :**
- E2E workflow : Sélection contexte → Génération → Export Unity
- Validation JSON Unity schema (100% conformité)

---

## Project Scoping & Phased Development

### MVP Strategy & Philosophy

**MVP Approach : Problem-Solving MVP**

DialogueGenerator MVP vise à **débloquer la production immédiate** de dialogues CRPG qualité Disco Elysium avec assistance LLM.

**Problem Solved :**
- **Manual production impossible** : 1M+ lignes à la main = 3-5 ans, 500K€+
- **Quality at scale challenge** : Maintenir qualité narrative sur volume massif
- **Blocker actuel** : Éditeur graphe non fonctionnel, workflow incomplet

**MVP Philosophy :**
- **Minimum that works** : 4 features critiques (éditeur graphe fonctionnel, génération continue + auto-link, validation structurelle, export Unity fiable)
- **User value immediate** : Marc/Mathieu génèrent 1 nœud qualité en <1min dès MVP
- **Foundation for scale** : Architecture supportant évolution vers 1M+ lignes sans refactoring majeur

**Validation Learning :**
- **Success metric MVP** : Marc/Mathieu produisent 10-20 dialogues complets validés (test préprod) en 3 mois
- **Key question** : Est-ce que le workflow LLM-assisted + graph editor permet de maintenir qualité Disco Elysium à l'échelle ?
- **Pivot triggers** : Si taux acceptation <60% ou coût >0.05€/nœud → fallback Plans B/C/D (dialogues losange, plus de retouches humaines, moins d'IA)

---

**Resource Requirements**

**MVP (Sprint 1-2, ~1 semaine) :**
- **Team** : Marc solo (dev + content producer)
- **Skills** : Full-stack (Python/FastAPI + React/TypeScript), LLM integration (OpenAI API), graph editor (React Flow)
- **Infrastructure** : Cloud hosting (backend + frontend), OpenAI API access, Git repo

**V1.0-V1.5 (Sprint 3-8, ~4-6 semaines) :**
- **Team** : Marc (dev) + Mathieu (testeur/feedback) + éventuellement IA dev assistant
- **Skills additionnelles** : Database/search (V1.0), RBAC/auth (V1.5), cost governance (V1.5)

**V2.0+ (Sprint 9+, ~10+ semaines) :**
- **Team expansion potentielle** : Writer à plein temps (production narrative), Unity dev (intégration), communauté (si open-source)
- **Skills additionnelles** : RAG/embeddings (Context Intelligence V2.0), template optimization (V2.5), multi-LLM orchestration (V2.5)

---

### MVP Feature Set (Phase 1)

**Core User Journeys Supported :**

**MVP supporte uniquement Journey Marc (power user) :**
- Marc génère 1 nœud de qualité en <1min
- Marc génère batch 3-8 nœuds en <2min
- Marc édite/connecte nœuds dans graphe fonctionnel
- Marc exporte dialogue vers Unity JSON (100% conformité schema)

**Journeys Mathieu, Sophie, Thomas = Post-MVP** (V1.0-V1.5)

---

**Must-Have Capabilities (MVP) :**

1. ✅ **Éditeur graphe fonctionnel** 
   - Fix display bug (rendering cassé actuellement)
   - Connexions nœuds (drag & drop, auto-link)
   - Édition basique (add/delete/modify nodes)
   - Performance : 100+ nœuds rendering <1s

2. ✅ **Génération continue + auto-link**
   - Générer depuis choix joueur existant
   - Batch generation (3-8 nœuds en <2min)
   - Auto-connexion graphe (link nouveaux nœuds automatiquement)
   - Context GDD intégré (sélection manuelle sections pertinentes)

3. ✅ **Validation structurelle**
   - DisplayName/stableID validation (champs requis Unity)
   - Nœuds vides detection (erreur si text manquant)
   - Orphans detection (nœuds non connectés au graphe)
   - Cycles detection (boucles infinies)

4. ✅ **Export Unity fiable**
   - Batch export (tous dialogues ou sélection)
   - Validation JSON schema Unity custom (100% conformité)
   - Format JSON optimisé (lisible + compact)
   - Download file (browser save dialog)

---

### Post-MVP Features

**Phase 2 : V1.0 - Editor Pro Foundation (Sprint 3-5, ~2-3 semaines)**

**Goal :** Atteindre moment "Aha!" Top (batch 3-8 nœuds 80%+ acceptés). Éditeur professionnel scalable.

**Should-Have (Pattern "Editor Pro") :**
5. 🟡 **Navigation Editor** : Jump-to-node, search texte/acteur, focus auto
6. 🟡 **Dialogue Database layer** : Index/search, renommage/refactor, refs cassées
7. 🟡 **Variable Inspector** : Variables/flags, scénarios presets, simulation basique
8. 🟡 **Simulation Coverage** : Run dialogue, dead ends/unreachable, rapport

**Success Criteria V1.0 :**
- Navigation fluide dialogues 500+ nœuds
- Refactoring (renommer acteur) propage automatiquement
- Simulation détecte >95% bugs structurels
- Production dialogue complet <4H

**User Journey Unlocked :** Mathieu (casual writer) peut utiliser l'outil avec wizard onboarding

---

**Phase 3 : V1.5 - Cost & Collaboration (Sprint 6-8, ~2-3 semaines)**

**Goal :** Gouvernance coûts + collaboration équipe (Marc + Mathieu + writer futur).

**Should-Have (Pattern "Cost Governance" + RBAC) :**
9. 🟡 **Cost Governance** : Estimation coût, transparence prompt, logs/audit
10. 🟡 **RBAC + Shared Dialogues** : Admin/writer/viewer, dialogues partagés
11. 🟡 **Template System v1** : Templates instructions/auteur, personnalisation, validation

**Success Criteria V1.5 :**
- Coûts LLM <0.01€ par nœud (optimisé)
- Marc + Mathieu collaborent sans friction
- Templates améliorent qualité +20% (LLM judge)

**User Journeys Unlocked :** Sophie (viewer, reporting) + Thomas (Unity dev, validation JSON stricte)

---

**Phase 4 : V2.0 - Context Intelligence (Sprint 9-12, ~4 semaines)**

**Goal :** Atteindre moment "Aha!" Vision (dialogue complet en <2H optimisé). Optimisation contextuelle.

**Could-Have (Pattern "Context Intelligence") :**
12. 🟢 **Intelligent Context Selection** : Extraction sous-parties pertinentes (règles explicites, outillées, évolutives, mesurables)
13. 🟢 **Hybrid Context Intelligence** : RAG + embeddings + règles métier
14. 🟢 **Contextual Link Exploitation** : Auto-suggest via liens JSON GDD
15. 🟢 **Dialogue History Recommender** : Re-utilisation contextes similaires

**Success Criteria V2.0 :**
- Réduction tokens -50% (5000 → 2500 tokens/prompt)
- Pertinence contexte >90% (validation humaine)
- Workflow accéléré : 4H → 2H par dialogue complet

---

**Phase 5 : V2.5 - Quality & Validation Pro (Sprint 13-15, ~3 semaines)**

**Goal :** Industrialisation qualité narrative (writer à plein temps opérationnel, 2-3+ dialogues/jour).

**Could-Have (Pattern "Quality & Validation") :**
16. 🟢 **Template Marketplace complet** : Bibliothèque admin, A/B testing, scoring
17. 🟢 **Template Quality Validation** : Tests auto, LLM judge, feedback loop
18. 🟢 **Multi-LLM Comparison** : Génération simultanée, LLM judge, sélection best

**Success Criteria V2.5 :**
- Taux acceptation qualité >90%
- Feedback loop améliore templates automatiquement
- Multi-LLM réduit coûts -30%

---

**Phase 6 : V3.0 - Advanced Features (Sprint 16+, ~6+ semaines)**

**Goal :** Features avancées pour scale ultime (support 1M+ lignes, game systems intégrés).

**Nice-to-Have :**
19. ⚪ **Multi-LLM Provider Architecture** : Support Anthropic/local LLM (Ollama)
20. ⚪ **Game System Integration** : Conditions stats, effets relations, hooks Unity
21. ⚪ **Conditions/Variables DSL** : Langage writer-friendly, validation, preview
22. ⚪ **Sequencer-lite RPG** : Delta influence, unlock traits, hooks Unity
23. ⚪ **Twine-like Passage Linking** : Draft rapide texte, compilation JSON
24. ⚪ **Git-like Narrative Versioning** : Branches narratives, merge assisté LLM

**Success Criteria V3.0 :**
- Support 3+ LLM providers
- Game systems intégrés (conditions/variables/effets)
- Workflow hybride texte/graphe opérationnel

---

**Phase 7 : Growth Features (Post-MVP, déploiement progressif)**

**Déploiement conditionnel selon feedback production réelle :**
- **DB migration** : Si filesystem devient douloureux (1000+ dialogues, search lente)
- **Advanced search** : Si volume nécessite (metadata search, filters avancés)
- **Dashboard analytics** : Si métriques critiques (coûts LLM, qualité trends)
- **Localization prep** : Si sortie internationale confirmée (Alteir multi-langue)

**Decision Point :** Features ajoutées uniquement si douleur identifiée en production.

---

**Phase 8 : Vision (Future, Post-2028)**

**Long Terme :**
- **Voice-Over metadata integration** : Prep enregistrements audio (acteurs, timing)
- **Real-time collaboration** : WebSockets, multi-user édition simultanée
- **Multi-game support** : Réutilisabilité GDD, templates cross-projects
- **Community marketplace** : Templates partagés, patterns anti-slop, open-source
- **Open-source release** : Si pertinent (vision Marc = open-source friendly)

---

### Risk Mitigation Strategy

**Technical Risks**

**Risk 1 : LLM Quality Degradation at Scale**
- **Problem** : Qualité dialogue se dégrade quand volume augmente (context dropping, AI slop, repetition)
- **Mitigation MVP** : Two-phase quality system
  - Phase 1 : Travail manuel premières centaines lignes (établir style par personnage)
  - Phase 2 : LLM continue dans style établi (context enrichi)
- **Mitigation V1.5-V2.0** : Validation multi-layer (structure, schema, lore, quality LLM judge)
- **Fallback** : Plans B/C/D (dialogues losange, plus humain, moins IA)

**Risk 2 : Architecture ne Scale Pas**
- **Problem** : Filesystem + Git ne supporte pas 1000+ dialogues (search lente, performance dégradée)
- **Mitigation MVP** : Architecture designed for scale (filesystem OK jusqu'à 1000+ dialogues)
- **Mitigation V1.0** : Search & Index Layer (navigation fluide)
- **Fallback V2.0** : DB migration si douloureux (décision data-driven, pas YAGNI premature)

**Risk 3 : Context Intelligence Échec**
- **Problem** : Règles pertinence contexte ne capturent pas la logique narrative (context trop large ou trop étroit)
- **Mitigation V2.0** : Règles explicites, outillées, évolutives, mesurables (feedback loop amélioration)
- **Fallback** : Manual context selection (Marc expertise, pas automation)

---

**Market Risks**

**Risk 1 : LLM-Assisted Narrative Pas Viable Qualitativement**
- **Problem** : LLM produit qualité insuffisante (AI slop, genericité, perte authorial control)
- **Validation MVP** : 10-20 dialogues complets validés en 3 mois (taux acceptation >80%)
- **Mitigation** : Anti-slop quality system (two-phase + validation multi-layer)
- **Fallback** : Réduction ratio IA (50% LLM draft → 50% human rewrite)

**Risk 2 : Marché Trop Niche**
- **Problem** : Seul Marc utilise l'outil (pas de demande externe, pas de communauté)
- **Validation V1.0** : Mathieu usage autonome (>95% sessions sans support Marc)
- **Validation V2.0** : Writer à plein temps opérationnel (production 2-3+ dialogues/jour)
- **Pivot** : Si marché niche confirmé, focus outil interne Alteir uniquement (pas open-source)

**Risk 3 : Concurrents Copient Rapidement**
- **Problem** : Inworld ou studios AA copient tech DialogueGenerator en 6-12 mois (first-mover window court)
- **Mitigation** : Documenter process agressivement, build communauté si open-source (moat = expertise + communauté, pas tech)
- **Acceptance** : Tech copiable OK si Marc veut open-source (vision = partage, pas monopole)

---

**Resource Risks**

**Risk 1 : Marc Seul, Bandwidth Limité**
- **Problem** : Marc = dev + content producer + PM, bandwidth limité pour dev tool + production Alteir
- **Mitigation MVP** : MVP lean (1 semaine, 4 features critiques)
- **Mitigation V1.0** : Mathieu testeur actif (feedback, bug reports)
- **Fallback** : Réduction scope (focus MVP + V1.0, skip V2.0+ si bandwidth insuffisant)

**Risk 2 : Budget LLM Coûts Explosent**
- **Problem** : Production 1M lignes = coûts LLM élevés (si >0.01€/nœud → 10K€+)
- **Mitigation MVP** : Monitoring coûts dès MVP (logs, estimation avant génération)
- **Mitigation V1.5** : Cost Governance (transparence, audit, rate limits)
- **Fallback** : Multi-LLM (V2.5, providers moins chers), local LLM (V3.0, Ollama)

**Risk 3 : Writer Futur Pas Autonome**
- **Problem** : Writer nécessite support Marc constant (pas scalable)
- **Mitigation V1.0** : Wizard onboarding (guided mode, templates pré-remplis)
- **Mitigation V1.5** : Templates + documentation (best practices, troubleshooting)
- **Validation** : Taux autonomie >95% (sessions sans support Marc)

---

**Timeline & Resource Summary**

**Total Estimated Timeline : ~20-25 semaines (~5-6 mois)**
- MVP : 1 semaine
- V1.0 : 2-3 semaines
- V1.5 : 2-3 semaines
- V2.0 : 4 semaines
- V2.5 : 3 semaines
- V3.0 : 6+ semaines
- Growth/Vision : Ongoing (post-V3.0)

**Critical Path to Business Goal (1M lines by 2028) :**
- **Q1 2026** (maintenant) : MVP + V1.0 (préprod ready)
- **Q2 2026** : V1.5 (collaboration équipe, cost governance)
- **Q3-Q4 2026** : Production ramp-up (1-2 dialogues/jour)
- **2027** : Production intensive (2-3+ dialogues/jour, writer full-time)
- **2028 Q1** : 1M+ lignes complétées (Alteir narrative content complete)

**Scope is Ambitious But Achievable Given :**
- Marc = experienced content producer + developer (rare profile)
- LLM tech mature (OpenAI API quality sufficient for narrative authoring)
- Architecture scalable (filesystem → DB migration si nécessaire)
- Fallback plans clear (Plans B/C/D si innovation échec)

---

## Journey Insights - Architecture Révélée

### Deux Modes d'Usage Distincts

Les journeys révèlent **deux personas avec besoins opposés** :

**Power Mode (Marc) :**
- Free-form : tous les champs visibles, customization totale
- Advanced features : multi-provider LLM, prompt override, cost estimation, debug console
- Manual control : auto-save OFF (manual Git commits), validation on-demand
- Tolérance friction : acceptable si contrôle total garanti

**Guided Mode (Mathieu + futur writer) :**
- Wizard : step-by-step guided flow (lieu → personnage → contexte → generate)
- Templates : instructions pré-remplies, optimisation anti context-dropping
- Automation maximale : auto-save ON, auto-link ON, validation auto ON
- Friction minimale : zéro barrière technique, autonomie complète

**Implementation Strategy :**
- **MVP** : Build pour Marc (power mode uniquement)
- **V1.0** : Add guided mode (wizard + templates + auto-save)
- **V1.5** : Mode detection automatique (skill level user → adapt UI)
- **V2.0** : Mode switch disponible (gear icon → "Advanced Mode" toggle)

### Cinq Systèmes Architecturaux Identifiés

Les journeys révèlent **5 systèmes critiques** :

**1. LLM Orchestration Layer**
- **MVP** : OpenAI uniquement, retry logic basique
- **V1.0** : Multi-provider (Anthropic fallback), error recovery gracieux
- **V2.0** : Local LLM support (Ollama), cost optimization intelligent

**2. State Management Layer**
- **MVP** : Manual save, Git commits
- **V1.0** : Auto-save toutes les 2min, session recovery automatique
- **V1.5** : Real-time sync (si collaboration), conflict resolution

**3. Validation & Quality Layer**
- **MVP** : Structure validation (nœuds vides, orphans, cycles)
- **V1.0** : JSON Unity validation stricte (100% conformité schema custom Unity)
- **V1.5** : Quality validation (lore checker, LLM judge score 8/10)
- **V2.0** : Template optimization (feedback loop anti context-dropping)

**4. Permission & Auth Layer**
- **MVP** : Single user (Marc)
- **V1.5** : RBAC 3 roles (Admin/Writer/Viewer)
- **V2.0** : Team permissions (shared dialogues, audit logs)

**5. Search & Index Layer**
- **MVP** : Basic search (filter côté client)
- **V1.0** : Full search & index (metadata, fast search, advanced filters)
- **V2.0** : Context Intelligence (embeddings RAG, auto-suggest contexte pertinent)

### Nouvelles Success Metrics

Les journeys révèlent **3 métriques manquantes** dans le PRD actuel :

**Autonomie (Journey Mathieu) :**
- **Metric** : % sessions Mathieu/Writer sans support Marc
- **Target** : >95%
- **Measurement** : Track support tickets, questions posées

**Onboarding (Journey Mathieu) :**
- **Metric** : Temps "nouveau user → 1er dialogue complet exporté"
- **Target** : <2H (idéal : <1H avec wizard)
- **Measurement** : Simulate new user journey, timer workflow

**Integration (Journey Thomas) :**
- **Metric** : % exports Unity sans erreurs schema
- **Target** : 100%
- **Measurement** : Validate all exports against schema custom Unity (automated tests)

### Test Strategy Révélée

**3 types de tests critiques** :

**1. Quality Tests (Journey Marc - context dropping) :**
- Test : "Context dropping detector" (detect lore explicite vs subtil)
- Test : "Lore accuracy checker" (detect contradictions GDD)
- Test : "Voice consistency checker" (tone personnage cohérent)
- **Implementation** : Unit tests (règles simples) + LLM judge (évaluation qualitative) + Human validation (ground truth)

**2. Resilience Tests (Journey Marc - edge cases) :**
- Test : LLM API down → fallback Anthropic (simulate OpenAI 503 → verify Anthropic called)
- Test : Session recovery → simulate crash → verify state restored
- Test : Conflict resolution → simulate concurrent edits → verify merge ou error
- **Implementation** : Integration tests (mock external services) + E2E tests (simulate failures)

**3. UX Tests (Journey Mathieu - autonomy) :**
- Test : Onboarding wizard → new user flow → verify 1st dialogue generated <2H
- Test : Autonomy → Mathieu generates dialogue without Marc help → 0 support tickets
- Test : Efficiency → time from "New dialogue" to "Export Unity" <1H
- **Implementation** : Playwright E2E tests (simulate user workflows) + Metrics tracking (analytics)

---

# Functional Requirements - Enhanced Version (Post Party Mode)

**Date:** 2026-01-13  
**Status:** Party Mode improvements validated by Marc  
**Total FRs:** 113 (up from 102)

---

## 💡 Changes Summary

**New FRs Added (11):**
- Context budget management (FR20-21)
- Bulk selection & contextual actions (FR31-33)
- Lore validation split (FR38-39)
- Context dropping detection (FR42-43)
- Anti-context-dropping templates (FR57)
- Fallback LLM provider (FR77)
- Batch operations (FR85-86)
- Basic dialogue history MVP (FR98)
- Guided vs Power mode explicit (FR105-106)
- UX patterns (FR107-109: preview, comparison, keyboard shortcuts)

**Cleanup:**
- Performance targets (FR21, FR94-97 original) → Moved to Non-Functional Requirements
- Clarified dependencies (FR13 ↔ FR14)
- Split ambiguous FRs (FR35 → FR38-39)
- Added tolerance to LLM judge (FR40: ±1 margin)

**Implementation Status:**
- ✅ Implemented: ~40-45 FRs (35-40%)
- ⚠️ Partial: ~30-35 FRs (25-30%)
- ❌ New: ~40-45 FRs (35-40%)

---

## Functional Requirements

### 1. Dialogue Authoring & Generation

**FR1:** Users can generate a single dialogue node with LLM assistance based on selected GDD context  
**FR2:** Users can generate batch of multiple nodes (3-8) from existing player choices  
**FR3:** Users can specify generation instructions (tone, style, theme) for dialogue nodes  
**FR4:** Users can accept or reject generated nodes inline in the graph editor  
**FR5:** Users can manually edit generated node content (text, speaker, metadata)  
**FR6:** Users can create new dialogue nodes manually (without LLM generation)  
**FR7:** Users can duplicate existing nodes to create variations  
**FR8:** Users can delete nodes from dialogues  
**FR9:** System can auto-link generated nodes to existing graph structure  
**FR10:** Users can regenerate rejected nodes with adjusted instructions  

---

### 2. Context Management & GDD Integration

**FR11:** Users can browse available GDD entities (characters, locations, regions, themes)  
**FR12:** Users can manually select GDD context relevant for dialogue generation  
**FR13:** System can automatically suggest relevant GDD context based on configured relevance rules *(Depends on FR14-15)*  
**FR14:** Users can define explicit context selection rules (lieu → region → characters → theme)  
**FR15:** Users can configure context selection rules per dialogue type  
**FR16:** System can measure context relevance (% GDD used in generated dialogue)  
**FR17:** Users can view which GDD sections were used in node generation  
**FR18:** System can sync GDD data from Notion (V2.0+)  
**FR19:** Users can update GDD data without regenerating existing dialogues  
**FR20:** Users can configure token budget for context selection *(NEW - Context budget management)*  
**FR21:** System can optimize context to fit within token budget while maintaining relevance *(NEW)*

---

### 3. Graph Editor & Visualization

**FR22:** Users can view dialogue structure as a visual graph (nodes and connections)  
**FR23:** Users can navigate large graphs (500+ nodes) *(Note: Performance target in NFRs)*  
**FR24:** Users can zoom, pan, and focus on specific graph areas  
**FR25:** Users can drag-and-drop nodes to reorganize graph layout  
**FR26:** Users can create connections between nodes manually  
**FR27:** Users can delete connections between nodes  
**FR28:** Users can search for nodes by text content or speaker name  
**FR29:** Users can jump to specific node by ID or name  
**FR30:** Users can filter graph view (show/hide node types, speakers)  
**FR31:** Users can select multiple nodes in graph (shift-click, lasso selection) *(NEW - Bulk selection)*  
**FR32:** Users can apply operations to multiple selected nodes (delete, tag, validate) *(NEW)*  
**FR33:** Users can access contextual actions on nodes (right-click menu) *(NEW)*  
**FR34:** System can auto-layout graph for readability  
**FR35:** Users can undo/redo graph edit operations  

---

### 4. Quality Assurance & Validation

**FR36:** System can validate node structure (required fields: DisplayName, stableID, text)  
**FR37:** System can detect empty nodes (missing text content)  
**FR38:** System can detect explicit lore contradictions (conflicting GDD facts) *(SPLIT from FR35 - Explicit contradictions)*  
**FR39:** System can flag potential lore inconsistencies for human review *(SPLIT from FR35 - Potential issues)*  
**FR40:** System can detect orphan nodes (nodes not connected to graph)  
**FR41:** System can detect cycles in dialogue flow  
**FR42:** System can assess dialogue quality with LLM judge (score 0-10, ±1 margin for variance) *(CLARIFIED - Added variance tolerance)*  
**FR43:** System can detect "AI slop" patterns (GPT-isms, repetition, generic phrases)  
**FR44:** System can detect context dropping in generated dialogue (lore explicite vs subtil) *(NEW - Context dropping detection)*  
**FR45:** Users can configure anti-context-dropping validation rules *(NEW)*  
**FR46:** Users can simulate dialogue flow to detect dead ends  
**FR47:** Users can view simulation coverage report (% reachable nodes, unreachable nodes)  
**FR48:** System can validate JSON Unity schema conformity (100%)  

---

### 5. Export & Integration

**FR49:** Users can export single dialogue to Unity JSON format  
**FR50:** Users can batch export multiple dialogues to Unity JSON  
**FR51:** System can validate exported JSON against Unity custom schema  
**FR52:** Users can download exported JSON files  
**FR53:** Users can preview export before download (JSON structure, size)  
**FR54:** System can generate export logs with metadata (generation date, cost, validation status)  

---

### 6. Template & Knowledge Management

**FR55:** Users can create custom instruction templates for dialogue generation  
**FR56:** Users can save, edit, and delete templates  
**FR57:** Users can apply templates to dialogue generation  
**FR58:** System can provide pre-built templates (salutations, confrontation, révélation, etc.)  
**FR59:** Users can configure anti-context-dropping templates (subtilité lore vs explicite) *(NEW)*  
**FR60:** Users can browse template marketplace (V1.5+)  
**FR61:** System can A/B test templates and score quality (V2.5+)  
**FR62:** Users can share templates with team members  
**FR63:** System can suggest templates based on dialogue scenario  

---

### 7. Collaboration & Access Control

**FR64:** Users can create accounts with username/password authentication  
**FR65:** Users can log in and log out of the system  
**FR66:** Administrators can assign roles to users (Admin, Writer, Viewer)  
**FR67:** Writers can create, edit, and delete dialogues  
**FR68:** Viewers can read dialogues but cannot edit  
**FR69:** Users can share dialogues with specific team members  
**FR70:** Users can view who has access to each dialogue  
**FR71:** System can track user actions for audit logs (V1.5+)  

---

### 8. Cost & Resource Management

**FR72:** System can estimate LLM cost before generating nodes  
**FR73:** Users can view cost breakdown per dialogue (total cost, cost per node)  
**FR74:** Users can view cumulative LLM costs (daily, monthly)  
**FR75:** System can enforce cost limits per user or team (V1.5+)  
**FR76:** Administrators can configure cost budgets and alerts  
**FR77:** System can display prompt transparency (show exact prompt sent to LLM)  
**FR78:** Users can view generation logs (prompts, responses, costs)  
**FR79:** System can fallback to alternate LLM provider on primary failure (OpenAI → Anthropic) *(NEW - Fallback provider)*  

---

### 9. Dialogue Database & Search

**FR80:** Users can list all dialogues in the system  
**FR81:** Users can search dialogues by name, character, location, or theme  
**FR82:** Users can filter dialogues by metadata (creation date, author, status)  
**FR83:** Users can sort dialogues (alphabetically, by date, by size)  
**FR84:** Users can create dialogue collections or folders for organization  
**FR85:** System can index dialogues for fast search (1000+ dialogues)  
**FR86:** Users can view dialogue metadata (node count, cost, last edited)  
**FR87:** Users can batch validate multiple dialogues *(NEW - Batch validation)*  
**FR88:** Users can batch generate nodes from multiple starting nodes *(NEW - Batch generation)*  

---

### 10. Variables & Game System Integration

**FR89:** Users can define variables and flags in dialogues (V1.0+)  
**FR90:** Users can set conditions on node visibility (if variable X = Y, show node)  
**FR91:** Users can define effects triggered by player choices (set variable, unlock flag)  
**FR92:** Users can preview scenarios with different variable states  
**FR93:** System can validate variable references (detect undefined variables)  
**FR94:** Users can integrate game system stats (character attributes, reputation) (V3.0+)  

---

### 11. Session & State Management

**FR95:** System can auto-save user work every 2 minutes (V1.0+)  
**FR96:** System can restore session after browser crash  
**FR97:** Users can manually save dialogue progress  
**FR98:** Users can commit dialogue changes to Git repository (manual workflow external)  
**FR99:** System can detect unsaved changes and warn before navigation  
**FR100:** Users can view previous versions of dialogue (basic history MVP) *(NEW - Basic history)*  
**FR101:** Users can view edit history for dialogue (detailed V2.0+)  

---

### 12. Onboarding & Guidance

**FR102:** New users can access wizard onboarding for first dialogue creation (V1.0+)  
**FR103:** Users can access in-app documentation and tutorials  
**FR104:** System can provide contextual help based on user actions  
**FR105:** Users can access sample dialogues for learning  
**FR106:** System can detect user skill level and adapt UI (power vs guided mode) (V1.5+)  
**FR107:** Power users can toggle advanced mode for full control *(NEW - Power mode explicit)*  
**FR108:** New users can activate guided mode with step-by-step wizard *(NEW - Guided mode explicit)*  

---

### 13. User Experience & Workflow

**FR109:** Users can preview estimated node structure before LLM generation (dry-run mode) *(NEW - Preview before generation)*  
**FR110:** Users can compare two dialogue nodes side-by-side *(NEW - Comparison)*  
**FR111:** Users can access keyboard shortcuts for common actions (Ctrl+G generate, Ctrl+S save, Ctrl+Z undo, etc.) *(NEW - Keyboard shortcuts)*  

---

### 14. Performance Monitoring

**Note:** Performance targets (generation time, rendering speed, API latency) moved to Non-Functional Requirements.

**FR112:** Users can monitor system performance metrics (generation time, API latency)  
**FR113:** Users can view performance trends over time (dashboard analytics)  

---

### 15. Accessibility & Usability

**FR114:** Users can navigate the graph editor with keyboard (Tab, Arrow keys, Enter, Escape, and shortcuts)  
**FR115:** System can provide visible focus indicators for keyboard navigation  
**FR116:** Users can customize color contrast (WCAG AA minimum)  
**FR117:** System can support screen readers with ARIA labels (V2.0+)  

---

## Implementation Status Details

### ✅ Fully Implemented (~35-40%)

- FR1, FR3, FR5-8: Dialogue authoring (UnityDialogueGenerationService)
- FR11-12, FR17: Context management (ContextSelector, ContextDetail)
- FR22, FR24-27: Graph editor basic (GraphEditor.tsx, React Flow)
- FR36-37, FR40-41, FR48: Validation structure (GraphValidationService)
- FR49-54: Export Unity (unity_dialogues router, UnityDialogueViewer)
- FR64-65: Auth basic (auth router, LoginForm)
- FR72-78: Cost tracking (LLMUsageService, UsageDashboard)
- FR80-84, FR86: Database & search basic (unity_dialogues list/filter)
- FR89, FR92-93: Variables basic (InGameFlagsModal, catalogs)
- FR97, FR99: Session management (save, unsaved warning)
- FR103, FR105: Documentation & samples (docs/, GDD samples)

### ⚠️ Partially Implemented (~25-30%)

- FR2, FR4, FR9-10: Batch generation (service exists, UI integration partial)
- FR13-15: Auto-suggest context (V2.0, needs rules system)
- FR18-19: Notion sync (service exists, workflow partial)
- FR20-21: Context budget (NEW, not implemented)
- FR28-30: Graph nav advanced (search exists, jump/filter partial)
- FR31-35: Bulk ops & UX (NEW, not implemented)
- FR42-45: Quality LLM judge (NarrativeValidator partial, V1.5)
- FR55-59: Templates (PromptsTab exists, full system V1.5)
- FR66-71: RBAC (auth exists, roles not implemented V1.5)
- FR85: Search advanced (basic exists, index V1.0)
- FR90-91: Conditions/effects advanced (partial, V1.0+)
- FR95-96, FR100-101: Auto-save & history (SaveStatusIndicator partial, history V2.0)

### ❌ Not Implemented (~35-40%)

- FR20-21: Context budget management (NEW V2.0)
- FR31-33: Bulk selection & contextual menu (NEW MVP-V1.0)
- FR38-39: Lore contradiction detection (NEW V1.5)
- FR42-45: Context dropping detection (NEW V1.5)
- FR46-47: Simulation flow (NEW V1.0)
- FR57: Anti-context-dropping templates (NEW V1.5)
- FR60-63: Template marketplace (NEW V1.5-V2.5)
- FR66-71: RBAC complete (NEW V1.5)
- FR79: Fallback LLM provider (NEW V1.0)
- FR85, FR87-88: Index & batch ops (NEW V1.0)
- FR94: Game stats integration (NEW V3.0)
- FR100-101: Dialogue history (NEW MVP basic, V2.0 detailed)
- FR102, FR106-108: Wizard onboarding & mode detection (NEW V1.0-V1.5)
- FR109-111: UX patterns (preview, comparison, shortcuts) (NEW V1.0)
- FR112-113: Performance monitoring dashboard (NEW V1.5)
- FR117: Screen readers (NEW V2.0)

---

## Next Steps

1. **Integrate into PRD:** Merge this enhanced FR list into main PRD document
2. **Update NFRs:** Add performance targets moved from FRs (generation time, rendering speed, API latency)
3. **Epic Breakdown:** Use these 113 FRs as capability contract for story creation
4. **Testing:** Each FR becomes testable acceptance criteria

---

## Party Mode Team Insights

**Mary (Analyst):** Identified 5 critical gaps (context dropping, versioning, batch ops, fallback provider, context budget)

**Winston (Architect):** Clarified FR/NFR separation, identified dependencies (FR13↔FR14), validated Unity scope (FR89-94)

**Sally (UX Designer):** Added 5 UX patterns (preview, comparison, bulk selection, contextual actions, guided/power mode)

**Amelia (Developer):** Confirmed implementation status accuracy, identified MVP gaps (FR4 inline accept/reject, FR9 auto-link, FR46-47 simulation)

**Murat (Test Architect):** Improved testability (FR38-39 split, FR42 variance tolerance, FR114 shortcuts spec)

**John (PM):** Synthesized all improvements, validated hybrid approach (add missing + cleanup)

---

## Non-Functional Requirements

### Performance

**NFR-P1: Graph Editor Rendering Performance**

**Requirement:** System must render dialogue graphs with 500+ nodes in <1 second.

**Rationale:** User Journey Marc - workflow itératif nécessite graph fluide. Performance dégradée = friction workflow critique.

**Measurement:**
- **Metric:** Time to render graph (500 nodes) from JSON load to visual display
- **Target:** <1 second (95th percentile)
- **Test:** Load dialogue 500 nodes, measure render time

**Acceptance Criteria:**
- Graph 100 nodes: <200ms
- Graph 500 nodes: <1s
- Graph 1000+ nodes: <2s (avec virtualization si nécessaire)

---

**NFR-P2: LLM Generation Response Time**

**Requirement:** System must generate dialogue nodes within acceptable time limits for iterative workflow.

**Rationale:** Success Criteria Technical - génération rapide = workflow efficace. Temps élevé = frustration utilisateur.

**Measurement:**
- **Metric:** Time from generation request to node available (prompt construction + LLM call + validation)
- **Targets:**
  - Single node: <30 seconds (95th percentile)
  - Batch 3-8 nodes: <2 minutes (95th percentile)
- **Test:** Measure end-to-end generation time (API call → response received)

**Acceptance Criteria:**
- 1 node generation: <30s (target), <60s (maximum acceptable)
- Batch 3-8 nodes: <2min (target), <5min (maximum acceptable)
- Timeout handling: If >5min, cancel and return error (user can retry)

---

**NFR-P3: API Response Time (Non-LLM Endpoints)**

**Requirement:** System must respond to non-LLM API requests within <200ms.

**Rationale:** User Experience - interactions UI (list dialogues, search, context selection) doivent être instantanées.

**Measurement:**
- **Metric:** API response time (GET endpoints: list, search, context, metadata)
- **Target:** <200ms (95th percentile)
- **Test:** Load test API endpoints, measure response times

**Acceptance Criteria:**
- GET /api/v1/dialogues (list): <200ms
- GET /api/v1/context (GDD entities): <200ms
- GET /api/v1/dialogues/{id} (read): <100ms
- POST /api/v1/dialogues (save): <500ms

---

**NFR-P4: UI Interaction Responsiveness**

**Requirement:** System must respond to user interactions (clicks, drags, keyboard) within <100ms.

**Rationale:** User Journey Marc - workflow itératif nécessite UI réactive. Latence = friction workflow.

**Measurement:**
- **Metric:** Time from user action to UI feedback (visual update)
- **Target:** <100ms (perceived instant)
- **Test:** Measure click-to-visual-feedback time in graph editor

**Acceptance Criteria:**
- Node click: <50ms
- Drag & drop: <100ms (smooth 60fps)
- Keyboard navigation: <50ms
- Search filter: <200ms (includes API call)

---

**NFR-P5: Initial Page Load Time**

**Requirement:** System must load initial page (dashboard) within acceptable time for good user experience.

**Rationale:** Web App - first impression critique. Load lent = frustration utilisateur.

**Measurement:**
- **Metric:** Time from page request to interactive (TTI - Time to Interactive)
- **Targets:**
  - First Contentful Paint (FCP): <1.5s
  - Time to Interactive (TTI): <3s
  - Largest Contentful Paint (LCP): <2.5s
- **Test:** Lighthouse performance audit, network throttling (fast 3G)

**Acceptance Criteria:**
- FCP: <1.5s (target), <3s (maximum acceptable)
- TTI: <3s (target), <5s (maximum acceptable)
- LCP: <2.5s (target), <4s (maximum acceptable)

---

### Security

**NFR-S1: LLM API Key Protection**

**Requirement:** System must never expose LLM API keys to frontend or client-side code.

**Rationale:** Security - API keys exposées = risque coût élevé (usage non autorisé).

**Measurement:**
- **Metric:** Zero API keys in frontend bundle, client-side code, or browser network requests
- **Target:** 100% protection (zero exposure)
- **Test:** Code audit, network inspection, bundle analysis

**Acceptance Criteria:**
- API keys stored backend only (environment variables)
- No API keys in frontend JavaScript bundle
- No API keys in browser network requests (all LLM calls via backend proxy)
- API keys rotation support (change key without downtime)

---

**NFR-S2: Authentication & Session Security**

**Requirement:** System must authenticate users securely and protect sessions from unauthorized access.

**Rationale:** RBAC V1.5 - collaboration équipe nécessite auth robuste.

**Measurement:**
- **Metric:** Session security (token expiration, HTTPS, secure cookies)
- **Target:** Industry standard (JWT tokens, 24h expiration, HTTPS only)
- **Test:** Security audit, penetration testing

**Acceptance Criteria:**
- Password hashing: bcrypt or Argon2 (never plaintext)
- Session tokens: JWT with expiration (24h default, configurable)
- HTTPS only: All API calls over HTTPS (no HTTP in production)
- Secure cookies: HttpOnly, Secure, SameSite=Strict flags

---

**NFR-S3: Data Protection (Dialogues & GDD)**

**Requirement:** System must protect dialogue data and GDD from unauthorized access or modification.

**Rationale:** IP Protection - dialogues = propriété Alteir, GDD = lore critique.

**Measurement:**
- **Metric:** Access control enforcement (RBAC, file permissions)
- **Target:** 100% enforcement (no unauthorized access)
- **Test:** Access control testing, RBAC validation

**Acceptance Criteria:**
- File permissions: Read/write restricted to authorized users only
- RBAC enforcement: Admin/Writer/Viewer roles respected (V1.5+)
- Audit logs: Track all access/modification (V1.5+)
- Backup security: Backups encrypted, access restricted

---

### Scalability

**NFR-SC1: Dialogue Storage Scalability**

**Requirement:** System must support 1000+ dialogues (100+ nodes each) without performance degradation.

**Rationale:** Success Criteria Technical - scale 1M+ lignes by 2028 = 1000+ dialogues minimum.

**Measurement:**
- **Metric:** Performance (search, list, load) with 1000+ dialogues
- **Target:** <10% performance degradation vs 100 dialogues baseline
- **Test:** Load test with 1000 dialogues, measure search/list/load times

**Acceptance Criteria:**
- List dialogues: <500ms (1000 dialogues)
- Search dialogues: <1s (1000 dialogues, indexed)
- Load dialogue: <200ms (100 nodes)
- Storage: Filesystem OK until 1000+, DB migration if >1000 (V2.0+)

---

**NFR-SC2: Concurrent User Support**

**Requirement:** System must support 3-5 concurrent users (MVP) scaling to 10+ users (V2.0+).

**Rationale:** Scoping - équipe future (Marc + Mathieu + writer + Unity dev + communauté).

**Measurement:**
- **Metric:** System performance with concurrent users (response time, no conflicts)
- **Target:** <20% performance degradation with 5 concurrent users vs 1 user
- **Test:** Load test with concurrent users, measure response times

**Acceptance Criteria:**
- MVP: 3-5 concurrent users (single instance, no conflicts)
- V1.5: 5-10 concurrent users (RBAC, shared dialogues)
- V2.0+: 10+ concurrent users (real-time collaboration, conflict resolution)
- Conflict handling: Detect concurrent edits, merge or error gracefully

---

**NFR-SC3: Graph Editor Scalability**

**Requirement:** System must support dialogues with 100+ nodes (Disco Elysium scale) with smooth performance.

**Rationale:** Domain Requirements - CRPG dialogues = 100+ nodes par dialogue.

**Measurement:**
- **Metric:** Graph editor performance (rendering, interaction) with 100+ nodes
- **Target:** <2s render, <100ms interactions (100 nodes)
- **Test:** Load dialogue 100 nodes, measure render/interaction times

**Acceptance Criteria:**
- 50 nodes: <500ms render, <50ms interactions
- 100 nodes: <1s render, <100ms interactions
- 500+ nodes: <2s render, <200ms interactions (avec virtualization)

---

### Reliability

**NFR-R1: Zero Blocking Bugs**

**Requirement:** System must have zero bugs that block production narrative work.

**Rationale:** Success Criteria Technical - 0 bugs bloquants = production-readiness.

**Measurement:**
- **Metric:** Bug count by severity (blocking = P0, critical = P1)
- **Target:** Zero P0 bugs, <5 P1 bugs
- **Test:** Bug tracking, production monitoring

**Acceptance Criteria:**
- P0 (Blocking): Zero bugs (éditeur graphe crash, data loss, export fail)
- P1 (Critical): <5 bugs (performance degradation, minor data issues)
- Bug definition: See Success Criteria Technical (éditeur inutilisable, génération fail >10%, export invalide, data loss, performance >5min)

---

**NFR-R2: System Uptime**

**Requirement:** System must be available >99% of the time (outil toujours accessible).

**Rationale:** User Journey Marc - downtime = perte production narrative.

**Measurement:**
- **Metric:** Uptime percentage (monthly)
- **Target:** >99% uptime (monthly)
- **Test:** Monitoring (health checks, uptime tracking)

**Acceptance Criteria:**
- Monthly uptime: >99% (target), >95% (minimum acceptable)
- Planned maintenance: <4h/month (scheduled, off-hours)
- Unplanned downtime: <1h/month (incidents)
- Recovery time: <15min (from incident detection to resolution)

---

**NFR-R3: Data Loss Prevention**

**Requirement:** System must prevent data loss (dialogues, GDD, user work).

**Rationale:** User Journey Marc - perte travail = frustration critique.

**Measurement:**
- **Metric:** Data loss incidents (lost dialogues, corrupted files)
- **Target:** Zero data loss incidents
- **Test:** Backup validation, recovery testing, auto-save verification

**Acceptance Criteria:**
- Auto-save: Every 2 minutes (V1.0+), LocalStorage backup
- Session recovery: Restore after browser crash (V1.0+)
- Git versioning: Manual commits (Marc workflow), auto-commit option (V2.0+)
- Backup: Daily backups (if cloud deployment), restore tested

---

**NFR-R4: Error Recovery (LLM API Failures)**

**Requirement:** System must gracefully handle LLM API failures with automatic retry and fallback.

**Rationale:** User Journey Marc edge case - LLM API down = fallback Anthropic.

**Measurement:**
- **Metric:** Error recovery success rate (retry success, fallback success)
- **Target:** >95% recovery (retry or fallback succeeds)
- **Test:** Simulate LLM API failures, measure recovery rate

**Acceptance Criteria:**
- Retry logic: 3 attempts, exponential backoff (1s, 2s, 4s)
- Fallback provider: OpenAI → Anthropic (V1.0+)
- User feedback: Clear error messages, retry option
- Timeout: 60s per attempt, cancel after 3 failures

---

### Accessibility

**NFR-A1: Keyboard Navigation**

**Requirement:** System must be fully navigable via keyboard (graph editor, forms, navigation).

**Rationale:** Developer Tool / Web App - keyboard nav critique pour power users.

**Measurement:**
- **Metric:** Keyboard navigation coverage (% UI elements accessible via keyboard)
- **Target:** 100% coverage (all interactive elements)
- **Test:** Keyboard-only navigation test, screen reader testing

**Acceptance Criteria:**
- Graph editor: Tab navigation (nodes), Arrow keys (move), Enter/Space (select), Escape (cancel)
- Forms: Tab navigation, Enter submit, Escape cancel
- Keyboard shortcuts: Ctrl+G (generate), Ctrl+S (save), Ctrl+Z (undo) (FR111)
- Focus indicators: Visible focus states (outline, highlight)

---

**NFR-A2: Color Contrast (WCAG AA)**

**Requirement:** System must meet WCAG AA color contrast requirements (4.5:1 text, 3:1 UI).

**Rationale:** Accessibility - WCAG AA minimum pour outil professionnel.

**Measurement:**
- **Metric:** Color contrast ratios (text, UI components)
- **Target:** WCAG AA (4.5:1 text, 3:1 UI)
- **Test:** Color contrast audit (Lighthouse, manual testing)

**Acceptance Criteria:**
- Text contrast: 4.5:1 minimum (normal text), 3:1 (large text)
- UI contrast: 3:1 minimum (buttons, borders, focus indicators)
- High contrast mode: Alternative theme (V2.0+)

---

**NFR-A3: Screen Reader Support (V2.0+)**

**Requirement:** System must support screen readers with ARIA labels and semantic HTML.

**Rationale:** Open-source vision - accessibilité = valeur communauté.

**Measurement:**
- **Metric:** Screen reader compatibility (ARIA labels, semantic HTML)
- **Target:** WCAG AA compliance (V2.0+)
- **Test:** Screen reader testing (NVDA, JAWS, VoiceOver)

**Acceptance Criteria:**
- ARIA labels: All interactive elements labeled
- Semantic HTML: Proper headings, landmarks, roles
- Live regions: Dynamic updates announced (generation progress, errors)
- Skip links: Skip to main content, skip navigation

---

### Integration

**NFR-I1: Unity JSON Export Reliability**

**Requirement:** System must export Unity JSON with 100% schema conformity (zero invalid exports).

**Rationale:** User Journey Thomas - export invalide = blocage pipeline Unity.

**Measurement:**
- **Metric:** Export validation success rate (% exports valid)
- **Target:** 100% valid exports (zero invalid)
- **Test:** Validate all exports against Unity custom schema

**Acceptance Criteria:**
- Schema validation: 100% before export (UnitySchemaValidator)
- Invalid export handling: Block export, show validation errors
- Export logs: Metadata (validation status, errors if any)

---

**NFR-I2: LLM API Integration Reliability**

**Requirement:** System must integrate with LLM APIs (OpenAI, Anthropic) with retry logic and fallback.

**Rationale:** Reliability - LLM API failures = génération impossible.

**Measurement:**
- **Metric:** LLM API success rate (after retries/fallback)
- **Target:** >99% success rate (retry + fallback)
- **Test:** Monitor LLM API calls, measure success rate

**Acceptance Criteria:**
- Retry logic: 3 attempts, exponential backoff
- Fallback provider: OpenAI → Anthropic (V1.0+)
- Error handling: Clear user feedback, retry option
- Rate limiting: Respect LLM API rate limits, queue requests if needed

---

**NFR-I3: Notion Integration (V2.0+)**

**Requirement:** System must sync GDD data from Notion reliably (webhook or polling).

**Rationale:** Integration Ecosystem - Notion sync bidirectionnel (V2.0+).

**Measurement:**
- **Metric:** Notion sync success rate (% syncs successful)
- **Target:** >95% success rate
- **Test:** Monitor Notion sync operations, measure success rate

**Acceptance Criteria:**
- Webhook support: Receive Notion updates (V2.0+)
- Polling fallback: Poll Notion if webhook unavailable
- Conflict resolution: Handle concurrent Notion ↔ DialogueGenerator edits
- Error handling: Log sync errors, manual retry option

---

## NFR Summary

**Total NFRs: 15** (5 Performance, 3 Security, 3 Scalability, 3 Reliability, 1 Accessibility MVP, 3 Integration)

**Critical NFRs (MVP):**
- NFR-P1, P2, P3, P4, P5: Performance (graph, generation, API, UI, load)
- NFR-S1, S2: Security (API keys, auth)
- NFR-SC1, SC3: Scalability (storage, graph editor)
- NFR-R1, R2, R3, R4: Reliability (bugs, uptime, data loss, error recovery)
- NFR-A1, A2: Accessibility (keyboard nav, contrast)
- NFR-I1, I2: Integration (Unity export, LLM APIs)

**V2.0+ NFRs:**
- NFR-S3: Data protection audit logs
- NFR-SC2: Concurrent users 10+
- NFR-A3: Screen reader support
- NFR-I3: Notion integration

---

## Automated Testing & Quality Framework

### Executive Summary

DialogueGenerator implements a **4-layer quality validation system** to maintain professional CRPG narrative quality at scale (1M+ lines by 2028):

**Testing Layers:**
- **Layer 1 (MVP, $0):** Structural tests - orphan nodes, cycles, player agency %, branching ratio
- **Layer 2 (V1.0, $0):** Slop detection - AI patterns, lexical diversity, lore dumps (EQ-Bench inspired)
- **Layer 3 (V1.5, $0.01/node):** LLM rubric scoring - 13 CRPG-specific abilities, selective user toggle
- **Layer 4 (V2.5, $0.02/comparison):** Pairwise Elo ranking - character ranking, template A/B testing (nice-to-have)

**Dual-Tier Baselines:**
- **Primary:** Planescape: Torment (150K words, professional CRPG reference) - validates genre-level quality
- **Secondary:** Character-specific manual baselines (Marc's writing per character) - validates voice consistency

**Key Metrics:** Slop Score (target <13 vs PS:T 10.38), Rubric Score (target >8/10), Acceptance Rate (target >80%)

**Annual Cost:** ~$1,100 for 1M nodes production (Layers 1-2 free, Layer 3 selective, Layer 4 minimal)

**Innovation:** Zero-cost baseline validation (deterministic tests + character-specific baseline comparison) + selective LLM judging for critical nodes only.

---

### Overview

DialogueGenerator implements a comprehensive, data-driven quality framework inspired by **EQ-Bench Creative Writing v3** and adapted for CRPG narrative authoring. This framework combines deterministic structural tests with LLM-assisted quality metrics, leveraging **dual-tier baselines** (Planescape: Torment professional reference + character-specific manual baselines) to ensure consistent, high-quality dialogue generation at scale.

**Philosophy:** Quality validation must be:
- **Automated** where possible (structural, slop detection) to enable scale (1M+ lines)
- **Human-guided** where needed (rubric feedback, manual baselines) to preserve craft
- **Data-driven** (metrics, baselines, trends) to enable objective improvement
- **Cost-conscious** (zero-cost layers prioritized, LLM judges selective)

**Key Innovation:** **Dual-tier baseline system** enables both character-specific style validation (character voice for Uresaïr, Genka Lien, etc.) AND genre-level quality benchmarking (Planescape: Torment gold standard).

---

### Testing Architecture Layers

The quality framework is organized in **4 layers** with increasing sophistication and cost:

**Layer 0: Baselines (Foundation)**
- Genre baseline: Planescape: Torment (1000 samples, 150K words total)
- Character-specific baselines: Manual writing samples per character (extensible)
- Storage: JSON files, `data/baselines/`
- **Cost:** One-time calculation ($0 ongoing)

**Layer 1: Structural Tests (MVP, $0 cost)**
- Deterministic validation (no LLM)
- Real-time feedback (inline badges)
- Tests: Orphan nodes, cycles, missing fields, player agency %, branching ratio
- **Implementation:** GraphValidationService (already exists), extend with metrics

**Layer 2: Slop Detection (V1.0, $0 cost)**
- Automated text analysis (no LLM)
- EQ-Bench slop metrics + CRPG-specific patterns
- Metrics: Slop words/trigrams, not-x-but-y patterns, lore dump patterns, lexical diversity
- **Implementation:** SlopDetector service (NLP library, regex)

**Layer 3: Rubric Scoring (V1.5, $0.01/node, selective)**
- LLM judge (Claude Sonnet 4)
- 13 CRPG-specific abilities (radar chart)
- User toggle ON/OFF (default OFF)
- **Cost:** ~$1,000/year (10% nodes evaluated)

**Layer 4: Pairwise Elo (V2.5, $0.02/comparison, nice-to-have)**
- Pairwise matchups for fine discrimination
- Monthly benchmark (20 characters x 30 nodes)
- Simplified Elo (not full Glicko loops)
- **Cost:** ~$72/year (monthly benchmarks)

**Total Annual Cost:** ~$1,100 for 1M nodes production (très acceptable)

---

### Dual-Tier Baseline System

#### Rationale

**Challenge:** DialogueGenerator serves two quality goals:
1. **Character Voice Fidelity** - Match Marc's unique writing style per character (poetic, metaphorical)
2. **Genre Quality Bar** - Achieve professional CRPG narrative quality (Planescape: Torment level)

**Solution:** Two-tier baselines enable both validations simultaneously, at zero ongoing cost.

#### Primary Baseline: Planescape: Torment

**Source:** Complete dialogue transcript (150,000 words, 10,000+ nodes)

**Justification:**
- **Gold Standard:** PS:T is industry reference for CRPG narrative excellence
- **Sample Size:** Massive dataset (1000+ sample nodes for baseline calculation)
- **Professional Quality:** Human-written, professionally edited, AAA game
- **Marketing Value:** "AI dialogue achieving Planescape: Torment quality" = investor pitch gold

**Baseline Metrics (calculated from 1000 random samples):**
```json
{
  "source": "Planescape: Torment",
  "sample_size": 1000,
  "total_words": 15420,
  "metrics": {
    "slop_score": 10.38,
    "slop_words_per_1k": 6.90,
    "slop_trigrams_per_1k": 0.09,
    "not_x_but_y_per_1k": 0.04,
    "vocab_level": 7.80,
    "sentence_length": 14.59,
    "lexical_diversity": 0.5065,
    "metaphor_density": 0.15
  }
}
```

**Usage:**
- All generated dialogues compared vs PS:T baseline
- Dashboard displays: "PS:T Quality: 8.6/10 ⭐ (Excellent)"
- Threshold: Generated slop score <13 (PS:T + 2.5 margin)

#### Secondary Baseline: Per-Character Manual Samples

**Source:** Marc's hand-written dialogue nodes (Articy Draft export)

**Current Samples:**
- **Uresaïr/Ethérée dialogue:** 22 nodes (12 NPC dialogue, 10 player choices)
- **Extensible:** Marc can write additional samples per character (Genka Lien, Raki-Biro, etc.)

**Example Character Baseline (Uresaïr):**
```json
{
  "character_name": "Uresaïr",
  "source": "Marc's manual nodes (Articy)",
  "sample_size": 12,
  "metrics": {
    "slop_score": 8.5,
    "vocab_level": 8.2,
    "sentence_length": 28.4,
    "lexical_diversity": 0.58,
    "metaphor_density": 0.42,
    "style_notes": "Poetic, metaphorical, contemplative"
  },
  "sample_excerpts": [
    "Le simoun m'apporte-t-il donc enfin un songe dont le parfum s'étende au-delà de ce monde ?",
    "Tu es une flamme qui brûle les mondes. Veux-tu nous brûler, nous aussi ?"
  ]
}
```

**Observations:**
- **Vocab Level:** 8.2 (character baseline) vs 7.8 (PS:T) - Character-specific baselines show elevated vocabulary
- **Sentence Length:** 28.4 (character baseline) vs 14.59 (PS:T) - Character baselines show longer, complex sentences
- **Metaphor Density:** 0.42 (character baseline) vs 0.15 (PS:T) - Character baselines show high metaphorical density
- **Slop Score:** 8.5 (character baseline) vs 10.38 (PS:T) - Manual baseline samples have less slop (as expected)

**Usage:**
- When character baseline exists: Compare generated vs character baseline
- Threshold: Generated slop ±2, vocab ±0.5, sentence length ±5 (acceptable deltas)
- Alert if deviation >threshold: "Déviation style Uresaïr détectée"

#### Validation Flow (Multi-Tier)

```
User generates node for Uresaïr
  ↓
Calculate node metrics (slop, vocab, style)
  ↓
Tier 1: Character-specific validation (if baseline exists)
  - Compare vs Uresaïr baseline
  - Score: 7.8/10 (Slop +2.7 borderline, vocab OK, metaphor OK)
  ↓
Tier 2: Genre validation (always)
  - Compare vs PS:T baseline
  - Score: 8.6/10 (Excellent vs professional reference)
  ↓
Dashboard display:
  Quality Score: 8.2/10
  ├─ Uresaïr Voice Match: 7.8/10 (Slop borderline)
  └─ PS:T Quality: 8.6/10 ⭐ (Excellent)
  
  Recommendations:
  - Reduce Slop Words (target <10 per 1k words)
  - Maintain metaphorical richness (OK)
```

---

### Layer 1: Structural Tests (MVP)

**Goal:** Catch graph structure bugs and validate dialogue flow logic.

**Cost:** $0 (deterministic code, no LLM)

**Tests:**

**ST-1: Orphan Nodes Detection**
- **Test:** Find nodes with no incoming/outgoing connections
- **Threshold:** 0 orphan nodes (except start/end nodes)
- **Alert:** "⚠️ 3 orphan nodes detected - graph incomplete"

**ST-2: Cycle Detection**
- **Test:** Find cycles in dialogue graph (A → B → C → A)
- **Threshold:** 0 infinite loops (warn if cycle detected)
- **Alert:** "⚠️ Cycle detected: Node A → B → C → A"

**ST-3: Missing Fields Validation**
- **Test:** Check required fields (speaker, text, connections)
- **Threshold:** 0 nodes with missing fields
- **Alert:** "❌ Node 42 missing speaker field"

**ST-4: Player Agency Ratio**
- **Test:** Calculate % of nodes that offer meaningful player choices
- **Formula:** `agency_ratio = (nodes_with_choices_2+) / total_nodes`
- **Threshold:** >40% (meaningful choice frequency)
- **Alert:** "⚠️ Agency 32% - below target 40%"

**ST-5: Branching Ratio**
- **Test:** Calculate branching/convergence balance
- **Formula:** `branching_ratio = divergence_points / convergence_points`
- **Threshold:** 0.8 - 1.5 (balanced graph)
- **Alert:** "⚠️ Branching 2.3 - too many divergences, graph may explode"

**Implementation:**
```python
# services/metrics/structural_validator.py

class StructuralValidator:
    def validate_dialogue(self, dialogue: Dialogue) -> StructuralReport:
        return {
            "orphan_nodes": self.find_orphans(dialogue),
            "cycles": self.detect_cycles(dialogue),
            "missing_fields": self.check_required_fields(dialogue),
            "agency_ratio": self.calculate_agency(dialogue),
            "branching_ratio": self.calculate_branching(dialogue)
        }
```

**UI Display:** Inline badges on graph nodes
- 🟢 Green: All tests pass
- 🟡 Yellow: Warnings (agency low, branching high)
- 🔴 Red: Errors (orphans, missing fields)

---

### Layer 2: Slop Detection (V1.0)

**Goal:** Detect "AI slop" patterns (overused phrases, purple prose, lore dumps) to maintain writing quality.

**Inspiration:** EQ-Bench Creative Writing v3 "Slop Score" methodology

**Cost:** $0 (NLP analysis, regex patterns, no LLM)

#### Slop Score Components

**SD-1: Slop Words (per 1k words)**

**Definition:** Overused words that indicate AI-generated text or lazy writing.

**EQ-Bench Base List (top 10):**
- whispered, stared, paused, glow, impossibly, trembling, nodded, shadows, flickered, shimmered

**CRPG-Specific Additions:**
- quest, tavern crowded, mysterious stranger, ancient artifact, destiny, prophecy, chosen one, fate

**Calculation:**
```python
def count_slop_words(text: str) -> float:
    word_count = len(text.split())
    slop_hits = sum(1 for word in SLOP_WORDS if word in text.lower())
    return (slop_hits / word_count) * 1000  # per 1k words
```

**Baseline Comparison:**
- **PS:T baseline:** 6.90 slop words per 1k
- **Character-specific baseline:** ~6-8 per 1k (manual writing)
- **Target:** <10 per 1k (acceptable), <15 (borderline), >15 (poor)

---

**SD-2: Slop Trigrams (per 1k words)**

**Definition:** Overused 3-word phrases that indicate formulaic writing.

**EQ-Bench Base List:**
- "something else something", "something else entirely", "one last time", "voice barely audible", "door swung open", "mind already racing"

**CRPG-Specific Additions:**
- "you must help", "but be warned", "time is short", "listen carefully now"

**Baseline Comparison:**
- **PS:T baseline:** 0.09 trigrams per 1k
- **Target:** <0.20 (good), <0.50 (acceptable), >0.50 (poor)

---

**SD-3: Not-X-But-Y Patterns (per 1k chars)**

**Definition:** Overused rhetorical pattern that indicates AI tendency to hedge or add unnecessary complexity.

**Pattern Detection (regex):**
```regex
(not|wasn't|isn't) .{1,50} (but|it was|it's)
```

**Examples:**
- "It wasn't the kind of kiss that promised to fix everything, it was something else entirely"
- "This wasn't the pleasant fog of endorphins. This was something closer to genuine amnesia."

**Baseline Comparison:**
- **PS:T baseline:** 0.04 per 1k chars
- **Target:** <0.10 (good), <0.20 (acceptable), >0.20 (poor)

---

**SD-4: Lore Dump Patterns (DialogueGenerator-Specific)**

**Definition:** Patterns indicating explicit exposition or "lore dumping" (violates "show don't tell").

**Pattern Detection (regex):**
```regex
(you know|as you remember|as you may recall|it is said that|allow me to explain|let me tell you)
```

**Examples:**
- "As you know, the Eternal Return is..."
- "You remember that Uresaïr is..."
- "Let me explain what happened..."

**Rationale:** CRPG dialogues should integrate lore naturally, not dump exposition.

**Target:** <2 patterns per dialogue (acceptable), >5 (poor)

---

**SD-5: Lexical Diversity (MATTR-500)**

**Definition:** Moving-Average Type-Token Ratio measures vocabulary richness (low diversity = repetitive).

**Calculation:**
- Sliding window of 500 words
- Calculate unique words / total words per window
- Average across all windows

**Baseline Comparison:**
- **PS:T baseline:** 0.5065 (human writing)
- **Target:** >0.55 (excellent), >0.50 (good), <0.45 (poor - too repetitive)

**Implementation:** NLTK or spaCy library

---

#### Composite Slop Score

**Formula (EQ-Bench inspired):**
```python
slop_score = (slop_words * 0.5) + (slop_trigrams * 2.0) + (not_x_but_y * 1.5) + (lore_dumps * 1.0)
```

**Interpretation:**
- **<12:** Excellent (comparable to human baseline)
- **12-15:** Good (acceptable for production)
- **15-20:** Borderline (review recommended)
- **>20:** Poor (needs revision)

**Dashboard Display:**
```
Slop Score: 12.3 (Good)

Details:
├─ Slop Words: 8.2 per 1k ✓ (target <10)
├─ Slop Trigrams: 0.15 per 1k ✓ (target <0.20)
├─ Not-X-But-Y: 0.08 per 1k chars ✓ (target <0.10)
├─ Lore Dumps: 1 detected ✓ (target <2)
└─ Lexical Diversity: 0.56 ⭐ (target >0.55)

Comparison:
- vs PS:T baseline: +1.9 (acceptable)
- vs Uresaïr baseline: +3.8 (borderline)
```

---

### Layer 3: Rubric Scoring (V1.5, Selective)

**Goal:** LLM-assisted quality feedback on 13 CRPG-specific abilities for targeted validation.

**Inspiration:** EQ-Bench rubric evaluation + CRPG narrative criteria

**Cost:** $0.01 per node (Claude Sonnet 4 judge)

**Strategy:** User toggle ON/OFF (default OFF) - use selective for critical nodes only

#### 13 CRPG-Specific Abilities

**Rubric evaluates each node on 13 dimensions (1-10 scale):**

**R1: Voice Consistency**
- Character speaks in established voice/dialect
- Vocabulary/tone match character baseline
- No jarring out-of-character moments

**R2: Lore Accuracy**
- Facts consistent with GDD
- No contradictions with established lore
- Accurate use of proper nouns, locations, history

**R3: Subtlety Lore Integration**
- "Show don't tell" - lore integrated naturally
- Avoids exposition dumps ("as you know...")
- Reveals lore through character actions/dialogue

**R4: Player Agency**
- Choices are meaningful (consequence-bearing)
- Player choices reflect distinct perspectives/values
- No false choices (all leading to same outcome)

**R5: Branching Coherence**
- Logical flow from previous node
- Choices connect coherently to next nodes
- No non-sequiturs or jarring transitions

**R6: Tone Consistency**
- Emotional tone appropriate for scene
- Maintains established mood (tragic, humorous, tense)
- Tone shifts are motivated, not random

**R7: Dialogue Naturalism**
- Avoids stilted/robotic phrasing
- Natural rhythm, not overly formal (unless character voice)
- Uses contractions, colloquialisms where appropriate

**R8: Character Insight**
- Reveals character motivation/personality
- Depth beyond surface dialogue
- Character growth or tension visible

**R9: Avoids Clichés**
- No generic CRPG tropes (mysterious tavern stranger, ancient prophecy)
- Fresh phrasing, not overused phrases
- Unique voice, not generic fantasy-speak

**R10: Avoids Flowery Verbosity**
- No excessive vocabulary flexing ("sempiternal", "ineffable" overused)
- Complexity serves character/scene, not show-off
- Balance sophistication with readability

**R11: Avoids Poetic Overload**
- Metaphor/poetry serves character voice, not excessive
- No purple prose or incoherent poetic rambling
- Clear meaning beneath poetic language

**R12: Plot/Character Coherence**
- Internal consistency (character choices logical)
- Plot developments motivated (no deus ex machina)
- Metaphors/symbols coherent with scene

**R13: Instruction Following**
- Dialogue follows generation prompt constraints
- Respects specified tone/length/context
- Includes required elements (choice count, branching)

#### Rubric Prompt (LLM Judge)

```
Evaluate the following CRPG dialogue node on these criteria (1-10 scale):

Context:
- Character: {character_name}
- Character baseline: {character_baseline_summary}
- Scene context: {scene_context}
- Previous node: {previous_node_text}

Generated Dialogue Node:
{generated_node_text}

Choices:
{generated_choices}

Criteria (score 1-10):
1. Voice Consistency (matches character baseline)
2. Lore Accuracy (consistent with GDD)
3. Subtlety Lore (show don't tell)
4. Player Agency (meaningful choices)
5. Branching Coherence (logical flow)
6. Tone Consistency (appropriate emotion)
7. Dialogue Naturalism (not stilted)
8. Character Insight (depth, motivation)
9. Avoids Clichés (fresh, unique)
10. Avoids Flowery Verbosity (no vocab flexing)
11. Avoids Poetic Overload (clear meaning)
12. Plot/Character Coherence (internal logic)
13. Instruction Following (prompt compliance)

For each criterion:
- Score (1-10)
- Brief explanation (1-2 sentences)
- Specific examples from text (quote)

Final composite score (average of 13 criteria).
```

**Output Format:**
```json
{
  "overall_score": 8.2,
  "criteria_scores": {
    "voice_consistency": {"score": 8, "explanation": "...", "example": "..."},
    "lore_accuracy": {"score": 9, "explanation": "...", "example": "..."},
    ...
  },
  "strengths": ["Natural dialogue flow", "Character voice consistent"],
  "weaknesses": ["Slight lore dump in opening line"],
  "recommendations": ["Reduce exposition, integrate lore through action"]
}
```

#### Rubric Usage Strategies

**Strategy A: Selective Rubric (MVP-V1.5)**
- User toggle ON/OFF per node (default OFF)
- Use for critical nodes (major NPCs, plot revelations)
- **Cost:** 10% nodes = 100K x $0.01 = $1,000/year (acceptable)

**Strategy B: Sampling Rubric (V2.0)**
- Automatic rubric on random sample (10% nodes)
- Statistical confidence: 90%+ with 10% sample
- **Cost:** 100K x $0.01 = $1,000/year

**Strategy C: Template Optimization Only (V2.5)**
- Rubric only for A/B testing templates
- 1000 tests/year x 60 nodes = 60K evaluations
- **Cost:** 60K x $0.01 = $600/year

**Recommendation:** Start with Strategy A (user toggle), evolve to C (template optimization).

---

### Layer 4: Pairwise Elo Ranking (V2.5, Nice-to-Have)

**Goal:** Fine discrimination between generated nodes for character ranking and template optimization.

**Inspiration:** EQ-Bench pairwise evaluation + Glicko rating system (simplified)

**Cost:** $0.02 per comparison (bidirectional)

**Status:** Nice-to-have (V2.5, not critical for production)

#### Methodology

**Pairwise Comparison Prompt:**
```
Compare the relative ability of each dialogue node on these criteria:

Node A (Character: Uresaïr):
{node_a_text}

Node B (Character: Uresaïr):
{node_b_text}

Criteria:
1. Character authenticity and insight
2. Interesting and original
3. Writing quality
4. Coherence (plot, character choices, metaphor)
5. Instruction following (prompt)
6. World and atmosphere
7. Avoids clichés (characters, dialogue, plot)
8. Avoids flowery verbosity & vocab maxxing
9. Avoids gratuitous metaphor or poetic overload

For each criterion:
- Pick the stronger node (no draws)
- Rate ability difference: + / ++ / +++ / ++++ / +++++ (1-5 scale)

Response format:
{
  "character_authenticity": {"winner": "A", "margin": "+++"},
  "interesting_original": {"winner": "B", "margin": "++"},
  ...
}
```

**Elo Calculation (Simplified):**
- Initial Elo: 1500 (all characters)
- Pairwise matchups: Sparse sampling (neighboring Elo scores)
- Win margin: Weighted by '+' count (1-5)
- Anchor scores: Reference node (human baseline) = 1500 fixed

**Use Cases:**

**UC-1: Character Ranking**
- Monthly benchmark: 20 characters x 30 nodes
- Pairwise matchups: ~300 comparisons (sparse)
- **Output:** Elo ranking per character (identify weak characters needing template tuning)
- **Cost:** 300 x $0.02 = $6/month ($72/year)

**UC-2: Template A/B Testing**
- Test template A vs B for same character
- 30 nodes each, 30 pairwise comparisons
- **Output:** Template A Elo 1420 vs Template B Elo 1350 → Use Template A
- **Cost:** 30 x $0.02 = $0.60 per A/B test

**UC-3: Quality Validation vs Baseline**
- Compare generated vs PS:T sample (human baseline)
- **Output:** DialogueGenerator avg Elo 1450 vs PS:T 1500 → "Near professional quality"

#### Implementation Notes

**Complexity:**
- Full Glicko system = complex (loops until stable)
- **Simplified approach:** Sparse sampling + anchor scores (no loops)
- **Sufficient for DialogueGenerator:** Ranking is relative, not absolute

**Alternative (V3.0+):**
- Skip Elo, use Rubric scores for ranking (simpler, cheaper)
- Elo adds fine discrimination but marginal value

**Recommendation:** Implement V2.5 if Marc wants character ranking dashboard. Otherwise, Rubric + Slop sufficient.

---

### Bias Mitigation Strategies

**Inspiration:** EQ-Bench identifies systematic biases in LLM judges. DialogueGenerator implements controls.

#### BM-1: Length Bias (Pairwise Comparisons)

**Problem:** LLM judges strongly favor longer outputs in pairwise tasks.

**Mitigation:** Truncate outputs at 4000 chars for pairwise comparisons.

**Rationale:** CRPG dialogue nodes rarely exceed 4000 chars. Truncation puts all nodes on equal footing.

**Impact:** No loss of judging ability (dialogue complete within 4000 chars).

---

#### BM-2: Position Bias

**Problem:** Judges may favor first or second position in pairwise comparisons.

**Mitigation:** Run all pairwise evaluations bidirectional (A vs B, then B vs A), average results.

**Cost:** 2x pairwise calls, but necessary for unbiased ranking.

---

#### BM-3: Complex Verbosity Bias

**Problem:** Judges easily impressed by vocab flexing (unnecessary sophistication).

**Mitigation:** Rubric criterion R10 (Avoids Flowery Verbosity) explicitly punishes excessive vocab.

**Prompt Guidance:** "Complexity should serve character/scene, not show off."

---

#### BM-4: Poetic Incoherence Bias

**Problem:** Judges impressed by relentless poetic prose bordering on incoherence (overtrained models).

**Challenge:** Difficult to differentiate purple prose from *good* poetic style (especially for highly poetic characters).

**Mitigation:** 
- Rubric criterion R11 (Avoids Poetic Overload) targets this explicitly
- Prompt guidance: "Clear meaning beneath poetic language required"
- Character baseline comparison: Uresaïr character baseline = high metaphor density (0.42) is *intended*

**Limitation:** Judge may still struggle. Manual review for highly poetic characters (Uresaïr).

---

#### BM-5: Lore Dump Bias (DialogueGenerator-Specific)

**Problem:** Judges may favor explicit exposition ("you know, the Eternal Return is...") over subtle integration.

**Mitigation:**
- Rubric criterion R3 (Subtlety Lore) explicitly values "show don't tell"
- Slop detection Layer 2 (SD-4: Lore Dump Patterns) detects explicit patterns
- Prompt guidance: "Lore integrated naturally through action/dialogue, not explained"

---

#### Biases NOT Controlled

**Self-Bias:** Judge may favor its own outputs (if same model used for generation + judging).
- **Mitigation:** Use different models (generate with GPT-4, judge with Claude Sonnet 4)

**Positivity Bias:** Unclear if judge favors positive/negative tone.
- **Mitigation:** None (assume balanced, monitor if pattern emerges)

**Smut Bias:** NSFW-tuned models may write towards erotica, judge punishes severely.
- **Mitigation:** None (DialogueGenerator not NSFW)

**Stylistic Biases:** Judge preferences may differ from author preferences or average human.
- **Mitigation:** Character-specific manual baselines override judge bias

---

### Implementation Roadmap

#### MVP (Sprint 1-2, ~5 days dev)

**Deliverables:**
- ✅ Baseline extraction scripts (Articy + PS:T)
- ✅ Layer 1: Structural tests (orphans, cycles, agency, branching)
- ✅ Inline badges (green/yellow/red, structural only)
- ✅ Storage: `data/baselines/*.json`

**Dependencies:**
- Python XML parser (Articy extraction)
- Graph traversal algorithms (cycle detection)

**Testing:**
- Unit tests: Structural validator (100% coverage)
- Integration test: Extract baselines from Marc's XML + PS:T TXT

---

#### V1.0 (Sprint 3-5, ~10 days dev)

**Deliverables:**
- ✅ Layer 2: Slop detection (words, trigrams, patterns, lexical diversity)
- ✅ Baseline comparison engine (dual-tier validation)
- ✅ SQLite migration (metrics storage, historical tracking)
- ✅ Dashboard: Slop Score + baseline comparison display

**Dependencies:**
- NLP library (NLTK or spaCy for MATTR calculation)
- Regex patterns (slop detection)
- SQLite schema design

**Testing:**
- Unit tests: Slop detector (verify counts, thresholds)
- Integration test: Calculate PS:T baseline, compare generated node

---

#### V1.5 (Sprint 6-8, ~15 days dev)

**Deliverables:**
- ✅ Layer 3: Rubric LLM judge (13 CRPG abilities, user toggle)
- ✅ Character-specific baselines (Marc writes more nodes per character)
- ✅ Analytics dashboard (per-dialogue, per-character, trends)
- ✅ Cost governance (track LLM judge usage, budget alerts)

**Dependencies:**
- Claude Sonnet 4 API integration (rubric judge)
- React dashboard components (metrics visualization)
- Per-character baseline storage expansion

**Testing:**
- Unit tests: Rubric prompt formatting, response parsing
- Integration test: Run rubric on sample node, verify scores

---

#### V2.5 (Sprint 13-15, ~10 days dev)

**Deliverables:**
- ✅ Layer 4: Pairwise Elo system (Simplified, sparse sampling)
- ✅ Monthly benchmark automation (20 characters x 30 nodes)
- ✅ Template A/B testing (automated feedback loop)

**Dependencies:**
- Elo calculation library (simplified Glicko)
- Pairwise comparison prompt engineering
- Benchmark scheduling (monthly cron job)

**Testing:**
- Unit tests: Elo calculation, anchor scores
- Integration test: Run monthly benchmark, verify ranking

---

### Success Metrics

**Quality Metrics (tracked in dashboard):**

**QM-1: Slop Score Trend**
- **Metric:** Average slop score per dialogue (over time)
- **Target:** Decreasing trend (improvement via template optimization)
- **Baseline:** PS:T 10.38, Marc's ~8.5

**QM-2: Baseline Match Rate**
- **Metric:** % generated nodes within acceptable delta vs baseline
- **Target:** >80% within thresholds (slop ±2, vocab ±0.5)

**QM-3: Rubric Score Average (if enabled)**
- **Metric:** Average rubric score (13 criteria, 1-10 scale)
- **Target:** >8.0 (excellent), >7.0 (good)

**QM-4: Manual Revision Rate**
- **Metric:** % nodes Marc edits after generation
- **Target:** <20% (80%+ accepted as-is)
- **Correlation:** Should correlate with slop/rubric scores

**QM-5: PS:T Quality Badge**
- **Metric:** % dialogues achieving "PS:T Quality: 8+/10"
- **Target:** >70% (marketing-ready benchmark)

---

### Cost Governance

**Annual Budget (1M nodes production):**

**Layer 1 (Structural):** $0
**Layer 2 (Slop):** $0
**Layer 3 (Rubric, 10% nodes):** ~$1,000
**Layer 4 (Elo, monthly):** ~$72
**Total:** ~$1,100/year

**Budget Alerts (V1.5+):**
- Monthly LLM judge usage tracking
- Alert if approaching budget ($100/month threshold)
- User dashboard: "Rubric calls this month: 420 / 1000"

**Optimization Strategies:**
- Default rubric OFF (user toggles for critical nodes)
- Rubric sampling (V2.0): 10% random vs 100% user-selected
- Elo benchmarks: Monthly vs weekly (reduce cost 4x)

---

### Reference Materials

**EQ-Bench Creative Writing v3:**
- Methodology: https://eqbench.com/creative_writing.html
- Slop Score: https://eqbench.com/slop-score.html
- Human Baseline: Slop 10.38, Lexical Diversity 0.5065

**Planescape: Torment:**
- Source: Linear dialogue transcript (150K words)
- Location: `docs/resources/Planescape_AStoryOfTorment.txt`

**Marc's Manual Nodes:**
- Source: Articy Draft XML export (22 nodes)
- Location: `docs/resources/MarcHumanDialogue.xml`
- Characters: Uresaïr, Ethérée (extensible: Genka Lien, Raki-Biro, etc.)

---

### Open Questions & Future Considerations

**OQ-1: Character Baseline Sample Size**
- Current: 22 nodes total (12 Uresaïr NPC, 10 player choices)
- Statistical minimum: 30 nodes for 90% confidence
- **Action:** Marc writes additional nodes per character (target 30+ per major character)

**OQ-2: Multi-Language Baselines (V3.0+)**
- Current: French only (Marc's primary language)
- Future: English translation support (if international release)
- **Challenge:** Baseline recalculation per language

**OQ-3: Rubric vs Elo Trade-Off**
- Both provide quality feedback, but Elo more expensive + complex
- **Question:** Is Elo ranking necessary, or Rubric + Slop sufficient?
- **Current decision:** Elo = nice-to-have (V2.5), evaluate based on V1.5 rubric results

**OQ-4: Real-Time Rubric Feedback (V2.0+)**
- Current: Rubric selective (user toggle)
- Future: Real-time rubric during generation? (UX: inline feedback while typing)
- **Challenge:** Latency (1-2s LLM call), cost (every node = $0.01)

---

## Summary: Automated Testing & Quality Framework

DialogueGenerator implements a **4-layer quality framework** inspired by EQ-Bench Creative Writing v3, adapted for CRPG narrative authoring:

**Layer 0 (Foundation):** Dual-tier baselines (Planescape: Torment professional reference + character-specific manual baselines)

**Layer 1 (MVP, $0):** Structural tests (orphans, cycles, agency, branching) - real-time inline badges

**Layer 2 (V1.0, $0):** Slop detection (EQ-Bench metrics + CRPG patterns) - automated text analysis

**Layer 3 (V1.5, $0.01/node):** Rubric LLM judge (13 CRPG abilities, user toggle) - targeted quality feedback

**Layer 4 (V2.5, $0.02/comparison):** Pairwise Elo ranking (character ranking, template A/B testing) - nice-to-have

**Total annual cost:** ~$1,100 for 1M nodes production (très acceptable)

**Key innovations:**
- **Zero-cost validation** via deterministic tests + baselines (Layers 1-2)
- **Dual-tier baselines** enable character-specific voice validation + genre-level quality benchmarking
- **Planescape: Torment baseline** provides marketing-ready quality badge ("PS:T Quality: 8.6/10 ⭐")
- **Selective LLM judging** (user toggle, 10% sampling) balances quality feedback with cost

**Success criteria:**
- 80%+ generated nodes within baseline thresholds (slop ±2, vocab ±0.5)
- <20% manual revision rate (Marc accepts 80%+ as-is)
- 70%+ dialogues achieve "PS:T Quality: 8+/10" (marketing benchmark)

This framework enables DialogueGenerator to achieve **professional CRPG narrative quality at scale (1M+ lines)** while preserving Marc's unique character voices and maintaining cost-conscious LLM usage.