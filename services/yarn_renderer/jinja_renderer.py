import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import jinja2

from DialogueGenerator.models.dialogue_structure import (
    Interaction, 
    AnyDialogueElement,
    DialogueLineElement,
    PlayerChoicesBlockElement, PlayerChoiceOption,
    CommandElement
)

class JinjaYarnRenderer:
    """Implémentation du renderer Yarn utilisant Jinja2 pour les templates."""
    
    DEFAULT_TEMPLATE_PATH = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 
        "templates"
    )
    
    def __init__(self, template_dir: Optional[str] = None):
        """Initialise le renderer avec un dossier de templates optionnel.
        
        Args:
            template_dir: Le chemin vers le dossier contenant les templates Jinja2.
                          Si non spécifié, utilise le dossier 'templates' par défaut.
        """
        template_path = template_dir or self.DEFAULT_TEMPLATE_PATH
        
        # Création du dossier de templates s'il n'existe pas
        os.makedirs(template_path, exist_ok=True)
        
        # Configuration de l'environnement Jinja2
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_path),
            trim_blocks=True,
            lstrip_blocks=True,
            autoescape=False  # Pas d'échappement HTML nécessaire pour Yarn
        )
        
        # Variables de template par défaut
        self._template_variables: Dict[str, Any] = {}
    
    def set_template_variables(self, variables: Dict[str, Any]) -> None:
        """Définit des variables à utiliser dans le rendu des templates.
        
        Args:
            variables: Dictionnaire des variables à utiliser dans les templates.
        """
        self._template_variables = variables.copy()
    
    def get_template_variables(self) -> Dict[str, Any]:
        """Récupère les variables de template actuelles.
        
        Returns:
            Dictionnaire des variables utilisées dans les templates.
        """
        return self._template_variables.copy()
    
    def render_to_string(self, interaction: Interaction) -> str:
        """Rend une interaction en texte au format Yarn Spinner.
        
        Args:
            interaction: L'interaction à rendre.
            
        Returns:
            Le contenu du fichier Yarn généré sous forme de chaîne.
        """
        # Construction du contexte pour le template
        context = {
            'interaction': interaction,
            'header_tags': interaction.header_tags,
            'header_commands': interaction.header_commands,
            'elements': interaction.elements,
            **self._template_variables
        }
        
        try:
            # Tente de charger le template par défaut
            template = self.env.get_template('default.yarn.jinja')
        except jinja2.exceptions.TemplateNotFound:
            # Utilisation d'un template en chaîne si le fichier n'existe pas
            template_content = self._get_default_template()
            template = self.env.from_string(template_content)
        
        return template.render(**context)
    
    def render_to_file(self, interaction: Interaction, output_path: str) -> None:
        """Rend une interaction et l'écrit dans un fichier Yarn.
        
        Args:
            interaction: L'interaction à rendre.
            output_path: Le chemin du fichier de sortie.
        """
        # Génération du contenu
        content = self.render_to_string(interaction)
        
        # Création du dossier de sortie si nécessaire
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        # Écriture dans le fichier
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _get_default_template(self) -> str:
        """Retourne le template par défaut pour le rendu Yarn.
        
        Returns:
            Le contenu du template par défaut sous forme de chaîne.
        """
        return """title: {{ interaction.title if interaction.title else interaction.interaction_id }}
---
{% if header_tags %}
tags: {{ header_tags|join(', ') }}
{% endif %}
{% if header_commands %}
{% for command in header_commands %}
<<{{ command }}>>
{% endfor %}
{% endif %}
===

{% for element in elements %}
{% if element.element_type == 'dialogue_line' %}
{{ element.speaker if element.speaker else 'Narrateur' }}: {{ element.text }}
{% for cmd in element.pre_line_commands %}<<{{ cmd }}>>
{% endfor %}
{% if element.speaker if element.speaker else 'Narrateur' %}: {% endif %}{{ element.text }}
{% for cmd in element.post_line_commands %}<<{{ cmd }}>>
{% endfor %}
{% elif element.element_type == 'player_choices_block' %}
{% for choice in element.choices %}
-> {{ choice.text }}
    <<jump {{ choice.next_interaction_id }}>>
{% endfor %}
{% elif element.element_type == 'command' %}
<<{{ element.command_string }}>>
{% endif %}
{% endfor %}
===""" 