"""Module ContextBuilder (DEPRECATED - Wrapper de compatibilité).

DEPRECATED: This module has moved to core.context.context_builder

This compatibility layer will be removed in version 2.0.
Please update your imports:
    from core.context.context_builder import ContextBuilder

All exports are re-exported from the new location with deprecation warnings.
"""
import warnings
from core.context.context_builder import *  # noqa: F403, F401

warnings.warn(
    "Importing from context_builder is deprecated. "
    "Use 'from core.context.context_builder import ContextBuilder' instead.",
    DeprecationWarning,
    stacklevel=2
)
