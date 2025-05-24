import json
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional
import re # Ajout de re pour slugify
import uuid
from DialogueGenerator.models.dialogue_structure import Interaction

logger = logging.getLogger(__name__)

class FileInteractionRepository:
    """Implémentation du repository d'interactions utilisant des fichiers JSON.
    
    Cette implémentation stocke chaque interaction dans un fichier JSON distinct
    dans un dossier spécifié. Les fichiers sont nommés [slug-titre]_[interaction_id-uuid].json
    ou [interaction_id-uuid].json si le titre n'est pas disponible.
    """
    
    def __init__(self, storage_dir: str):
        """Initialise le repository avec un dossier de stockage.
        
        Args:
            storage_dir: Le chemin vers le dossier où stocker les fichiers JSON.
        """
        self.storage_dir = Path(storage_dir)
        os.makedirs(self.storage_dir, exist_ok=True)
        logger.info(f"FileInteractionRepository initialisé avec le dossier de stockage : {self.storage_dir.absolute()}")
    
    def _slugify_title(self, title: str, max_length: int = 50) -> str:
        """Nettoie et tronque un titre pour l'utiliser dans un nom de fichier."""
        if not title:
            return ""
        # Convertir en minuscules
        slug = title.lower()
        # Remplacer les caractères non alphanumériques par des underscores
        slug = re.sub(r'[^a-z0-9]+', '_', slug)
        # Supprimer les underscores en début et fin de chaîne
        slug = slug.strip('_')
        # Limiter la longueur
        if len(slug) > max_length:
            # Essayer de couper à un underscore si possible pour ne pas couper un mot
            if '_' in slug[:max_length]:
                slug = slug[:slug.rfind('_', 0, max_length)]
            else:
                slug = slug[:max_length]
        return slug

    def _construct_filename(self, interaction_id: str, title: Optional[str] = None) -> str:
        """Construit le nom de fichier pour une interaction.
        Format: [slug-titre]_[interaction_id-uuid].json ou [interaction_id-uuid].json.
        """
        try:
            # S'assurer que interaction_id est bien un UUID valide pour le nommage
            uuid_obj = uuid.UUID(interaction_id)
            id_part = str(uuid_obj)
        except ValueError:
            # Si ce n'est pas un UUID valide (cas d'anciens IDs ou IDs corrompus), 
            # on utilise l'ID tel quel mais on log un avertissement.
            # Cela ne devrait plus arriver avec la génération d'ID par UUID pur.
            logger.warning(f"L'ID d'interaction '{interaction_id}' n'est pas un UUID valide. Utilisation directe dans le nom de fichier.")
            id_part = interaction_id # Fallback pour les anciens IDs

        if title:
            slug = self._slugify_title(title)
            if slug: # Si le slug n'est pas vide après nettoyage
                return f"{slug}_{id_part}.json"
        return f"{id_part}.json" # Fallback si pas de titre ou slug vide

    def _get_file_path(self, interaction_id: str) -> Path:
        """DEPRECATED ou à réviser. Utiliser _find_file_path_for_id pour la lecture.
        Cette méthode construisait un nom de fichier basé uniquement sur l'ID.
        """
        # Cette méthode est simpliste et suppose que le nom de fichier est juste l'ID.
        # Avec le nouveau nommage, elle n'est plus fiable pour trouver un fichier existant.
        # Elle pourrait être utilisée pour _construire_ un chemin cible si on n'a pas le titre,
        # mais _construct_filename est plus approprié.
        logger.warning("_get_file_path est appelée, ce qui peut ne plus être correct pour trouver des fichiers existants.")
        return self.storage_dir / f"{interaction_id}.json"
    
    def get_by_id(self, interaction_id: str) -> Optional[Interaction]:
        """Récupère une interaction par son ID depuis le fichier correspondant.
        
        Args:
            interaction_id: L'identifiant unique de l'interaction.
            
        Returns:
            L'interaction si elle existe, None sinon.
        """
        file_path = self._find_file_path_for_id(interaction_id) # Modifié pour utiliser la recherche
        if not file_path or not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                interaction = Interaction.model_validate(data)
                # Optionnel: vérifier si le nom de fichier actuel correspond au nom attendu et renommer si besoin
                # expected_filename = self._construct_filename(interaction.interaction_id, interaction.title)
                # if file_path.name != expected_filename:
                #    logger.info(f"Nom de fichier désynchronisé pour {interaction.interaction_id}. Actuel: {file_path.name}, Attendu: {expected_filename}. L'interaction sera re-sauvegardée au prochain save().")
                return interaction
        except (json.JSONDecodeError, KeyError, FileNotFoundError, TypeError) as e: # Ajout TypeError pour from_dict
            logger.error(f"Erreur lors de la lecture ou du parsing de {file_path}: {e}")
            return None
    
    def save(self, interaction: Interaction) -> None:
        """Sauvegarde une interaction dans un fichier JSON.
        Le nom du fichier sera [slug-titre]_[interaction_id-uuid].json.
        Supprime les anciens fichiers pour cet ID si le nom de fichier change.
        """
        if not interaction or not hasattr(interaction, 'interaction_id'):
            logger.error("Tentative de sauvegarde d'une interaction invalide ou sans ID.")
            return

        # Construire le nom de fichier attendu/nouveau
        new_filename = self._construct_filename(interaction.interaction_id, getattr(interaction, 'title', None))
        new_file_path = self.storage_dir / new_filename

        # Rechercher les fichiers existants pour cet ID (UUID)
        # Ils pourraient avoir un ancien nom (juste UUID.json) ou un ancien slug.
        # L'ID de l'interaction est supposé être un UUID pur.
        try:
            uuid.UUID(interaction.interaction_id) # Valide que c'est bien un UUID
            # Modèles de recherche pour les fichiers potentiellement existants pour cet ID
            # 1. Nom de fichier exact avec slug différent et même UUID
            # 2. Nom de fichier étant juste l'UUID (ancien format)
            # Note : *_{interaction.interaction_id}.json inclut les fichiers avec slug.
            # {interaction.interaction_id}.json est pour les fichiers sans slug.
            
            existing_files_to_check = list(self.storage_dir.glob(f"*_{interaction.interaction_id}.json"))
            plain_uuid_file = self.storage_dir / f"{interaction.interaction_id}.json"
            if plain_uuid_file.exists() and plain_uuid_file not in existing_files_to_check:
                existing_files_to_check.append(plain_uuid_file)

            for existing_file in existing_files_to_check:
                if existing_file.resolve() != new_file_path.resolve(): # Vérifier si c'est un fichier différent du nouveau
                    logger.info(f"Suppression de l'ancien fichier d'interaction '{existing_file.name}' pour l'ID '{interaction.interaction_id}' car le nom de fichier cible est '{new_filename}'.")
                    try:
                        existing_file.unlink()
                    except OSError as e:
                        logger.error(f"Impossible de supprimer l'ancien fichier {existing_file}: {e}")
        
        except ValueError:
            # interaction.interaction_id n'est pas un UUID. Cela ne devrait pas arriver.
            # Dans ce cas, on ne peut pas faire de nettoyage intelligent basé sur l'UUID.
            logger.warning(f"L'ID {interaction.interaction_id} n'est pas un UUID. Le nettoyage d'anciens fichiers est ignoré.")


        # Sauvegarder l'interaction dans le nouveau fichier
        data = interaction.model_dump(mode='json')
        try:
            with open(new_file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Interaction '{getattr(interaction, 'title', 'N/A')}' (ID: {interaction.interaction_id}) sauvegardée dans '{new_filename}'.")
        except IOError as e:
            logger.error(f"Impossible de sauvegarder l'interaction dans {new_file_path}: {e}")

    def _find_file_path_for_id(self, interaction_id: str) -> Optional[Path]:
        """Trouve le chemin du fichier pour un ID d'interaction donné.
        Cherche d'abord un fichier avec un préfixe (slug), puis un fichier nommé uniquement avec l'ID.
        """
        try:
            uuid.UUID(interaction_id) # Vérifie que c'est un format UUID
        except ValueError:
            logger.warning(f"Tentative de recherche de fichier pour un ID non-UUID: {interaction_id}. Recherche directe du nom de fichier.")
            # Pour les IDs non-UUID (anciens/corrompus), on essaie une correspondance exacte.
            # Et aussi avec un préfixe slug, bien que la construction du slug sans titre ici soit impossible.
            # Cette branche ne devrait plus être atteinte avec les IDs UUID purs.
            direct_match = self.storage_dir / f"{interaction_id}.json"
            if direct_match.exists():
                return direct_match
            # La recherche avec glob *_{interaction_id}.json pourrait quand même fonctionner si l'ID est à la fin.
            
        # Chercher les fichiers qui se terminent par _interaction_id.json (format avec slug)
        # Le glob doit être sensible à la casse sur certains systèmes, mais les UUIDs sont souvent en minuscules.
        # Pour être sûr, on peut chercher les deux casses si nécessaire, mais UUID standard est minuscule.
        potential_files = list(self.storage_dir.glob(f"*_{interaction_id}.json"))
        if potential_files:
            if len(potential_files) > 1:
                logger.warning(f"Plusieurs fichiers trouvés pour l'ID {interaction_id} avec des slugs différents: {[f.name for f in potential_files]}. Retour du premier: {potential_files[0].name}")
            return potential_files[0]

        # Si non trouvé, chercher un fichier nommé juste interaction_id.json (ancien format sans slug)
        plain_file = self.storage_dir / f"{interaction_id}.json"
        if plain_file.exists():
            return plain_file
            
        return None

    def get_all(self) -> List[Interaction]:
        """Récupère toutes les interactions depuis tous les fichiers JSON.
        
        Returns:
            La liste de toutes les interactions.
        """
        logger.info(f"[DEBUG] FileRepo.get_all: dossier={self.storage_dir}")
        interactions = []
        
        # print(f"[DEBUG] Chargement des interactions depuis : {self.storage_dir.absolute()}")
        json_files = list(self.storage_dir.glob('*.json'))
        # print(f"[DEBUG] Fichiers JSON trouvés : {len(json_files)}")
        
        for file_path in json_files:
            # print(f"[DEBUG] Traitement du fichier : {file_path}")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    interaction = Interaction.model_validate(data)
                    interactions.append(interaction)
                    # print(f"[DEBUG] Interaction chargée : {interaction.interaction_id}, titre: {getattr(interaction, 'title', '<sans titre>')}")
                    logger.info(f"[DEBUG] Interaction chargée: id={getattr(interaction, 'interaction_id', None)}, titre={getattr(interaction, 'title', None)}")
            except (json.JSONDecodeError, KeyError, FileNotFoundError, TypeError) as e: # Ajout de TypeError
                logger.error(f"[DEBUG] Erreur lors de la lecture ou du parsing de {file_path}: {e}")
                continue
        
        # print(f"[DEBUG] Total des interactions chargées : {len(interactions)}")
        logger.info(f"[DEBUG] Total interactions lues: {len(interactions)}")
        return interactions
    
    def delete(self, interaction_id: str) -> bool:
        """Supprime le fichier d'une interaction par son ID.
        
        Args:
            interaction_id: L'identifiant unique de l'interaction à supprimer.
            
        Returns:
            True si l'interaction a été supprimée, False si elle n'existait pas.
        """
        file_path = self._find_file_path_for_id(interaction_id) # Modifié
        if file_path and file_path.exists():
            try:
                file_path.unlink()
                logger.info(f"Fichier d'interaction {file_path.name} (ID: {interaction_id}) supprimé.")
                return True
            except (PermissionError, OSError) as e:
                logger.error(f"Erreur lors de la suppression de {file_path}: {e}")
                return False
        logger.warning(f"Tentative de suppression d'une interaction non trouvée pour ID: {interaction_id}")
        return False
    
    def exists(self, interaction_id: str) -> bool:
        """Vérifie si un fichier d'interaction existe.
        
        Args:
            interaction_id: L'identifiant unique de l'interaction.
            
        Returns:
            True si l'interaction existe, False sinon.
        """
        file_path = self._find_file_path_for_id(interaction_id) # Modifié
        return file_path is not None and file_path.exists()
    
    def clear(self) -> None:
        """Supprime tous les fichiers d'interaction du dossier de stockage."""
        count = 0
        for file_path in self.storage_dir.glob('*.json'):
            try:
                file_path.unlink()
                count +=1
            except (PermissionError, OSError) as e:
                logger.error(f"Erreur lors de la suppression de {file_path}: {e}")
                continue
        logger.info(f"{count} fichier(s) d'interaction supprimé(s) du dossier {self.storage_dir}.")

    def add(self, interaction): # Conserver pour compatibilité potentielle avec IInteractionRepository si elle a add
        """Méthode alias pour save, pour une potentielle compatibilité d'interface."""
        logger.info(f"[DEBUG] FileRepo.add appelée (alias pour save): id={interaction.interaction_id}, titre={getattr(interaction, 'title', None)}")
        self.save(interaction) # Appelle la nouvelle logique de save
        # Le retour de save est None, add devrait peut-être retourner l'interaction ou un booléen.
        # Pour l'instant, on garde le comportement de save.
        return None # Ou interaction si l'interface le demande. 