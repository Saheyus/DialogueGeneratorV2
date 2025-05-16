# DialogueGenerator/yarn_renderer.py
import logging
import yaml # Pour générer l'en-tête YAML proprement

logger = logging.getLogger(__name__)

class YarnRenderer:
    def __init__(self):
        pass

    def render(self, llm_output_body: str, title: str = "GeneratedNode", tags: list[str] = None) -> str:
        """
        Prend la sortie brute du LLM (corps du dialogue) et la formate en un noeud Yarn complet.

        Args:
            llm_output_body (str): Le corps du dialogue généré par le LLM (sans l'en-tête YAML).
            title (str): Le titre du noeud Yarn.
            tags (list[str], optional): Une liste de tags pour le noeud.

        Returns:
            str: Le noeud Yarn complet sous forme de chaîne de caractères.
        """
        if tags is None:
            tags = ["gdd_generated_dialogue"]
        
        header_data = {
            "title": title,
            "tags": ' '.join(tags) if tags else ''
        }
        
        # yaml.dump ajoute un "...\n" à la fin si le document se termine, et un "\n" s'il y en a déjà un.
        # Nous voulons un format propre pour l'en-tête, sans le "..." final.
        # dump ne met pas de --- au début par défaut pour un seul doc.
        yaml_header = yaml.dump(header_data, sort_keys=False, width=float("inf")).strip()
        
        # S'assurer que le corps commence bien sur une nouvelle ligne après l'en-tête
        # et qu'il n'y a pas de multiples lignes vides entre l'en-tête et le corps.
        cleaned_llm_output_body = llm_output_body.strip()

        # Assemblage final
        # Le format Yarn typique est :
        # ---
        # title: Test
        # tags: 
        # ---
        # Contenu...
        # ===
        
        # Ajustement pour que le dump YAML soit plus proche du format attendu pour l'en-tête Yarn
        # En général, l'en-tête est simple et ne nécessite pas de complexité de dump YAML.
        # On peut le construire manuellement pour plus de contrôle.
        
        header_lines = []
        header_lines.append(f"title: {title}")
        if tags:
            header_lines.append(f"tags: {' '.join(tags)}")
        else:
            header_lines.append("tags:") # ou omettre la ligne tags si vide
        
        final_header = "\n".join(header_lines)

        yarn_node_parts = [
            "---",
            final_header,
            "---",
            cleaned_llm_output_body,
            "==="
        ]
        
        full_yarn_node = "\n".join(yarn_node_parts)
        logger.info(f"Noeud Yarn rendu pour le titre: {title}")
        return full_yarn_node

# Pour des tests rapides
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    renderer = YarnRenderer()

    dummy_llm_output = \
"""Player: Salut ! Comment ça va ?
NPC: Bien, merci. Et toi ?
    -> Option 1 [[Suite_Option1]]
        Player: J'ai choisi l'option 1.
    -> Option 2
        NPC: Intéressant choix que l'option 2.
Player: Au revoir.
"""
    node_title = "TestInteraction"
    node_tags = ["test", "npc_greeting"]

    rendered_yarn = renderer.render(dummy_llm_output, node_title, node_tags)
    print("--- NOEUD YARN RENDU ---")
    print(rendered_yarn)

    rendered_yarn_no_tags = renderer.render(dummy_llm_output, "TestSansTags")
    print("\n--- NOEUD YARN SANS TAGS (avec tag par défaut) ---")
    print(rendered_yarn_no_tags)
    
    rendered_yarn_tags_vides = renderer.render(dummy_llm_output, "TestTagsVides", tags=[])
    print("\n--- NOEUD YARN AVEC TAGS VIDES ---")
    print(rendered_yarn_tags_vides) 