"""Tests pour GraphValidationService."""
import pytest
from services.graph_validation_service import GraphValidationService, ValidationResult


class TestValidateCycles:
    """Tests pour la détection de cycles avec chemin complet."""
    
    def test_detect_single_cycle_with_full_path(self):
        """Test: Détecte un cycle simple et retourne le chemin complet."""
        nodes = [
            {"id": "A", "data": {"label": "Node A"}},
            {"id": "B", "data": {"label": "Node B"}},
            {"id": "C", "data": {"label": "Node C"}},
        ]
        edges = [
            {"id": "e1", "source": "A", "target": "B"},
            {"id": "e2", "source": "B", "target": "C"},
            {"id": "e3", "source": "C", "target": "A"},  # Cycle: A → B → C → A
        ]
        
        result = ValidationResult()
        GraphValidationService._validate_cycles(nodes, edges, result)
        
        assert len(result.warnings) == 1
        warning = result.warnings[0]
        assert warning.type == "cycle_detected"
        assert warning.cycle_path == "A → B → C → A"
        assert set(warning.cycle_nodes) == {"A", "B", "C"}
        assert warning.cycle_id is not None
        assert warning.cycle_id.startswith("cycle_")
    
    def test_detect_multiple_cycles_with_paths(self):
        """Test: Détecte plusieurs cycles distincts avec leurs chemins."""
        nodes = [
            {"id": "A", "data": {"label": "Node A"}},
            {"id": "B", "data": {"label": "Node B"}},
            {"id": "C", "data": {"label": "Node C"}},
            {"id": "D", "data": {"label": "Node D"}},
            {"id": "E", "data": {"label": "Node E"}},
        ]
        edges = [
            {"id": "e1", "source": "A", "target": "B"},
            {"id": "e2", "source": "B", "target": "A"},  # Cycle 1: A → B → A
            {"id": "e3", "source": "C", "target": "D"},
            {"id": "e4", "source": "D", "target": "E"},
            {"id": "e5", "source": "E", "target": "C"},  # Cycle 2: C → D → E → C
        ]
        
        result = ValidationResult()
        GraphValidationService._validate_cycles(nodes, edges, result)
        
        assert len(result.warnings) == 2
        
        # Vérifier que chaque cycle a un ID unique
        cycle_ids = [w.cycle_id for w in result.warnings]
        assert len(set(cycle_ids)) == 2
        
        # Vérifier les chemins
        paths = [w.cycle_path for w in result.warnings]
        assert "A → B → A" in paths or "B → A → B" in paths
        assert "C → D → E → C" in paths or "D → E → C → D" in paths or "E → C → D → E" in paths
    
    def test_no_cycles_no_warnings(self):
        """Test: Graphe sans cycles ne génère pas de warnings."""
        nodes = [
            {"id": "A", "data": {"label": "Node A"}},
            {"id": "B", "data": {"label": "Node B"}},
            {"id": "C", "data": {"label": "Node C"}},
        ]
        edges = [
            {"id": "e1", "source": "A", "target": "B"},
            {"id": "e2", "source": "B", "target": "C"},
            # Pas de cycle
        ]
        
        result = ValidationResult()
        GraphValidationService._validate_cycles(nodes, edges, result)
        
        assert len(result.warnings) == 0
    
    def test_cycle_id_stable_for_same_nodes(self):
        """Test: Le cycle_id est stable pour le même ensemble de nœuds."""
        nodes = [
            {"id": "A", "data": {"label": "Node A"}},
            {"id": "B", "data": {"label": "Node B"}},
            {"id": "C", "data": {"label": "Node C"}},
        ]
        edges = [
            {"id": "e1", "source": "A", "target": "B"},
            {"id": "e2", "source": "B", "target": "C"},
            {"id": "e3", "source": "C", "target": "A"},
        ]
        
        result1 = ValidationResult()
        GraphValidationService._validate_cycles(nodes, edges, result1)
        
        result2 = ValidationResult()
        GraphValidationService._validate_cycles(nodes, edges, result2)
        
        assert result1.warnings[0].cycle_id == result2.warnings[0].cycle_id
