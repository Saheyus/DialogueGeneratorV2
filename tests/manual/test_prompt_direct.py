import sys
sys.path.insert(0, '.')

from core.prompt.prompt_engine import PromptEngine, PromptInput

# Créer une instance de PromptEngine
engine = PromptEngine()

# Construire le prompt avec les mêmes paramètres que le test
prompt_input = PromptInput(
    user_instructions="Test",
    npc_speaker_id="Akthar-Neth Amatru, l'Exégète",
    player_character_id="URESAIR",
    skills_list=[],
    traits_list=[],
    context_summary="",
    scene_location=None,
    max_choices=None,
    narrative_tags=None,
    author_profile=None,
    vocabulary_config={"Mondialement": "all"},
    include_narrative_guides=True
)
built = engine.build_prompt(prompt_input)
prompt = built.raw_prompt
tokens = built.token_count

print('=== LONGUEUR DU PROMPT ===')
print(f'Longueur: {len(prompt)} caractères')

print('\n=== PREMIERS 2000 CARACTÈRES ===')
print(prompt[:2000])

print('\n=== RECHERCHE DES SECTIONS ===')
sections = ['SECTION 0', 'SECTION 1', 'SECTION 2', 'SECTION 3', 'VOCABULAIRE ET GUIDES NARRATIFS', '[VOCABULAIRE ALTEIR]']
for section in sections:
    pos = prompt.find(section)
    if pos >= 0:
        print(f'{section}: position {pos}')
    else:
        print(f'{section}: NON TROUVÉ')

print('\n=== STRUCTURE DU PROMPT (premières 30 lignes) ===')
lines = prompt.split('\n')
for i, line in enumerate(lines[:30]):
    print(f'{i+1:3d}: {line[:100]}')
