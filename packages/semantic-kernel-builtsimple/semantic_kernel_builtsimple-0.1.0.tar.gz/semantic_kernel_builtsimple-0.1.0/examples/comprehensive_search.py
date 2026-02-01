"""Comprehensive search example using all sources.

This example shows how to search all sources at once
for interdisciplinary research topics.
"""

import asyncio
from semantic_kernel import Kernel
from semantic_kernel_builtsimple import BuiltSimpleResearchPlugin


async def main():
    kernel = Kernel()
    
    # Add combined research plugin
    kernel.add_plugin(BuiltSimpleResearchPlugin(), plugin_name="research")

    # Search all sources for an interdisciplinary topic
    query = "artificial intelligence in drug discovery"
    
    print(f"Searching all sources for: '{query}'")
    print("=" * 70)
    
    result = await kernel.invoke(
        plugin_name="research",
        function_name="search_all_sources",
        query=query,
        limit_per_source=3,
    )
    
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
