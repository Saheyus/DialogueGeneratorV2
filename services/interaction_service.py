from typing import List, Optional, Dict, Tuple, Any
from pathlib import Path
from models.dialogue_structure import Interaction, DialogueLineElement, PlayerChoicesBlockElement
from .repositories import IInteractionRepository
from services.repositories import (
    InMemoryInteractionRepository, FileInteractionRepository, IInteractionRepository
)
from services.json_renderer import UnityJsonRenderer
import logging
import uuid
import re
from datetime import datetime

logger = logging.getLogger(__name__)

class InteractionService:
    """Service d'accès aux interactions pour l'UI."""
    def __init__(self, repository: Optional[IInteractionRepository] = None):
        """Initialise le service avec un repository (mémoire par défaut)."""
        if repository is None:
            self._repo = InMemoryInteractionRepository()
        else:
            self._repo = repository
            
        # Index des parents : child_interaction_id -> List[(parent_interaction_id, choice_index)]
        # choice_index = -1 pour next_interaction_id_if_no_choices
        self._parent_index: Dict[str, List[Tuple[str, int]]] = {}
        
        # Initialiser l'index au démarrage
        self._rebuild_parent_index()
        
    def _rebuild_parent_index(self) -> None:
        """Reconstruit l'index des parents en parcourant toutes les interactions."""
        logger.info("Reconstruction de l'index des parents au démarrage...")
        self._parent_index.clear()
        
        interactions = self._repo.get_all()
        for interaction in interactions:
            self._index_interaction_links(interaction)
            
        logger.info(f"Index des parents reconstruit avec {len(self._parent_index)} entrées.")
        
    def _index_interaction_links(self, interaction: Interaction) -> None:
        """Indexe les liens d'une interaction vers ses enfants."""
        parent_id = interaction.interaction_id
        
        # Indexer next_interaction_id_if_no_choices
        if interaction.next_interaction_id_if_no_choices:
            child_id = interaction.next_interaction_id_if_no_choices
            if child_id not in self._parent_index:
                self._parent_index[child_id] = []
            # -1 indique une transition automatique
            self._parent_index[child_id].append((parent_id, -1))
            
        # Indexer les choix dans les PlayerChoicesBlockElement
        for element in interaction.elements:
            if isinstance(element, PlayerChoicesBlockElement):
                for choice_index, choice in enumerate(element.choices):
                    if choice.next_interaction_id:
                        child_id = choice.next_interaction_id
                        if child_id not in self._parent_index:
                            self._parent_index[child_id] = []
                        self._parent_index[child_id].append((parent_id, choice_index))
                        
    def _remove_interaction_from_index(self, interaction_id: str) -> None:
        """Retire une interaction de l'index (comme parent et comme enfant)."""
        # Retirer comme enfant
        if interaction_id in self._parent_index:
            del self._parent_index[interaction_id]
            
        # Retirer comme parent dans toutes les autres entrées
        for child_id, parents in self._parent_index.items():
            self._parent_index[child_id] = [(pid, choice_idx) for pid, choice_idx in parents 
                                          if pid != interaction_id]
        
        # Nettoyer les entrées vides
        empty_keys = [k for k, v in self._parent_index.items() if not v]
        for k in empty_keys:
            del self._parent_index[k]

    def get_all(self) -> List[Interaction]:
        """Retourne toutes les interactions."""
        logger.info("[DEBUG] Appel à get_all sur InteractionService")
        interactions = self._repo.get_all()
        logger.info(f"[DEBUG] Interactions récupérées: {[getattr(i, 'interaction_id', None) for i in interactions]}")
        return interactions

    def get_by_id(self, interaction_id: str) -> Optional[Interaction]:
        """Retourne une interaction par son ID."""
        return self._repo.get_by_id(interaction_id)

    def save(self, interaction: Interaction) -> None:
        """Sauvegarde une interaction (création ou mise à jour)."""
        logger.info(f"[DEBUG] Sauvegarde de l'interaction: id={interaction.interaction_id}, titre={getattr(interaction, 'title', None)}")
        
        # Vérifier si l'interaction existe déjà pour mise à jour de l'index
        existing_interaction = self._repo.get_by_id(interaction.interaction_id)
        
        # Si c'est une mise à jour, retirer l'ancienne version de l'index
        if existing_interaction:
            self._remove_interaction_from_index(interaction.interaction_id)
            
        # Sauvegarder l'interaction
        result = self._repo.save(interaction)
        
        # Mettre à jour l'index avec la nouvelle version
        self._index_interaction_links(interaction)
        
        logger.info(f"[DEBUG] Résultat de l'ajout dans le repo: {result}")
        logger.debug(f"Index des parents mis à jour. Entrées totales: {len(self._parent_index)}")
        return result

    def delete(self, interaction_id: str) -> bool:
        """Supprime une interaction par son ID."""
        # Retirer de l'index avant suppression
        self._remove_interaction_from_index(interaction_id)
        
        result = self._repo.delete(interaction_id)
        logger.debug(f"Interaction {interaction_id} supprimée. Index mis à jour.")
        return result

    def exists(self, interaction_id: str) -> bool:
        """Vérifie si une interaction existe."""
        return self._repo.exists(interaction_id)

    def set_repository(self, repository: IInteractionRepository) -> None:
        """Change dynamiquement le backend de persistance."""
        self._repo = repository 

    def generate_interaction_id(self, prefix: Optional[str] = None, use_readable_format: bool = False) -> str:
        """Génère un ID d'interaction unique.
        
        Args:
            prefix: Un préfixe optionnel pour l'ID (ex: "rencontre" pour "rencontre_123e4567-e89b").
                    Si None, seul l'UUID sera retourné par défaut.
            use_readable_format: Si True, génère un ID dans un format plus lisible mais moins unique
                                (à utiliser pour tests/démos uniquement).
        
        Returns:
            Un identifiant unique pour une nouvelle interaction.
        """
        # Format UUID standard (garantit l'unicité)
        if not use_readable_format:
            unique_id = str(uuid.uuid4())
            
            if prefix:
                clean_prefix = re.sub(r'[^a-zA-Z0-9_]', '_', prefix.lower())
                if len(clean_prefix) > 20:
                    clean_prefix = clean_prefix[:20]
                return f"{clean_prefix}_{unique_id}"
            return unique_id  # Retourne l'UUID seul si pas de préfixe
        
        # Format lisible (UNIQUEMENT pour démo/test)
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            random_suffix = uuid.uuid4().hex[:6]
            
            if prefix:
                clean_prefix = re.sub(r'[^a-zA-Z0-9_]', '_', prefix.lower())
                if len(clean_prefix) > 20:
                    clean_prefix = clean_prefix[:20]
                return f"{clean_prefix}_{timestamp}_{random_suffix}"
            return f"interaction_{timestamp}_{random_suffix}"
    
    def create_interaction(self, title: str = "", elements: Optional[List] = None, 
                          header_commands: Optional[List[str]] = None, 
                          header_tags: Optional[List[str]] = None,
                          prefix: Optional[str] = None) -> Interaction:
        """Crée une nouvelle interaction avec un ID unique.
        
        Args:
            title: Titre de l'interaction
            elements: Liste d'éléments de dialogue (optionnel)
            header_commands: Liste de commandes d'en-tête (optionnel)
            header_tags: Liste de tags d'en-tête (optionnel)
            prefix: Préfixe optionnel pour l'ID. Si non fourni, seul un UUID sera utilisé.
            
        Returns:
            La nouvelle interaction créée.
        """
        # Le préfixe n'est plus dérivé du titre automatiquement.
        # Si un préfixe est explicitement fourni, il sera utilisé. Sinon, seul l'UUID.
        interaction_id = self.generate_interaction_id(prefix=prefix)
        
        interaction = Interaction(
            interaction_id=interaction_id,
            elements=elements or [],
            header_commands=header_commands or [],
            header_tags=header_tags or [],
            title=title
        )
        
        self.save(interaction)
        logger.info(f"Nouvelle interaction créée: id={interaction_id}, titre={title}")
        return interaction
        
    def migrate_legacy_ids(self) -> int:
        """Migre les anciennes interactions avec des IDs non-standards vers des UUID.
        
        Cette méthode est à utiliser pour la migration de données existantes.
        
        Returns:
            Nombre d'interactions migrées
        """
        migrations = 0
        
        # Récupérer toutes les interactions
        interactions = self.get_all()
        
        for interaction in interactions:
            # Vérifier si l'ID n'est pas déjà un UUID ou un ID au nouveau format
            current_id = interaction.interaction_id
            
            try:
                # Tester si l'ID est un UUID valide
                uuid.UUID(current_id)
                # Si on arrive ici, c'est un UUID valide, on ne fait rien
                continue
            except ValueError:
                # Ce n'est pas un UUID valide, vérifier si c'est au format prefix_uuid
                if '_' in current_id:
                    parts = current_id.split('_')
                    try:
                        # Essayer de parser la dernière partie comme UUID
                        uuid.UUID(parts[-1])
                        # Bon format prefix_uuid, on ne fait rien
                        continue
                    except (ValueError, IndexError):
                        # Pas au bon format, on migre
                        pass
                
                # Extraire un préfixe potentiel si l'ID contient des underscores
                prefix = None
                if '_' in current_id:
                    prefix = current_id.split('_')[0]
                
                # Créer un nouvel ID
                new_id = self.generate_interaction_id(prefix)
                
                # Mettre à jour l'interaction avec le nouvel ID
                old_id = interaction.interaction_id
                interaction.interaction_id = new_id
                
                # Sauvegarder l'interaction mise à jour
                self.save(interaction)
                
                # Supprimer l'ancienne interaction
                self._repo.delete(old_id)
                
                logger.info(f"ID d'interaction migré: {old_id} -> {new_id}")
                migrations += 1
        
        return migrations 

    def get_dialogue_path(self, interaction_id: str, max_depth: int = 10) -> List[Interaction]:
        """Reconstruit le chemin de dialogue menant à une interaction donnée.
        
        Args:
            interaction_id: L'ID de l'interaction terminale
            max_depth: Profondeur maximale de remontée (protection contre boucles)
            
        Returns:
            Liste des interactions du chemin, ordonnée du plus ancien au plus récent
        """
        path = []
        current_id = interaction_id
        depth = 0
        
        # Remonter la chaîne des parents
        while current_id and depth < max_depth:
            # Récupérer l'interaction actuelle
            interaction = self.get_by_id(current_id)
            if not interaction:
                logger.warning(f"Interaction {current_id} non trouvée lors de la reconstruction du chemin.")
                break
                
            # Ajouter au début du chemin (ordre chronologique)
            path.insert(0, interaction)
            
            # Chercher le parent dans l'index
            parents = self._parent_index.get(current_id, [])
            if not parents:
                # Pas de parent trouvé, c'est l'interaction racine
                break
                
            # Pour la V1, prendre le premier parent trouvé
            # (plus tard on pourra implémenter une logique de sélection plus sophistiquée)
            parent_id, choice_index = parents[0]
            
            # Si plusieurs parents, logger un warning
            if len(parents) > 1:
                logger.debug(f"Interaction {current_id} a plusieurs parents: {parents}. "
                           f"Utilisation du premier: {parent_id}")
                
            current_id = parent_id
            depth += 1
            
        if depth >= max_depth:
            logger.warning(f"Profondeur maximale atteinte lors de la reconstruction du chemin pour {interaction_id}")
            
        logger.info(f"Chemin de dialogue reconstruit pour {interaction_id}: "
                   f"{[i.interaction_id for i in path]} (longueur: {len(path)})")
        return path
        
    def get_parent_info(self, interaction_id: str) -> List[Tuple[str, int]]:
        """Retourne les informations des parents d'une interaction.
        
        Args:
            interaction_id: L'ID de l'interaction enfant
            
        Returns:
            Liste de tuples (parent_interaction_id, choice_index)
            choice_index = -1 pour next_interaction_id_if_no_choices
        """
        return self._parent_index.get(interaction_id, [])
        
    def get_choice_text_for_transition(self, parent_id: str, child_id: str) -> Optional[str]:
        """Retourne le texte du choix qui mène d'un parent à un enfant.
        
        Args:
            parent_id: ID de l'interaction parente
            child_id: ID de l'interaction enfant
            
        Returns:
            Le texte du choix ou None si pas trouvé
        """
        parent_interaction = self.get_by_id(parent_id)
        if not parent_interaction:
            return None
            
        # Vérifier si c'est une transition automatique
        if parent_interaction.next_interaction_id_if_no_choices == child_id:
            return "(transition automatique)"
            
        # Chercher dans les choix
        parents_info = self.get_parent_info(child_id)
        choice_index = None
        for pid, cidx in parents_info:
            if pid == parent_id and cidx >= 0:
                choice_index = cidx
                break
                
        if choice_index is None:
            return None
            
        # Trouver le choix correspondant dans l'interaction parente
        for element in parent_interaction.elements:
            if isinstance(element, PlayerChoicesBlockElement):
                if 0 <= choice_index < len(element.choices):
                    return element.choices[choice_index].text
                    
        return None
    
    def export_to_unity_json(
        self, 
        interaction_ids: List[str], 
        output_path: Path,
        normalize: bool = True
    ) -> None:
        """Exporte plusieurs interactions vers un fichier JSON Unity.
        
        Args:
            interaction_ids: Liste des IDs d'interactions à exporter.
            output_path: Chemin du fichier JSON de sortie.
            normalize: Si True, normalise le JSON (supprime champs vides, etc.).
            
        Raises:
            ValueError: Si certaines interactions n'existent pas ou si la validation échoue.
        """
        # Récupérer toutes les interactions
        interactions: List[Interaction] = []
        missing_ids: List[str] = []
        
        for interaction_id in interaction_ids:
            interaction = self.get_by_id(interaction_id)
            if interaction:
                interactions.append(interaction)
            else:
                missing_ids.append(interaction_id)
        
        if missing_ids:
            raise ValueError(f"Interactions introuvables : {missing_ids}")
        
        if not interactions:
            raise ValueError("Aucune interaction à exporter")
        
        # Utiliser UnityJsonRenderer pour la conversion
        renderer = UnityJsonRenderer()
        
        # Valider avant export
        nodes = renderer.render_interactions(interactions)
        is_valid, errors = renderer.validate_nodes(nodes)
        
        if not is_valid:
            error_msg = "Erreurs de validation avant export :\n" + "\n".join(errors)
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Exporter vers fichier
        renderer.render_interactions_to_file(interactions, output_path, normalize=normalize)
        logger.info(f"Export Unity JSON réussi : {len(interactions)} interactions vers {output_path}") 
