import requests
import json

data = {
    'user_instructions': 'Test',
    'context_selections': {
        'characters': ['Akthar-Neth Amatru, l\'Exégète', 'Valkazer Reitar']
    },
    'vocabulary_config': {'Mondialement': 'all'},
    'include_narrative_guides': True
}

r = requests.post('http://localhost:4243/api/v1/dialogues/estimate-tokens', json=data)
resp = r.json()
prompt = resp.get('raw_prompt', '')

print('=== LONGUEUR DU PROMPT ===')
print(f'Longueur: {len(prompt)} caractères')

print('\n=== PREMIERS 2000 CARACTÈRES ===')
print(prompt[:2000])

print('\n=== RECHERCHE DES SECTIONS ===')
sections = ['SECTION 0', 'SECTION 1', 'SECTION 2', 'SECTION 3', 'VOCABULAIRE ET GUIDES NARRATIFS']
for section in sections:
    pos = prompt.find(section)
    if pos >= 0:
        print(f'{section}: position {pos}')
        # Afficher 100 caractères avant et après
        start = max(0, pos - 100)
        end = min(len(prompt), pos + len(section) + 100)
        print(f'  Contexte: ...{prompt[start:end]}...')
    else:
        print(f'{section}: NON TROUVÉ')

print('\n=== STRUCTURE DU PROMPT ===')
# Compter les lignes
lines = prompt.split('\n')
print(f'Nombre de lignes: {len(lines)}')
print(f'Premières 20 lignes:')
for i, line in enumerate(lines[:20]):
    print(f'{i+1:3d}: {line[:80]}')
