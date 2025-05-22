from typing import List, Optional
from DialogueGenerator.models.dialogue_structure import Interaction
from DialogueGenerator.services.repositories import (
    InMemoryInteractionRepository, FileInteractionRepository, IInteractionRepository
)
import logging

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