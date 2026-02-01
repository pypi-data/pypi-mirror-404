"""
LanguageRegistry: Registry for language configurations.

Provides:
- Registration of language configs
- Lookup by file extension (.py, .ts, .js)
- Language detection and grammar loading
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp_context_graph.languages.base import LanguageConfig

logger = logging.getLogger(__name__)


class LanguageRegistry:
    """
    Registry for language configurations.

    The registry provides a central place to register and look up
    language configurations by name or file extension. It supports:
    - Registration of LanguageConfig instances
    - Lookup by language name (e.g., "python")
    - Lookup by file extension (e.g., ".py", ".ts")
    - Auto-registration of built-in languages

    Example:
        registry = LanguageRegistry()
        registry.register_builtin_languages()

        # Lookup by name
        config = registry.get("python")

        # Lookup by extension
        config = registry.get_by_extension(".py")
    """

    __slots__ = ("_by_name", "_by_extension")

    def __init__(self) -> None:
        """Initialize an empty registry."""
        self._by_name: dict[str, LanguageConfig] = {}
        self._by_extension: dict[str, LanguageConfig] = {}

    def register(self, config: LanguageConfig) -> None:
        """
        Register a language configuration.

        Args:
            config: The LanguageConfig instance to register.

        Raises:
            ValueError: If language name is already registered.
        """
        name = config.name

        if name in self._by_name:
            msg = f"Language '{name}' is already registered"
            raise ValueError(msg)

        self._by_name[name] = config

        # Register all extensions
        for ext in config.file_extensions:
            ext_lower = ext.lower()
            if ext_lower in self._by_extension:
                existing = self._by_extension[ext_lower]
                logger.warning(
                    "Extension %r already registered for %s, overwriting with %s",
                    ext_lower,
                    existing.name,
                    name,
                )
            self._by_extension[ext_lower] = config

        logger.debug(
            "Registered language %s with extensions %s",
            name,
            config.file_extensions,
        )

    def get(self, name: str) -> LanguageConfig | None:
        """
        Get a language configuration by name.

        Args:
            name: The language name (e.g., "python", "typescript").

        Returns:
            The LanguageConfig if found, None otherwise.
        """
        return self._by_name.get(name.lower())

    def get_by_extension(self, extension: str) -> LanguageConfig | None:
        """
        Get a language configuration by file extension.

        Args:
            extension: The file extension with or without leading dot
                      (e.g., ".py", "py", ".ts", "ts").

        Returns:
            The LanguageConfig if found, None otherwise.
        """
        # Normalize extension
        ext = extension.lower()
        if not ext.startswith("."):
            ext = f".{ext}"
        return self._by_extension.get(ext)

    def get_for_file(self, file_path: Path | str) -> LanguageConfig | None:
        """
        Get a language configuration for a file based on its extension.

        Args:
            file_path: Path to the file.

        Returns:
            The LanguageConfig if found, None otherwise.
        """
        path = Path(file_path) if isinstance(file_path, str) else file_path
        return self.get_by_extension(path.suffix)

    def supported_extensions(self) -> list[str]:
        """
        Get list of all supported file extensions.

        Returns:
            List of extensions with leading dots.
        """
        return list(self._by_extension.keys())

    def supported_languages(self) -> list[str]:
        """
        Get list of all registered language names.

        Returns:
            List of language names.
        """
        return list(self._by_name.keys())

    def is_supported(self, file_path: Path | str) -> bool:
        """
        Check if a file type is supported.

        Args:
            file_path: Path to the file.

        Returns:
            True if the file extension is supported.
        """
        return self.get_for_file(file_path) is not None

    def register_builtin_languages(self) -> None:
        """
        Register all built-in language configurations.

        This method registers Python, TypeScript, and JavaScript
        language configurations.
        """
        # Import here to avoid circular imports
        from mcp_context_graph.languages.python.config import PythonConfig
        from mcp_context_graph.languages.typescript.config import (
            JavaScriptConfig,
            TypeScriptConfig,
        )

        self.register(PythonConfig())
        self.register(TypeScriptConfig())
        self.register(JavaScriptConfig())

        logger.info(
            "Registered %d built-in languages: %s",
            len(self._by_name),
            list(self._by_name.keys()),
        )

    def __len__(self) -> int:
        """Return number of registered languages."""
        return len(self._by_name)

    def __contains__(self, name: str) -> bool:
        """Check if a language is registered."""
        return name.lower() in self._by_name

    def __repr__(self) -> str:
        """Return string representation."""
        return f"LanguageRegistry(languages={list(self._by_name.keys())})"


# Global registry instance (lazy initialization)
_default_registry: LanguageRegistry | None = None


def get_registry() -> LanguageRegistry:
    """
    Get the default language registry with built-in languages.

    Returns:
        The global LanguageRegistry instance.
    """
    global _default_registry
    if _default_registry is None:
        _default_registry = LanguageRegistry()
        _default_registry.register_builtin_languages()
    return _default_registry


def get_language_for_file(file_path: Path | str) -> LanguageConfig | None:
    """
    Convenience function to get language config for a file.

    Args:
        file_path: Path to the file.

    Returns:
        The LanguageConfig if found, None otherwise.
    """
    return get_registry().get_for_file(file_path)
