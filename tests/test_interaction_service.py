import unittest
from unittest.mock import patch, MagicMock
import sys
import os
from pathlib import Path

# Ajuster le sys.path pour permettre l'import de DialogueGenerator
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from DialogueGenerator.services.interaction_service import InteractionService
from DialogueGenerator.services.repositories import InMemoryInteractionRepository
from DialogueGenerator.models.dialogue_structure.interaction import Interaction
from DialogueGenerator.models.dialogue_structure.dialogue_elements import (
    DialogueLineElement, PlayerChoicesBlockElement, PlayerChoiceOption
)

class TestInteractionService(unittest.TestCase):
    """Tests pour InteractionService, en particulier l'index des parents."""

    def setUp(self):
        """Initialise un service avec repository en mémoire pour chaque test."""
        self.repo = InMemoryInteractionRepository()
        self.service = InteractionService(self.repo)

    def test_empty_service_initialization(self):
        """Teste l'initialisation d'un service vide."""
        self.assertEqual(len(self.service.get_all()), 0)
        self.assertEqual(len(self.service._parent_index), 0)

    def test_parent_index_creation_simple_chain(self):
        """Teste la création de l'index avec une chaîne simple d'interactions."""
        # Créer trois interactions liées en chaîne
        interaction1 = Interaction(
            interaction_id="interaction1",
            elements=[DialogueLineElement(text="Bonjour!")],
            next_interaction_id_if_no_choices="interaction2"
        )
        
        interaction2 = Interaction(
            interaction_id="interaction2", 
            elements=[
                DialogueLineElement(text="Comment allez-vous?"),
                PlayerChoicesBlockElement(choices=[
                    PlayerChoiceOption(text="Bien", next_interaction_id="interaction3"),
                    PlayerChoiceOption(text="Mal", next_interaction_id="interaction4")
                ])
            ]
        )
        
        interaction3 = Interaction(
            interaction_id="interaction3",
            elements=[DialogueLineElement(text="Tant mieux!")]
        )
        
        interaction4 = Interaction(
            interaction_id="interaction4",
            elements=[DialogueLineElement(text="Désolé d'entendre ça.")]
        )
        
        # Sauvegarder les interactions
        self.service.save(interaction1)
        self.service.save(interaction2)
        self.service.save(interaction3)
        self.service.save(interaction4)
        
        # Vérifier l'index des parents
        # interaction2 doit avoir interaction1 comme parent (transition auto)
        self.assertIn("interaction2", self.service._parent_index)
        self.assertEqual(self.service._parent_index["interaction2"], [("interaction1", -1)])
        
        # interaction3 doit avoir interaction2 comme parent (choix index 0)
        self.assertIn("interaction3", self.service._parent_index)
        self.assertEqual(self.service._parent_index["interaction3"], [("interaction2", 0)])
        
        # interaction4 doit avoir interaction2 comme parent (choix index 1)
        self.assertIn("interaction4", self.service._parent_index)
        self.assertEqual(self.service._parent_index["interaction4"], [("interaction2", 1)])
        
        # interaction1 ne doit pas être dans l'index (pas d'enfant)
        self.assertNotIn("interaction1", self.service._parent_index)

    def test_get_dialogue_path_simple_chain(self):
        """Teste la reconstruction du chemin de dialogue."""
        # Utiliser les mêmes interactions que le test précédent
        interaction1 = Interaction(
            interaction_id="interaction1",
            elements=[DialogueLineElement(text="Bonjour!")],
            next_interaction_id_if_no_choices="interaction2"
        )
        
        interaction2 = Interaction(
            interaction_id="interaction2", 
            elements=[
                DialogueLineElement(text="Comment allez-vous?"),
                PlayerChoicesBlockElement(choices=[
                    PlayerChoiceOption(text="Bien", next_interaction_id="interaction3")
                ])
            ]
        )
        
        interaction3 = Interaction(
            interaction_id="interaction3",
            elements=[DialogueLineElement(text="Tant mieux!")]
        )
        
        # Sauvegarder
        self.service.save(interaction1)
        self.service.save(interaction2)
        self.service.save(interaction3)
        
        # Tester le chemin vers interaction3
        path = self.service.get_dialogue_path("interaction3")
        self.assertEqual(len(path), 3)
        self.assertEqual(path[0].interaction_id, "interaction1")
        self.assertEqual(path[1].interaction_id, "interaction2")
        self.assertEqual(path[2].interaction_id, "interaction3")
        
        # Tester le chemin vers interaction2
        path = self.service.get_dialogue_path("interaction2")
        self.assertEqual(len(path), 2)
        self.assertEqual(path[0].interaction_id, "interaction1")
        self.assertEqual(path[1].interaction_id, "interaction2")
        
        # Tester le chemin vers interaction1 (racine)
        path = self.service.get_dialogue_path("interaction1")
        self.assertEqual(len(path), 1)
        self.assertEqual(path[0].interaction_id, "interaction1")

    def test_get_choice_text_for_transition(self):
        """Teste la récupération du texte d'un choix pour une transition."""
        interaction_parent = Interaction(
            interaction_id="parent",
            elements=[
                DialogueLineElement(text="Que voulez-vous faire?"),
                PlayerChoicesBlockElement(choices=[
                    PlayerChoiceOption(text="Explorer", next_interaction_id="child1"),
                    PlayerChoiceOption(text="Se reposer", next_interaction_id="child2")
                ])
            ]
        )
        
        interaction_child1 = Interaction(
            interaction_id="child1",
            elements=[DialogueLineElement(text="Vous explorez...")]
        )
        
        interaction_child2 = Interaction(
            interaction_id="child2",
            elements=[DialogueLineElement(text="Vous vous reposez...")]
        )
        
        # Sauvegarder
        self.service.save(interaction_parent)
        self.service.save(interaction_child1)
        self.service.save(interaction_child2)
        
        # Tester la récupération du texte de choix
        choice_text1 = self.service.get_choice_text_for_transition("parent", "child1")
        self.assertEqual(choice_text1, "Explorer")
        
        choice_text2 = self.service.get_choice_text_for_transition("parent", "child2")
        self.assertEqual(choice_text2, "Se reposer")
        
        # Tester un lien inexistant
        choice_text3 = self.service.get_choice_text_for_transition("parent", "nonexistent")
        self.assertIsNone(choice_text3)

    def test_get_choice_text_for_automatic_transition(self):
        """Teste la récupération du texte pour une transition automatique."""
        interaction_parent = Interaction(
            interaction_id="parent",
            elements=[DialogueLineElement(text="Texte automatique")],
            next_interaction_id_if_no_choices="child"
        )
        
        interaction_child = Interaction(
            interaction_id="child",
            elements=[DialogueLineElement(text="Suite automatique")]
        )
        
        # Sauvegarder
        self.service.save(interaction_parent)
        self.service.save(interaction_child)
        
        # Tester la transition automatique
        choice_text = self.service.get_choice_text_for_transition("parent", "child")
        self.assertEqual(choice_text, "(transition automatique)")

    def test_index_update_on_modification(self):
        """Teste que l'index est mis à jour quand une interaction est modifiée."""
        # Créer une interaction initiale
        interaction = Interaction(
            interaction_id="test",
            elements=[DialogueLineElement(text="Initial")],
            next_interaction_id_if_no_choices="target1"
        )
        
        target1 = Interaction(
            interaction_id="target1",
            elements=[DialogueLineElement(text="Target 1")]
        )
        
        # Sauvegarder
        self.service.save(interaction)
        self.service.save(target1)
        
        # Vérifier l'index initial
        self.assertEqual(self.service._parent_index["target1"], [("test", -1)])
        
        # Modifier l'interaction pour pointer vers une autre cible
        interaction.next_interaction_id_if_no_choices = "target2"
        target2 = Interaction(
            interaction_id="target2",
            elements=[DialogueLineElement(text="Target 2")]
        )
        
        # Sauvegarder les modifications
        self.service.save(interaction)
        self.service.save(target2)
        
        # Vérifier que l'index a été mis à jour
        self.assertNotIn("target1", self.service._parent_index)
        self.assertEqual(self.service._parent_index["target2"], [("test", -1)])

    def test_index_cleanup_on_deletion(self):
        """Teste que l'index est nettoyé quand une interaction est supprimée."""
        # Créer des interactions liées
        parent = Interaction(
            interaction_id="parent",
            elements=[DialogueLineElement(text="Parent")],
            next_interaction_id_if_no_choices="child"
        )
        
        child = Interaction(
            interaction_id="child",
            elements=[DialogueLineElement(text="Child")]
        )
        
        # Sauvegarder
        self.service.save(parent)
        self.service.save(child)
        
        # Vérifier l'index
        self.assertIn("child", self.service._parent_index)
        
        # Supprimer le parent
        self.service.delete("parent")
        
        # Vérifier que l'entrée a été nettoyée
        self.assertNotIn("child", self.service._parent_index)

    def test_multiple_parents_handling(self):
        """Teste la gestion d'une interaction ayant plusieurs parents."""
        # Créer deux parents pointant vers le même enfant
        parent1 = Interaction(
            interaction_id="parent1",
            elements=[
                DialogueLineElement(text="Parent 1"),
                PlayerChoicesBlockElement(choices=[
                    PlayerChoiceOption(text="Aller vers commune", next_interaction_id="commune")
                ])
            ]
        )
        
        parent2 = Interaction(
            interaction_id="parent2",
            elements=[
                DialogueLineElement(text="Parent 2"),
                PlayerChoicesBlockElement(choices=[
                    PlayerChoiceOption(text="Aller vers commune", next_interaction_id="commune")
                ])
            ]
        )
        
        commune = Interaction(
            interaction_id="commune",
            elements=[DialogueLineElement(text="Interaction commune")]
        )
        
        # Sauvegarder
        self.service.save(parent1)
        self.service.save(parent2)
        self.service.save(commune)
        
        # Vérifier que l'interaction commune a bien deux parents
        parents_info = self.service.get_parent_info("commune")
        self.assertEqual(len(parents_info), 2)
        
        # Vérifier que les IDs des parents sont corrects
        parent_ids = [info[0] for info in parents_info]
        self.assertIn("parent1", parent_ids)
        self.assertIn("parent2", parent_ids)
        
        # Tester la reconstruction de chemin (doit choisir un parent)
        path = self.service.get_dialogue_path("commune")
        self.assertEqual(len(path), 2)  # parent + commune
        self.assertIn(path[0].interaction_id, ["parent1", "parent2"])
        self.assertEqual(path[1].interaction_id, "commune")

    def test_create_interaction_with_proper_id_generation(self):
        """Teste la création d'interaction avec génération d'ID appropriée."""
        # Tester création sans préfixe
        interaction1 = self.service.create_interaction(title="Test 1")
        self.assertIsNotNone(interaction1.interaction_id)
        self.assertTrue(len(interaction1.interaction_id) > 0)
        
        # Tester création avec préfixe
        interaction2 = self.service.create_interaction(
            title="Test 2", 
            prefix="dialogue"
        )
        self.assertTrue(interaction2.interaction_id.startswith("dialogue_"))
        
        # Vérifier que les IDs sont uniques
        self.assertNotEqual(interaction1.interaction_id, interaction2.interaction_id)
        
        # Vérifier que les interactions sont bien sauvegardées
        self.assertEqual(len(self.service.get_all()), 2)

if __name__ == '__main__':
    unittest.main() 