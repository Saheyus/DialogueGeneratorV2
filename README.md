# DialogueGenerator - Outil de Génération de Dialogues IA

Ce projet vise à créer une application autonome pour assister à la création de dialogues pour jeux de rôle, en s'interfaçant avec des modèles de langage (LLM) et en s'appuyant sur un Game Design Document (GDD) existant.

## 🚀 Démarrage rapide

```bash
npm install          # Première fois seulement
npm run dev          # Lance backend + frontend automatiquement
```

**L'app sera accessible sur http://localhost:3000**

⚠️ **IMPORTANT** : L'application utilise désormais **uniquement l'interface web** (React + FastAPI).
- **Interface Web (PRINCIPALE)** : `npm run dev` — ✅ **Utiliser cette interface**
- ⚠️ **Interface Desktop (DÉPRÉCIÉE)** : `python main_app.py` — Ne plus utiliser, maintenue uniquement pour compatibilité

## Objectif Principal (Rappel des Spécifications)

1.  Charger le GDD (via des fichiers JSON extraits de Notion).
2.  Permettre à l'utilisateur de sélectionner un contexte (personnages, lieux, etc.).
3.  Générer des nœuds de dialogue au format JSON Unity en utilisant un LLM.
4.  Faciliter l'écriture, l'évaluation et la validation de ces dialogues.
5.  S'intégrer avec une pipeline de production de jeu (export JSON Unity, commit Git).

## État Actuel du Projet (Mai 2024)

L'application est en cours de développement actif. Les fonctionnalités suivantes sont implémentées :

*   **Chargement des Données du GDD (`ContextBuilder`)** :
    *   Lecture des fichiers JSON générés par les scripts `filter.py` et `main.py` (situés dans `../GDD/categories/`).
    *   Chargement de `Vision.json` depuis `../import/Bible_Narrative/`.
    *   Les données (personnages, lieux, objets, espèces, communautés, dialogues exemples, structures narratives/macro/micro) sont stockées en mémoire.
*   ⚠️ **Interface Utilisateur Desktop (`PySide6`) — DÉPRÉCIÉE** :
    *   ⚠️ Cette interface est dépréciée. Utiliser l'interface web React à la place (`npm run dev`).
    *   Fenêtre principale avec plusieurs panneaux redimensionnables (`QSplitter`).
    *   **Panneau de Sélection du Contexte (Gauche)** :
        *   Listes distinctes pour les personnages, lieux, objets, espèces, communautés et exemples de dialogues.
        *   Chaque élément des listes peut être coché pour inclusion dans le contexte additionnel.
        *   Champs de filtre textuel pour chaque liste.
        *   Affichage du nombre d'éléments (filtrés/total) pour chaque liste.
    *   **Panneau de Détails (Centre)** :
        *   Affichage des détails complets de l'élément sélectionné dans une liste (format arborescent `QTreeView` avec "Propriété" et "Valeur").
    *   **Panneau de Génération (Droite)** :
        *   Sélection du **Personnage A**, du **Personnage B (Interlocuteur)** et du **Lieu de la Scène** via des listes déroulantes (`QComboBox`) affichant plus d'éléments pour faciliter la sélection.
        *   Champ pour spécifier le nombre de variantes `k` à générer (valeur par défaut : 1).
        *   Case à cocher **"Mode Test (contexte limité)"** :
            *   Si activée, les détails de chaque élément inclus dans le contexte (personnages principaux, lieu, éléments cochés) sont simplifiés : seules certaines clés prioritaires sont conservées et leurs valeurs textuelles sont tronquées (ex: à 30 mots par champ).
        *   Champ de texte multiligne avec l'étiquette **"Instructions spécifiques pour la scène / Prompt utilisateur:"** pour l'objectif et les détails de la scène.
        *   Affichage dynamique de l'**estimation du nombre de mots** du prompt final.
        *   Bouton "Générer le Dialogue".
        *   Un `QTabWidget` pour afficher les variantes de dialogue générées, chaque variante dans un `QTextEdit` en lecture seule.
