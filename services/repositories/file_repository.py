import json
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional
from DialogueGenerator.models.dialogue_structure import Interaction

logger = logging.getLogger(__name__)

class FileInteractionRepository:
    """Implémentation du repository d'interactions utilisant des fichiers JSON.
    
    Cette implémentation stocke chaque interaction dans un fichier JSON distinct
    dans un dossier spécifié. Les fichiers sont nommés [interaction_id].json.
    """
    
    def __init__(self, storage_dir: str):
        """Initialise le repository avec un dossier de stockage.
        
        Args:
            storage_dir: Le chemin vers le dossier où stocker les fichiers JSON.
        """
        self.storage_dir = Path(storage_dir)
        os.makedirs(self.storage_dir, exist_ok=True)
        logger.info(f"FileInteractionRepository initialisé avec le dossier de stockage : {self.storage_dir.absolute()}")
    
    def _get_file_path(self, interaction_id: str) -> Path:
        """Obtient le chemin du fichier pour une interaction donnée.
        
        Args:
            interaction_id: L'identifiant unique de l'interaction.
            
        Returns:
            Le chemin du fichier JSON correspondant.
        """
        return self.storage_dir / f"{interaction_id}.json"
    
    def get_by_id(self, interaction_id: str) -> Optional[Interaction]:
        """Récupère une interaction par son ID depuis le fichier correspondant.
        
        Args:
            interaction_id: L'identifiant unique de l'interaction.
            
        Returns:
            L'interaction si elle existe, None sinon.
        """
        file_path = self._get_file_path(interaction_id)
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return Interaction.from_dict(data)
        except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
            print(f"Erreur lors de la lecture de {file_path}: {e}")
            return None
    
    def save(self, interaction: Interaction) -> None:
        """Sauvegarde une interaction dans un fichier JSON.
        
        Args:
            interaction: L'interaction à sauvegarder.
        """
        file_path = self._get_file_path(interaction.interaction_id)
        data = interaction.to_dict()
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def get_all(self) -> List[Interaction]:
        """Récupère toutes les interactions depuis tous les fichiers JSON.
        
        Returns:
            La liste de toutes les interactions.
        """
        logger.info(f"[DEBUG] FileRepo.get_all: dossier={self.storage_dir}")
        interactions = []
        
        print(f"[DEBUG] Chargement des interactions depuis : {self.storage_dir.absolute()}")
        json_files = list(self.storage_dir.glob('*.json'))
        print(f"[DEBUG] Fichiers JSON trouvés : {len(json_files)}")
        
        for file_path in json_files:
            print(f"[DEBUG] Traitement du fichier : {file_path}")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    interaction = Interaction.from_dict(data)
                    interactions.append(interaction)
                    print(f"[DEBUG] Interaction chargée : {interaction.interaction_id}, titre: {getattr(interaction, 'title', '<sans titre>')}")
                    logger.info(f"[DEBUG] Interaction chargée: id={getattr(interaction, 'interaction_id', None)}, titre={getattr(interaction, 'title', None)}")
            except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
                print(f"[DEBUG] Erreur lors de la lecture de {file_path}: {e}")
                continue
        
        print(f"[DEBUG] Total des interactions chargées : {len(interactions)}")
        logger.info(f"[DEBUG] Total interactions lues: {len(interactions)}")
        return interactions
    
    def delete(self, interaction_id: str) -> bool:
        """Supprime le fichier d'une interaction par son ID.
        
        Args:
            interaction_id: L'identifiant unique de l'interaction à supprimer.
            
        Returns:
            True si l'interaction a été supprimée, False si elle n'existait pas.
        """
        file_path = self._get_file_path(interaction_id)
        if file_path.exists():
            try:
                file_path.unlink()
                return True
            except (PermissionError, OSError) as e:
                print(f"Erreur lors de la suppression de {file_path}: {e}")
                return False
        return False
    
    def exists(self, interaction_id: str) -> bool:
        """Vérifie si un fichier d'interaction existe.
        
        Args:
            interaction_id: L'identifiant unique de l'interaction.
            
        Returns:
            True si l'interaction existe, False sinon.
        """
        file_path = self._get_file_path(interaction_id)
        return file_path.exists()
    
    def clear(self) -> None:
        """Supprime tous les fichiers d'interaction du dossier de stockage."""
        for file_path in self.storage_dir.glob('*.json'):
            try:
                file_path.unlink()
            except (PermissionError, OSError) as e:
                print(f"Erreur lors de la suppression de {file_path}: {e}")
                continue

    def add(self, interaction):
        logger.info(f"[DEBUG] FileRepo.add: id={interaction.interaction_id}, titre={getattr(interaction, 'title', None)}")
        path = self._get_file_path(interaction.interaction_id)
        logger.info(f"[DEBUG] Chemin de sauvegarde: {path}")
        with open(path, 'w', encoding='utf-8') as f:
            f.write(interaction.to_json())
        logger.info(f"[DEBUG] Interaction écrite dans {path}")
        return interaction 