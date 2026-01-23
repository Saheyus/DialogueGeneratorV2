# Analyse : Approche de suggestion de traits/relations - Cas concret

## Scénario testé

**Personnage** : Uresaïr (PJ)  
**Interlocuteur** : Akthar-Neth Amatru, l'Exégète (PNJ)  
**Objectif** : Suggérer des traits pertinents pour des choix PJ dans un dialogue avec Akthar-Neth

## Données extraites de la fiche

### Champ "Relations" de Uresaïr (texte libre)

```
• L'Exégète : Akthar-Neth provoque chez Uresaïr un conflit aigu. Elle reconnaît 
  son érudition et trouve son sacrifice (son bras) touchant mais perturbant. 
  Elle perçoit dans sa vénération une déformation dangereuse de sa propre nature. 
  Elle se raidit à son approche et communique uniquement via intermédiaires ou 
  en encodant des messages dans les fluctuations de son aura, jamais directement.

• Vol Reitar : De l'admiration intellectuelle mutuelle à la collaboration créative, 
  leur relation s'est effondrée après l'échec d'Uresaïr à lui conférer l'immortalité. 
  Sa peur de l'intimité l'a empêchée de révéler les limites de ses pouvoirs, 
  créant une asymétrie fatale. Elle refuse tout contact avec son essence spectrale 
  tout en gardant secrètement ses objets personnels, incapable de faire son deuil.
```

## Résultats des différentes approches

### 1. Approche Pattern Matching Simple ❌

**Ce que ça trouve** :
- ✅ Trouve "conflit" → suggère trait "Intolérant" (confiance 0.7)
- ❌ Trouve "amoureuse" dans le texte (mais avec Vol Reitar, pas présent)
- ❌ Trouve "froide" dans le texte (mais où ? Pas de contexte)

**Problèmes identifiés** :
1. Ne distingue pas qui avec qui
2. Trouve tous les mots-clés sans contexte
3. Suggère des traits basés sur des relations avec des personnages non présents

**Résultat** : ❌ **Non utilisable** - Suggestions incorrectes ou hors contexte

---

### 2. Approche Parsing Amélioré (par personnage) ⚠️

**Ce que ça fait** :
- Parse le texte en sections séparées par "•"
- Extrait le nom du personnage (avant ":")
- Extrait la description de la relation (après ":")
- Filtre pour trouver uniquement la relation avec l'interlocuteur

**Ce que ça trouve** :
- ✅ Extrait 11 relations au total
- ✅ Identifie la relation avec Akthar-Neth : "provoque chez Uresaïr un conflit aigu..."
- ✅ Ignore volontairement Vol Reitar (non présent)

**Suggestions générées** :
1. **Méfiant** (confiance 0.9) : "Conflit aigu avec Akthar-Neth"
2. **Prudent** (confiance 0.85) : "Tension avec Akthar-Neth (se raidit à son approche)"
3. **Humble** (confiance 0.7) : "Rejette la vénération de Akthar-Neth"

**Avantages** :
- ✅ Distingue qui avec qui
- ✅ Filtre correctement (ignore Vol Reitar)
- ✅ Suggestions pertinentes et contextualisées

**Limitations** :
- ⚠️ Parsing fragile : dépend du format exact du texte ("•", ":", structure)
- ⚠️ Ne comprend pas les nuances : "conflit aigu" vs "conflit passif" vs "conflit intérieur"
- ⚠️ Ne comprend pas le contexte émotionnel : "touchant mais perturbant" = ambivalence
- ⚠️ Suggestions limitées : seulement 3 traits basés sur pattern matching simple

**Résultat** : ⚠️ **Utilisable mais limité** - Fonctionne pour ce cas mais fragile

---

### 3. Approche Contexte Textuel (laisser le LLM comprendre) ✅

**Ce que ça fait** :
- Injecte le texte complet des relations dans le prompt
- Indique explicitement l'interlocuteur (Akthar-Neth)
- Laisse le LLM comprendre naturellement le contexte