*   **Moteur de Prompt (`PromptEngine`)** :
    *   Classe `PromptEngine` capable de combiner un *system prompt*, un résumé de contexte (incluant les détails JSON des éléments sélectionnés/cochés), et l'instruction utilisateur pour former un prompt complet.
    *   *System prompt* par défaut basique inclus, avec une brève introduction au format JSON Unity.
*   **Client LLM (`LLMClient`)** :
    *   Interface `IGenerator` définissant la méthode `async generate_variants(prompt, k)`.
    *   `OpenAIClient` : Implémentation utilisant l'API OpenAI (modèle par défaut actuel : `gpt-4o-mini`). Nécessite la variable d'environnement `OPENAI_API_KEY`.
    *   `DummyLLMClient` : Implémentation factice utilisée en fallback si `OpenAIClient` ne peut s'initialiser (ex: clé API manquante) ou pour des tests rapides. Simule la génération de `k` variantes au format JSON Unity.
*   **Flux de Génération Initial** :
    *   La sélection d'éléments dans les listes et les `QComboBox` du panneau de génération, ainsi que la modification de l'instruction utilisateur ou de l'état du "Mode Test", mettent à jour l'estimation du nombre de mots du prompt.
    *   Le bouton "Générer le Dialogue" déclenche :
        *   La récupération du contexte : détails complets (ou simplifiés/tronqués en "Mode Test") des Personnages A & B, du Lieu, et de tous les éléments cochés dans les listes de gauche.
        *   La récupération de l'instruction utilisateur.
        *   La construction du prompt complet via `PromptEngine`.
        *   L'appel asynchrone au client LLM configuré (OpenAI ou Dummy) via `asyncio.run()`.
        *   L'affichage des variantes (ou des messages d'erreur) dans les onglets.

## Structure du Projet

Le code est organisé dans le dossier `DialogueGenerator/` avec les principaux modules suivants :

*   `main_app.py`: Point d'entrée de l'application. Initialise l'application Qt et la fenêtre principale.
*   `__main__.py`: Point d'entrée alternatif pour un lancement en tant que module (ex: `python -m DialogueGenerator`), bien que le lancement direct de `main_app.py` soit privilégié.
*   `config/`: Contient les fichiers de configuration (ex: `llm_config.json`, `context_config.json`, `ui_settings.json`).
*   `core/`: Logique métier principale, indépendante de l'interface utilisateur ou des frameworks externes.
    *   `dialogue_system/`: Classes et fonctions liées au système de dialogue.
*   `data/`: Données persistantes de l'application.
    *   `interactions/`: Stockage des dialogues générés (fichiers JSON).
*   `domain/`: Modèles de données et services du domaine de l'application.
*   `llm_client/`: Clients pour interagir avec les modèles de langage (OpenAI, Dummy).
*   `models/`: Structures de données Pydantic utilisées dans l'application.
    *   `dialogue_structure/`: Modèles pour les éléments de dialogue et les interactions.
*   `services/`: Services applicatifs (ex: gestion des interactions, rendu JSON Unity).
    *   `repositories/`: Abstractions pour l'accès aux données (ex: `FileInteractionRepository`).
    *   `json_renderer/`: Logique pour convertir les interactions en format JSON Unity.
*   `tests/`: Tests unitaires et d'intégration.
*   `ui/`: Code relatif à l'interface utilisateur (PySide6).
    *   `generation_panel/`: Widgets spécifiques au panneau de génération.
    *   `left_panel/`: Widgets spécifiques au panneau de sélection de gauche.
*   `context_builder.py`: Responsable du chargement, du stockage et de l'accès aux données du GDD.
*   `prompt_engine.py`: Construit les prompts à envoyer aux LLMs.
*   `config_manager.py`: Gère le chargement et la sauvegarde des configurations.

