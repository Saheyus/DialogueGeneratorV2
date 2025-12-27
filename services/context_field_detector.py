"""Service pour détecter automatiquement les champs disponibles dans les fiches GDD."""
import logging
from typing import List, Dict, Set, Optional, Any
from collections import defaultdict
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class FieldInfo:
    """Informations sur un champ détecté."""
    path: str
    label: str
    type: str  # "string", "list", "dict"
    depth: int
    frequency: float  # % de fiches ayant ce champ (0.0 à 1.0)
    suggested: bool = False  # Suggéré pour le type de génération
    category: Optional[str] = None  # "identity", "characterization", "voice", "background", "mechanics"
    is_essential: bool = False  # Champ essentiel (court, toujours sélectionné, non désélectionnable)


class ContextFieldDetector:
    """Détecte automatiquement les champs disponibles dans les fiches GDD."""
    
    # Mapping des types d'éléments vers les attributs dans ContextBuilder
    ELEMENT_TYPE_TO_ATTR = {
        "character": "characters",
        "location": "locations",
        "item": "items",
        "species": "species",
        "community": "communities",
    }
    
    # Catégories de champs pour l'organisation narrative
    FIELD_CATEGORIES = {
        "identity": ["Nom", "Alias", "Occupation", "Archétype", "Type", "Rôle", "Catégorie"],
        "characterization": ["Désir", "Faiblesse", "Compulsion", "Qualités", "Défauts"],
        "voice": ["Dialogue Type", "Registre", "Champs lexicaux", "Expressions courantes"],
        "background": ["Background", "Contexte", "Histoire", "Relations", "Évènements", "Centres d'intérêt"],
        "mechanics": ["Pouvoirs", "Héritage", "Stats", "Compétences", "Traits"],
    }
    
    def __init__(self, context_builder=None):
        """Initialise le détecteur.
        
        Args:
            context_builder: Instance de ContextBuilder pour accéder aux données GDD.
        """
        self.context_builder = context_builder
    
    def detect_available_fields(
        self, 
        element_type: str, 
        sample_data: Optional[List[Dict]] = None
    ) -> Dict[str, FieldInfo]:
        """Détecte tous les champs disponibles pour un type d'élément.
        
        Args:
            element_type: Type d'élément ("character", "location", "item", "species", "community")
            sample_data: Données d'échantillon. Si None, utilise les données du ContextBuilder.
            
        Returns:
            Dictionnaire de {path: FieldInfo} pour tous les champs détectés.
        """
        if sample_data is None:
            sample_data = self._get_sample_data(element_type)
        
        if not sample_data:
            logger.warning(f"Aucune donnée disponible pour le type '{element_type}'")
            return {}
        
        # Collecter tous les champs avec leur fréquence
        field_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "count": 0,
            "types": set(),
            "max_depth": 0,
            "paths": set()
        })
        
        total_items = len(sample_data)
        
        for item in sample_data:
            if not isinstance(item, dict):
                continue
            
            # Extraire tous les chemins de champs (y compris imbriqués)
            paths = self._extract_all_paths(item)
            
            for path, value, depth in paths:
                field_stats[path]["count"] += 1
                field_stats[path]["types"].add(self._get_value_type(value))
                field_stats[path]["max_depth"] = max(field_stats[path]["max_depth"], depth)
                field_stats[path]["paths"].add(path)
        
        # Convertir en FieldInfo
        fields = {}
        for path, stats in field_stats.items():
            frequency = stats["count"] / total_items if total_items > 0 else 0.0
            
            # Déterminer le type principal (le plus fréquent)
            type_str = self._determine_primary_type(stats["types"])
            
            # Générer un label lisible
            label = self._generate_label(path)
            
            # Déterminer la catégorie
            category = self._categorize_field(path, element_type)
            
            fields[path] = FieldInfo(
                path=path,
                label=label,
                type=type_str,
                depth=stats["max_depth"],
                frequency=frequency,
                suggested=False,  # Sera déterminé par FieldSuggestionService
                category=category
            )
        
        logger.info(f"Détecté {len(fields)} champs pour '{element_type}' sur {total_items} fiches")
        return fields
    
    def _get_sample_data(self, element_type: str) -> List[Dict]:
        """Récupère les données d'échantillon depuis ContextBuilder."""
        if not self.context_builder:
            logger.warning("ContextBuilder non fourni, impossible de récupérer les données")
            return []
        
        attr_name = self.ELEMENT_TYPE_TO_ATTR.get(element_type.lower())
        if not attr_name:
            logger.warning(f"Type d'élément inconnu: {element_type}")
            return []
        
        data = getattr(self.context_builder, attr_name, [])
        if not isinstance(data, list):
            return []
        
        return [item for item in data if isinstance(item, dict)]
    
    def _extract_all_paths(
        self, 
        data: Dict, 
        prefix: str = "", 
        depth: int = 0
    ) -> List[tuple]:
        """Extrait tous les chemins de champs d'un dictionnaire, y compris imbriqués.
        
        Returns:
            Liste de tuples (path, value, depth)
        """
        paths = []
        
        for key, value in data.items():
            current_path = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict):
                # Récursif pour les dictionnaires imbriqués
                paths.extend(self._extract_all_paths(value, current_path, depth + 1))
                # Ajouter aussi le chemin du dict lui-même
                paths.append((current_path, value, depth))
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                # Liste de dictionnaires - extraire les champs du premier élément
                if value:
                    paths.append((current_path, value, depth))
                    # Optionnel: extraire les champs du premier élément comme exemple
                    paths.extend(self._extract_all_paths(value[0], current_path, depth + 1))
            else:
                # Valeur simple (string, number, list simple, etc.)
                paths.append((current_path, value, depth))
        
        return paths
    
    def _get_value_type(self, value: Any) -> str:
        """Détermine le type d'une valeur."""
        if isinstance(value, dict):
            return "dict"
        elif isinstance(value, list):
            return "list"
        elif isinstance(value, str):
            return "string"
        elif isinstance(value, (int, float)):
            return "number"
        elif isinstance(value, bool):
            return "boolean"
        else:
            return "unknown"
    
    def _determine_primary_type(self, types: Set[str]) -> str:
        """Détermine le type principal parmi plusieurs types observés."""
        # Priorité: dict > list > string > number > boolean > unknown
        priority = ["dict", "list", "string", "number", "boolean", "unknown"]
        for ptype in priority:
            if ptype in types:
                return ptype
        return "unknown"
    
    def _generate_label(self, path: str) -> str:
        """Génère un label lisible à partir d'un chemin."""
        # Prendre la dernière partie du chemin
        parts = path.split(".")
        last_part = parts[-1]
        
        # Remplacer les underscores et capitaliser
        label = last_part.replace("_", " ").replace("-", " ")
        # Capitaliser chaque mot
        label = " ".join(word.capitalize() for word in label.split())
        
        # Si le chemin a plusieurs parties, ajouter le contexte
        if len(parts) > 1:
            parent = parts[-2].replace("_", " ").capitalize()
            label = f"{parent} > {label}"
        
        return label
    
    def _categorize_field(self, path: str, element_type: str) -> Optional[str]:
        """Catégorise un champ selon son chemin."""
        path_lower = path.lower()
        
        # Catégories spécifiques par type (vérifier en premier pour avoir la priorité)
        if element_type == "character":
            if "dialogue" in path_lower or "voix" in path_lower or "langage" in path_lower:
                return "voice"
            if "caractérisation" in path_lower:
                return "characterization"
            if "background" in path_lower or "histoire" in path_lower or "relations" in path_lower:
                return "background"
            if "pouvoir" in path_lower or "héritage" in path_lower or "compétence" in path_lower:
                return "mechanics"
        
        # Vérifier chaque catégorie
        for category, keywords in self.FIELD_CATEGORIES.items():
            for keyword in keywords:
                if keyword.lower() in path_lower:
                    return category
        
        # Par défaut, essayer de deviner depuis le chemin
        if any(kw in path_lower for kw in ["nom", "alias", "occupation", "type", "rôle"]):
            return "identity"
        
        return None
    
    def classify_field_importance(self, frequency: float) -> str:
        """Classifie l'importance d'un champ selon sa fréquence.
        
        Returns:
            "essential" (>80%), "common" (20-80%), "rare" (<20%)
        """
        if frequency >= 0.8:
            return "essential"
        elif frequency >= 0.2:
            return "common"
        else:
            return "rare"
    
    def _identify_essential_fields(self, element_type: str, context_config: Dict) -> Set[str]:
        """Identifie les champs essentiels depuis context_config.json et par analyse des données.
        
        Les champs essentiels sont :
        1. Ceux avec truncate: -1 ou truncate <= 200 dans context_config.json
        2. Les champs de catégorie "identity" (Type, État, Espèce, Genre, Âge, etc.)
        3. Les champs avec des valeurs typiquement courtes (tags, sélecteurs, nombres, dates)
        
        Args:
            element_type: Type d'élément
            context_config: Configuration depuis context_config.json
            
        Returns:
            Set des chemins de champs essentiels
        """
        essential_fields = set()
        ESSENTIAL_TRUNCATE_THRESHOLD = 200
        
        # 1. Champs depuis context_config.json
        element_config = context_config.get(element_type, {})
        for priority_level, fields in element_config.items():
            for field_config in fields:
                path = field_config.get("path", "")
                if path:
                    truncate = field_config.get("truncate", -1)
                    if truncate == -1 or (isinstance(truncate, int) and truncate <= ESSENTIAL_TRUNCATE_THRESHOLD):
                        essential_fields.add(path)
        
        # 2. Identifier les champs essentiels par analyse des données réelles
        if self.context_builder:
            sample_data = self._get_sample_data(element_type)
            if sample_data:
                detected_fields = self.detect_available_fields(element_type, sample_data)
                
                logger.info(f"Analyse de {len(detected_fields)} champs détectés pour identifier les métadonnées")
                for path, field_info in detected_fields.items():
                    # Si déjà dans essential_fields, on skip
                    if path in essential_fields:
                        continue
                    
                    # Vérifier si c'est une métadonnée Notion typique
                    is_metadata = self._is_metadata_field(path, field_info, sample_data)
                    if is_metadata:
                        essential_fields.add(path)
                        logger.debug(f"Champ '{path}' identifié comme métadonnée (catégorie: {field_info.category}, type: {field_info.type})")
        
        return essential_fields
    
    def _is_metadata_field(self, path: str, field_info: FieldInfo, sample_data: List[Dict]) -> bool:
        """Détermine si un champ est une métadonnée Notion (court, essentiel).
        
        Les métadonnées sont typiquement :
        - Champs de catégorie "identity" (Type, État, Espèce, Genre, Âge, etc.)
        - Champs avec valeurs courtes (tags, sélecteurs, nombres, dates)
        - Relations simples (listes courtes de noms)
        - Champs booléens
        
        Args:
            path: Chemin du champ
            field_info: Informations sur le champ
            sample_data: Données d'échantillon pour analyser les valeurs
            
        Returns:
            True si le champ est une métadonnée
        """
        # 1. Vérifier la catégorie
        if field_info.category == "identity":
            return True
        
        # 2. Vérifier les noms de champs typiques des métadonnées Notion
        path_lower = path.lower()
        metadata_keywords = [
            "type", "état", "state", "espèce", "species", "genre", "gender",
            "âge", "age", "qualités", "qualities", "défauts", "flaws",
            "archétype", "archetype", "axe", "idéologique", "ideological",
            "communautés", "communities", "lieux", "places", "relations",
            "détient", "possesses", "portrait", "référence", "reference",
            "sprint", "dates", "assets", "scènes", "scenes", "dialogues",
            "présence", "presence", "feuilles", "sheets"
        ]
        
        for keyword in metadata_keywords:
            if keyword in path_lower:
                return True
        
        # 3. Analyser les valeurs réelles pour déterminer si elles sont courtes
        if sample_data:
            max_value_length = 0
            total_samples = 0
            
            for item in sample_data[:10]:  # Analyser jusqu'à 10 échantillons
                value = self._extract_field_value(item, path)
                if value is not None:
                    total_samples += 1
                    value_str = self._value_to_string(value)
                    max_value_length = max(max_value_length, len(value_str))
            
            # Si toutes les valeurs sont courtes (< 150 caractères), c'est probablement une métadonnée
            if total_samples > 0 and max_value_length < 150:
                # Vérifier aussi le type : listes courtes, nombres, booléens sont des métadonnées
                if field_info.type in ["list", "number", "boolean"]:
                    return True
                # Si c'est une liste de tags courts
                if field_info.type == "list":
                    for item in sample_data[:5]:
                        value = self._extract_field_value(item, path)
                        if isinstance(value, list) and len(value) > 0:
                            # Si les éléments de la liste sont courts (tags)
                            for elem in value[:3]:  # Vérifier les 3 premiers
                                elem_str = str(elem)
                                if len(elem_str) > 50:  # Si un élément est long, ce n'est pas une métadonnée
                                    return False
                            return True
            
            # Si la valeur max est très courte (< 50), c'est sûrement une métadonnée
            if total_samples > 0 and max_value_length < 50:
                return True
        
        return False
    
    def _extract_field_value(self, data: Dict, path: str) -> Optional[Any]:
        """Extrait la valeur d'un champ depuis un chemin."""
        keys = path.split(".")
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        
        return current
    
    def _value_to_string(self, value: Any) -> str:
        """Convertit une valeur en string pour mesurer sa longueur."""
        if isinstance(value, (list, tuple)):
            # Pour les listes, joindre les éléments
            if not value:
                return ""
            if isinstance(value[0], dict):
                # Liste de dicts - extraire les noms si possible
                names = [item.get("Nom", item.get("Titre", str(item))) for item in value]
                return ", ".join(names)
            else:
                return ", ".join(str(item) for item in value)
        elif isinstance(value, dict):
            # Pour les dicts, essayer de trouver un résumé ou convertir en JSON
            if "Résumé" in value or "Résumé de la fiche" in value:
                return str(value.get("Résumé") or value.get("Résumé de la fiche", ""))
            # Sinon, juste la représentation string
            return str(value)
        else:
            return str(value)

