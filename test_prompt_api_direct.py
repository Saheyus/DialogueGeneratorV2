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

print("Envoi de la requête à l'API...")
r = requests.post('http://localhost:4243/api/v1/dialogues/estimate-tokens', json=data)
resp = r.json()
prompt = resp.get('raw_prompt', '')

print('\n=== LONGUEUR DU PROMPT ===')
print(f'Longueur: {len(prompt)} caractères')

print('\n=== PREMIERS 3000 CARACTÈRES ===')
print(prompt[:3000])

print('\n=== RECHERCHE DES SECTIONS ===')
sections = ['SECTION 0', 'SECTION 1', 'SECTION 2', 'SECTION 3', 'VOCABULAIRE ET GUIDES NARRATIFS', '[VOCABULAIRE ALTEIR]']
for section in sections:
    pos = prompt.find(section)
    if pos >= 0:
        print(f'{section}: position {pos}')
        # Afficher 200 caractères avant et après
        start = max(0, pos - 200)
        end = min(len(prompt), pos + len(section) + 200)
        context = prompt[start:end].replace('\n', '\\n')
        print(f'  Contexte: ...{context}...')
    else:
        print(f'{section}: NON TROUVÉ')

print('\n=== STRUCTURE DU PROMPT (premières 50 lignes) ===')
lines = prompt.split('\n')
print(f'Nombre de lignes total: {len(lines)}')
for i, line in enumerate(lines[:50]):
    print(f'{i+1:3d}: {line[:120]}')
