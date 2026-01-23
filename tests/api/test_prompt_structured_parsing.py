"""Tests d'intégration pour le parsing structuré du prompt avec vraies données.

Ce module teste que le prompt brut retourné par l'API peut être correctement
parsé par la fonction parsePromptSections du frontend, et que toutes les
sections sont correctement détectées et structurées.

Types de tests :
- Tests d'intégration : Utilisent les vraies données GDD et l'API réelle
- Tests de parsing : Vérifient que le format du prompt est compatible avec le parser frontend
"""
import pytest
from fastapi.testclient import TestClient
from api.main import app


@pytest.fixture
def real_client():
    """Client de test sans mocks - utilise les vrais services."""
    yield TestClient(app)


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.api
def test_prompt_structured_parsing_with_real_data(real_client):
    """Test que le prompt brut peut être parsé en sections structurées.
    
    Ce test vérifie que :
    1. Le prompt brut contient SECTION 2A avec le contexte GDD
    2. Le format est compatible avec parsePromptSections (frontend)
    3. Les sections CHARACTERS sont correctement formatées
    """
    # Récupérer un personnage depuis le GDD (générique, pas hardcodé)
    from context_builder import ContextBuilder
    cb = ContextBuilder()
    cb.load_gdd_files()
    all_characters = cb.get_characters_names()
    character_name = all_characters[0] if all_characters else None
    assert character_name is not None, "Aucun personnage chargé depuis le GDD"
    
    # Le schéma ContextSelection attend characters_full ou characters_excerpt, pas characters
    response = real_client.post(
        "/api/v1/dialogues/estimate-tokens",
        json={
            "context_selections": {
                "characters_full": [character_name],  # Utiliser characters_full au lieu de characters
                "locations_full": [],
                "items_full": [],
                "species_full": [],
                "communities_full": []
            },
            "field_configs": {
                "characters": ["Nom", "Résumé", "Introduction", "Faiblesse", "Compulsion", "Désir Principal", "Caractérisation", "Contexte Background"]
            },
            "user_instructions": "Test de parsing structuré",
            "max_context_tokens": 2000,
            "npc_speaker_id": character_name
        }
    )
    
    assert response.status_code == 200, f"Erreur: {response.status_code} - {response.text}"
    data = response.json()
    raw_prompt = data.get("raw_prompt", "")
    
    assert len(raw_prompt) > 0, "Le prompt brut ne doit pas être vide"
    
    # Vérifier que SECTION 2A est présente
    has_section_2a = "### SECTION 2A" in raw_prompt
    assert has_section_2a, f"SECTION 2A absente. Sections trouvées: {[s for s in ['SECTION 0', 'SECTION 1', 'SECTION 2A', 'SECTION 2B', 'SECTION 2C', 'SECTION 3'] if f'### {s}' in raw_prompt]}"
    
    # Extraire SECTION 2A pour vérifier le format
    import re
    match = re.search(r'### SECTION 2A.*?(?=### SECTION|---\s*$|$)', raw_prompt, re.DOTALL)
    assert match is not None, "Impossible d'extraire SECTION 2A"
    section_2a_content = match.group(0)
    
    # Vérifier que SECTION 2A contient le contexte GDD
    assert "CONTEXTE GÉNÉRAL" in section_2a_content or "CONTEXTE GÉNÉRAL DE LA SCÈNE" in section_2a_content, \
        "SECTION 2A devrait contenir 'CONTEXTE GÉNÉRAL'"
    
    # Vérifier le format pour le parsing structuré
    # Le parser frontend cherche --- CHARACTERS --- ou --- CHARACTER ---
    has_characters_marker = "--- CHARACTERS ---" in section_2a_content or "--- CHARACTER ---" in section_2a_content
    has_identity_section = "--- IDENTITÉ ---" in section_2a_content or "--- IDENTITE ---" in section_2a_content
    
    # Le format peut varier selon l'organisateur, mais on doit avoir au moins un marqueur
    character_first_part = character_name.split(',')[0] if ',' in character_name else character_name
    assert has_characters_marker or has_identity_section or character_first_part in section_2a_content, \
        f"SECTION 2A devrait contenir des marqueurs de sections ou le nom du personnage. Contenu (500 chars): {section_2a_content[:500]}"
    
    # Vérifier que le personnage est présent dans le contexte
    # Le nom peut être avec apostrophe typographique ou droite (normalisation)
    character_normalized = character_name.replace('\u2019', "'").replace('\u2018', "'")
    assert character_name in section_2a_content or character_normalized in section_2a_content or character_first_part in section_2a_content, \
        f"Le nom du personnage devrait être dans SECTION 2A. Nom GDD: {character_name}, Normalisé: {character_normalized}"
    
    print(f"\n[OK] SECTION 2A trouvee et format correct")
    print(f"  Longueur SECTION 2A: {len(section_2a_content)} caracteres")
    print(f"  Contient CHARACTERS marker: {has_characters_marker}")
    print(f"  Contient IDENTITE section: {has_identity_section}")
    print(f"  Contient nom personnage: {character_first_part in section_2a_content}")
