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
    *   *System prompt* par défaut basique inclus, avec une brève introduction au format Yarn Spinner.
*   **Client LLM (`LLMClient`)** :
    *   Interface `IGenerator` définissant la méthode `async generate_variants(prompt, k)`.
    *   `OpenAIClient` : Implémentation utilisant l'API OpenAI (modèle par défaut actuel : `gpt-4o-mini`). Nécessite la variable d'environnement `OPENAI_API_KEY`.
    *   `DummyLLMClient` : Implémentation factice utilisée en fallback si `OpenAIClient` ne peut s'initialiser (ex: clé API manquante) ou pour des tests rapides. Simule la génération de `k` variantes au format Yarn Spinner.
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