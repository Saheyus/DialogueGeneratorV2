from typing import Protocol, Dict, Any, Optional
from models.dialogue_structure import Interaction

class IYarnRenderer(Protocol):
    """Interface pour le rendu des interactions en format Yarn Spinner."""
    
    def render_to_string(self, interaction: Interaction) -> str:
        """Rend une interaction en texte au format Yarn Spinner.
        
        Args:
            interaction: L'interaction à rendre.
            
        Returns:
            Le contenu du fichier Yarn généré sous forme de chaîne.
        """
        ...
    
    def render_to_file(self, interaction: Interaction, output_path: str) -> None:
        """Rend une interaction et l'écrit dans un fichier Yarn.
        
        Args:
            interaction: L'interaction à rendre.
            output_path: Le chemin du fichier de sortie.
        """
        ...
    
    def set_template_variables(self, variables: Dict[str, Any]) -> None:
        """Définit des variables à utiliser dans le rendu des templates.
        
        Ces variables peuvent être utilisées pour ajouter des informations 
        contextuelles lors du rendu (par exemple: informations sur le jeu, 
        métadonnées spécifiques, etc.).
        
        Args:
            variables: Dictionnaire des variables à utiliser dans les templates.
        """
        ...
    
    def get_template_variables(self) -> Dict[str, Any]:
        """Récupère les variables de template actuelles.
        
        Returns:
            Dictionnaire des variables utilisées dans les templates.
        """
        ... 
