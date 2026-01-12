#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test pour afficher le prompt réel avec 2 personnages et 1 lieu sélectionnés.
"""
import logging
import sys
import io
from pathlib import Path

# Configuration de l'encodage UTF-8 pour stdout (Windows)
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import des modules
from context_builder import ContextBuilder
from prompt_engine import PromptEngine, PromptInput

def main():
    print("=" * 80)
    print("TEST DU PROMPT REEL - 2 PERSONNAGES + 1 LIEU")
    print("=" * 80)
    
    # 1. Charger le ContextBuilder
    print("\n[1/5] Chargement du ContextBuilder et des données GDD...")
    cb = ContextBuilder()
    cb.load_gdd_files()
    
    # 2. Récupérer les personnages et lieux disponibles
    print("\n[2/5] Récupération des personnages et lieux disponibles...")
    characters = cb.get_characters_names()
    locations = cb.get_locations_names()
    
    if len(characters) < 2:
        print(f"ERREUR: Pas assez de personnages disponibles ({len(characters)}). Minimum requis: 2")
        sys.exit(1)
    
    if len(locations) < 1:
        print(f"ERREUR: Pas assez de lieux disponibles ({len(locations)}). Minimum requis: 1")
        sys.exit(1)
    
    # Sélectionner 2 personnages et 1 lieu
    selected_characters = characters[:2]
    selected_location = locations[0]
    
    print(f"\n[OK] Personnages selectionnes: {selected_characters}")
    print(f"[OK] Lieu selectionne: {selected_location}")
    
    # 3. Construire le contexte GDD
    print("\n[3/5] Construction du contexte GDD...")
    selected_elements = {
        "characters": selected_characters,
        "locations": [selected_location]
    }
    scene_instruction = "Une rencontre fortuite dans ce lieu. Les personnages echangent des informations importantes."
    
    context_summary = cb.build_context(
        selected_elements=selected_elements,
        scene_instruction=scene_instruction,
        max_tokens=70000,
        include_dialogue_type=True
    )
    
    context_tokens = cb._count_tokens(context_summary)
    print(f"[OK] Contexte construit: {context_tokens} tokens")
    
    # 4. Construire le prompt complet
    print("\n[4/5] Construction du prompt complet...")
    prompt_engine = PromptEngine()
    
    # Déterminer le PNJ interlocuteur (premier personnage)
    npc_speaker_id = selected_characters[0]
    
    # Créer le PromptInput
    prompt_input = PromptInput(
        user_instructions=scene_instruction,
        npc_speaker_id=npc_speaker_id,
        player_character_id="URESAIR",
        context_summary=context_summary,
        scene_location={"lieu": selected_location},
        choices_mode="free",
        include_narrative_guides=True
    )
    
    # Construire le prompt
    built_prompt = prompt_engine.build_prompt(prompt_input)
    
    print(f"[OK] Prompt construit: {built_prompt.token_count} tokens")
    print(f"[OK] Hash du prompt: {built_prompt.prompt_hash[:16]}...")
    
    # 5. Afficher le prompt complet
    print("\n[5/5] Affichage du prompt complet...")
    print("\n" + "=" * 80)
    print("PROMPT COMPLET")
    print("=" * 80)
    print(built_prompt.raw_prompt)
    print("\n" + "=" * 80)
    
    # Afficher aussi les sections structurées si disponibles
    if built_prompt.structured_prompt:
        print("\n" + "=" * 80)
        print("SECTIONS DU PROMPT (STRUCTURÉ)")
        print("=" * 80)
        for section in built_prompt.structured_prompt.sections:
            print(f"\n{section.title}:")
            print("-" * 80)
            print(section.content[:500] + "..." if len(section.content) > 500 else section.content)
            print("-" * 80)
    
    # Résumé final
    print("\n" + "=" * 80)
    print("RESUME")
    print("=" * 80)
    print(f"Personnages: {', '.join(selected_characters)}")
    print(f"Lieu: {selected_location}")
    print(f"Contexte GDD: {context_tokens} tokens")
    print(f"Prompt total: {built_prompt.token_count} tokens")
    if built_prompt.structured_prompt:
        print(f"Nombre de sections: {len(built_prompt.structured_prompt.sections)}")
    print("=" * 80)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Erreur lors du test: {e}", exc_info=True)
        sys.exit(1)
