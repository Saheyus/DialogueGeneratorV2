# Analyse des niveaux de prompts - Vérification cohérence et hiérarchie

## Architecture actuelle

Le système utilise 3 niveaux de prompts :

1. **System Prompt** (prompt système)
   - Rôle : Définit le rôle de l'IA et les règles générales de dialogue
   - Niveau : Système (passé séparément au LLM)
   - Source : `prompt_engine.py::_get_default_system_prompt()` ou `system_prompt_override`
   - Portée : Global (réutilisable)

2. **Author Profile** (profil auteur)
   - Rôle : Style d'écriture global réutilisable entre scènes
   - Niveau : Prompt utilisateur (section "--- DIRECTIVES D'AUTEUR (GLOBAL) ---")
   - Source : `author_profile_templates.json` ou saisie manuelle
   - Portée : Global (réutilisable entre scènes)

3. **Scene Instructions** (instructions de scène)
   - Rôle : Instructions spécifiques à une scène (ton, rythme, objectifs)
   - Niveau : Prompt utilisateur (section "--- BRIEF DE SCÈNE (LOCAL) ---")
   - Source : `scene_instruction_templates.json` (ajouté aux `user_instructions`) ou saisie manuelle
   - Portée : Local (spécifique à la scène)

## Problèmes identifiés

### 1. REDONDANCE : Duplication de la "GUIDANCE NARRATIVE" dans `build_unity_dialogue_prompt()`

**Localisation** : `prompt_engine.py`, lignes 363-389

**Problème** : La méthode `build_unity_dialogue_prompt()` inclut une "GUIDANCE NARRATIVE" codée en dur qui duplique le contenu du system prompt par défaut :

```python
# Guidance narrative (avant les instructions techniques)
prompt_parts.append("--- GUIDANCE NARRATIVE ---")
prompt_parts.append("Tu es un dialoguiste expert en jeux de rôle narratifs...")
# RÈGLES DE CARACTÉRISATION
# RÈGLES DE RYTHME
# RÈGLES DE PROGRESSION NARRATIVE
# RÈGLES DE TON
```

Cette guidance :
- Duplique le system prompt par défaut (`_get_default_system_prompt()`)
- Est codée en dur alors qu'elle devrait utiliser le `system_prompt_template` du PromptEngine
- N'est pas utilisée si un `system_prompt_override` est fourni (car il remplace le system prompt, mais cette guidance reste dans le prompt user)

**Impact** :
- Redondance inutile (consomme des tokens)
- Risque de contradiction si le system prompt override contient des règles différentes
- Mauvaise séparation des responsabilités (règles générales dans le prompt user au lieu du system prompt)

### 2. CONTRADICTION POTENTIELLE : Règles de rythme entre niveaux

**Problème** : Les règles de rythme peuvent entrer en contradiction entre :

- **System prompt** : Règles générales de rythme (lignes 66-70 de `prompt_engine.py`)
  - "Varie la longueur des répliques pour créer du rythme"
  - "Les répliques courtes créent de la tension, les longues développent l'émotion"
  - "Évite les monologues trop longs (max 3-4 phrases par réplique)"

- **Scene instructions** : Règles spécifiques de rythme (ex: `scene_instruction_templates.json`)
  - Template "action_scene" : "Privilégie les répliques COURTES et PERCUTANTES (1-2 phrases maximum)"
  - Template "intimate_moment" : "Privilégie les répliques LONGUES et DÉVELOPPÉES (2-4 phrases)"

- **Author profile** : Style général qui peut aussi mentionner le rythme
  - Template "minimal" : "Les répliques courtes sont la norme"
  - Template "literary" : "La longueur est un paramètre expressif, modulé par la situation"

**Analyse** : Les contradictions sont **acceptables** car :
- Les scene instructions sont plus spécifiques (prévalent sur le général)
- Les author profiles définissent une préférence de style (pas une règle absolue)

**Mais** : Le problème est que ces règles sont mélangées sans hiérarchie claire dans le prompt final.

### 3. PLACEMENT INCORRECT : Règles générales dans le prompt user

**Problème** : Dans `build_unity_dialogue_prompt()`, la "GUIDANCE NARRATIVE" (règles générales) est placée dans le prompt user alors qu'elle devrait être dans le system prompt.

**Hiérarchie attendue** :
- **System prompt** : Règles générales, rôle de l'IA, principes de base
- **Prompt user** : Contexte spécifique, instructions de scène, style d'auteur

**Actuellement** : Les règles générales sont dans les deux, ce qui crée une redondance.

### 4. REDONDANCE : Règles de caractérisation dupliquées

**Problème** : Les règles de caractérisation apparaissent dans plusieurs endroits :

1. System prompt (`_get_default_system_prompt()`, lignes 59-64)
2. Guidance narrative dans `build_unity_dialogue_prompt()` (lignes 369-373)
3. Templates de `prompt_templates.json` (qui semblent inutilisés actuellement)

**Impact** : Redondance inutile.

## Recommandations

### 1. Supprimer la "GUIDANCE NARRATIVE" codée en dur de `build_unity_dialogue_prompt()`

**Action** : Supprimer les lignes 363-389 de `prompt_engine.py` (la section "GUIDANCE NARRATIVE").

