"""Semantic Kernel plugins for Built-Simple research APIs.

This package provides Semantic Kernel plugins for searching scientific
literature through Built-Simple's research APIs:

- **PubMed**: 4.5M+ peer-reviewed biomedical and life sciences articles
- **ArXiv**: 2.7M+ preprints in physics, math, computer science, and ML
- **Wikipedia**: Semantic search over Wikipedia articles

Example:
    >>> from semantic_kernel import Kernel
    >>> from semantic_kernel_builtsimple import (
    ...     BuiltSimplePubMedPlugin,
    ...     BuiltSimpleArxivPlugin,
    ...     BuiltSimpleWikipediaPlugin,
    ...     BuiltSimpleResearchPlugin,
    ... )
    >>>
    >>> kernel = Kernel()
    >>> kernel.add_plugin(BuiltSimplePubMedPlugin(), plugin_name="pubmed")
    >>> kernel.add_plugin(BuiltSimpleArxivPlugin(), plugin_name="arxiv")
    >>> kernel.add_plugin(BuiltSimpleWikipediaPlugin(), plugin_name="wikipedia")
    >>>
    >>> # Or use the combined plugin
    >>> kernel.add_plugin(BuiltSimpleResearchPlugin(), plugin_name="research")
"""

from semantic_kernel_builtsimple.plugins import (
    BuiltSimpleArxivPlugin,
    BuiltSimplePubMedPlugin,
    BuiltSimpleResearchPlugin,
    BuiltSimpleWikipediaPlugin,
)
from semantic_kernel_builtsimple.client import (
    BuiltSimpleClient,
    BuiltSimpleAPIError,
)

__version__ = "0.1.0"

__all__ = [
    # Plugins
    "BuiltSimplePubMedPlugin",
    "BuiltSimpleArxivPlugin",
    "BuiltSimpleWikipediaPlugin",
    "BuiltSimpleResearchPlugin",
    # Client
    "BuiltSimpleClient",
    "BuiltSimpleAPIError",
]
