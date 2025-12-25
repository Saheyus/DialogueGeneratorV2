# Spécification Technique : Génération Modulaire de Dialogues

## 1. Introduction et Objectifs

Ce document décrit l'architecture et la conception pour la refonte du système de génération de dialogues au sein de l'application DialogueGenerator. L'objectif principal est de passer d'une génération de dialogues monolithiques à un système modulaire basé sur des "Interactions". Cette approche permettra une plus grande flexibilité d'édition, une meilleure gestion du contexte pour le LLM, et une expérience utilisateur plus intuitive pour la création de dialogues complexes ("dialogue heavy").

L'utilisateur interagira avec le système uniquement via l'interface graphique de l'outil DialogueGenerator ; une interaction directe avec les fichiers `.yarn` n'est pas prévue pour la création ou l'édition.

## 2. Principes de Conception

L'implémentation suivra les principes SOLID pour assurer une base de code maintenable, extensible et robuste.

*   **Modèle "Interaction"** : L'unité centrale de dialogue sera l'objet `Interaction`. Une `Interaction` regroupe une séquence d'éléments de dialogue (répliques de PNJ, choix du joueur, commandes Yarn) et correspondra à un nœud unique dans le fichier `.yarn` exporté.
*   **Granularité d'Édition** : Bien qu'une `Interaction` soit une unité logique, l'outil permettra l'édition fine de ses composants internes (chaque ligne de PNJ, chaque choix, chaque commande).
*   **Services Dédiés** : Des services distincts géreront la logique métier (gestion des interactions), le rendu en format Yarn, et la persistance des données.
*   **Interface Utilisateur Intuitive** : L'UI sera réorganisée pour refléter cette nouvelle approche modulaire, en séparant clairement la gestion de la séquence d'interactions, l'édition d'une interaction spécifique, et la configuration de la génération LLM.

## 3. Modèles de Données (Basés sur Python)

Les modèles de données suivants définissent la structure des objets manipulés par le système.

```python
from typing import List, Optional, Dict, Any, Union
from abc import ABC, abstractmethod

# --- Éléments constitutifs d'une Interaction ---

class AbstractDialogueElement(ABC):
    """Classe de base pour tout élément pouvant apparaître dans une interaction."""
    element_type: str 

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AbstractDialogueElement':
        pass

class DialogueLineElement(AbstractDialogueElement):
    """Représente une ligne de dialogue (PNJ ou PJ si panneau)."""
    element_type: str = "dialogue_line"
    speaker: Optional[str]
    text: str
    tags: List[str] = []
    pre_line_commands: List[str] = []
    post_line_commands: List[str] = []

    def __init__(self, text: str, speaker: Optional[str] = None, tags: Optional[List[str]] = None,
                 pre_line_commands: Optional[List[str]] = None, post_line_commands: Optional[List[str]] = None):
        self.speaker = speaker
        self.text = text
        self.tags = tags or []
        self.pre_line_commands = pre_line_commands or []
        self.post_line_commands = post_line_commands or []
    # ... to_dict, from_dict ...

class PlayerChoiceOption:
    """Détail d'une option de choix pour le joueur."""
    text: str
    next_interaction_id: str
    condition: Optional[str] = None
    actions: List[str] = []
    tags: List[str] = []

    def __init__(self, text: str, next_interaction_id: str, condition: Optional[str] = None,
                 actions: Optional[List[str]] = None, tags: Optional[List[str]] = None):
        self.text = text
        self.next_interaction_id = next_interaction_id
        self.condition = condition
        self.actions = actions or []
        self.tags = tags or []
    # ... to_dict, from_dict ...

class PlayerChoicesBlockElement(AbstractDialogueElement):
    """Représente un bloc de choix pour le joueur."""
    element_type: str = "player_choices_block"
    choices: List[PlayerChoiceOption] = []

    def __init__(self, choices: Optional[List[PlayerChoiceOption]] = None):
        self.choices = choices or []
    # ... to_dict, from_dict ...

class CommandElement(AbstractDialogueElement):
    """Représente une commande Yarn générique."""
    element_type: str = "command"
    command_string: str # Sans les << >>

    def __init__(self, command_string: str):
        self.command_string = command_string
    # ... to_dict, from_dict ...

# --- L'Interaction elle-même ---

class Interaction:
    """Représente une "Interaction" complète, qui sera un nœud Yarn."""
    interaction_id: str # Deviendra le 'title' du nœud Yarn
    elements: List[AbstractDialogueElement] = []
    header_commands: List[str] = []
    header_tags: List[str] = []
    next_interaction_id_if_no_choices: Optional[str] = None

    def __init__(self, interaction_id: str, elements: Optional[List[AbstractDialogueElement]] = None,
                 header_commands: Optional[List[str]] = None, header_tags: Optional[List[str]] = None,
                 next_interaction_id_if_no_choices: Optional[str] = None):
        self.interaction_id = interaction_id
        self.elements = elements or []
        self.header_commands = header_commands or []
        self.header_tags = header_tags or []
        self.next_interaction_id_if_no_choices = next_interaction_id_if_no_choices
    # ... to_dict, from_dict (avec logique pour désérialiser les types d'éléments) ...
```
*(Note: Les implémentations complètes de `to_dict` et `from_dict` pour chaque classe, comme esquissées précédemment, devront être finalisées.)*

