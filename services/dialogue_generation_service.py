import logging
import json
import re
from typing import Optional, Any, Tuple, List, Dict, Union, Type
from pydantic import BaseModel
import uuid
import asyncio

try:
    from ..context_builder import ContextBuilder
    from ..prompt_engine import PromptEngine
    from ..llm_client import ILLMClient # Utiliser l'interface
except ImportError:
    # Support pour exécution directe ou tests unitaires hors contexte de package complet
    import sys
    from pathlib import Path
    current_dir = Path(__file__).resolve().parent.parent
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    from context_builder import ContextBuilder
    from prompt_engine import PromptEngine
    from llm_client import ILLMClient

logger = logging.getLogger(__name__)

# IDialogueGenerationService supprimé - interface vide après suppression du système texte libre

class DialogueGenerationService:
    def __init__(self, context_builder: ContextBuilder, prompt_engine: PromptEngine):
        """
        Initialise le service de génération de dialogues.
        
        Args:
            context_builder: Composant qui construit le contexte basé sur les sélections utilisateur
            prompt_engine: Composant qui construit les prompts pour le LLM
        """
        self.context_builder = context_builder
        self.prompt_engine = prompt_engine
        
        # Initialisation du logger
        self.logger = logging.getLogger(__name__)
        logger.info("DialogueGenerationService initialized.")

    # generate_dialogue_variants supprimé - système texte libre obsolète, utiliser Unity JSON à la place
    # generate_interaction_variants supprimé - système obsolète remplacé par Unity JSON

    def _build_context_summary(self, context_selections: Dict[str, Any], user_instructions: str, max_tokens: int, no_limit: bool = False, field_configs: Optional[Dict[str, List[str]]] = None, organization_mode: Optional[str] = None) -> str:
        """
        Construit le résumé contextuel à partir des sélections et instructions utilisateur.
        Si no_limit est True, max_tokens est ignoré (valeur très haute transmise).
        
        Args:
            context_selections: Sélections de contexte GDD.
            user_instructions: Instructions utilisateur.
            max_tokens: Nombre maximum de tokens.
            no_limit: Si True, ignore la limite de tokens.
            field_configs: Configuration des champs à inclure (optionnel).
            organization_mode: Mode d'organisation du contexte (optionnel).
        """
        if no_limit:
            max_tokens = 999999
        # Log pour déboguer les personnages sélectionnés
        logger.debug(f"[_build_context_summary] context_selections reçu: {context_selections}")
        logger.debug(f"[_build_context_summary] characters dans context_selections: {context_selections.get('characters', [])}")
        
        # Extraire _element_modes si présent
        element_modes = context_selections.pop("_element_modes", None) if isinstance(context_selections, dict) else None
        
        # Utiliser build_context_json (obligatoire, plus de fallback)
        structured_context = self.context_builder.build_context_json(
            selected_elements=context_selections,
            scene_instruction=user_instructions,
            field_configs=field_configs,
            organization_mode=organization_mode or "narrative",
            max_tokens=max_tokens,
            include_dialogue_type=True,
            element_modes=element_modes
        )
        # Sérialiser en texte pour compatibilité avec l'ancienne signature
        return self.context_builder._context_serializer.serialize_to_text(structured_context)

    def _restore_prompt_on_error(self, original_system_prompt: Optional[str]):
        if original_system_prompt is not None:
            if hasattr(self.prompt_engine, 'system_prompt_template') and self.prompt_engine.system_prompt_template != original_system_prompt:
                self.prompt_engine.system_prompt_template = original_system_prompt
                logger.info("Original system prompt restored after operation or error.")
            elif not hasattr(self.prompt_engine, 'system_prompt_template'):
                 logger.warning("PromptEngine does not have system_prompt_template attribute during error recovery.")
        # else: logger.debug("No original system prompt to restore or no override was made.")

    def _extract_json_from_text(self, text: str) -> Optional[str]:
        """Extracts a JSON string from a text that might contain markdown code blocks.

        Args:
            text: The input text.

        Returns:
            The extracted JSON string, or None if not found.
        """
        # Regex to find JSON within markdown-style code blocks (```json ... ``` or ``` ... ```)
        # It captures the content within the innermost curly braces assuming it's the JSON object.
        match = re.search(r'```(?:json)?\s*({.*?})\s*```', text, re.DOTALL)
        if match:
            return match.group(1)
        
        # If no markdown block is found, try to find a JSON object directly
        # This is a simplified regex, might need to be more robust depending on expected LLM output
        match = re.search(r'({.*?})', text, re.DOTALL)
        if match:
            return match.group(1)
            
        return None

    # _parse_llm_response_to_interaction supprimé - système obsolète
    # _is_valid_id supprimé - système obsolète
    # _find_first_dialogue_text supprimé - système obsolète 

    # prepare_generation_preview supprimé - système texte libre obsolète
    # parse_interaction_response supprimé - système obsolète 
    # generate_structured_object_variants supprimé - système obsolète
