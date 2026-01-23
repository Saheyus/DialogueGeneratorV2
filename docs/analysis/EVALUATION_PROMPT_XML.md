# Évaluation de la Construction du Prompt XML

## Vue d'ensemble

Cette évaluation analyse la structure XML actuelle du prompt envoyé au LLM, en se concentrant sur :
- La qualité de la structure hiérarchique
- L'organisation et la lisibilité
- L'efficacité pour la génération de dialogues
- Les points d'amélioration potentiels

## Structure Actuelle

### Architecture Générale

Le prompt XML suit une structure hiérarchique en 6 sections principales :

```xml
<prompt>
  <contract>...</contract>              <!-- Section 0 : Contrat global -->
  <technical>...</technical>            <!-- Section 1 : Instructions techniques -->
  <context>...</context>                <!-- Section 2A : Contexte GDD -->
  <narrative_guides>...</narrative_guides>  <!-- Section 2B : Guides narratifs -->
  <vocabulary>...</vocabulary>           <!-- Section 2C : Vocabulaire -->
  <scene_instructions priority="high">...</scene_instructions>  <!-- Section 3 : Instructions de scène -->
</prompt>
```

**✅ Points forts** :
- Séparation claire des responsabilités par section
- Ordre logique (contrat → technique → contexte → guides → vocabulaire → instructions)
- Hiérarchie limitée à 3-4 niveaux (conforme aux bonnes pratiques)
- Utilisation minimale d'attributs (seulement `priority` et `name`)

## Analyse par Section

### 1. Section `<contract>` (Section 0)

**Structure actuelle** :
```xml
<contract>
  <author_directives>...</author_directives>
  <narrative_tone>...</narrative_tone>
  <priority_rules>...</priority_rules>
  <output_format>...</output_format>
</contract>
```

**✅ Points forts** :
- Contrat explicite avec règles de priorité claires
- Format de sortie bien défini
- Directives d'auteur séparées du ton narratif

**⚠️ Points d'amélioration** :
- Les règles de priorité sont en texte libre, pourraient être plus structurées
- Le format de sortie mélange instructions métier et format technique

**Recommandation** : Considérer une structure plus granulaire :
```xml
<contract>
  <author_directives>...</author_directives>
  <narrative_tone>...</narrative_tone>
  <priority_rules>
    <rule priority="1">Instructions de scène (SECTION 3)</rule>
    <rule priority="2">Directives d'auteur (SECTION 0)</rule>
    <rule priority="3">System prompt</rule>
  </priority_rules>
  <output_format>
    <constraint>UN SEUL nœud de dialogue</constraint>
    <constraint>Pas de séquence de nœuds</constraint>
  </output_format>
</contract>
```

### 2. Section `<technical>` (Section 1)

**Structure actuelle** :
```xml
<technical>
  <generation_instructions>...</generation_instructions>
  <available_skills>...</available_skills>
  <available_traits>...</available_traits>
</technical>
```

**✅ Points forts** :
- Instructions techniques clairement séparées du contexte narratif
- Liste des compétences et traits disponibles bien identifiée
- Format des tests d'attributs explicite

**⚠️ Points d'amélioration** :
- Les instructions de génération sont en texte libre avec listes à puces
- Les compétences/traits sont en texte brut avec troncature ("et 83 autres compétences")
- Pas de structure pour les contraintes de nombre de choix

**Recommandation** : Structurer davantage :
```xml
<technical>
  <generation_instructions>
    <speaker>PNJ_ID</speaker>
    <player>URESAIR</player>
    <attribute_test_format>AttributeType+SkillId:DD</attribute_test_format>
    <choices>
      <mode>free</mode>
      <min>2</min>
      <max>8</max>
    </choices>
  </generation_instructions>
  <available_skills count="133">...</available_skills>
  <available_traits count="40">...</available_traits>
</technical>
```

### 3. Section `<context>` (Section 2A)

**Structure actuelle** :
```xml
<context>
  <characters>
    <character name="...">
      <identity>...</identity>
      <characterization>...</characterization>
      <voice>...</voice>
      <background>...</background>
      <mechanics>...</mechanics>
      <summary>...</summary>
      <section title="...">...</section>  <!-- Sections génériques -->
    </character>
  </characters>
  <locations>...</locations>
  <items>...</items>
  <!-- etc. -->
</context>
```

**✅ Points forts** :
- Hiérarchie claire : catégorie → item → section
- Tags sémantiques pour les sections courantes (identity, characterization, voice, etc.)
- Support des sections génériques avec attribut `title`
- Nom de l'item en attribut (accessible sans parsing du contenu)

**❌ Problèmes identifiés** :

1. **Contenu JSON inclus dans le XML** :
   ```xml
   <characterization>{"Faiblesse": "...", "Compulsion": "...", "Désir": "..."}</characterization>
   ```
   - Le JSON est difficile à parser pour le LLM
   - Double structure (XML + JSON) crée de la confusion
   - Perte de la structure hiérarchique XML

