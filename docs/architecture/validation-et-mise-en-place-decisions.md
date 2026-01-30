# Validation et mise en place des décisions architecturales (BMAD)

Ce document décrit comment **valider** et **mettre en place** une décision architecturale globale dans le projet DialogueGenerator, selon le workflow BMAD.

## Est-ce une ADR ?

**Oui.** Dans ce projet, toute décision architecturale majeure est enregistrée sous forme d’**Architecture Decision Record (ADR)** dans `_bmad-output/planning-artifacts/architecture/v10-architectural-decisions-adrs.md`. Chaque ADR a un numéro (ADR-001, ADR-002, …), un **Context**, une **Decision**, un **Technical Design**, des **Constraints**, un **Rationale**, des **Risks** et des **Tests Required**. Une décision déjà prise (ex. revue consultant + 6 points validés par le stakeholder) est **consignée comme une nouvelle ADR** (ex. ADR-008) plutôt que de relancer le workflow « create-architecture » (qui sert à la *découverte* collaborative).

## Validation de la décision

1. **Enregistrement**  
   La décision est rédigée en ADR (même structure que les ADRs existants) et ajoutée au fichier des ADRs. Les « hypothèses » ou décisions associées (ex. les 6 points : propriétaire du document, layout partagé, schemaVersion, Unity, refus sans choiceId, cible perf) sont soit intégrées dans l’ADR, soit dans une section « Décisions associées / Hypothèses » avec référence au document de synthèse (consultant) si celui-ci est déposé dans `docs/architecture/` ou `_bmad-output/`.

2. **Référence**  
   Le document de synthèse (recommandation consultant + 6 points) est conservé comme **référence** (lien depuis l’ADR vers ce doc). Ainsi, l’ADR reste le point d’entrée unique ; le détail reste dans le doc de synthèse.

3. **Sign-off**  
   Validation par le stakeholder (ex. Marc) et le PM : la décision est acceptée comme cible d’architecture. Aucun outil BMAD obligatoire pour ce sign-off ; il peut être informel (validation orale/écrite) ou formalisé dans un compte rendu.

4. **Implementation Readiness (optionnel)**  
   Si besoin, exécuter le workflow BMAD **Implementation Readiness Review** (`[IR]` dans le menu Architect) pour vérifier que PRD, epics et stories sont alignés avec cette nouvelle ADR avant de lancer l’implémentation.

## Mise en place

1. **Documentation**  
   - Mettre à jour les docs qui contredisent la nouvelle cible (ex. `docs/architecture/graph-conversion-architecture.md`, `docs/architecture/state-management-frontend.md`) pour qu’ils pointent vers l’ADR et décrivent l’état cible (document canonique JSON, SoT frontend, layout partagé, etc.).  
   - Déposer le document de synthèse (consultant + 6 points) dans `docs/architecture/` (ex. `pipeline-unity-backend-front-architecture.md`) et le lier depuis l’ADR.

2. **Schéma et références**  
   - Aligner le schéma JSON (ex. `docs/resources/dialogue-format.schema.json`) avec la décision (ex. `schemaVersion`, `choiceId`) dès que le format cible est figé.  
   - Mettre à jour l’index / table des matières de l’architecture si un nouveau document est ajouté.

3. **Plan d’implémentation**  
   - Créer ou mettre à jour les **epics et stories** (workflow BMAD « Create Epics and Stories » ou mise à jour manuelle) pour couvrir : migration des documents (choiceId), nouveau contrat API (GET/PUT documents, layout), frontend (SoT document + projection), validation (draft vs export), etc.  
   - Les critères d’acceptation des stories doivent renvoyer explicitement à l’ADR (ex. « Conformément à ADR-008 »).

4. **Exécution**  
   - Implémentation par le dev (stories, migration, tests).  
   - Les tests (golden, E2E, perf) définis dans l’ADR ou dans le doc de synthèse servent de critères de non-régression et de validation de la mise en place.

## Résumé

| Étape | Action |
|-------|--------|
| **Valider** | Rédiger l’ADR (ex. ADR-008) → déposer le doc de synthèse → sign-off stakeholder/PM → (optionnel) Implementation Readiness |
| **Mettre en place** | Mettre à jour les docs existants → aligner le schéma → créer/mettre à jour epics et stories → implémenter et tester |

L’ADR est le **point d’entrée** pour tout agent (humain ou IA) : une seule source pour « quelle est la décision » ; le document de synthèse (consultant + 6 points) reste la **référence détaillée** pour l’implémentation.
