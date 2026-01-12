"""Module PromptEngine (DEPRECATED - Wrapper de compatibilité).

DEPRECATED: This module has moved to core.prompt.prompt_engine

This compatibility layer will be removed in version 2.0.
Please update your imports:
    from core.prompt.prompt_engine import PromptEngine, PromptInput, BuiltPrompt

All exports are re-exported from the new location with deprecation warnings.
"""
import warnings
from core.prompt.prompt_engine import *  # noqa: F403, F401

warnings.warn(
    "Importing from prompt_engine is deprecated. "
    "Use 'from core.prompt.prompt_engine import PromptEngine' instead.",
    DeprecationWarning,
    stacklevel=2
)
