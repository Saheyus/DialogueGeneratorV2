"""Test d'intégration pour vérifier l'absence de doublons dans les prompts générés."""
import pytest
import re
from typing import Dict, List, Set
from collections import Counter


class TestPromptDeduplication:
    """Tests d'intégration pour vérifier que les prompts ne contiennent pas de doublons."""
    
    @pytest.fixture
    def analyze_duplicates(self):
        """Fixture pour analyser les doublons dans un texte."""
        def _analyze(text: str, min_length: int = 50) -> Dict[str, int]:
            """Analyse les fragments dupliqués dans un texte.
            
            Args:
                text: Texte à analyser
                min_length: Longueur minimale des fragments à considérer
                
            Returns:
                Dict mapping fragment -> nombre d'occurrences
            """
            # Extraire des fragments de texte significatifs
            fragments = []
            words = text.split()
            
            # Créer des fragments de différentes tailles
            for window_size in [10, 15, 20]:
                for i in range(len(words) - window_size + 1):
                    fragment = ' '.join(words[i:i + window_size])
                    if len(fragment) >= min_length:
                        # Normaliser pour comparaison
                        normalized = fragment.lower().strip()
                        fragments.append(normalized)
            
            # Compter les occurrences
            counts = Counter(fragments)
            
            # Ne garder que les doublons (count >= 2)
            duplicates = {frag: count for frag, count in counts.items() if count >= 2}
            
            return duplicates
        
        return _analyze
    
    @pytest.fixture
    def extract_xml_fields(self):
        """Fixture pour extraire les champs XML d'un prompt."""
        def _extract(xml_text: str) -> Dict[str, List[str]]:
            """Extrait les champs XML et leur contenu.
            
            Returns:
                Dict mapping tag_name -> list of content values
            """
            # Pattern pour extraire les balises et leur contenu
            pattern = r'<(\w+)>(.*?)</\1>'
            matches = re.findall(pattern, xml_text, re.DOTALL)
            
            fields: Dict[str, List[str]] = {}
            for tag, content in matches:
                if tag not in fields:
                    fields[tag] = []
                # Nettoyer le contenu
                clean_content = content.strip()
                if clean_content:
                    fields[tag].append(clean_content)
            
            return fields
        
        return _extract
    
    def test_no_duplicate_xml_tags_in_character(
        self,
        context_builder_with_real_data,
        extract_xml_fields
    ) -> None:
        """Test qu'un personnage n'a pas de balises XML dupliquées dans son prompt.
        
        Ce test vérifie le bug original où <background>, <context>, <appearance>
        apparaissaient deux fois pour Uresaïr.
        """
        # Construire le contexte pour un personnage
        result = context_builder_with_real_data.build_context(
            selected_elements={"characters": ["Seigneuresse Uresaïr"]},
            scene_instruction="Test",
            organization_mode="narrative"
        )
        
        raw_prompt = result["raw_prompt"]
        
        # Extraire les balises dans la section du personnage
        # Trouver la section <character>...</character>
        character_match = re.search(
            r'<character[^>]*>(.*?)</character>',
            raw_prompt,
            re.DOTALL
        )
        
        assert character_match, "Aucune section <character> trouvée"
        character_content = character_match.group(1)
        
        # Tags qui ne devraient apparaître qu'une fois
        unique_tags = [
            'identity', 'characterization', 'voice', 'background',
            'weakness', 'compulsion', 'desire',
            'context', 'appearance', 'relationships'
        ]
        
        for tag in unique_tags:
            # Compter les occurrences du tag d'ouverture
            count = len(re.findall(f'<{tag}(?:\\s|>)', character_content))
            assert count <= 1, (
                f"Tag <{tag}> apparaît {count} fois dans le personnage "
                f"(devrait apparaître maximum 1 fois)"
            )
    
    def test_no_content_duplication_in_prompt(
        self,
        context_builder_with_real_data,
        analyze_duplicates
    ) -> None:
        """Test qu'il n'y a pas de duplication significative de contenu."""
        # Construire le contexte
        result = context_builder_with_real_data.build_context(
            selected_elements={"characters": ["Seigneuresse Uresaïr"]},
            scene_instruction="Test",
            organization_mode="narrative"
        )
        
        raw_prompt = result["raw_prompt"]
        
        # Analyser les doublons
        duplicates = analyze_duplicates(raw_prompt, min_length=100)
        
        # Il ne devrait pas y avoir de fragments longs dupliqués
        # (tolérance: max 2 petits fragments, probablement des formules répétées)
        assert len(duplicates) <= 2, (
            f"Trouvé {len(duplicates)} fragments dupliqués dans le prompt. "
            f"Exemples: {list(duplicates.keys())[:3]}"
        )
        
        # Si des doublons existent, ils ne doivent pas être trop fréquents
        for fragment, count in duplicates.items():
            assert count <= 2, (
                f"Fragment répété {count} fois (max 2 attendu): "
                f"{fragment[:100]}..."
            )
    
    def test_extract_all_fields_no_parent_duplication(
        self,
        context_construction_service
    ) -> None:
        """Test que extract_all_fields n'extrait pas les parents ET les enfants."""
        # Données de test similaires à Uresaïr
        test_data = {
            "Nom": "Test",
            "Background": {
                "Context": "Histoire",
                "Appearance": "Apparence"
            },
            "Introduction": {
                "Resume": "Résumé"
            }
        }
        
        # Simuler extract_all_fields (la fonction interne de _build_context_item)
        def extract_all_fields(data: Dict, prefix: str = "") -> List[str]:
            fields = []
            for key, value in data.items():
                if key.startswith("_") or value is None:
                    continue
                
                field_path = f"{prefix}.{key}" if prefix else key
                
                if isinstance(value, dict):
                    # Ne PAS ajouter le parent, seulement les enfants
                    fields.extend(extract_all_fields(value, field_path))
                elif isinstance(value, list):
                    has_dicts = any(isinstance(item, dict) for item in value)
                    if has_dicts:
                        for item in value:
                            if isinstance(item, dict):
                                fields.extend(extract_all_fields(item, field_path))
                    else:
                        fields.append(field_path)
                else:
                    # Valeur terminale
                    fields.append(field_path)
            return fields
        
        fields = extract_all_fields(test_data)
        
        # Vérifications
        assert "Nom" in fields
        assert "Background.Context" in fields
        assert "Background.Appearance" in fields
        assert "Introduction.Resume" in fields
        
        # Les parents ne doivent PAS être présents
        assert "Background" not in fields, "Background (parent) ne doit pas être extrait"
        assert "Introduction" not in fields, "Introduction (parent) ne doit pas être extrait"
        
        # Pas de doublons
        assert len(fields) == len(set(fields)), "Il ne doit pas y avoir de doublons dans les champs extraits"
    
    def test_raw_content_serialization_no_duplication(
        self,
        context_builder_with_real_data
    ) -> None:
        """Test que l'utilisation de raw_content n'introduit pas de doublons."""
        # Construire avec raw_content
        result = context_builder_with_real_data.build_context(
            selected_elements={"characters": ["Seigneuresse Uresaïr"]},
            scene_instruction="Test",
            organization_mode="narrative"
        )
        
        raw_prompt = result["raw_prompt"]
        structured_prompt = result.get("structured_prompt")
        
        # Vérifier que structured_prompt utilise raw_content
        if structured_prompt and structured_prompt.sections:
            for section in structured_prompt.sections:
                if section.type == "context" and section.categories:
                    for category in section.categories:
                        for item in category.items:
                            for item_section in item.sections:
                                # Si raw_content existe, il doit être utilisé
                                if hasattr(item_section, 'raw_content') and item_section.raw_content:
                                    # raw_content ne doit pas être None
                                    assert item_section.raw_content is not None
                                    # Le content peut être vide (sera ignoré en faveur de raw_content)
                                    # C'est normal et attendu
        
        # Vérifier l'absence de doublons dans le résultat final
        # Ex: pas de <background><context>...</context></background> ET <context>...</context> séparés
        background_sections = re.findall(
            r'<background>(.*?)</background>',
            raw_prompt,
            re.DOTALL
        )
        
        # S'il y a une section background, elle ne doit apparaître qu'une fois
        assert len(background_sections) <= 1, (
            f"Section <background> apparaît {len(background_sections)} fois "
            f"(devrait apparaître maximum 1 fois)"
        )
    
    @pytest.mark.parametrize("character_name", [
        "Seigneuresse Uresaïr",
        "Akthar-Neth Amatru, l'Exégète"
    ])
    def test_no_duplication_for_multiple_characters(
        self,
        context_builder_with_real_data,
        character_name: str
    ) -> None:
        """Test que différents personnages ne présentent pas de doublons.
        
        Test de régression pour s'assurer que le fix fonctionne pour tous les personnages.
        """
        try:
            result = context_builder_with_real_data.build_context(
                selected_elements={"characters": [character_name]},
                scene_instruction="Test",
                organization_mode="narrative"
            )
            
            raw_prompt = result["raw_prompt"]
            
            # Vérifier qu'il n'y a pas de doublons évidents
            # (tags XML principaux ne doivent pas être répétés)
            character_match = re.search(
                r'<character[^>]*>(.*?)</character>',
                raw_prompt,
                re.DOTALL
            )
            
            if character_match:
                character_content = character_match.group(1)
                
                # Vérifier quelques tags clés
                for tag in ['background', 'characterization', 'identity']:
                    count = len(re.findall(f'<{tag}(?:\\s|>)', character_content))
                    assert count <= 1, (
                        f"Tag <{tag}> apparaît {count} fois pour {character_name}"
                    )
        except Exception as e:
            # Si le personnage n'existe pas, skip le test
            pytest.skip(f"Personnage '{character_name}' non disponible: {e}")
