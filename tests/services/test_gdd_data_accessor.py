"""Tests pour le service GDDDataAccessor."""
import pytest
from services.gdd_data_accessor import GDDDataAccessor
from services.element_resolver import ElementResolver
from services.element_linker import ElementLinker
from services.element_repository import ElementRepository
from services.gdd_loader import GDDData


@pytest.fixture
def sample_gdd_data():
    """Données GDD de test."""
    return GDDData(
        characters=[
            {"Nom": "Character 1", "Age": 25},
            {"Nom": "Character 2", "Age": 30}
        ],
        locations=[
            {"Nom": "Location 1", "Type": "City", "Catégorie": "Ville"},
            {"Nom": "Location 2", "Type": "Forest", "Catégorie": "Lieu"},
            {"Nom": "Forêt Sombre", "Catégorie": "Région", "Contient": "Clairière, Ruines Antiques"}
        ],
        items=[
            {"Nom": "Item 1", "Type": "Weapon"}
        ],
        species=[
            {"Nom": "Species 1"}
        ],
        communities=[
            {"Nom": "Community 1"}
        ],
        quests=[
            {"Nom": "Quest 1"}
        ],
        dialogues_examples=[
            {"Nom": "Dialogue 1", "Titre": "Title 1"}
        ],
        narrative_structures=[
            {"Nom": "Structure 1"}
        ],
        macro_structure={"Nom": "Macro"},
        micro_structure={"Nom": "Micro"},
        vision_data={"Nom": "Vision"}
    )


@pytest.fixture
def repository(sample_gdd_data):
    """Repository de test."""
    return ElementRepository(sample_gdd_data)


@pytest.fixture
def resolver(repository):
    """Resolver de test."""
    return ElementResolver(repository)


@pytest.fixture
def linker(resolver):
    """Linker de test."""
    return ElementLinker(element_repository=None, element_resolver=resolver)


@pytest.fixture
def accessor(sample_gdd_data, resolver, linker):
    """Accessor de test."""
    return GDDDataAccessor(
        gdd_data=sample_gdd_data,
        element_resolver=resolver,
        element_linker=linker
    )


class TestGDDDataAccessor:
    """Tests pour GDDDataAccessor."""
    
    def test_characters_property(self, accessor):
        """Test de la propriété characters."""
        assert len(accessor.characters) == 2
        assert accessor.characters[0]["Nom"] == "Character 1"
    
    def test_characters_property_empty(self):
        """Test de la propriété characters sans données."""
        accessor = GDDDataAccessor()
        assert accessor.characters == []
    
    def test_locations_property(self, accessor):
        """Test de la propriété locations."""
        assert len(accessor.locations) == 3
    
    def test_get_characters_names(self, accessor):
        """Test de récupération des noms de personnages."""
        names = accessor.get_characters_names()
        assert len(names) == 2
        assert "Character 1" in names
        assert "Character 2" in names
    
    def test_get_characters_names_without_resolver(self, sample_gdd_data):
        """Test sans resolver."""
        accessor = GDDDataAccessor(gdd_data=sample_gdd_data)
        names = accessor.get_characters_names()
        assert names == []
    
    def test_get_character_details_by_name(self, accessor):
        """Test de récupération des détails d'un personnage."""
        details = accessor.get_character_details_by_name("Character 1")
        assert details is not None
        assert details["Nom"] == "Character 1"
        assert details["Age"] == 25
    
    def test_get_character_details_by_name_not_found(self, accessor):
        """Test de récupération d'un personnage inexistant."""
        details = accessor.get_character_details_by_name("Nonexistent")
        assert details is None
    
    def test_get_locations_names(self, accessor):
        """Test de récupération des noms de lieux."""
        names = accessor.get_locations_names()
        assert len(names) == 3
    
    def test_get_location_details_by_name(self, accessor):
        """Test de récupération des détails d'un lieu."""
        details = accessor.get_location_details_by_name("Location 1")
        assert details is not None
        assert details["Nom"] == "Location 1"
    
    def test_get_items_names(self, accessor):
        """Test de récupération des noms d'objets."""
        names = accessor.get_items_names()
        assert len(names) == 1
        assert "Item 1" in names
    
    def test_get_species_names(self, accessor):
        """Test de récupération des noms d'espèces."""
        names = accessor.get_species_names()
        assert len(names) == 1
    
    def test_get_communities_names(self, accessor):
        """Test de récupération des noms de communautés."""
        names = accessor.get_communities_names()
        assert len(names) == 1
    
    def test_get_quests_names(self, accessor):
        """Test de récupération des noms de quêtes."""
        names = accessor.get_quests_names()
        assert len(names) == 1
    
    def test_get_dialogue_examples_titles(self, accessor):
        """Test de récupération des titres d'exemples de dialogues."""
        titles = accessor.get_dialogue_examples_titles()
        assert len(titles) == 1
        assert "Dialogue 1" in titles
    
    def test_get_narrative_structures(self, accessor):
        """Test de récupération des structures narratives."""
        structures = accessor.get_narrative_structures()
        assert len(structures) == 1
    
    def test_get_macro_structure(self, accessor):
        """Test de récupération de la structure macro."""
        structure = accessor.get_macro_structure()
        assert structure is not None
        assert structure["Nom"] == "Macro"
    
    def test_get_micro_structure(self, accessor):
        """Test de récupération de la structure micro."""
        structure = accessor.get_micro_structure()
        assert structure is not None
        assert structure["Nom"] == "Micro"
    
    def test_get_regions(self, accessor):
        """Test de récupération des régions."""
        regions = accessor.get_regions()
        assert len(regions) == 1
        assert "Forêt Sombre" in regions
    
    def test_get_sub_locations(self, accessor):
        """Test de récupération des sous-lieux."""
        sub_locs = accessor.get_sub_locations("Forêt Sombre")
        assert len(sub_locs) == 2
        assert "Clairière" in sub_locs
        assert "Ruines Antiques" in sub_locs
    
    def test_get_linked_elements(self, accessor):
        """Test de récupération des éléments liés."""
        linked = accessor.get_linked_elements(character_name="Character 1")
        assert isinstance(linked, dict)
        assert "characters" in linked
        assert "locations" in linked
        assert "items" in linked
    
    def test_get_linked_elements_without_linker(self, sample_gdd_data, resolver):
        """Test sans linker."""
        accessor = GDDDataAccessor(gdd_data=sample_gdd_data, element_resolver=resolver)
        linked = accessor.get_linked_elements()
        assert linked == {
            "characters": set(),
            "locations": set(),
            "items": set(),
            "species": set(),
            "communities": set(),
            "quests": set()
        }
    
    def test_vision_data_property(self, accessor):
        """Test de la propriété vision_data."""
        vision = accessor.vision_data
        assert vision is not None
        assert vision["Nom"] == "Vision"
    
    def test_gdd_data_property(self, accessor):
        """Test de la propriété gdd_data (compatibilité)."""
        gdd_data = accessor.gdd_data
        assert isinstance(gdd_data, dict)
        assert gdd_data == {}
