"""Basic usage example for semantic-kernel-builtsimple.

This example demonstrates how to use the plugins directly without an LLM.
"""

import asyncio
from semantic_kernel import Kernel
from semantic_kernel_builtsimple import (
    BuiltSimplePubMedPlugin,
    BuiltSimpleArxivPlugin,
    BuiltSimpleWikipediaPlugin,
)


async def main():
    # Create kernel and add plugins
    kernel = Kernel()
    kernel.add_plugin(BuiltSimplePubMedPlugin(), plugin_name="pubmed")
    kernel.add_plugin(BuiltSimpleArxivPlugin(), plugin_name="arxiv")
    kernel.add_plugin(BuiltSimpleWikipediaPlugin(), plugin_name="wikipedia")

    # Search PubMed
    print("=" * 60)
    print("PubMed Search: 'CRISPR gene therapy'")
    print("=" * 60)
    result = await kernel.invoke(
        plugin_name="pubmed",
        function_name="search_pubmed",
        query="CRISPR gene therapy",
        limit=3,
    )
    print(result)

    # Search ArXiv
    print("\n" + "=" * 60)
    print("ArXiv Search: 'transformer attention mechanism'")
    print("=" * 60)
    result = await kernel.invoke(
        plugin_name="arxiv",
        function_name="search_arxiv",
        query="transformer attention mechanism",
        limit=3,
    )
    print(result)

    # Search Wikipedia
    print("\n" + "=" * 60)
    print("Wikipedia Search: 'quantum computing'")
    print("=" * 60)
    result = await kernel.invoke(
        plugin_name="wikipedia",
        function_name="search_wikipedia",
        query="quantum computing",
        limit=3,
    )
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
