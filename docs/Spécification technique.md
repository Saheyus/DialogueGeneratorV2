# Spécification technique — Outil de génération de dialogues IA

## 0. Objectif

Concevoir une **application autonome** (exécutable Windows) qui :

1. Charge le GDD complet (via l’API Notion ou via les JSON créés par `main.py` / `filter.py`, sans les modifier).

2. Permet à l’utilisateur de **sélectionner** rapidement le contexte (personnages, lieux, scène) et d’enrichir les métadonnées (conditions de compétence, traits, effets).

3. Génère, évalue et valide des **interactions de dialogue** au format JSON custom (compatible Unity) en appelant un LLM (cloud ou local).

4. Écrit les fichiers JSON sous `Assets/Dialogues/generated/` et, sur validation, commit Git.

5. Laisse intacte la pipeline existante.

---

## 1. Contraintes & hypothèses

| ID  | Contrainte                                     | Commentaire / doute                            |
| --- | ---------------------------------------------- | ---------------------------------------------- |
| C1  | Windows 10, lancement via double‑clic `.exe`   | Emballage par PyInstaller ou .NET 8 AOT ?      |
| C2  | Scripts `main.py`, `filter.py` inaltérés       | Le nouvel outil lit leurs dossiers de sortie.  |
| C3  | IA cloud (GPT‑4o) mais option GPU local (5090) | Insérer un backend abstrait.                   |
| C4  | Interface « peu de clics »                     | UX minimaliste ; auto‑détection changements.   |
| C5  | Schéma JSON pivot évolutif                     | `additionalProperties:true`, gestion versions. |

---

## 2. Architecture globale

```
┌────────┐   Notion API    ┌────────────┐
│ GDD DB │───────────────▶│ Extracteurs │ (scripts existants)
└────────┘                 └────────────┘
                              │  JSON
                              ▼
┌─────────────────────────────┐
│  Nouvelle appli (_generator_)│
│  - UI Qt / WinUI3           │
│  - ContextBuilder           │
│  - PromptEngine             │
│  - LLMClient (pluggable)    │
│  - JSON Exporter            │
│  - GitService               │
└─────────────────────────────┘
                              │  .json
                              ▼
                     Unity (format JSON custom)
```

---

## 3. Modules détaillés

### 3.1 ContextBuilder

- Lit le **cache JSON** produit par `main.py` (lore, personnages, lieux).

- Filtre par **UI à facettes** : listes déroulantes Personnage / Lieu / Quête.

- Regroupe les blocs pertinents et prépare un **contexte GDD** dont la taille maximale en tokens est configurable par l'utilisateur (par défaut 50k tokens), permettant un équilibre entre richesse du contexte et coût/performance du LLM.

- **Question :** faut‑il mémoriser des « presets de contexte » ?

### 3.2 PromptEngine

- Combine :
  
  - *system prompt* fixe (format JSON custom Unity, règles RPG).
  
  - *context* (output ContextBuilder).
  
  - *instruction* saisie utilisateur (but de la scène, ton, nombre de variants).

- Supporte **templates** paramétrables (YAML).

### 3.3 LLMClient

Interface `IGenerator` :

```python
async def generate_variants(prompt: str, k:int) -> list[str]
```

Implémentations :

- **OpenAIClient** (`openai>=1.15`).

- **OllamaClient** ou **vLLM** local (future).

### 3.4 AutoCritique (option v2)

- Ragas ou GPT‑4o‑critic.

- Score > threshold sinon relance (max rounds configurable).

### 3.5 JSON Exporter

- Exporte les interactions au format JSON custom Unity.

- Utilise le modèle Pydantic `Interaction` pour garantir la validité du schéma.

- Les interactions sont stockées directement en JSON dans `data/interactions/`.

### 3.6 (Legacy) YarnRenderer

- **Note :** Conservé pour compatibilité, mais Unity utilise maintenant directement le format JSON.

- Peut être utilisé pour exporter vers Yarn si nécessaire pour d'autres outils.

### 3.7 GitService

- `git add .; git commit -m "Generate …"` via libgit2sharp (si .NET) ou subprocess.

- Gestion des credentials (store Windows ou token).

### 3.8 UI/UX

- **Stack :** ⚠️ Qt (PySide6) déprécié — Utiliser l'interface web React (`npm run dev`) qui est l'interface principale.

- Écrans :
  
  1. Sélection contexte (facettes + search).
  
  2. Paramètres génération (k, modèle, température, tags).
  
  3. Aperçu variants (tabs), diff Markdown.
  
  4. Bouton **Valider** → commit.

- **Raccourci F5** : re‑générer.

---

## 4. Flux utilisateur pas‑à‑pas

| Étape | Action UI                             | Travail interne                     |
| ----- | ------------------------------------- | ----------------------------------- |
| 1     | Ouvrir `.exe`                         | Charge cache JSON (500 ms)          |
| 2     | Sélectionne « Barmaid » + « Taverne » | ContextBuilder renvoie 1 200 tokens |
| 3     | Règle *k=3*, modèle `gpt‑4o-mini`     | PromptEngine compose prompt         |
| 4     | Clique **Generate**                   | LLMClient → 3 variants              |
| 5     | Lit, choisit la nº2                   | Export JSON                        |
| 6     | **Commit**                            | GitService push                     |
| 7     | Alt‑Tab Unity ➜ Play                  | Import auto, test                   |

Total clics : ≃ 6.

---

## 5. Stockage & versions

| Artefact    | Format        | Emplacement                         |
| ----------- | ------------- | ----------------------------------- |
| Cache GDD   | JSON lines    | `%APPDATA%\RPGGen\cache.jsonl`      |
| Config      | `config.yaml` | même dossier que l'exe              |
| Dialogues générés | JSON         | `Assets/Dialogues/generated/*.json` |
| Logs        | HTML (rich)   | `logs/YYYY-MM-DD.html`              |

---

## 6. Build & déploiement

- **Langage** : Python 3.12 recommandé.

- **Packaging** : PyInstaller `--onefile --noconsole` (≈ 80 MiB) ou **.NET 8 + pythonnet** si UI Avalonia.

- **CI** : GitHub Actions ➜ build exe, artefact.

- **Mises à jour** : simple remplacement du binaire ; vérifier la compatibilité du cache JSON.

---

## 7. Points d'incertitude / à trancher

1. **UI tech** : ⚠️ PySide6 déprécié — L'interface web React est maintenant l'interface principale.

2. **Cache Notion** : rafraîchir à chaque ouverture ou bouton *Sync* ?

3. **Auto‑critique** dès v1 ou livré plus tard ?

4. **Gestion multi‑utilisateur** (fichiers lock) : pas prévu -> prototypage solo.

5. **Local LLM** : priorité basse, mais prévoir interface asynchrone générique.

---

## 9. Conclusion

Cette architecture isole la **génération IA** dans un outil léger, diff‑friendly, et compatible avec votre pipeline Unity (format JSON custom). Elle laisse la porte ouverte à des extensions (auto‑critique, modèle local, version web) sans perturber `main.py`/`filter.py`. ⚠️ **Note** : L'interface desktop PySide6 est dépréciée. L'interface web React (`npm run dev`) est maintenant l'interface principale et doit être utilisée pour le développement.

> **Doutes restants :** quelle granularité pour les presets de contexte ? faut‑il une prévisualisation RichText du Yarn ? Ces points peuvent être affinés lors du premier sprint.
