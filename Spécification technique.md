# Spécification technique — Outil de génération de dialogues IA

## 0. Objectif

Concevoir une **application autonome** (exécutable Windows) qui :

1. Charge le GDD complet (via l’API Notion ou via les JSON créés par `main.py` / `filter.py`, sans les modifier).

2. Permet à l’utilisateur de **sélectionner** rapidement le contexte (personnages, lieux, scène) et d’enrichir les métadonnées (conditions de compétence, traits, effets).

3. Génère, évalue et valide des nœuds **Yarn** complets en appelant un LLM (cloud ou local).

4. Écrit les fichiers `.yarn` sous `Assets/Dialogues/`, compile‑les et, sur validation, commit Git.

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
│  - YarnRenderer (Jinja2)    │
│  - CompilerWrapper          │
│  - GitService               │
└─────────────────────────────┘
                              │  .yarn
                              ▼
                     Unity + Yarn Spinner
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
  
  - *system prompt* fixe (grammaire Yarn, règles RPG).
  
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

### 3.5 YarnRenderer

- Jinja2 → `.yarn` : entête YAML, balises `<<if>>`, etc.

- Garantit l’échappement des guillemets et caractères spéciaux.

### 3.6 CompilerWrapper

- Appelle `yarnspinner-cli compile`.

- Capture erreurs, renvoie ligne/colonne à la UI.

- **Doute :** faut‑il proposer un *lint* supplémentaire ?

### 3.7 GitService

- `git add .; git commit -m "Generate …"` via libgit2sharp (si .NET) ou subprocess.

- Gestion des credentials (store Windows ou token).

### 3.8 UI/UX

- **Stack :** Qt (PySide6) ou Avalonia (.NET).

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
| 5     | Lit, choisit la nº2                   | YarnRenderer + compile              |
| 6     | **Commit**                            | GitService push                     |
| 7     | Alt‑Tab Unity ➜ Play                  | Import auto, test                   |

Total clics : ≃ 6.

---

## 5. Stockage & versions

| Artefact    | Format        | Emplacement                         |
| ----------- | ------------- | ----------------------------------- |
| Cache GDD   | JSON lines    | `%APPDATA%\RPGGen\cache.jsonl`      |
| Config      | `config.yaml` | même dossier que l'exe              |
| Yarn généré | Texte         | `Assets/Dialogues/generated/*.yarn` |
| Logs        | HTML (rich)   | `logs/YYYY-MM-DD.html`              |

---

## 6. Build & déploiement

- **Langage** : Python 3.12 recommandé.

- **Packaging** : PyInstaller `--onefile --noconsole` (≈ 80 MiB) ou **.NET 8 + pythonnet** si UI Avalonia.

- **CI** : GitHub Actions ➜ build exe, artefact.

- **Mises à jour** : simple remplacement du binaire ; vérifier la compatibilité du cache JSON.

---

## 7. Points d'incertitude / à trancher

1. **UI tech** : PySide6 (licence LGPL, ok) ou Avalonia ?

2. **Cache Notion** : rafraîchir à chaque ouverture ou bouton *Sync* ?

3. **Auto‑critique** dès v1 ou livré plus tard ?

4. **Gestion multi‑utilisateur** (fichiers lock) : pas prévu -> prototypage solo.

5. **Local LLM** : priorité basse, mais prévoir interface asynchrone générique.

---

## 9. Conclusion

Cette architecture isole la **génération IA** dans un outil léger, diff‑friendly, et compatible avec votre pipeline Unity/Yarn existant. Elle laisse la porte ouverte à des extensions (auto‑critique, modèle local) sans perturber `main.py`/`filter.py`. Les choix techniques (JSON pivot, Yarn simplifié, UI desktop autonome) visent à minimiser les clics et les erreurs, tout en préservant votre contrôle rédactionnel.

> **Doutes restants :** quelle granularité pour les presets de contexte ? faut‑il une prévisualisation RichText du Yarn ? Ces points peuvent être affinés lors du premier sprint.
