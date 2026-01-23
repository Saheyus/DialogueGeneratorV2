"""Vérifie les doublons dans les données GDD pour Seigneuresse Uresaïr."""
import json
from pathlib import Path

# Charger les données
gdd_path = Path('data/GDD_categories/personnages.json')
with open(gdd_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Chercher Uresaïr
uresair = None
for char in data:
    if isinstance(char, dict):
        nom = char.get('Nom', '')
        if 'Uresair' in str(nom) or 'Uresa' in str(nom):
            uresair = char
            break

if not uresair:
    print("Personnage Uresair non trouve")
    exit(1)

print(f"Personnage trouve: {uresair.get('Nom', 'Sans nom')}\n")
print("=" * 80)
print("ANALYSE DES CHAMPS")
print("=" * 80)

# Vérifier les champs qui peuvent avoir des doublons
champs_racine = list(uresair.keys())
print(f"\nChamps au niveau racine ({len(champs_racine)}):")
for field in champs_racine[:40]:
    value = uresair.get(field)
    if isinstance(value, dict):
        print(f"  - {field}: DICT avec cles {list(value.keys())[:10]}")
    elif isinstance(value, str):
        preview = value[:100] if len(value) > 100 else value
        print(f"  - {field}: STR ({len(value)} chars) - {preview}...")
    else:
        print(f"  - {field}: {type(value).__name__}")

# Vérifier spécifiquement les champs mentionnés par l'utilisateur
print("\n" + "=" * 80)
print("VERIFICATION DES DOUBLONS POTENTIELS")
print("=" * 80)

# Vérifier Introduction vs Résumé
introduction = uresair.get('Introduction')
resume = uresair.get('Resume') or uresair.get('Résumé') or uresair.get('résumé')

if introduction:
    if isinstance(introduction, dict):
        resume_fiche = introduction.get('Résumé de la fiche') or introduction.get('Résumé') or introduction.get('resume')
        if resume_fiche:
            print(f"\n[DOUBLON POTENTIEL] Introduction contient 'Résumé de la fiche': {len(resume_fiche)} caracteres")
            if resume and isinstance(resume, str):
                if resume == resume_fiche or resume in resume_fiche or resume_fiche in resume:
                    print(f"  [CONFIRME] 'Résumé' au niveau racine contient le même contenu")
                    print(f"  Resume racine: {resume[:100]}...")
                    print(f"  Resume dans Introduction: {resume_fiche[:100]}...")

# Vérifier Caractérisation vs Faiblesse/Compulsion/Désir
caracterisation = uresair.get('Caracterisation') or uresair.get('Caractérisation') or uresair.get('caracterisation')
faiblesse = uresair.get('Faiblesse') or uresair.get('faiblesse')
compulsion = uresair.get('Compulsion') or uresair.get('compulsion')
desir = uresair.get('Desir') or uresair.get('Désir') or uresair.get('desir') or uresair.get('Désir Principal')

if caracterisation:
    if isinstance(caracterisation, dict):
        caract_faiblesse = caracterisation.get('Faiblesse') or caracterisation.get('faiblesse')
        caract_compulsion = caracterisation.get('Compulsion') or caracterisation.get('compulsion')
        caract_desir = caracterisation.get('Désir') or caracterisation.get('Desir') or caracterisation.get('desir') or caracterisation.get('Désir Principal')
        
        if caract_faiblesse and faiblesse:
            print(f"\n[DOUBLON POTENTIEL] Faiblesse:")
            print(f"  - Dans Caractérisation: {len(str(caract_faiblesse))} caracteres")
            print(f"  - Au niveau racine: {len(str(faiblesse))} caracteres")
            if str(faiblesse) == str(caract_faiblesse) or str(faiblesse) in str(caract_faiblesse) or str(caract_faiblesse) in str(faiblesse):
                print(f"  [CONFIRME] Contenu identique ou similaire")
        
        if caract_compulsion and compulsion:
            print(f"\n[DOUBLON POTENTIEL] Compulsion:")
            print(f"  - Dans Caractérisation: {len(str(caract_compulsion))} caracteres")
            print(f"  - Au niveau racine: {len(str(compulsion))} caracteres")
        
        if caract_desir and desir:
            print(f"\n[DOUBLON POTENTIEL] Désir:")
            print(f"  - Dans Caractérisation: {len(str(caract_desir))} caracteres")
            print(f"  - Au niveau racine: {len(str(desir))} caracteres")

# Vérifier Background vs Contexte Background
background = uresair.get('Background') or uresair.get('background')
contexte_background = uresair.get('Contexte Background') or uresair.get('Contexte') or uresair.get('contexte')

if background and isinstance(background, dict):
    bg_contexte = background.get('Contexte') or background.get('contexte')
    if bg_contexte and contexte_background:
        print(f"\n[DOUBLON POTENTIEL] Contexte/Background:")
        print(f"  - Dans Background.Contexte: {len(str(bg_contexte))} caracteres")
        print(f"  - Au niveau racine (Contexte Background): {len(str(contexte_background))} caracteres")
        if str(contexte_background) == str(bg_contexte) or str(contexte_background) in str(bg_contexte) or str(bg_contexte) in str(contexte_background):
            print(f"  [CONFIRME] Contenu identique ou similaire")

print("\n" + "=" * 80)
print("ANALYSE TERMINEE")
print("=" * 80)
