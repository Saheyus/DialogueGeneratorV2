from typing import List, Optional
from DialogueGenerator.models.dialogue_structure import Interaction
from DialogueGenerator.services.repositories import (
    InMemoryInteractionRepository, FileInteractionRepository, IInteractionRepository
)
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
        result = self._repo.save(interaction)
        logger.info(f"[DEBUG] Résultat de l'ajout dans le repo: {result}")
        return result

    def delete(self, interaction_id: str) -> bool:
        """Supprime une interaction par son ID."""
        return self._repo.delete(interaction_id)

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