"""Renderer for Unity JSON dialogue format."""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple

from models.dialogue_structure import (
    Interaction,
    DialogueLineElement,
    PlayerChoicesBlockElement,
    PlayerChoiceOption,
    CommandElement,
)

logger = logging.getLogger(__name__)


class UnityJsonRenderer:
    """Renderer qui convertit des Interactions en format JSON Unity normalisé.
    
    Le format Unity attend un tableau de nœuds à la racine : [{"id": "...", ...}, ...]
    Chaque Interaction est convertie en un DialogueNodeJson.
    """

    def render_interactions(self, interactions: List[Interaction]) -> List[Dict[str, Any]]:
        """Convertit une liste d'Interactions en liste de nœuds JSON Unity.
        
        Args:
            interactions: Liste d'Interactions à convertir.
            
        Returns:
            Liste de dictionnaires représentant les nœuds Unity (non normalisés).
            
        Raises:
            ValueError: Si les IDs ne sont pas uniques ou si les références sont invalides.
        """
        # Validation : IDs uniques
        interaction_ids = [interaction.interaction_id for interaction in interactions]
        if len(interaction_ids) != len(set(interaction_ids)):
            duplicate_ids = [id for id in interaction_ids if interaction_ids.count(id) > 1]
            raise ValueError(f"IDs d'interactions dupliqués : {set(duplicate_ids)}")
        
        # Construire un set des IDs valides pour validation des références
        valid_ids: Set[str] = set(interaction_ids)
        
        # Convertir chaque Interaction en nœud Unity
        nodes: List[Dict[str, Any]] = []
        for interaction in interactions:
            node = self._interaction_to_node(interaction, valid_ids)
            nodes.append(node)
        
        return nodes
    
    def render_interactions_to_string(
        self, 
        interactions: List[Interaction], 
        normalize: bool = True
    ) -> str:
        """Convertit des Interactions en chaîne JSON Unity.
        
        Args:
            interactions: Liste d'Interactions à convertir.
            normalize: Si True, normalise le JSON (supprime champs vides, etc.).
            
        Returns:
            Chaîne JSON formatée (indentée de 2 espaces).
        """
        nodes = self.render_interactions(interactions)
        
        if normalize:
            nodes = [self._normalize_node(node) for node in nodes]
        
        return json.dumps(nodes, indent=2, ensure_ascii=False)
    
    def render_interactions_to_file(
        self,
        interactions: List[Interaction],
        output_path: Path,
        normalize: bool = True
    ) -> None:
        """Convertit des Interactions et les écrit dans un fichier JSON Unity.
        
        Args:
            interactions: Liste d'Interactions à convertir.
            output_path: Chemin du fichier de sortie.
            normalize: Si True, normalise le JSON avant écriture.
        """
        json_content = self.render_interactions_to_string(interactions, normalize=normalize)
        
        # Créer le dossier parent si nécessaire
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Écrire le fichier
        output_path.write_text(json_content, encoding='utf-8')
        logger.info(f"Fichier JSON Unity écrit : {output_path}")
    
    def _interaction_to_node(self, interaction: Interaction, valid_ids: Set[str]) -> Dict[str, Any]:
        """Convertit une Interaction en nœud DialogueNodeJson.
        
        Args:
            interaction: L'Interaction à convertir.
            valid_ids: Set des IDs valides pour validation des références.
            
        Returns:
            Dictionnaire représentant un nœud Unity (non normalisé).
        """
        node: Dict[str, Any] = {
            "id": interaction.interaction_id,  # Toujours présent (requis)
        }
        
        # Trouver les lignes de dialogue (DialogueLineElement)
        dialogue_lines = [
            elem for elem in interaction.elements 
            if isinstance(elem, DialogueLineElement)
        ]
        
        # Prendre la première ligne pour speaker/line
        # Si plusieurs lignes, on pourrait les concaténer, mais pour l'instant on prend la première
        if dialogue_lines:
            first_line = dialogue_lines[0]
            if first_line.speaker:
                node["speaker"] = first_line.speaker
            if first_line.text:
                # Si plusieurs lignes, concaténer avec des sauts de ligne
                if len(dialogue_lines) > 1:
                    all_texts = [line.text for line in dialogue_lines if line.text]
                    node["line"] = "\n".join(all_texts)
                else:
                    node["line"] = first_line.text
        
        # Trouver les blocs de choix (PlayerChoicesBlockElement)
        choices_blocks = [
            elem for elem in interaction.elements 
            if isinstance(elem, PlayerChoicesBlockElement)
        ]
        
        if choices_blocks:
            # Prendre le premier bloc de choix (normalement il n'y en a qu'un)
            choices_block = choices_blocks[0]
            choices = []
            for choice_option in choices_blocks[0].choices:
                choice_dict: Dict[str, Any] = {
                    "text": choice_option.text,  # Requis
                    "targetNode": choice_option.next_interaction_id,  # Requis, toujours présent même vide
                }
                
                # Validation : vérifier que targetNode référence un ID valide (s'il n'est pas vide)
                if choice_option.next_interaction_id and choice_option.next_interaction_id not in valid_ids:
                    logger.warning(
                        f"Référence invalide dans l'interaction {interaction.interaction_id}: "
                        f"targetNode '{choice_option.next_interaction_id}' n'existe pas dans les interactions fournies"
                    )
                
                # Champs optionnels du choix
                if choice_option.condition:
                    choice_dict["condition"] = choice_option.condition
                # Note: Les autres champs (traitRequirements, influenceThreshold, etc.) 
                # ne sont pas dans PlayerChoiceOption actuellement, donc on ne les ajoute pas
                
                choices.append(choice_dict)
            
            if choices:
                node["choices"] = choices
        
        # nextNode : si pas de choix et qu'il y a un next_interaction_id_if_no_choices
        if not choices_blocks and interaction.next_interaction_id_if_no_choices:
            node["nextNode"] = interaction.next_interaction_id_if_no_choices
            
            # Validation
            if node["nextNode"] not in valid_ids:
                logger.warning(
                    f"Référence invalide dans l'interaction {interaction.interaction_id}: "
                    f"nextNode '{node['nextNode']}' n'existe pas dans les interactions fournies"
                )
        
        # Note: Les autres champs Unity (cutsceneMode, test, consequences, etc.)
        # ne sont pas mappés depuis Interaction actuellement.
        # Ils pourraient être ajoutés plus tard si nécessaire via des extensions du modèle Interaction.
        
        return node
    
    def _normalize_node(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """Normalise un nœud en supprimant les champs vides selon les règles Unity.
        
        Règles de normalisation :
        - Supprimer les champs vides (`""`, `null`)
        - Supprimer les booléens à `false` et nombres à `0` (valeurs par défaut)
        - Supprimer les tableaux/objets vides
        - Conserver toujours `id` et `targetNode` même s'ils sont vides
        
        Args:
            node: Dictionnaire représentant un nœud (peut être modifié).
            
        Returns:
            Dictionnaire normalisé.
        """
        normalized: Dict[str, Any] = {}
        
        # Conserver toujours 'id'
        if "id" in node:
            normalized["id"] = node["id"]
        
        # Parcourir tous les autres champs
        for key, value in node.items():
            if key == "id":
                continue  # Déjà traité
            
            # Conserver targetNode même s'il est vide
            if key == "targetNode":
                normalized[key] = value
                continue
            
            # Ignorer None et chaînes vides
            if value is None or value == "":
                continue
            
            # Ignorer booléens False
            if value is False:
                continue
            
            # Ignorer nombres à 0
            if isinstance(value, (int, float)) and value == 0:
                continue
            
            # Ignorer listes/tableaux vides
            if isinstance(value, list) and len(value) == 0:
                continue
            
            # Ignorer dictionnaires/objets vides
            if isinstance(value, dict) and len(value) == 0:
                continue
            
            # Récursivement normaliser les dictionnaires imbriqués
            if isinstance(value, dict):
                normalized_value = self._normalize_node(value)
                # Ne garder que si le dict normalisé n'est pas vide (sauf pour id/targetNode)
                if normalized_value or key in ("id", "targetNode"):
                    normalized[key] = normalized_value
            # Récursivement normaliser les choix dans choices[]
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                normalized_choices = [self._normalize_node(choice) for choice in value]
                # Filtrer les choix vides (mais normalement il ne devrait pas y en avoir)
                normalized_choices = [c for c in normalized_choices if c]
                if normalized_choices:
                    normalized[key] = normalized_choices
            else:
                normalized[key] = value
        
        return normalized
    
    def validate_nodes(self, nodes: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """Valide une liste de nœuds Unity.
        
        Args:
            nodes: Liste de nœuds à valider.
            
        Returns:
            Tuple (is_valid, errors) où errors est la liste des messages d'erreur.
        """
        errors: List[str] = []
        
        # Vérifier qu'il y a au moins un nœud
        if not nodes:
            errors.append("Au moins un nœud est requis")
            return (False, errors)
        
        # Extraire tous les IDs
        node_ids = [node.get("id") for node in nodes]
        
        # Vérifier que tous les nœuds ont un ID
        if None in node_ids or "" in node_ids:
            errors.append("Tous les nœuds doivent avoir un 'id' non vide")
        
        # Vérifier que les IDs sont uniques
        if len(node_ids) != len(set(node_ids)):
            duplicate_ids = [id for id in node_ids if node_ids.count(id) > 1]
            errors.append(f"IDs dupliqués : {set(duplicate_ids)}")
        
        # Valider les références de nœuds
        valid_ids = set(id for id in node_ids if id)
        # "END" est un nœud spécial reconnu par Unity pour terminer le dialogue
        # Il peut être omis du JSON (Unity le gère), mais on l'ajoute généralement explicitement
        valid_ids.add("END")
        reference_fields = ["nextNode", "targetNode", "successNode", "failureNode", "testSuccessNode", "testFailureNode"]
        
        for node in nodes:
            node_id = node.get("id", "?")
            for ref_field in reference_fields:
                ref_value = node.get(ref_field)
                if ref_value and ref_value not in valid_ids:
                    errors.append(
                        f"Nœud '{node_id}': Référence invalide dans '{ref_field}': '{ref_value}'"
                    )
            
            # Valider les références dans choices[]
            if "choices" in node:
                for i, choice in enumerate(node["choices"]):
                    target = choice.get("targetNode")
                    if target and target not in valid_ids:
                        errors.append(
                            f"Nœud '{node_id}', choix {i+1}: Référence invalide dans 'targetNode': '{target}'"
                        )
        
        return (len(errors) == 0, errors)
    
    def render_unity_nodes(
        self,
        nodes: List[Dict[str, Any]],
        normalize: bool = True
    ) -> str:
        """Rend une liste de nœuds Unity en JSON normalisé.
        
        Cette méthode accepte directement des nœuds enrichis (avec IDs) et les normalise
        selon les règles Unity.
        
        Args:
            nodes: Liste de dictionnaires représentant les nœuds Unity (avec IDs).
            normalize: Si True, normalise le JSON (supprime champs vides, etc.).
            
        Returns:
            Chaîne JSON formatée (indentée de 2 espaces).
            
        Raises:
            ValueError: Si la validation échoue.
        """
        # Valider les nœuds avant rendu
        is_valid, errors = self.validate_nodes(nodes)
        if not is_valid:
            error_msg = "Erreurs de validation avant rendu :\n" + "\n".join(errors)
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Normaliser si demandé
        if normalize:
            nodes = [self._normalize_node(node) for node in nodes]
        
        # Rendre en JSON
        return json.dumps(nodes, indent=2, ensure_ascii=False)

