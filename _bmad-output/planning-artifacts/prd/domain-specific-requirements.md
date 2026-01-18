# Domain-Specific Requirements

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
