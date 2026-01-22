"""Extraction du reasoning trace depuis les réponses OpenAI Responses API."""

import json
import logging
from typing import Dict, Any, List, Optional, Callable, Coroutine

logger = logging.getLogger(__name__)


class OpenAIReasoningExtractor:
    """Extrait le reasoning trace depuis les réponses OpenAI.
    
    Le reasoning trace peut être trouvé dans deux endroits:
    1. `response.reasoning` : Métadonnées (effort, summary configuré)
    2. `response.output` : Contenu réel (item avec type="reasoning")
    """

    @staticmethod
    def extract_reasoning_from_response_metadata(
        response: Any, variant_index: int = 1
    ) -> Optional[Dict[str, Any]]:
        """Extrait le reasoning trace depuis response.reasoning (métadonnées).
        
        Args:
            response: Réponse de l'API OpenAI Responses.
            variant_index: Index de la variante (pour logging).
            
        Returns:
            Dictionnaire avec le reasoning trace, ou None si pas disponible.
        """
        reasoning_data = getattr(response, "reasoning", None)
        if not reasoning_data:
            logger.debug(
                f"Aucun reasoning trace disponible pour la variante {variant_index} "
                f"(response.reasoning non présent)."
            )
            return None
        
        try:
            # Essayer d'accéder aux différents champs du reasoning
            reasoning_effort = getattr(reasoning_data, "effort", None)
            reasoning_summary = getattr(reasoning_data, "summary", None)
            reasoning_items = getattr(reasoning_data, "items", None)
            
            # Construire un dictionnaire avec le reasoning trace
            reasoning_trace_dict = {
                "effort": reasoning_effort,
                "summary": reasoning_summary,
                "items": None,
                "items_count": len(reasoning_items) if reasoning_items else 0,
            }
            
            # Convertir les items en dict si disponibles
            if reasoning_items:
                try:
                    reasoning_trace_dict["items"] = [
                        item.model_dump() if hasattr(item, 'model_dump') else str(item)
                        for item in reasoning_items
                    ]
                except Exception:
                    reasoning_trace_dict["items"] = [str(item) for item in reasoning_items]
            
            # NOTE: Ce code gère le cas où l'API retournerait "detailed" dans la réponse
            # (protection défensive), même si nous ne demandons jamais "detailed" car notre organisation
            # n'est pas vérifiée. Si l'API retourne "detailed" avec des items, on construit un résumé.
            # Pour GPT-5.2, les items peuvent contenir le contenu réel du reasoning
            if reasoning_summary == "detailed" and reasoning_items and len(reasoning_items) > 0:
                # Construire un résumé textuel depuis les items
                try:
                    summary_parts = []
                    for item in reasoning_items:
                        if hasattr(item, 'model_dump'):
                            item_dict = item.model_dump()
                            # Chercher des champs textuels dans l'item
                            for key in ['text', 'content', 'summary', 'message', 'reasoning']:
                                if key in item_dict and item_dict[key]:
                                    if isinstance(item_dict[key], str):
                                        summary_parts.append(item_dict[key])
                                    elif isinstance(item_dict[key], list):
                                        summary_parts.extend([str(p) for p in item_dict[key] if p])
                        else:
                            summary_parts.append(str(item))
                    
                    if summary_parts:
                        # Joindre les parties avec des retours à la ligne
                        constructed_summary = "\n".join(summary_parts)
                        reasoning_trace_dict["summary"] = constructed_summary
                except Exception as e:
                    logger.warning(f"Erreur lors de la construction du résumé depuis les items: {e}")
            
            # Logger les informations de reasoning
            logger.info(
                f"\n{'='*80}\n"
                f"PHASE RÉFLEXIVE (Reasoning Trace) - Variante {variant_index}\n"
                f"{'='*80}\n"
                f"Effort: {reasoning_effort}\n"
                f"Summary: {reasoning_summary}\n"
            )
            
            if reasoning_items:
                logger.info(f"Nombre d'étapes de raisonnement: {len(reasoning_items)}")
                for idx, item in enumerate(reasoning_items[:10], 1):  # Limiter à 10 pour éviter les logs trop longs
                    try:
                        item_str = json.dumps(
                            item.model_dump() if hasattr(item, 'model_dump') else str(item),
                            indent=2,
                            ensure_ascii=False
                        )
                        logger.info(f"Étape {idx}:\n{item_str}")
                    except Exception:
                        logger.info(f"Étape {idx}: {str(item)[:500]}")
                
                if len(reasoning_items) > 10:
                    logger.info(f"... ({len(reasoning_items) - 10} étapes supplémentaires)")
            
            # Afficher le reasoning complet en JSON si disponible
            try:
                reasoning_json = (
                    reasoning_data.model_dump_json(indent=2)
                    if hasattr(reasoning_data, 'model_dump_json')
                    else json.dumps(reasoning_data, indent=2, ensure_ascii=False, default=str)
                )
                logger.debug(f"Reasoning trace complet (JSON):\n{reasoning_json}")
            except Exception:
                pass
            
            logger.info(f"{'='*80}\n")
            
            return reasoning_trace_dict
            
        except Exception as reasoning_error:
            logger.warning(f"Erreur lors de l'extraction du reasoning trace: {reasoning_error}")
            # Fallback: essayer d'afficher le reasoning brut
            try:
                logger.info(f"Reasoning trace (brut): {str(reasoning_data)[:1000]}")
            except Exception:
                pass
            return None

    @staticmethod
    def extract_reasoning_from_output(
        output_items: List[Any], 
        existing_trace: Optional[Dict[str, Any]] = None,
        model_name: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Extrait le reasoning trace depuis response.output (contenu réel).
        
        Args:
            output_items: Liste des items dans response.output.
            existing_trace: Reasoning trace existant (depuis response.reasoning) à enrichir.
            
        Returns:
            Dictionnaire avec le reasoning trace enrichi, ou None si pas de reasoning dans output.
        """
        # Chercher l'item avec type="reasoning"
        reasoning_content_item = None
        for item in output_items:
            if getattr(item, "type", None) == "reasoning":
                reasoning_content_item = item
                break
        
        if not reasoning_content_item:
            return existing_trace
        
        try:
            # Extraire le contenu du reasoning depuis l'item
            # Le résumé peut être une liste d'objets ou une chaîne
            summary_raw = getattr(reasoning_content_item, "summary", None)
            reasoning_summary_text = None
            
            if isinstance(summary_raw, list):
                # Selon la doc OpenAI, summary est un tableau de chaînes de caractères
                # Joindre avec des retours à la ligne pour une meilleure lisibilité
                parts = []
                for part in summary_raw:
                    if isinstance(part, str) and part.strip():  # Ignorer les chaînes vides
                        parts.append(part.strip())
                    elif hasattr(part, "text") and part.text:
                        parts.append(str(part.text).strip())
                    elif isinstance(part, dict):
                        # Chercher différents champs possibles
                        for key in ["text", "content", "summary", "message"]:
                            if key in part and part[key] and isinstance(part[key], str):
                                parts.append(str(part[key]).strip())
                                break
                        # Si aucun champ textuel trouvé, convertir tout le dict
                        if not parts or parts[-1] != str(part).strip():
                            parts.append(str(part).strip())
                    elif part:  # Ignorer None, "", etc.
                        # Fallback: convertir en string
                        parts.append(str(part).strip())
                reasoning_summary_text = "\n".join(parts) if parts else None
            elif isinstance(summary_raw, str) and summary_raw.strip():
                reasoning_summary_text = summary_raw.strip()
            
            # Si summary est vide mais qu'on a encrypted_content, essayer de l'utiliser
            if not reasoning_summary_text:
                encrypted_content = getattr(reasoning_content_item, "encrypted_content", None)
                if encrypted_content:
                    # Pour l'instant, on ne peut pas décrypter encrypted_content sans clé
                    # Mais on peut indiquer qu'il y a du contenu chiffré
                    reasoning_summary_text = "[Contenu de raisonnement chiffré - non disponible]"
            
            # Si summary est toujours vide, gérer selon le modèle
            if not reasoning_summary_text:
                reasoning_id = getattr(reasoning_content_item, "id", None)
                is_mini_or_nano = model_name and ("mini" in model_name.lower() or "nano" in model_name.lower())
                
                if is_mini_or_nano:
                    # Pour mini/nano, si le summary est vide, c'est un bug connu de l'API
                    reasoning_summary_text = "Thinking output non disponible"
                else:
                    # Pour GPT-5.2, si le summary est vide, le contenu n'est pas disponible
                    # (Note: nous n'utilisons jamais "detailed" car notre organisation n'est pas vérifiée)
                    reasoning_summary_text = "Thinking output non disponible"
            
            # Fallback sur content ou text si summary est toujours vide
            if not reasoning_summary_text:
                text_value = getattr(reasoning_content_item, "text", None)
                content_value = getattr(reasoning_content_item, "content", None)
                
                # Si text ou content sont des listes, les joindre
                if isinstance(text_value, list):
                    text_value = "\n".join([str(p).strip() for p in text_value if p]).strip() or None
                if isinstance(content_value, list):
                    content_value = "\n".join([str(p).strip() for p in content_value if p]).strip() or None
                
                reasoning_summary_text = (text_value or content_value)
            
            # Construire ou enrichir le reasoning trace
            if existing_trace:
                reasoning_trace = existing_trace.copy()
            else:
                reasoning_trace = {
                    "effort": None,
                    "summary": None,
                    "items": None,
                    "items_count": 0,
                }
            
            # Vérifier la longueur du summary (en tokens approximatifs: ~4 caractères = 1 token)
            summary_token_count = 0
            if reasoning_summary_text:
                summary_token_count = len(reasoning_summary_text.split())  # Approximation: nombre de mots
                is_mini_or_nano = model_name and ("mini" in model_name.lower() or "nano" in model_name.lower())
                
                # Pour mini/nano, si le summary est trop court (< 10 tokens), considérer comme non disponible
                if is_mini_or_nano and summary_token_count < 10:
                    reasoning_summary_text = "Thinking output non disponible"
            
            # Remplacer le summary par le vrai texte si disponible
            # NOTE: Protection défensive - si l'API retourne "detailed" (ne devrait pas arriver car on ne le demande pas),
            # on gère quand même le cas. Pour mini/nano, on affiche "Thinking output non disponible" si le contenu est vide/court.
            is_mini_or_nano = model_name and ("mini" in model_name.lower() or "nano" in model_name.lower())
            
            if reasoning_summary_text:
                # Si le texte extrait est un vrai contenu (pas "detailed", pas un message d'info/erreur), on l'utilise TOUJOURS
                if (reasoning_summary_text != "detailed" 
                    and reasoning_summary_text != "Thinking output non disponible"
                    and not reasoning_summary_text.startswith("[")):
                    # C'est un vrai contenu, on remplace toujours
                    reasoning_trace["summary"] = reasoning_summary_text
                # Si le texte extrait est un message d'info/erreur ou "Thinking output non disponible", on l'utilise pour informer l'utilisateur
                elif (reasoning_summary_text.startswith("[") 
                      or reasoning_summary_text == "Thinking output non disponible"):
                    # On remplace seulement si on n'avait rien avant
                    if not existing_trace or not existing_trace.get("summary"):
                        reasoning_trace["summary"] = reasoning_summary_text
                # Si le texte extrait est "detailed" (ne devrait pas arriver), on le garde comme fallback
                elif not existing_trace or not existing_trace.get("summary"):
                    reasoning_trace["summary"] = reasoning_summary_text
            
            # Essayer d'extraire des items structurés si disponibles
            reasoning_items_content = getattr(reasoning_content_item, "items", None)
            if reasoning_items_content:
                try:
                    reasoning_trace["items"] = [
                        item.model_dump() if hasattr(item, 'model_dump') else str(item)
                        for item in reasoning_items_content
                    ]
                    reasoning_trace["items_count"] = len(reasoning_items_content)
                except Exception:
                    reasoning_trace["items"] = [str(item) for item in reasoning_items_content]
                    reasoning_trace["items_count"] = len(reasoning_items_content)
            
            logger.info(
                f"Reasoning trace extrait depuis output: "
                f"summary présent={bool(reasoning_trace.get('summary'))}, "
                f"items présents={bool(reasoning_trace.get('items'))}"
            )
            
            return reasoning_trace
            
        except Exception as e:
            logger.warning(f"Erreur lors de l'extraction du reasoning depuis output: {e}")
            return existing_trace

    @staticmethod
    async def extract_and_notify_reasoning(
        response: Any,
        variant_index: int,
        reasoning_callback: Optional[Callable[[Dict[str, Any]], Coroutine[Any, Any, None]]] = None,
        model_name: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Extrait le reasoning trace complet et appelle le callback si fourni.
        
        Args:
            response: Réponse de l'API OpenAI Responses.
            variant_index: Index de la variante (pour logging).
            reasoning_callback: Callback optionnel pour streaming du reasoning.
            
        Returns:
            Dictionnaire avec le reasoning trace complet, ou None si pas disponible.
        """
        # Extraire depuis response.reasoning (métadonnées)
        reasoning_trace = OpenAIReasoningExtractor.extract_reasoning_from_response_metadata(
            response, variant_index
        )
        
        # Enrichir depuis response.output (contenu réel)
        output_items = getattr(response, "output", None) or []
        reasoning_trace = OpenAIReasoningExtractor.extract_reasoning_from_output(
            output_items, reasoning_trace, model_name
        )
        
        # Appeler le callback si fourni pour streaming
        if reasoning_trace and reasoning_callback:
            try:
                await reasoning_callback(reasoning_trace)
            except Exception as callback_error:
                logger.warning(f"Erreur lors de l'appel du callback reasoning: {callback_error}")
        
        return reasoning_trace
