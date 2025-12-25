import pytest

# Import du service
try:
    from services.linked_selector import LinkedSelectorService
except ImportError:
    import sys, os
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    from services.linked_selector import LinkedSelectorService


class DummyContextBuilder:
    """Contexte minimal pour tester LinkedSelectorService."""

    def __init__(self):
        # Données factices
        self._linked_by_character = {
            "Alice": {"items": ["Sword", "Ring"]},
            "Bob": {"items": ["Potion"]},
        }
        self._linked_by_location = {
            "Forest": {"items": ["Herb", "Wood"]},
            "Cave": {"items": ["Stone"]},
        }

    # Méthodes utilisées par LinkedSelectorService
    def get_linked_elements(self, character_name=None, location_names=None):
        if character_name:
            return self._linked_by_character.get(character_name, {})
        if location_names:
            # Fusionne les dicts des différents lieux
            merged: dict[str, list[str]] = {}
            for loc in location_names:
                data = self._linked_by_location.get(loc, {})
                for cat, items in data.items():
                    merged.setdefault(cat, []).extend(items)
            return merged
        return {}

    def get_character_details_by_name(self, name):
        if name == "Alice":
            return {
                "Nom": "Alice",
                "ItemsPossedes": ["Sword", "Ring"],
                "Lieu": "Forest",
            }
        if name == "Bob":
            return {"Nom": "Bob", "ItemsPossedes": ["Potion"]}
        return {}

    def get_location_details_by_name(self, name):
        if name == "Forest":
            return {"Nom": "Forest", "Ressources": ["Herb", "Wood"]}
        return {}


def test_get_elements_to_select_character():
    ctx = DummyContextBuilder()
    service = LinkedSelectorService(ctx)

    result = service.get_elements_to_select("Alice", None, None, None)
    assert {"Alice", "Sword", "Ring"}.issubset(result)


def test_get_elements_to_select_location():
    ctx = DummyContextBuilder()
    service = LinkedSelectorService(ctx)

    result = service.get_elements_to_select(None, None, "Forest", None)
    assert {"Forest", "Herb", "Wood"}.issubset(result)


def test_compute_items_to_keep_checked():
    ctx = DummyContextBuilder()
    service = LinkedSelectorService(ctx)

    currently = {"Alice", "Ring", "Herb", "Foo"}
    keep = service.compute_items_to_keep_checked(currently, "Alice", None, "Forest", None)

    assert set(keep) == {"Alice", "Ring", "Herb"} 