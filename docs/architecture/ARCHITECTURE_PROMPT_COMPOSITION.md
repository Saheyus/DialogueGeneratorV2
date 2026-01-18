# Analyse Architecturale : Système de Composition des Prompts

## Vue d'ensemble

Le système de composition des prompts est composé de plusieurs couches :
1. **PromptEngine** : Construction des prompts finaux
2. **ContextBuilder** : Construction du contexte GDD
3. **ContextOrganizer** : Organisation des champs en sections
4. **ContextFieldDetector** : Détection automatique des champs disponibles

## Problèmes Architecturaux Identifiés

### 1. Duplication de Code Critique

**Problème** : `build_prompt()` et `build_unity_dialogue_prompt()` dupliquent la logique d'injection de vocabulaire et guides narratifs.

```python
# Code dupliqué dans build_prompt() (lignes 126-149)
if vocabulary_min_importance:
    try:
        from services.vocabulary_service import VocabularyService
        vocab_service = VocabularyService()
        # ... logique d'injection

# Code identique dans build_unity_dialogue_prompt() (lignes 255-280)
if vocabulary_min_importance:
    try:
        from services.vocabulary_service import VocabularyService
        vocab_service = VocabularyService()
        # ... même logique
```

**Impact** :
- Maintenance difficile : toute modification doit être faite en deux endroits
- Risque d'incohérence entre les deux méthodes
- Violation du principe DRY (Don't Repeat Yourself)

**Recommandation** : Extraire la logique d'injection dans des méthodes privées réutilisables.

---

### 2. Responsabilités Mélangées dans PromptEngine

**Problème** : `PromptEngine` fait trop de choses :
- Construction de la structure du prompt
- Injection de services externes (vocabulaire, guides narratifs)
- Comptage de tokens
- Formatage de sections

**Impact** :
- Difficile à tester (dépendances multiples)
- Difficile à étendre (ajouter un nouveau type d'injection nécessite modifier PromptEngine)
- Violation du principe de responsabilité unique (SRP)

**Recommandation** : Séparer en :
- `PromptBuilder` : Construction de la structure
- `PromptEnricher` : Injection de contenu enrichi (vocabulaire, guides)
- `TokenCounter` : Comptage de tokens (déjà partiellement séparé)

---

### 3. ContextBuilder : Classe Trop Grosse (God Object)

**Problème** : `ContextBuilder` fait :
- Chargement des fichiers GDD (900+ lignes)
- Extraction de données par nom
- Formatage de champs
- Organisation du contexte
- Gestion du dialogue précédent
- Troncature de texte
- Comptage de tokens

**Impact** :
- Classe difficile à maintenir (900+ lignes)
- Tests complexes (beaucoup de dépendances)
- Violation du SRP

**Recommandation** : Séparer en :
- `GDDLoader` : Chargement des fichiers JSON
- `ElementRepository` : Accès aux éléments par nom
- `ContextFormatter` : Formatage des champs
- `ContextBuilder` : Orchestration uniquement

---

### 4. Injection de Dépendances Manuelle

**Problème** : Importations dynamiques dans les méthodes :

```python
# Dans PromptEngine.build_prompt()
if vocabulary_min_importance:
    try:
        from services.vocabulary_service import VocabularyService
        vocab_service = VocabularyService()
```

**Impact** :
- Difficile à tester (impossible de mocker facilement)
- Couplage fort avec les services
- Pas de gestion d'erreurs claire

**Recommandation** : Utiliser l'injection de dépendances (via constructeur ou DI container).

---

### 5. Configuration Rigide

**Problème** : Les sections du prompt sont codées en dur dans les méthodes :

```python
# Dans build_prompt()
prompt_parts.append("\n--- CADRE DE LA SCÈNE ---")
prompt_parts.append("\n--- CONTEXTE GÉNÉRAL DE LA SCÈNE ---")
prompt_parts.append("\n--- OBJECTIF DE LA SCÈNE (Instruction Utilisateur) ---")
```

**Impact** :
- Impossible de personnaliser l'ordre des sections
- Impossible d'ajouter/supprimer des sections sans modifier le code
- Pas de support pour différents formats de prompt

**Recommandation** : Utiliser un système de templates ou de configuration.

---

### 6. Gestion d'Erreurs Incohérente

**Problème** : Mélange de `try/except` silencieux et de logging :

```python
try:
    from services.vocabulary_service import VocabularyService
    # ...
except Exception as e:
    logger.warning(f"Erreur lors de l'injection du vocabulaire: {e}")
    # Continue silencieusement
```

**Impact** :
- Erreurs masquées
- Comportement imprévisible en cas d'échec
- Difficile à déboguer

**Recommandation** : Stratégie claire de gestion d'erreurs (fail-fast vs graceful degradation).

---

### 7. Pas de Séparation Claire entre Structure et Contenu

**Problème** : La structure du prompt (sections, titres) est mélangée avec le contenu (texte).

**Impact** :
- Impossible de changer le format sans modifier le code
- Difficile de générer différents formats (Markdown, HTML, etc.)

**Recommandation** : Séparer en :
- `PromptStructure` : Définition de la structure (sections, ordre)
- `PromptContent` : Contenu de chaque section

---

### 8. Tests Difficiles

**Problème** : Les classes sont difficiles à tester à cause de :
- Dépendances multiples (services, fichiers)
- Importations dynamiques
- État partagé (variables de classe)

**Impact** :
- Couverture de tests faible
- Tests fragiles
- Difficile de tester des cas isolés

**Recommandation** : Refactoriser pour permettre l'injection de dépendances et l'isolation.

---

## Recommandations Architecturales

### Architecture Proposée

```
┌─────────────────────────────────────────────────────────┐
│              DialogueGenerationService                   │
│              (Orchestrateur principal)                  │
└──────────────────┬──────────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
┌───────▼────────┐   ┌────────▼──────────┐
│ PromptBuilder  │   │  ContextBuilder   │
│                │   │                   │
│ - Structure    │   │ - Orchestration   │
│ - Sections     │   │ - Coordination    │
│ - Formatage    │   └────────┬──────────┘
└───────┬────────┘            │
        │                     │
        │            ┌────────▼──────────┐
        │            │  GDDLoader        │
        │            │  ElementRepo      │
        │            │  ContextFormatter │
        │            └───────────────────┘
        │
┌───────▼────────┐
│ PromptEnricher │
│                │
│ - Vocabulaire  │
│ - Guides       │
│ - Extensions   │
└────────────────┘
```

### Refactoring Prioritaire

1. **Extraire les injections communes** (Priorité : Haute)
   - Créer `_inject_vocabulary()` et `_inject_guides()` dans PromptEngine
   - Réutiliser dans `build_prompt()` et `build_unity_dialogue_prompt()`

2. **Séparer PromptBuilder de PromptEnricher** (Priorité : Haute)
   - `PromptBuilder` : Structure et sections
   - `PromptEnricher` : Enrichissements (vocabulaire, guides)

3. **Refactoriser ContextBuilder** (Priorité : Moyenne)
   - Extraire `GDDLoader`
   - Extraire `ElementRepository`
   - Garder `ContextBuilder` comme orchestrateur

4. **Injection de dépendances** (Priorité : Moyenne)
   - Passer les services en paramètres du constructeur
   - Utiliser un DI container si nécessaire

5. **Système de templates** (Priorité : Basse)
   - Permettre la personnalisation de l'ordre des sections
   - Support pour différents formats

### Exemple de Refactoring

```python
# Avant (duplication)
def build_prompt(...):
    if vocabulary_min_importance:
        try:
            from services.vocabulary_service import VocabularyService
            vocab_service = VocabularyService()
            # ... logique

def build_unity_dialogue_prompt(...):
    if vocabulary_min_importance:
        try:
            from services.vocabulary_service import VocabularyService
            vocab_service = VocabularyService()
            # ... même logique

# Après (réutilisable)
class PromptEnricher:
    def __init__(self, vocab_service: Optional[VocabularyService] = None,
                 guides_service: Optional[NarrativeGuidesService] = None):
        self.vocab_service = vocab_service
        self.guides_service = guides_service
    
    def enrich_with_vocabulary(self, prompt_parts: List[str], 
                               min_importance: str) -> List[str]:
        if not self.vocab_service:
            return prompt_parts
        # ... logique d'injection
        return prompt_parts
    
    def enrich_with_guides(self, prompt_parts: List[str]) -> List[str]:
        if not self.guides_service:
            return prompt_parts
        # ... logique d'injection
        return prompt_parts

class PromptBuilder:
    def __init__(self, enricher: PromptEnricher):
        self.enricher = enricher
    
    def build_prompt(self, ...) -> Tuple[str, int]:
        prompt_parts = [self.system_prompt]
        prompt_parts = self.enricher.enrich_with_vocabulary(
            prompt_parts, vocabulary_min_importance
        )
        # ... reste de la construction
```

## Métriques de Qualité

### Avant Refactoring
- **Lignes de code dupliquées** : ~50 lignes
- **Responsabilités par classe** : 5-7 (trop élevé)
- **Couplage** : Fort (importations dynamiques)
- **Testabilité** : Faible (dépendances multiples)

### Après Refactoring (Objectif)
- **Lignes de code dupliquées** : 0
- **Responsabilités par classe** : 1-2 (idéal)
- **Couplage** : Faible (injection de dépendances)
- **Testabilité** : Élevée (isolation possible)

## Plan d'Action

1. **Phase 1** : Extraire les injections communes (1-2h)
2. **Phase 2** : Créer PromptEnricher (2-3h)
3. **Phase 3** : Refactoriser ContextBuilder (4-6h)
4. **Phase 4** : Injection de dépendances (2-3h)
5. **Phase 5** : Tests et validation (3-4h)

**Total estimé** : 12-18h de refactoring

## Conclusion

L'architecture actuelle fonctionne mais présente des problèmes de maintenabilité et d'extensibilité. Les refactorings proposés amélioreront significativement :
- La maintenabilité (moins de duplication)
- La testabilité (isolation possible)
- L'extensibilité (ajout facile de nouvelles fonctionnalités)
- La lisibilité (responsabilités claires)

