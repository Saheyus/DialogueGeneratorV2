"""Module LLM Client (DEPRECATED - Wrapper de compatibilité).

DEPRECATED: This module has moved to core.llm.llm_client

This compatibility layer will be removed in version 2.0.
Please update your imports:
    from core.llm.llm_client import ILLMClient, OpenAIClient, DummyLLMClient

All exports are re-exported from the new location with deprecation warnings.
"""
import warnings
from core.llm.llm_client import *  # noqa: F403, F401

warnings.warn(
    "Importing from llm_client is deprecated. "
    "Use 'from core.llm.llm_client import ILLMClient' instead.",
    DeprecationWarning,
    stacklevel=2
)
