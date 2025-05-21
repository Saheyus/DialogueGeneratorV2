"""Module pour parser les fichiers Yarn en objets Interaction."""

import re
from typing import List, Optional, Dict, Any, Union, Tuple

from DialogueGenerator.models.dialogue_structure import (
    DialogueLineElement, PlayerChoiceOption, PlayerChoicesBlockElement, Interaction
)

class YarnParser:
    """Parseur de fichiers Yarn pour les convertir en objets Interaction."""
    
    def __init__(self):
        """Initialise le parseur."""
        # Regex pour les différentes parties du fichier Yarn
        self.header_regex = r"title:\s*(?P<title>.*?)\n---\n(?P<headers>.*?)\n===\n"
        self.tags_regex = r"tags:\s*(?P<tags>.*?)(?:\n|$)"
        self.command_regex = r"<<(?P<command>.*?)>>"
        self.dialogue_regex = r"(?P<speaker>.*?):\s*(?P<text>.*?)(?:\n|$)"
        self.choice_start_regex = r"->\s*(?P<text>.*?)(?:\n|$)"
        self.jump_regex = r"<<jump\s+(?P<node_id>.*?)>>"
    
    def parse_file(self, file_path: str) -> Optional[Interaction]:
        """Parse un fichier Yarn et le convertit en objet Interaction.
        
        Args:
            file_path: Le chemin du fichier Yarn à parser.
            
        Returns:
            L'objet Interaction créé, ou None si le parsing a échoué.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return self.parse_string(content)
        except (FileNotFoundError, IOError) as e:
            print(f"Erreur lors de la lecture du fichier {file_path}: {e}")
            return None
    
    def parse_string(self, content: str) -> Optional[Interaction]:
        """Parse une chaîne de caractères au format Yarn et la convertit en objet Interaction.
        
        Args:
            content: Le contenu Yarn à parser.
            
        Returns:
            L'objet Interaction créé, ou None si le parsing a échoué.
        """
        try:
            # Extraction de l'en-tête et du contenu
            header_match = re.search(self.header_regex, content, re.DOTALL)
            if not header_match:
                print("Erreur: format Yarn invalide, en-tête introuvable")
                return None
                
            title = header_match.group('title').strip()
            headers = header_match.group('headers')
            
            # Extraction du contenu (tout ce qui est après l'en-tête et avant la fin)
            body_start = header_match.end()
            body_end = content.rfind('===')
            if body_end <= body_start:
                print("Erreur: format Yarn invalide, balise de fin introuvable")
                return None
                
            body = content[body_start:body_end].strip()
            
            # Extraction des tags et des commandes
            tags = []
            tag_match = re.search(self.tags_regex, headers)
            if tag_match:
                tags = [tag.strip() for tag in tag_match.group('tags').split(',')]
            
            commands = []
            for cmd_match in re.finditer(self.command_regex, headers):
                commands.append(cmd_match.group('command').strip())
            
            # Parsing du contenu pour extraire les éléments de dialogue
            elements = self._parse_body(body)
            
            # Création de l'objet Interaction
            return Interaction(
                interaction_id=title,
                elements=elements,
                header_tags=tags,
                header_commands=commands
            )
        except Exception as e:
            print(f"Erreur lors du parsing: {e}")
            return None
    
    def _parse_body(self, body: str) -> List[Union[DialogueLineElement, PlayerChoicesBlockElement]]:
        """Parse le corps du fichier Yarn pour en extraire les éléments de dialogue.
        
        Args:
            body: Le corps du fichier Yarn.
            
        Returns:
            Une liste d'éléments de dialogue.
        """
        elements = []
        lines = body.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Si la ligne est vide, on passe à la suivante
            if not line:
                i += 1
                continue
            
            # Si c'est une ligne de dialogue
            dialogue_match = re.match(self.dialogue_regex, line)
            if dialogue_match:
                speaker = dialogue_match.group('speaker').strip()
                text = dialogue_match.group('text').strip()
                elements.append(DialogueLineElement(text=text, speaker=speaker))
                i += 1
                continue
            
            # Si c'est un début de choix
            choice_match = re.match(self.choice_start_regex, line)
            if choice_match:
                choices, new_i = self._parse_choices(lines, i)
                if choices:
                    elements.append(PlayerChoicesBlockElement(choices))
                i = new_i
                continue
            
            # Si c'est une commande, on l'ignore pour l'instant
            # (on pourrait l'ajouter à l'élément précédent si nécessaire)
            i += 1
        
        return elements
    
    def _parse_choices(self, lines: List[str], start_index: int) -> Tuple[List[PlayerChoiceOption], int]:
        """Parse les choix à partir de l'indice de départ.
        
        Args:
            lines: Les lignes du fichier Yarn.
            start_index: L'indice de la première ligne de choix.
            
        Returns:
            Un tuple contenant la liste des choix et l'indice de la ligne après les choix.
        """
        choices = []
        i = start_index
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Si c'est un début de choix
            choice_match = re.match(self.choice_start_regex, line)
            if choice_match:
                text = choice_match.group('text').strip()
                
                # Recherche du saut associé
                next_interaction_id = None
                if i + 1 < len(lines):
                    jump_line = lines[i + 1].strip()
                    jump_match = re.search(self.jump_regex, jump_line)
                    if jump_match:
                        next_interaction_id = jump_match.group('node_id').strip()
                        i += 2  # On saute la ligne du choix et celle du saut
                    else:
                        i += 1  # On saute seulement la ligne du choix
                else:
                    i += 1
                
                # Ajout du choix
                choices.append(PlayerChoiceOption(
                    text=text, 
                    next_interaction_id=next_interaction_id or ""
                ))
                continue
            
            # Si ce n'est pas un choix, on quitte la boucle
            break
        
        return choices, i 