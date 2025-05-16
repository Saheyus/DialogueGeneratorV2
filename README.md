# DialogueGenerator - Outil de Génération de Dialogues IA

Ce projet vise à créer une application autonome pour assister à la création de dialogues pour jeux de rôle, en s'interfaçant avec des modèles de langage (LLM) et en s'appuyant sur un Game Design Document (GDD) existant.

## Objectif Principal (Rappel des Spécifications)

1.  Charger le GDD (via des fichiers JSON extraits de Notion).
2.  Permettre à l'utilisateur de sélectionner un contexte (personnages, lieux, etc.).
3.  Générer des nœuds de dialogue au format Yarn Spinner en utilisant un LLM.
4.  Faciliter l'écriture, l'évaluation et la validation de ces dialogues.
5.  S'intégrer avec une pipeline de production de jeu (export `.yarn`, compilation, commit Git).

## État Actuel du Projet (Mai 2024)

L'application est en cours de développement actif. Les fonctionnalités suivantes sont implémentées :

*   **Chargement des Données du GDD (`ContextBuilder`)** :
    *   Lecture des fichiers JSON générés par les scripts `filter.py` et `main.py` (situés dans `../GDD/categories/`).
    *   Chargement de `Vision.json` depuis `../import/Bible_Narrative/`.
    *   Les données (personnages, lieux, objets, espèces, communautés, dialogues exemples, structures narratives/macro/micro) sont stockées en mémoire.
*   **Interface Utilisateur (`PySide6`)** :
    *   Fenêtre principale avec plusieurs panneaux redimensionnables (`QSplitter`).
    *   **Panneau de Sélection du Contexte (Gauche)** :
        *   Listes distinctes pour les personnages, lieux, objets, espèces, communautés et exemples de dialogues.
        *   Champs de filtre textuel pour chaque liste.
        *   Affichage du nombre d'éléments (filtrés/total) pour chaque liste.
    *   **Panneau de Détails (Centre)** :
        *   Affichage des détails complets de l'élément sélectionné dans une liste (format arborescent `QTreeView` avec "Propriété" et "Valeur").
    *   **Panneau de Génération (Droite)** :
        *   Champ pour spécifier le nombre de variantes `k` à générer.
        *   Champ de texte multiligne pour l'"Instruction utilisateur" (objectif de la scène).
        *   Bouton "Générer le Dialogue".
        *   Un `QTabWidget` pour afficher les variantes de dialogue générées, chaque variante dans un `QTextEdit` en lecture seule.
*   **Moteur de Prompt (`PromptEngine`)** :
    *   Classe `PromptEngine` capable de combiner un *system prompt*, un résumé de contexte, et l'instruction utilisateur pour former un prompt complet.
    *   *System prompt* par défaut basique inclus, avec une brève introduction au format Yarn Spinner.
*   **Client LLM (`LLMClient`)** :
    *   Interface `IGenerator` définissant la méthode `async generate_variants(prompt, k)`.
    *   `DummyLLMClient` : une implémentation factice qui simule la génération de `k` variantes au format Yarn Spinner avec un délai configurable, sans appel réseau réel.
*   **Flux de Génération Initial** :
    *   La sélection d'éléments dans les listes met à jour le panneau de détails.
    *   Le bouton "Générer le Dialogue" déclenche :
        *   La récupération du contexte sélectionné (actuellement, premier personnage et premier lieu sélectionnés) et de l'instruction utilisateur.
        *   La construction du prompt via `PromptEngine`.
        *   L'appel à `DummyLLMClient` (de manière synchrone/bloquante via `asyncio.run()` pour l'instant).
        *   L'affichage des variantes dans les onglets.

## Structure du Projet

Le code est organisé dans le dossier `DialogueGenerator/` avec les principaux modules suivants :

*   `main_app.py`: Point d'entrée de l'application. Initialise l'application Qt et la fenêtre principale.
*   `context_builder.py`: Responsable du chargement, du stockage et de l'accès aux données du GDD.
*   `prompt_engine.py`: Construit les prompts à envoyer aux LLMs en combinant les informations système, le contexte et les instructions utilisateur.
*   `llm_client.py`: Contient l'interface `IGenerator` pour les clients LLM et les implémentations concrètes (actuellement `DummyLLMClient`).
*   `ui/main_window.py`: Définit la classe `MainWindow` (héritant de `QMainWindow`) qui construit et gère l'interface utilisateur principale.
*   `ui/__init__.py`: (Si nécessaire, pour que `ui` soit traité comme un package).

## Prérequis et Installation

1.  **Python** : Version 3.10 ou ultérieure recommandée.
2.  **PySide6** : Bibliothèque pour l'interface graphique Qt.
    ```bash
    pip install PySide6
    ```
3.  **Autres dépendances** : (À compléter au fur et à mesure, par exemple `openai` lorsque `OpenAIClient` sera utilisé).

## Comment Lancer l'Application

1.  Assurez-vous que les fichiers JSON du GDD sont présents dans le dossier `../GDD/categories/` par rapport à la racine du projet `Notion_Scrapper/` (c'est-à-dire que `DialogueGenerator` et `GDD` sont au même niveau hiérarchique).
2.  Ouvrez un terminal à la racine du dossier `DialogueGenerator/`.
3.  Exécutez la commande :
    ```bash
    python main_app.py
    ```

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
    *   Instructions plus détaillées pour Yarn Spinner.
*   **Interface pour plus de `generation_params`** (ton, style, température, sélection de modèle).
*   **Sorties Structurées (Structured Outputs)** : Explorer l'utilisation de JSON Schema avec l'API OpenAI pour un output plus fiable.
*   **`YarnRenderer`** : Module pour convertir la sortie LLM (potentiellement structurée) en fichiers `.yarn` valides.
*   **`CompilerWrapper`** : Pour appeler `yarnspinner-cli compile`.
*   **`GitService`** : Pour l'intégration Git.

---
*Ce document sera mis à jour au fur et à mesure de l'avancement du projet.* 