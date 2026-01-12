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

print('=== POSITION DU VOCABULAIRE ===')
vocab_pos = prompt.find('[VOCABULAIRE ALTEIR]')
section0_pos = prompt.find('SECTION 0')
section2_pos = prompt.find('SECTION 2')
print(f'Vocabulaire position: {vocab_pos}')
print(f'SECTION 0 position: {section0_pos}')
print(f'SECTION 2 position: {section2_pos}')
print(f'Vocabulaire après SECTION 2: {vocab_pos > section2_pos if vocab_pos > 0 and section2_pos > 0 else False}')
print(f'Vocabulaire avant SECTION 0: {vocab_pos < section0_pos if vocab_pos > 0 and section0_pos > 0 else False}')

print('\n=== PREMIÈRES 1000 CARACTÈRES ===')
print(prompt[:1000])

print('\n=== AUTOUR DU VOCABULAIRE ===')
if vocab_pos > 0:
    print(prompt[max(0, vocab_pos-300):vocab_pos+800])
