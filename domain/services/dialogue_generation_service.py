from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Tuple
import logging
import asyncio

# Tentative d'imports pour ContextBuilder et PromptEngine
try:
    from ...context_builder import ContextBuilder
    from ...prompt_engine import PromptEngine
    from ...llm_client import ILLMClient
except ImportError:
    import sys
    from pathlib import Path
    project_root = Path(__file__).resolve().parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from DialogueGenerator.context_builder import ContextBuilder
    from DialogueGenerator.prompt_engine import PromptEngine
    from DialogueGenerator.llm_client import ILLMClient

logger = logging.getLogger(__name__)

class IDialogueGenerationService(ABC):
    @abstractmethod
    async def generate_dialogue_variants(self, 
                                         llm_client: ILLMClient, 
                                         k_variants: int, 
                                         max_context_tokens_for_context_builder: int, 
                                         structured_output: bool, 
                                         user_instructions: str, 
                                         system_prompt_override: Optional[str], 
                                         context_selections: Dict[str, Any], 
                                         current_llm_model_identifier: str
                                         ) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str], Optional[int]]:
        pass

class DialogueGenerationService(IDialogueGenerationService):
    def __init__(self, context_builder: ContextBuilder, prompt_engine: PromptEngine):
        self.context_builder = context_builder
        self.prompt_engine = prompt_engine
        logger.info("DialogueGenerationService initialized.")

    async def generate_dialogue_variants(self, 
                                         llm_client: ILLMClient, 
                                         k_variants: int, 
                                         max_context_tokens_for_context_builder: int, 
                                         structured_output: bool,
                                         user_instructions: str, 
                                         system_prompt_override: Optional[str], 
                                         context_selections: Dict[str, Any],
                                         current_llm_model_identifier: str
                                         ) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str], Optional[int]]:
        logger.info(f"DialogueGenerationService: Starting dialogue generation. Model: {current_llm_model_identifier}, K: {k_variants}")
        original_system_prompt = None
        final_prompt_str = None
        estimated_tokens = 0
        variants_output: Optional[List[Dict[str, Any]]] = []

        try:
            # 1. Construire la chaîne de contexte
            # Note: include_dialogue_type (maintenant structured_output) n'est pas un param direct de build_context ici.
            # Il est utilisé pour le prompt_engine plus bas.
            # Les clés _scene_protagonists et _scene_location sont attendues dans context_selections si présentes.
            
            scene_instruction_parts = []
            if "_scene_protagonists" in context_selections:
                protagonists = context_selections["_scene_protagonists"]
                char_a = protagonists.get("personnage_a")
                char_b = protagonists.get("personnage_b")
                if char_a and char_b:
                    scene_instruction_parts.append(f"Scene between {char_a} and {char_b}.")
                elif char_a:
                    scene_instruction_parts.append(f"Scene with {char_a}.")
                elif char_b: # Théoriquement pas possible si A est None, mais pour être complet
                    scene_instruction_parts.append(f"Scene with {char_b}.")
            
            if "_scene_location" in context_selections:
                location_info = context_selections["_scene_location"]
                loc = location_info.get("lieu")
                sub_loc = location_info.get("sous_lieu")
                if sub_loc:
                    scene_instruction_parts.append(f"Takes place at {sub_loc} ({loc}).")
                elif loc:
                    scene_instruction_parts.append(f"Takes place at {loc}.")
            
            # scene_instruction pour context_builder: peut être juste user_instructions ou une combinaison
            # Pour l'instant, utilisons user_instructions comme c'était fait implicitement.
            # Le ContextBuilder.build_context s'attend à 'scene_instruction'
            # Dans la version originale de GenerationPanel, user_instructions était utilisé pour cela ET pour user_specific_goal.
            # Gardons cela pour l'instant, mais c'est un point à clarifier/améliorer (DTOs).
            context_summary_text = self.context_builder.build_context(
                selected_elements=context_selections,
                scene_instruction=user_instructions, # Ou une version plus structurée des infos de scène
                max_tokens=max_context_tokens_for_context_builder,
                # include_dialogue_type n'est pas un param de build_context, il est pour le prompt_engine
            )
            logger.debug(f"Context built by service: {len(context_summary_text)} chars, first 100: {context_summary_text[:100]}")

            # 2. Mettre à jour le prompt système du moteur si un override est fourni
            if system_prompt_override is not None and self.prompt_engine.system_prompt_template != system_prompt_override:
                original_system_prompt = self.prompt_engine.system_prompt_template
                self.prompt_engine.system_prompt_template = system_prompt_override
                logger.info(f"System prompt temporarily set to: '{system_prompt_override[:100]}...'")

            # 3. Construire le prompt final
            generation_params_for_prompt_build = {
                "structured_generation_request": structured_output
                # Autres paramètres potentiels pour le prompt engine si nécessaire
            }
            final_prompt_str, estimated_tokens = self.prompt_engine.build_prompt(
                context_summary=context_summary_text,
                user_specific_goal=user_instructions,
                generation_params=generation_params_for_prompt_build
            )
            logger.info(f"Final prompt built. Estimated tokens: {estimated_tokens}. Length: {len(final_prompt_str)} chars.")
            
            if not final_prompt_str:
                logger.error("Failed to build prompt string (empty).")
                # Restaurer le prompt système ici aussi
                if original_system_prompt is not None:
                    self.prompt_engine.system_prompt_template = original_system_prompt
                return None, "Error: Prompt could not be built.", 0

            # 4. Appeler le LLM pour générer les variantes
            if not llm_client: # Vérification ajoutée
                logger.error("LLM client is None, cannot generate variants.")
                if original_system_prompt is not None:
                    self.prompt_engine.system_prompt_template = original_system_prompt
                return None, final_prompt_str, estimated_tokens # Retourne le prompt même si pas de LLM

            logger.debug(f"Calling LLM to generate {k_variants} variants.")
            llm_raw_variants = await llm_client.generate_variants(prompt=final_prompt_str, k=k_variants)
            
            # Transformer les variantes brutes (list[str]) en list[dict] comme attendu par l'UI
            # { "id": str(uuid.uuid4()), "title": f"Variante {i+1}", "content": variant_text, "is_new": True }
            if llm_raw_variants:
                variants_output = []
                for i, variant_text in enumerate(llm_raw_variants):
                    variants_output.append({
                        "id": str(asyncio.get_event_loop().time()) + f"-{i}", # Utilisation d'un ID plus simple pour l'instant
                        "title": f"Variante {i+1}",
                        "content": variant_text,
                        "is_new": True 
                    })
                logger.info(f"LLM generated {len(variants_output)} variants.")
            else:
                logger.warning("LLM returned no variants.")
                variants_output = [] # Assurer que c'est une liste vide et non None

            # 5. Restaurer le prompt système original s'il a été changé
            if original_system_prompt is not None:
                self.prompt_engine.system_prompt_template = original_system_prompt
                logger.info("Original system prompt restored.")
            
            return variants_output, final_prompt_str, estimated_tokens

        except Exception as e:
            logger.exception("Error during dialogue generation in DialogueGenerationService:")
            if original_system_prompt is not None and hasattr(self.prompt_engine, 'system_prompt_template'):
                if self.prompt_engine.system_prompt_template != original_system_prompt:
                    self.prompt_engine.system_prompt_template = original_system_prompt
                    logger.debug("Restored original system_prompt_template after error in service.")
            # Retourner le prompt s'il a été construit, même en cas d'erreur LLM
            return None, final_prompt_str if final_prompt_str else "Error during generation.", estimated_tokens
    
    # Ancienne méthode, à traiter
    async def generate_dialogue(self, params: dict) -> dict:
        logger.warning("[DialogueGenerationService] generate_dialogue (ancienne signature) appelée. Rediriger ou supprimer.")
        # Pour l'instant, pas d'implémentation directe, car les paramètres sont différents.
        # Cela devrait lever une erreur ou être mappé correctement.
        return {"variants": [], "full_prompt": "Not implemented via old signature", "estimated_tokens": 0} 