## 4. Services et Interfaces

### 4.1. Interfaces (Protocoles Python)

```python
from typing import Protocol, List, Optional

class IInteractionRepository(Protocol):
    """Interface pour la persistance des Interactions."""
    def get_by_id(self, interaction_id: str) -> Optional[Interaction]: ...
    def save(self, interaction: Interaction) -> None: ...
    def get_all(self) -> List[Interaction]: ...
    def delete(self, interaction_id: str) -> None: ...

class IYarnRenderer(Protocol):
    """Interface pour transformer une Interaction en chaîne Yarn."""
    def render_interaction_to_yarn(self, interaction: Interaction) -> str: ...
    def render_all_to_yarn_file_content(self, interactions: List[Interaction]) -> str: ...

# Optionnel:
# class IYarnParser(Protocol):
#     """Interface pour transformer une chaîne Yarn en liste d'Interactions."""
#     def parse_yarn_to_interactions(self, yarn_content: str) -> List[Interaction]: ...
```

### 4.2. Implémentations des Services

*   **`YarnRendererService`**: Implémente `IYarnRenderer`.
    *   `render_interaction_to_yarn()`: Prend un objet `Interaction` et génère la chaîne de caractères formatée pour un nœud Yarn. Gère la transformation des `DialogueElement`s, les `<<jump>>`, les conditions, les tags, etc.
    *   `render_all_to_yarn_file_content()`: Prend une liste d'objets `Interaction` et produit le contenu complet d'un fichier `.yarn`.
*   **`InteractionService`**: Gère la logique métier des interactions.
    *   Dépend de `IInteractionRepository` (injecté).
    *   Méthodes pour créer, récupérer, mettre à jour et supprimer des `Interaction`s.
    *   Méthodes pour ajouter, supprimer, modifier et réorganiser les `AbstractDialogueElement`s au sein d'une `Interaction` spécifique.
*   **`InMemoryInteractionRepository`** (et/ou futures implémentations de `IInteractionRepository` comme `FileInteractionRepository`):
    *   Implémente `IInteractionRepository` pour la persistance des objets `Interaction` (en mémoire, sur disque, etc.).

*(Les détails des méthodes de ces services, comme esquissés précédemment, devront être implémentés.)*

## 5. Correspondance Modèle Interne (JSON) <=> Format Yarn

Le modèle `Interaction` et ses composants (`DialogueElement`) sont la source de vérité. Le `YarnRendererService` assure la traduction vers le format `.yarn`.

**Exemple : `Interaction` JSON (conceptuel) vers Yarn**

*   **Interaction (simplifiée) :**
    ```json
    {
      "interaction_id": "NPC_Greeting",
      "header_tags": ["intro"],
      "elements": [
        {
          "element_type": "dialogue_line",
          "speaker": "Marchand",
          "text": "Bonjour, voyageur !"
        },
        {
          "element_type": "dialogue_line",
          "text": "Que puis-je pour vous ?"
        },
        {
          "element_type": "player_choices_block",
          "choices": [
            {
              "text": "Des potions ?",
              "next_interaction_id": "NPC_Potions"
            },
            {
              "text": "Rien, merci.",
              "next_interaction_id": "NPC_Farewell",
              "condition": "<<if $player_is_rude>>"
            }
          ]
        }
      ]
    }
    ```