2. **Section `<section title="INFORMATIONS">` trop générique** :
   - Mélange de nombreux champs différents (Nom, Alias, Espèce, Relations, etc.)
   - Pas de structure sémantique claire
   - Difficile pour le LLM de distinguer les différents types d'informations

3. **Profondeur variable** :
   - Certains items ont des sections structurées (identity, characterization)
   - D'autres ont une section générique avec tout le contenu
   - Incohérence dans la structure

**Recommandations** :

1. **Déstructurer le JSON en XML** :
   ```xml
   <characterization>
     <weakness>...</weakness>
     <compulsion>...</compulsion>
     <desire>...</desire>
   </characterization>
   ```

2. **Remplacer `<section title="INFORMATIONS">` par des tags sémantiques** :
   ```xml
   <character name="...">
     <identity>
       <name>...</name>
       <alias>...</alias>
       <species>...</species>
       <age>...</age>
     </identity>
     <metadata>
       <occupation>...</occupation>
       <communities>...</communities>
       <sprint>...</sprint>
     </metadata>
     <relationships>
       <relation name="..." type="...">...</relation>
     </relationships>
   </character>
   ```

3. **Normaliser la structure** :
   - Tous les items devraient suivre la même structure de base
   - Utiliser des tags sémantiques plutôt que des sections génériques
   - Éviter le mélange de formats (JSON dans XML)

### 4. Section `<narrative_guides>` (Section 2B)

**Structure actuelle** :
```xml
<narrative_guides>
  [GUIDE DE DIALOGUE]
  ...
  [GUIDE NARRATIF]
  ...
</narrative_guides>
```

**❌ Problèmes majeurs** :

1. **Contenu en texte brut** :
   - Pas de structure XML pour les guides
   - Format Markdown/textuel mélangé dans le XML
   - Difficile pour le LLM de distinguer les différentes parties

2. **Pas de hiérarchie** :
   - Tous les guides sont au même niveau
   - Pas de distinction entre guide de dialogue et guide narratif
   - Pas de sections (habillage, technique, interactivité, etc.)

**Recommandation** : Structurer les guides :
```xml
<narrative_guides>
  <dialogue_guide>
    <habillage>
      <language_level>...</language_level>
      <complexity>...</complexity>
      <structure>...</structure>
    </habillage>
    <technique>
      <character_limits>...</character_limits>
      <formatting>...</formatting>
    </technique>
    <interactivity>
      <choices>...</choices>
      <branching>...</branching>
    </interactivity>
  </dialogue_guide>
  <narrative_guide>
    <themes>...</themes>
    <tone>...</tone>
    <style>...</style>
  </narrative_guide>
</narrative_guides>
```

### 5. Section `<vocabulary>` (Section 2C)

**Structure actuelle** :
```xml
<vocabulary>
  [VOCABULAIRE ALTEIR]
  Mondialement:
  - Terme 1: Définition
  - Terme 2: Définition
  ...
</vocabulary>
```

**⚠️ Points d'amélioration** :
- Format texte avec marqueurs (`Mondialement:`, `Régionalement:`)
- Pas de structure XML pour les termes
- Difficile de référencer un terme spécifique

**Recommandation** : Structurer le vocabulaire :
```xml
<vocabulary>
  <scope level="mondial">
    <term name="Terme 1">Définition</term>
    <term name="Terme 2">Définition</term>
  </scope>
  <scope level="regional">
    <term name="Terme 3">Définition</term>
  </scope>
</vocabulary>
```

### 6. Section `<scene_instructions>` (Section 3)

**Structure actuelle** :
```xml
<scene_instructions priority="high">
  Brief de scène local avec instructions spécifiques...
</scene_instructions>
```

**✅ Points forts** :
- Attribut `priority="high"` bien utilisé
- Section claire et concise
- Positionnée en dernier (priorité visuelle)

**✅ Pas de changement nécessaire** : Cette section est bien conçue.

## Problèmes Transversaux

### 1. Mélange de Formats

**Problème** : Le XML contient du JSON, du Markdown et du texte libre :
- JSON dans `<characterization>` : `{"Faiblesse": "...", "Compulsion": "..."}`
- Markdown dans `<narrative_guides>` : `**Niveau de langue**`, `• - Registre variable`
- Texte libre dans plusieurs sections

**Impact** :
- Le LLM doit parser plusieurs formats différents
- Perte de la cohérence structurelle
- Difficulté à référencer des éléments spécifiques

**Solution** : Unifier tout en XML structuré.

### 2. Profondeur et Complexité

**Problème** : La section `<context>` peut être très profonde :
```
<prompt> (niveau 1)
  <context> (niveau 2)
    <characters> (niveau 3)
      <character> (niveau 4)
        <characterization> (niveau 5)
          {"Faiblesse": "...", ...} (contenu JSON)
```

**Impact** :
- Le LLM peut avoir du mal à suivre la hiérarchie profonde
- Risque de perte de contexte dans les sections imbriquées
- Parsing complexe pour extraire des informations spécifiques

