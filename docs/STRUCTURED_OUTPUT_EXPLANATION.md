# Structured Output : Pourquoi des instructions explicites sont nécessaires

## Contexte

Le projet utilise **Structured Output via Function Calling** (tools) d'OpenAI pour générer des dialogues Unity JSON. Le modèle Pydantic `UnityDialogueGenerationResponse` est converti en schéma JSON et passé comme paramètre d'une fonction que l'IA doit appeler.

## Ce que le Structured Output garantit

✅ **Structure JSON** : Champs, types, champs requis  
✅ **Conformité au schéma** : L'IA ne peut pas générer des champs qui n'existent pas dans le schéma  
✅ **Types corrects** : Les valeurs respectent les types définis (string, int, bool, etc.)

## Ce que le Structured Output NE garantit PAS

❌ **Logique métier** : "Un seul nœud", "réplique PNJ + choix joueur"  
❌ **Formats spécifiques** : Même si décrits dans `Field.description`, l'IA peut les ignorer  
❌ **Contexte métier** : Qui est le speaker, qui est le joueur  
❌ **Qualité du contenu créatif** : Le structured output ne garantit pas la pertinence narrative

## Exemple concret

### Sans instructions explicites

Le schéma Pydantic définit :
```python
title: str = Field(..., description="Titre descriptif du dialogue")
node: UnityDialogueNodeContent = Field(..., description="Un seul nœud")
```

L'IA pourrait générer :
- Un titre générique : "Dialogue"
- Plusieurs nœuds (en essayant de contourner le schéma)
- Un format de test incorrect : "Raison:8" au lieu de "Raison+Rhétorique:8"

### Avec instructions explicites

Les instructions dans le prompt guident l'IA sur :
- La logique métier : "UN SEUL nœud = réplique PNJ + choix joueur"
- Les formats spécifiques : "AttributeType+SkillId:DD"
- Le contexte : "Speaker = npc_speaker_id, Choix = options du joueur"

## Optimisations apportées

### ❌ Supprimé (redondant avec le schéma)

- **"Ne génère PAS d'IDs de nœuds"** → Ces champs n'existent pas dans le schéma, l'IA ne peut pas les générer
- **"Utilise nextNode pour la navigation"** → `nextNode` n'existe pas dans le modèle Pydantic, c'est un champ technique ajouté par l'application

### ✅ Conservé (nécessaire pour la logique métier)

- **"Génère UN SEUL nœud"** → Logique métier non garantie par le schéma
- **"Format AttributeType+SkillId:DD"** → Format spécifique, même si décrit dans Field.description
- **"Speaker = npc_speaker_id"** → Contexte métier dynamique
- **"Choix = options du joueur"** → Logique métier

## Références

- [OpenAI Structured Outputs Documentation](https://platform.openai.com/docs/guides/structured-outputs)
- [Function Calling vs JSON Schema](https://platform.openai.com/docs/guides/function-calling)

## Conclusion

Le Structured Output garantit la **structure**, mais pas la **sémantique**. Les instructions explicites dans le prompt guident l'IA sur :
1. La logique métier (ce que le schéma ne peut pas exprimer)
2. Les formats spécifiques (même si décrits dans Field.description)
3. Le contexte dynamique (qui est le speaker, qui est le joueur)

Ces instructions sont **complémentaires** au Structured Output, pas redondantes.


