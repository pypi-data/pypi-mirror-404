"""
Languages module: Language-specific configurations.

This module provides language configurations for tree-sitter parsing:
- LanguageConfig: Base class for language configurations
- LanguageRegistry: Registry for looking up languages by extension
- PythonConfig, TypeScriptConfig, JavaScriptConfig: Built-in configs
"""

from mcp_context_graph.languages.base import LanguageConfig
from mcp_context_graph.languages.registry import (
    LanguageRegistry,
    get_language_for_file,
    get_registry,
)

__all__ = [
    "LanguageConfig",
    "LanguageRegistry",
    "get_language_for_file",
    "get_registry",
]
