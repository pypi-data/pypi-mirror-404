"""Tests for semantic-kernel-builtsimple plugins."""

import asyncio
from semantic_kernel_builtsimple import (
    BuiltSimplePubMedPlugin,
    BuiltSimpleArxivPlugin,
    BuiltSimpleWikipediaPlugin,
)


async def test_pubmed_plugin():
    """Test PubMed plugin returns results."""
    plugin = BuiltSimplePubMedPlugin()
    results = await plugin.search_pubmed("mRNA vaccines", limit=2)
    
    assert isinstance(results, str), "Should return formatted string"
    assert "Result" in results or "mRNA" in results, "Should contain results"


async def test_arxiv_plugin():
    """Test ArXiv plugin returns results."""
    plugin = BuiltSimpleArxivPlugin()
    results = await plugin.search_arxiv("neural networks", limit=2)
    
    assert isinstance(results, str), "Should return formatted string"


async def test_wikipedia_plugin():
    """Test Wikipedia plugin returns results."""
    plugin = BuiltSimpleWikipediaPlugin()
    results = await plugin.search_wikipedia("artificial intelligence", limit=2)
    
    assert isinstance(results, str), "Should return formatted string"


def run_tests():
    """Run tests synchronously for manual testing."""
    print("Testing PubMed plugin...")
    result = asyncio.run(test_pubmed_plugin())
    print("✓ PubMed works")
    
    print("Testing ArXiv plugin...")
    result = asyncio.run(test_arxiv_plugin())
    print("✓ ArXiv works")
    
    print("Testing Wikipedia plugin...")
    result = asyncio.run(test_wikipedia_plugin())
    print("✓ Wikipedia works")
    
    print("\nAll tests passed! ✓")


if __name__ == "__main__":
    run_tests()