## Prérequis et Installation

1.  **Python** : Version 3.10 ou ultérieure recommandée.
2.  **Dépendances Python** : Installer les dépendances listées dans `requirements.txt`.
    ```bash
    pip install -r requirements.txt
    ```
    Ce fichier inclut `PySide6`, `openai`, et d'autres bibliothèques nécessaires.

## Comment Lancer l'Application

1.  **Positionnement des Données du GDD** :
    *   Les fichiers JSON du Game Design Document (GDD) doivent être accessibles. Par défaut, l'application s'attend à les trouver dans un dossier `GDD/categories/` et `import/Bible_Narrative/` situés **au même niveau que le dossier `DialogueGenerator`**.
    *   Exemple de structure attendue :
        ```
        Parent_Folder/
        ├── DialogueGenerator/  <-- Racine du projet de l'application
        │   ├── main_app.py
        │   └── ... (autres fichiers et dossiers du projet)
        ├── GDD/
        │   └── categories/
        │       ├── personnages.json
        │       └── ... (autres fichiers JSON du GDD)
        └── import/
            └── Bible_Narrative/
                └── Vision.json
        ```
    *   Le chemin d'accès aux données du GDD est configurable dans `context_config.json`.

2.  **Clé API OpenAI (Optionnel mais recommandé)** :
    *   Pour utiliser le client OpenAI, assurez-vous que la variable d'environnement `OPENAI_API_KEY` est définie, ou que votre clé est présente dans `config/llm_config.json`.
    *   Si aucune clé n'est configurée, l'application utilisera `DummyLLMClient` qui simule les réponses.

3.  **Lancement** :
    *   ⚠️ **IMPORTANT** : Utiliser l'interface web React, pas l'interface desktop Python.
    *   **Interface Web (RECOMMANDÉE)** :
        ```bash
        npm run dev
        ```
        L'application sera accessible sur http://localhost:3000
    *   ⚠️ **Interface Desktop (DÉPRÉCIÉE)** — Ne plus utiliser :
        ```bash
        python main_app.py
        ```
        Cette interface est maintenue uniquement pour compatibilité mais ne doit plus être utilisée pour le développement.

## Prochaines Étapes Prévues

*   **Amélioration de la Sélection/Construction du Contexte** :
    *   Permettre la sélection explicite de plusieurs personnages (Acteur A, Acteur B).
    *   Enrichir le résumé de contexte avec plus de détails pertinents des éléments sélectionnés.