**Stratégie dans le prompt** :
```
Relations de Uresaïr :
[Texte complet des relations...]

Contexte de la scène : Dialogue avec Akthar-Neth
Le LLM comprendra que seule la relation avec Akthar-Neth est pertinente.
```

**Ce que le LLM comprend naturellement** :
- ✅ La relation avec Akthar-Neth est pertinente (mentionné dans le contexte)
- ✅ La relation avec Vol Reitar n'est pas pertinente (personnage non présent)
- ✅ Les nuances : "conflit aigu", "se raidit", "jamais directement" → traduit en comportement
- ✅ L'ambivalence : "touchant mais perturbant", "rejette mais fascinée" → complexité émotionnelle

**Avantages** :
- ✅ Compréhension naturelle du contexte (qui avec qui)
- ✅ Capture les nuances et l'ambivalence
- ✅ Pas de parsing fragile
- ✅ S'adapte automatiquement au format du texte

**Limitations** :
- ⚠️ Pas de suggestions explicites de traits (le LLM décide seul)
- ⚠️ Moins de contrôle sur les suggestions

**Résultat** : ✅ **Recommandé** - Le LLM comprend mieux que le pattern matching

---

## Conclusion : Quelle approche utiliser ?

### Recommandation : **Approche hybride**

**Pour les relations** (texte libre complexe) :
- **Laisser le LLM comprendre** via contexte textuel
- Injecter le texte complet des relations dans le prompt
- Indiquer explicitement l'interlocuteur
- Le LLM adapte naturellement le ton et les choix

**Pour les traits** (extraction depuis données structurées) :
- **Extraction structurée** si le champ `traits: []` existe dans la fiche JSON
- Si les traits sont dans "Qualités" / "Défauts" → extraction simple
- Injection dans le prompt : `[TRAIT PJ] Impulsif, Loyal`

**Pour les tests/compétences** (données structurées) :
- **Règles heuristiques** basées sur contexte structuré
- Si la fiche mentionne des compétences → suggérer tests utilisant ces compétences
- Si le lieu a une faction → suggérer tests de réputation pour cette faction

**Pour la réputation** (contexte structuré) :
- **Extraction depuis données structurées** (faction du lieu, relations structurées)
- Si le lieu a un champ "Faction" → suggérer condition réputation
- Si les relations sont structurées par personnage → extraction précise

## Cas d'usage : Uresaïr discute avec Akthar-Neth

**Ce qui fonctionne avec l'approche hybride** :

1. **Relations** → Contexte textuel au LLM
   - Le LLM lit : "Akthar-Neth provoque chez Uresaïr un conflit aigu..."
   - Le LLM génère des choix qui reflètent cette tension (se raidit, communication indirecte)

2. **Traits** → Extraction depuis "Qualités" / "Défauts" si disponibles
   - Si la fiche a : `"Qualités": ["Intelligente", "Prudente"]`
   - Injection : `[TRAIT PJ] Intelligent, Prudent`
   - Le LLM adapte les choix pour refléter ces traits

3. **Tests/Compétences** → Règles heuristiques
   - Si la scène mentionne "forcer" → suggérer test Force
   - Si la fiche mentionne des compétences → tests utilisant ces compétences

**Ce qui ne fonctionne PAS** :
- ❌ Pattern matching simple sur texte libre → trop imprécis
- ❌ Suggestion automatique de traits basés sur relations complexes → nécessite compréhension sémantique

## Réponse à la question initiale

> "Si les relations mentionnent une relation froide avec l'interlocuteur, et une relation amoureuse avec un autre personnage non présent, ton approche peut-elle vraiment comprendre ?"

**Réponse** : 

- **Pattern matching simple** : ❌ Non, ne peut pas comprendre
- **Parsing amélioré** : ⚠️ Peut extraire mais fragile et limité
- **Contexte textuel au LLM** : ✅ Oui, le LLM comprend naturellement

**Recommandation finale** : Utiliser le contexte textuel pour les relations complexes, et laisser le LLM comprendre. Pour les autres mécaniques (traits, tests, réputation), utiliser extraction structurée + règles heuristiques quand c'est possible.