*   **Traduction Yarn correspondante :**
    ```yarn
    title: NPC_Greeting
    tags: intro
    ---
    Marchand: Bonjour, voyageur !
    Que puis-je pour vous ?
    -> Des potions ?
        <<jump NPC_Potions>>
    <<if $player_is_rude>>
    -> Rien, merci.
        <<jump NPC_Farewell>>
    <<endif>>
    ===
    ```
Le `YarnRendererService` devra gérer l'indentation correcte pour les conditions et les `jump` sous les choix.

## 6. Interface Utilisateur (UI) - Réorganisation Proposée

L'interface utilisateur sera réorganisée pour s'adapter à ce nouveau modèle de génération modulaire.

### 6.1. Panneau de Gauche (Contexte GDD)

*   **Reste globalement inchangé.**
*   Sections `Selection` (Characters, Locations, Items, etc.) et `Details`.
*   La section `Yarn Files (Project)` servira à charger/sauvegarder des ensembles d'interactions.

### 6.2. Zone Centrale/Droite : "Atelier de Dialogue"

Cette zone sera divisée en plusieurs volets/onglets :

*   **A. Gestionnaire de Séquence d'Interactions :**
    *   Affiche une liste ordonnée des `interaction_id` (titres des nœuds Yarn) de la scène/dialogue en cours.
    *   Permet d'ajouter, supprimer, et réordonner les `Interaction`s.
    *   La sélection d'une `Interaction` ici charge ses détails dans le volet d'édition.

*   **B. Volet d'Édition d'Interaction :**
    *   Zone principale pour l'édition détaillée des `DialogueElement`s de l'`Interaction` sélectionnée.
    *   Affiche une liste verticale des éléments (lignes PNJ, bloc de choix, commandes).
    *   Chaque élément est un widget permettant l'édition de ses propriétés (texte, speaker, conditions, `next_interaction_id`, etc.).
    *   Boutons pour ajouter de nouveaux `DialogueElement`s (ligne PNJ, bloc de choix, commande) à l'interaction courante.
    *   Boutons pour supprimer ou réordonner les éléments au sein de l'interaction.

*   **C. Volet de Génération et Configuration LLM :**
    *   **Contexte Précédent :** Affiche l'`interaction_id` servant de contexte pour la prochaine génération.
    *   **"Instructions pour la Prochaine Interaction"**: Champ texte pour guider le LLM.
    *   **"Instructions Système LLM"**.
    *   **"Options LLM"**: Modèle, Nombre de Variantes (k).
    *   **Nouveau : "Nombre d'Interactions à Générer"** (1 par défaut).
    *   "Limite de tokens (contexte GDD)", "Utiliser Sortie Structurée (JSON)".
    *   "Tokens (contexte GDD/prompt total)".
    *   Bouton **"Générer Dialogue(s)"**.

*   **D. Volet d'Information/Prévisualisation (avec Onglets) :**
    *   **"Prompt LLM Estimé"**: Affiche le prompt complet qui sera envoyé au LLM.
    *   **"Variantes Générées"**: Si k > 1, affiche les variantes pour sélection par l'utilisateur.
    *   **"Prévisualisation Yarn"**: Affiche le rendu Yarn de l'`Interaction` sélectionnée ou de toute la séquence.
    *   **"Contexte GDD Complet"**: Affiche le contexte GDD utilisé.

## 7. Flux de Travail Utilisateur Envisagé

1.  Chargement d'un projet/fichier existant (séquence d'interactions) ou création d'un nouveau dialogue.
2.  Sélection du contexte GDD (personnages, lieux, etc.) dans le panneau de gauche.
3.  Utilisation du "Gestionnaire de Séquence" pour naviguer, ajouter ou sélectionner une `Interaction`.
4.  Édition manuelle des `DialogueElement`s de l'interaction sélectionnée dans le "Volet d'Édition".
5.  Pour la génération LLM :
    *   Configuration des instructions et options dans le "Volet de Génération".
    *   Lancement de la génération.
    *   Les nouvelles interactions générées (et potentiellement sélectionnées parmi des variantes) sont ajoutées à la séquence.
6.  Prévisualisation du rendu Yarn.
7.  Sauvegarde du projet.

## 8. Conclusion

Cette approche modulaire par "Interactions" vise à fournir un outil puissant et flexible pour la création de dialogues complexes. La séparation claire des responsabilités dans le code (modèles, services) et dans l'interface utilisateur devrait faciliter le développement, la maintenance et l'utilisation future de l'application DialogueGenerator. 