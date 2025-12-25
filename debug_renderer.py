"""Script de débogage pour le YarnRenderer."""

import os
import sys
import inspect

# Ajouter le répertoire parent au path pour permettre les imports relatifs
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from models.dialogue_structure import (
    DialogueLineElement, PlayerChoiceOption, PlayerChoicesBlockElement, Interaction
)
from services.yarn_renderer import JinjaYarnRenderer

def main():
    """Fonction principale de débogage."""
    # Création d'une interaction de test
    line1 = DialogueLineElement("Bonjour aventurier !", "Marchand")
    line2 = DialogueLineElement("Qu'est-ce qui vous amène dans ma boutique ?", "Marchand")
    
    choice1 = PlayerChoiceOption("Je cherche des armes", "acheter_armes")
    choice2 = PlayerChoiceOption("Je veux vendre des objets", "vendre_objets")
    choice3 = PlayerChoiceOption("Juste en train de regarder", "fin_dialogue")
    
    choices = PlayerChoicesBlockElement([choice1, choice2, choice3])
    
    interaction = Interaction(
        interaction_id="dialogue_marchand",
        elements=[line1, line2, choices],
        header_tags=["boutique", "marchand"],
        header_commands=["set $has_visited_shop = true"]
    )
    
    # Débogage des objets
    print("\n--- Objets de dialogue ---")
    print(f"DialogueLineElement: {dir(line1)}")
    print(f"line1.__dict__: {line1.__dict__}")
    print(f"PlayerChoiceOption: {dir(choice1)}")
    print(f"choice1.__dict__: {choice1.__dict__}")
    
    # Vérification des types et propriétés des éléments de l'interaction
    print("\n--- Éléments de l'interaction ---")
    for i, element in enumerate(interaction.elements):
        print(f"Élément {i+1} - Type: {element.__class__.__name__}")
        print(f"  Attributs: {element.__dict__}")
    
    # Création du renderer
    renderer = JinjaYarnRenderer()
    
    # Rendu de l'interaction
    result = renderer.render_to_string(interaction)
    
    # Affichage du résultat
    print("\nInteraction :")
    print(f"ID: {interaction.interaction_id}")
    print(f"Tags: {interaction.header_tags}")
    print(f"Commands: {interaction.header_commands}")
    print(f"Elements: {len(interaction.elements)}")
    
    print("\nRésultat du rendu :")
    print("-" * 50)
    print(result)
    print("-" * 50)
    
    # Écriture dans un fichier
    output_path = os.path.join(current_dir, "debug_output.yarn")
    renderer.render_to_file(interaction, output_path)
    print(f"\nFichier écrit : {output_path}")

if __name__ == "__main__":
    main() 
