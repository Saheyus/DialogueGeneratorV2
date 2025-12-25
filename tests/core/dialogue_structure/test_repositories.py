import pytest
import tempfile
import os
import shutil
from pathlib import Path

from models.dialogue_structure import (
    DialogueLineElement, PlayerChoiceOption, PlayerChoicesBlockElement, Interaction
)
from services.repositories import (
    InMemoryInteractionRepository, FileInteractionRepository
)

class TestInMemoryInteractionRepository:
    @pytest.fixture
    def memory_repo(self):
        repo = InMemoryInteractionRepository()
        yield repo
        repo.clear()  # Nettoyage après chaque test
    
    @pytest.fixture
    def sample_interaction(self):
        line1 = DialogueLineElement(text="Bonjour !", speaker="PNJ1")
        choice1 = PlayerChoiceOption(text="Réponse 1", next_interaction_id="next_node_1")
        choice2 = PlayerChoiceOption(text="Réponse 2", next_interaction_id="next_node_2")
        choices = PlayerChoicesBlockElement(choices=[choice1, choice2])
        
        return Interaction(
            interaction_id="test_interaction",
            elements=[line1, choices],
            header_tags=["test"],
            header_commands=["set $test = true"]
        )
    
    def test_save_and_get_by_id(self, memory_repo, sample_interaction):
        # Sauvegarde
        memory_repo.save(sample_interaction)
        
        # Récupération
        retrieved = memory_repo.get_by_id("test_interaction")
        
        # Vérification
        assert retrieved is not None
        assert retrieved.interaction_id == "test_interaction"
        assert len(retrieved.elements) == 2
        assert retrieved.header_tags == ["test"]
        assert retrieved.header_commands == ["set $test = true"]
    
    def test_get_all(self, memory_repo, sample_interaction):
        # Sauvegarde de deux interactions
        memory_repo.save(sample_interaction)
        
        interaction2 = Interaction(
            interaction_id="test_interaction_2",
            elements=[DialogueLineElement(text="Bonjour 2!", speaker="PNJ2")]
        )
        memory_repo.save(interaction2)
        
        # Récupération de toutes les interactions
        all_interactions = memory_repo.get_all()
        
        # Vérification
        assert len(all_interactions) == 2
        interaction_ids = [i.interaction_id for i in all_interactions]
        assert "test_interaction" in interaction_ids
        assert "test_interaction_2" in interaction_ids
    
    def test_delete(self, memory_repo, sample_interaction):
        # Sauvegarde
        memory_repo.save(sample_interaction)
        
        # Vérification de l'existence
        assert memory_repo.exists("test_interaction") is True
        
        # Suppression
        result = memory_repo.delete("test_interaction")
        
        # Vérification de la suppression
        assert result is True
        assert memory_repo.exists("test_interaction") is False
        assert memory_repo.get_by_id("test_interaction") is None
    
    def test_delete_nonexistent(self, memory_repo):
        # Suppression d'une interaction inexistante
        result = memory_repo.delete("nonexistent")
        
        # Vérification du résultat
        assert result is False
    
    def test_exists(self, memory_repo, sample_interaction):
        # Vérification d'une interaction inexistante
        assert memory_repo.exists("test_interaction") is False
        
        # Sauvegarde
        memory_repo.save(sample_interaction)
        
        # Vérification d'une interaction existante
        assert memory_repo.exists("test_interaction") is True
    
    def test_clear(self, memory_repo, sample_interaction):
        # Sauvegarde
        memory_repo.save(sample_interaction)
        
        # Vérification de l'existence
        assert memory_repo.exists("test_interaction") is True
        
        # Suppression de toutes les interactions
        memory_repo.clear()
        
        # Vérification que toutes les interactions ont été supprimées
        assert memory_repo.get_all() == []
        assert memory_repo.exists("test_interaction") is False


class TestFileInteractionRepository:
    @pytest.fixture
    def temp_dir(self):
        # Création d'un dossier temporaire pour les tests
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Nettoyage après chaque test
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def file_repo(self, temp_dir):
        return FileInteractionRepository(temp_dir)
    
    @pytest.fixture
    def sample_interaction(self):
        line1 = DialogueLineElement(text="Bonjour !", speaker="PNJ1")
        choice1 = PlayerChoiceOption(text="Réponse 1", next_interaction_id="next_node_1")
        choice2 = PlayerChoiceOption(text="Réponse 2", next_interaction_id="next_node_2")
        choices = PlayerChoicesBlockElement(choices=[choice1, choice2])
        
        return Interaction(
            interaction_id="test_interaction",
            elements=[line1, choices],
            header_tags=["test"],
            header_commands=["set $test = true"]
        )
    
    def test_save_and_get_by_id(self, file_repo, sample_interaction, temp_dir):
        # Sauvegarde
        file_repo.save(sample_interaction)
        
        # Vérification que le fichier a été créé
        file_path = Path(temp_dir) / "test_interaction.json"
        assert file_path.exists()
        
        # Récupération
        retrieved = file_repo.get_by_id("test_interaction")
        
        # Vérification
        assert retrieved is not None
        assert retrieved.interaction_id == "test_interaction"
        assert len(retrieved.elements) == 2
        assert retrieved.header_tags == ["test"]
        assert retrieved.header_commands == ["set $test = true"]
    
    def test_get_all(self, file_repo, sample_interaction):
        # Sauvegarde de deux interactions
        file_repo.save(sample_interaction)
        
        interaction2 = Interaction(
            interaction_id="test_interaction_2",
            elements=[DialogueLineElement(text="Bonjour 2!", speaker="PNJ2")]
        )
        file_repo.save(interaction2)
        
        # Récupération de toutes les interactions
        all_interactions = file_repo.get_all()
        
        # Vérification
        assert len(all_interactions) == 2
        interaction_ids = sorted([i.interaction_id for i in all_interactions])
        assert interaction_ids == ["test_interaction", "test_interaction_2"]
    
    def test_delete(self, file_repo, sample_interaction, temp_dir):
        # Sauvegarde
        file_repo.save(sample_interaction)
        
        # Vérification de l'existence
        file_path = Path(temp_dir) / "test_interaction.json"
        assert file_path.exists()
        
        # Suppression
        result = file_repo.delete("test_interaction")
        
        # Vérification de la suppression
        assert result is True
        assert not file_path.exists()
        assert file_repo.get_by_id("test_interaction") is None
    
    def test_delete_nonexistent(self, file_repo):
        # Suppression d'une interaction inexistante
        result = file_repo.delete("nonexistent")
        
        # Vérification du résultat
        assert result is False
    
    def test_exists(self, file_repo, sample_interaction):
        # Vérification d'une interaction inexistante
        assert file_repo.exists("test_interaction") is False
        
        # Sauvegarde
        file_repo.save(sample_interaction)
        
        # Vérification d'une interaction existante
        assert file_repo.exists("test_interaction") is True
    
    def test_clear(self, file_repo, sample_interaction, temp_dir):
        # Sauvegarde de deux interactions
        file_repo.save(sample_interaction)
        
        interaction2 = Interaction(
            interaction_id="test_interaction_2",
            elements=[DialogueLineElement(text="Bonjour 2!", speaker="PNJ2")]
        )
        file_repo.save(interaction2)
        
        # Vérification de l'existence des fichiers
        assert Path(temp_dir).glob("*.json").__sizeof__() > 0
        
        # Suppression de toutes les interactions
        file_repo.clear()
        
        # Vérification que tous les fichiers ont été supprimés
        assert list(Path(temp_dir).glob("*.json")) == [] 
