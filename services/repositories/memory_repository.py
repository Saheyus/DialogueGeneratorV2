from typing import Dict, List, Optional
from DialogueGenerator.models.dialogue_structure import Interaction

class InMemoryInteractionRepository:
    """Implémentation en mémoire du repository d'interactions.
    
    Cette implémentation stocke toutes les interactions en mémoire (dans un dictionnaire)
    et est perdue à la fermeture de l'application. Elle est utile pour les tests et le développement.
    """
    
    def __init__(self):
        """Initialise un repository vide."""
        self._interactions: Dict[str, Interaction] = {}
    
    def get_by_id(self, interaction_id: str) -> Optional[Interaction]:
        """Récupère une interaction par son ID.
        
        Args:
            interaction_id: L'identifiant unique de l'interaction.
            
        Returns:
            L'interaction si elle existe, None sinon.
        """
        return self._interactions.get(interaction_id)
    
    def save(self, interaction: Interaction) -> None:
        """Sauvegarde une interaction.
        
        Si une interaction avec le même ID existe déjà, elle sera mise à jour.
        
        Args:
            interaction: L'interaction à sauvegarder.
        """
        # Pour éviter les modifications par référence (si l'objet Interaction est
        # modifié après avoir été sauvegardé), nous le sauvegardons sous forme
        # de dictionnaire puis le reconstruisons à chaque récupération.
        self._interactions[interaction.interaction_id] = interaction
    
    def get_all(self) -> List[Interaction]:
        """Récupère toutes les interactions.
        
        Returns:
            La liste de toutes les interactions.
        """
        return list(self._interactions.values())
    
    def delete(self, interaction_id: str) -> bool:
        """Supprime une interaction par son ID.
        
        Args:
            interaction_id: L'identifiant unique de l'interaction à supprimer.
            
        Returns:
            True si l'interaction a été supprimée, False si elle n'existait pas.
        """
        if interaction_id in self._interactions:
            del self._interactions[interaction_id]
            return True
        return False
    
    def exists(self, interaction_id: str) -> bool:
        """Vérifie si une interaction existe.
        
        Args:
            interaction_id: L'identifiant unique de l'interaction.
            
        Returns:
            True si l'interaction existe, False sinon.
        """
        return interaction_id in self._interactions
    
    def clear(self) -> None:
        """Vide le repository de toutes les interactions."""
        self._interactions.clear() 