**Solution** : Limiter la profondeur à 4 niveaux maximum, aplatir si nécessaire.

### 3. Redondance et Verbosité

**Problème** : Certaines informations sont répétées ou trop verbeuses :
- Les compétences listées avec troncature ("et 83 autres compétences")
- Les guides narratifs complets à chaque fois
- Le vocabulaire peut être très long

**Impact** :
- Augmentation du nombre de tokens
- Risque de dépassement de contexte
- Information diluée dans la verbosité

**Solution** : 
- Référencer plutôt que dupliquer (ex: "Utilise les compétences de la liste standard")
- Filtrer le vocabulaire selon le contexte
- Option de guides abrégés

### 4. Manque de Métadonnées Structurelles

**Problème** : Pas d'informations sur la structure elle-même :
- Pas de version du format XML
- Pas d'indication de la taille/complexité des sections
- Pas de métadonnées sur les items (source, date, etc.)

**Impact** :
- Difficile de faire évoluer le format
- Pas de validation de structure possible
- Pas de traçabilité

**Solution** : Ajouter des métadonnées :
```xml
<prompt version="1.0" total_tokens="...">
  <context token_count="...">
    <characters count="...">
      <character name="..." source="GDD" last_updated="...">
```

## Évaluation Globale

### Points Forts ✅

1. **Séparation claire des responsabilités** : Chaque section a un rôle bien défini
2. **Hiérarchie logique** : Ordre de priorité respecté dans la structure
3. **Tags sémantiques** : Utilisation de balises XML significatives (identity, characterization, etc.)
4. **Échappement correct** : Gestion appropriée des caractères spéciaux
5. **Attributs minimaux** : Utilisation parcimonieuse et pertinente des attributs

### Points Faibles ❌

1. **Mélange de formats** : JSON, Markdown et texte libre dans le XML
2. **Structure incohérente** : Sections génériques vs tags sémantiques
3. **Profondeur excessive** : Hiérarchie trop complexe dans certains cas
4. **Verbosite** : Contenu redondant ou trop long
5. **Manque de structure** : Guides et vocabulaire en texte brut

### Score Global : 6.5/10

**Justification** :
- ✅ Architecture solide (8/10)
- ⚠️ Cohérence structurelle (5/10)
- ⚠️ Efficacité pour le LLM (6/10)
- ✅ Maintenabilité (7/10)
- ❌ Optimisation tokens (5/10)

## Recommandations Prioritaires

### Priorité 1 : Déstructurer le JSON dans le contexte

**Impact** : Élevé - Améliore significativement la lisibilité pour le LLM
**Effort** : Moyen - Nécessite de modifier `serialize_context_to_xml()`

**Action** : Convertir les structures JSON en XML hiérarchique :
```xml
<!-- Avant -->
<characterization>{"Faiblesse": "...", "Compulsion": "..."}</characterization>

<!-- Après -->
<characterization>
  <weakness>...</weakness>
  <compulsion>...</compulsion>
  <desire>...</desire>
</characterization>
```

### Priorité 2 : Structurer les guides narratifs

**Impact** : Élevé - Améliore la navigation et la référence
**Effort** : Moyen - Nécessite de modifier `NarrativeGuidesService.format_for_prompt()`

**Action** : Convertir le texte Markdown en structure XML :
```xml
<narrative_guides>
  <dialogue_guide>
    <habillage>
      <language_level>...</language_level>
      <complexity>...</complexity>
    </habillage>
  </dialogue_guide>
</narrative_guides>
```

### Priorité 3 : Normaliser la section "INFORMATIONS"

**Impact** : Moyen - Améliore la cohérence structurelle
**Effort** : Élevé - Nécessite de mapper tous les champs GDD vers des tags XML

**Action** : Remplacer `<section title="INFORMATIONS">` par des tags sémantiques :
```xml
<identity>
  <name>...</name>
  <alias>...</alias>
  <species>...</species>
</identity>
<metadata>
  <occupation>...</occupation>
  <communities>...</communities>
</metadata>
```

### Priorité 4 : Structurer le vocabulaire

**Impact** : Faible - Amélioration marginale
**Effort** : Faible - Structure simple à implémenter

**Action** : Convertir le format texte en XML :
```xml
<vocabulary>
  <scope level="mondial">
    <term name="...">...</term>
  </scope>
</vocabulary>
```

## Conclusion

La structure XML actuelle est **solide dans son architecture globale** mais souffre de **problèmes de cohérence structurelle** et de **mélange de formats**. Les principales améliorations à apporter sont :

1. **Unifier les formats** : Tout en XML structuré, pas de JSON/Markdown
2. **Normaliser la structure** : Tags sémantiques partout, pas de sections génériques
3. **Limiter la profondeur** : Maximum 4 niveaux, aplatir si nécessaire
4. **Optimiser la verbosité** : Référencer plutôt que dupliquer

Ces améliorations rendront le prompt **plus lisible pour le LLM**, **plus facile à maintenir** et **plus efficace en tokens**.
