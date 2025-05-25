from typing import Protocol, List, Optional
from models.dialogue_structure import Interaction

class IInteractionRepository(Protocol):
    """Interface pour la persistance des Interactions."""
    
    def get_by_id(self, interaction_id: str) -> Optional[Interaction]:
        """Récupère une interaction par son ID.
        
        Args:
            interaction_id: L'identifiant unique de l'interaction.
            
        Returns:
            L'interaction si elle existe, None sinon.
        """
        ...

    def save(self, interaction: Interaction) -> None:
        """Sauvegarde une interaction.
        
        Si une interaction avec le même ID existe déjà, elle sera mise à jour.
        
        Args:
            interaction: L'interaction à sauvegarder.
        """
        ...

    def get_all(self) -> List[Interaction]:
        """Récupère toutes les interactions.
        
        Returns:
            La liste de toutes les interactions.
        """
        ...

    def delete(self, interaction_id: str) -> bool:
        """Supprime une interaction par son ID.
        
        Args:
            interaction_id: L'identifiant unique de l'interaction à supprimer.
            
        Returns:
            True si l'interaction a été supprimée, False si elle n'existait pas.
        """
        ...
    
    def exists(self, interaction_id: str) -> bool:
        """Vérifie si une interaction existe.
        
        Args:
            interaction_id: L'identifiant unique de l'interaction.
            
        Returns:
            True si l'interaction existe, False sinon.
        """
        ... 