*   **Implémentation d'un Client LLM Réel (`OpenAIClient`)** :
    *   Gérer la configuration de la clé API (probablement via `config.yaml` ou variable d'environnement).
    *   Permettre de switcher entre `DummyLLMClient` et `OpenAIClient`.
*   **Gestion Asynchrone Améliorée** :
    *   Utiliser `asyncqt` ou `QThread` pour les appels LLM afin de ne pas bloquer l'UI.
*   **Amélioration du `PromptEngine` et du *System Prompt*** :
    *   Itérer sur le *system prompt* basé sur les résultats réels.
    *   Instructions plus détaillées pour le format JSON Unity.
*   **Interface pour plus de `generation_params`** (ton, style, température, sélection de modèle).
*   **Sorties Structurées (Structured Outputs)** : Explorer l'utilisation de JSON Schema avec l'API OpenAI pour un output plus fiable.
*   **`UnityJsonRenderer`** : Module pour convertir les Interactions en fichiers JSON Unity (tableau de nœuds normalisé).
*   **`GitService`** : Pour l'intégration Git.
*   **Stratégie Avancée de Génération de Variantes : Les "Événements Notables"**
    *   Pour améliorer la réactivité des dialogues et gérer la multiplicité des états du monde d'un RPG, une stratégie avancée est envisagée pour la construction du contexte et la génération de variantes.
    *   **Concept Principal :**
        *   Au lieu de se baser uniquement sur des variables simples, cette approche introduit la notion d'"**Événements Notables**".
        *   Chaque événement ou point de divergence narratif clé est identifié (ex: `decision_guilde_voleurs`, `issue_bataille_fort_dragon`).
        *   Chaque événement peut avoir plusieurs **états distincts** (ex: pour `decision_guilde_voleurs` : état 0 = non survenu, état 1 = joueur trahit la guilde, état 2 = joueur reste loyal).
    *   **Structure d'un État d'Événement :**
        *   **Valeur pour le Code :** Un identifiant simple (entier, chaîne courte) utilisé dans la logique du jeu.
        *   **Description Textuelle pour le LLM :** Une description narrative détaillée de l'état et de ses implications. Cette description fournit un contexte riche au LLM.
            *   Exemple pour `decision_guilde_voleurs` état 1 : *"Lors d'un assaut dramatique de la garde royale sur le repaire de la guilde des voleurs, le joueur, bien que membre de la guilde, a choisi de coopérer avec la garde, livrant des informations cruciales en échange d'une promesse de clémence."*
    *   **Processus de Génération de Dialogue :**
        *   **Sélection dans l'Interface :**
            *   Dans `DialogueGenerator`, l'utilisateur sélectionne le dialogue de base à continuer.
            *   L'utilisateur active ensuite un ou plusieurs "Événements Notables" pertinents pour cette interaction.
            *   Pour chaque événement activé, tous ses états possibles (ou un sous-ensemble choisi par l'utilisateur) sont considérés.
        *   **Génération de Variantes Multiples :**
            *   Le système génère automatiquement une variante de dialogue pour **chaque combinaison possible** des états des événements sélectionnés.
            *   Si un seul événement `E_A` avec 3 états (A0, A1, A2) est activé, 3 variantes de dialogue sont générées.
            *   Si deux événements, `E_A` (3 états) et `E_B` (2 états), sont activés, 3 * 2 = 6 variantes sont générées.
        *   **Appels au LLM :**
            *   Chaque variante de dialogue nécessite un **appel séparé au LLM**, car le contexte textuel fourni est unique.
    *   **Avantages :**
        *   Contexte sémantique riche pour le LLM.
        *   Automatisation des branches narratives.
        *   Contrôle fin par le designer.
        *   Intégration avec le format JSON Unity.
    *   **Défis et Considérations :**
        *   Explosion combinatoire des variantes.
        *   Cohérence des descriptions combinées.
        *   Gestion des dépendances entre événements.
        *   Adaptation de l'interface utilisateur de `DialogueGenerator`.
    *   Cette approche représente une évolution significative pour la génération de dialogues dynamiques et contextuellement conscients.

## Dépannage

### Erreur Git "fatal: bad object refs/heads/desktop.ini" (Windows)

**Symptôme** : Git affiche des erreurs comme `fatal: bad object refs/heads/desktop.ini` ou `fatal: bad object refs/desktop.ini`.

**Cause** : Windows crée automatiquement des fichiers `desktop.ini` dans les dossiers pour la personnalisation de l'affichage. Si ces fichiers sont créés dans `.git/refs/`, Git les traite comme des références invalides.

**Solution** : Exécuter le script de nettoyage :
```powershell
powershell -ExecutionPolicy Bypass -File scripts/cleanup_desktop_ini.ps1
```

Ce script déplace tous les fichiers `desktop.ini` de `.git/` vers `.git/_desktop_ini_quarantine/` sans les supprimer. Vous pouvez supprimer le dossier de quarantaine une fois que Git fonctionne correctement.

**Prévention** : Le `.gitignore` ignore déjà `desktop.ini`, mais cela n'empêche pas Windows d'en créer dans `.git/`. Si le problème réapparaît, réexécutez le script de nettoyage.

---
*Ce document sera mis à jour au fur et à mesure de l'avancement du projet.* 