**Justification** : Ces règles doivent être dans le system prompt, pas dans le prompt user. Si un `system_prompt_override` est fourni, il doit contenir ces règles. Sinon, le system prompt par défaut (`_get_default_system_prompt()`) est utilisé.

### 2. Clarifier la hiérarchie des règles de rythme

**Recommandation** : Documenter explicitement la hiérarchie dans les commentaires :

- **System prompt** : Règles générales (principes de base)
- **Author profile** : Préférences de style (modulation)
- **Scene instructions** : Règles spécifiques (prévalent sur les autres)

**Action** : Ajouter un commentaire dans `build_unity_dialogue_prompt()` expliquant que :
- Les scene instructions (dans `user_instructions`) peuvent surcharger les règles générales
- L'author profile module le style sans imposer de règles absolues
- Les règles du system prompt sont des principes généraux

### 3. Vérifier l'utilisation de `prompt_templates.json`

**Observation** : Le fichier `prompt_templates.json` contient des templates similaires aux scene instructions mais avec des prompts complets (incluant toutes les règles). Ce fichier semble inutilisé.

**Action** : Vérifier si ce fichier est utilisé quelque part. S'il ne l'est pas, considérer le supprimer ou documenter son rôle.

### 4. Structure du prompt final (IMPLÉMENTÉE)

**Structure actuelle** : Le prompt est organisé en 4 sections claires :

```
### SECTION 0. CONTRAT GLOBAL (tout en haut)
- DIRECTIVES D'AUTEUR (GLOBAL) - Style réutilisable
- TON NARRATIF - Résumé (tags narratifs)
- RÈGLES DE PRIORITÉ - Hiérarchie des instructions
- FORMAT DE SORTIE / INTERDICTIONS - Contraintes techniques

### SECTION 1. INSTRUCTIONS TECHNIQUES (NORMATIVES)
- INSTRUCTIONS DE GÉNÉRATION - Règles techniques Unity
- COMPÉTENCES DISPONIBLES
- TRAITS DISPONIBLES

### SECTION 2. CONTEXTE (ZONE FRAGILE ASSUMÉE)
- CONTEXTE GÉNÉRAL DE LA SCÈNE - Personnages, lieux, objets
- LIEU DE LA SCÈNE
- VOCABULAIRE ET GUIDES NARRATIFS (si nécessaires)

### SECTION 3. INSTRUCTIONS DE SCÈNE (PRIORITÉ EFFECTIVE)
- BRIEF DE SCÈNE (LOCAL) - Instructions spécifiques (prévalent sur tout)
```

**Principe** : Aucune information indispensable ne doit apparaître uniquement dans la SECTION 2 (contexte fragile). Les instructions critiques sont dans les sections 0, 1 et 3.

## Hiérarchie recommandée des informations

### System Prompt (niveau système)
- ✅ Rôle de l'IA : "Tu es un dialoguiste expert..."
- ✅ Règles générales de caractérisation (principes de base)
- ✅ Règles générales de progression narrative
- ✅ Règles générales de ton (adaptation au contexte)
- ✅ Format de sortie (si applicable)
- ❌ Règles de rythme spécifiques (devrait être dans scene instructions ou author profile)
- ❌ Instructions de scène (trop spécifiques)

### Author Profile (niveau global, dans prompt user)
- ✅ Identité d'écriture (position esthétique)
- ✅ Style général (dense, concis, littéraire, etc.)
- ✅ Préférences de rythme (modulation, pas règles absolues)
- ✅ Bonnes pratiques d'écriture
- ❌ Règles techniques (format, structure)
- ❌ Instructions spécifiques à une scène

### Scene Instructions (niveau local, dans prompt user)
- ✅ Ton spécifique de la scène
- ✅ Rythme spécifique (courtes/longues répliques selon le contexte)
- ✅ Objectifs narratifs de la scène
- ✅ Instructions de structure (si nécessaire)
- ❌ Règles générales (doivent être dans system prompt)
- ❌ Style global (doit être dans author profile)

## Actions proposées

1. ✅ **Supprimer la GUIDANCE NARRATIVE codée en dur** dans `build_unity_dialogue_prompt()` - **FAIT**
2. ✅ **Clarifier dans les commentaires** la hiérarchie des règles (system > author > scene) - **FAIT**
3. **Vérifier et nettoyer** `prompt_templates.json` (s'il est inutilisé) - **À FAIRE** : Le fichier est exposé via l'API mais n'est pas utilisé dans le frontend. C'est un fichier obsolète qui pourrait être supprimé ou documenté comme tel.
4. **Améliorer la documentation** du rôle de chaque niveau de prompt - **FAIT** (ce document)

## Corrections appliquées

### Suppression de la GUIDANCE NARRATIVE codée en dur

**Fichier modifié** : `prompt_engine.py`

**Changement** : Suppression des lignes 363-389 qui dupliquaient le system prompt dans le prompt user.

**Impact** :
- ✅ Élimination de la redondance (réduction des tokens)
- ✅ Clarification de la séparation system prompt / prompt user
- ✅ Les règles générales sont maintenant uniquement dans le system prompt (ou system_prompt_override)
- ✅ Ajout de commentaires explicatifs sur la hiérarchie des règles

