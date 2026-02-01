"""Semantic Kernel plugins for Built-Simple research APIs.

This module provides plugin classes that can be registered with a Semantic Kernel
instance to enable AI agents to search scientific literature.

Example:
    >>> from semantic_kernel import Kernel
    >>> from semantic_kernel_builtsimple import BuiltSimplePubMedPlugin
    >>>
    >>> kernel = Kernel()
    >>> kernel.add_plugin(BuiltSimplePubMedPlugin(), plugin_name="pubmed")
"""

from typing import Annotated, Optional
import logging

from semantic_kernel.functions.kernel_function_decorator import kernel_function

from semantic_kernel_builtsimple.client import (
    BuiltSimpleClient,
    BuiltSimpleAPIError,
    clean_text,
    format_authors,
)

logger = logging.getLogger(__name__)


class BuiltSimplePubMedPlugin:
    """Semantic Kernel plugin for searching PubMed via Built-Simple API.
    
    This plugin provides access to 4.5M+ peer-reviewed biomedical and life
    sciences articles from PubMed through semantic and hybrid search.
    
    Features:
        - Hybrid search combining semantic and keyword matching
        - Full article text available (not just abstracts)
        - Rich metadata including journal, DOI, authors
    
    Example:
        >>> kernel = Kernel()
        >>> kernel.add_plugin(BuiltSimplePubMedPlugin(), plugin_name="pubmed")
    """

    BASE_URL = "https://pubmed.built-simple.ai"

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
    ):
        """Initialize the PubMed plugin.
        
        Args:
            base_url: Override the default API URL
            api_key: Optional API key for higher rate limits
            timeout: Request timeout in seconds (default: 30)
        """
        self._base_url = base_url or self.BASE_URL
        self._api_key = api_key
        self._timeout = timeout

    def _get_client(self) -> BuiltSimpleClient:
        """Create a new client instance."""
        return BuiltSimpleClient(
            base_url=self._base_url,
            api_key=self._api_key,
            timeout=self._timeout,
        )

    @kernel_function(
        name="search_pubmed",
        description=(
            "Search PubMed for peer-reviewed biomedical and life sciences literature. "
            "Use for medical, biological, pharmaceutical, and healthcare research. "
            "Returns paper titles, abstracts, journals, and publication years. "
            "Best for: clinical studies, drug research, genomics, disease mechanisms, "
            "medical treatments, and biological sciences."
        ),
    )
    async def search_pubmed(
        self,
        query: Annotated[str, "Search query describing the research topic"],
        limit: Annotated[int, "Maximum number of results to return (1-20)"] = 5,
    ) -> Annotated[str, "Formatted search results with paper details"]:
        """Search PubMed and return formatted results.
        
        Args:
            query: Natural language search query
            limit: Maximum results (1-20)
            
        Returns:
            Formatted string with paper titles, abstracts, and metadata
        """
        limit = max(1, min(limit, 20))  # Clamp between 1-20
        
        async with self._get_client() as client:
            try:
                data = await client.post(
                    "/hybrid-search",
                    data={"query": query, "limit": limit},
                )
            except BuiltSimpleAPIError as e:
                return f"Error searching PubMed: {e.message}"

        results = data.get("results", [])
        if not results:
            return f"No PubMed results found for: {query}"

        output_parts = [f"Found {len(results)} PubMed results for '{query}':\n"]

        for i, result in enumerate(results, 1):
            parts = [f"\n--- Result {i} ---"]
            
            title = clean_text(result.get("title"))
            if title:
                parts.append(f"Title: {title}")
            
            journal = result.get("journal")
            if journal:
                parts.append(f"Journal: {journal}")
            
            pub_year = result.get("pub_year") or result.get("year")
            if pub_year:
                parts.append(f"Year: {pub_year}")
            
            pmid = result.get("pmid")
            if pmid:
                parts.append(f"PMID: {pmid}")
                parts.append(f"URL: https://pubmed.ncbi.nlm.nih.gov/{pmid}/")
            
            doi = result.get("doi")
            if doi:
                parts.append(f"DOI: {doi}")
            
            authors = format_authors(result.get("authors"))
            if authors:
                # Truncate long author lists
                if len(authors) > 200:
                    authors = authors[:200] + "..."
                parts.append(f"Authors: {authors}")
            
            abstract = clean_text(result.get("abstract"))
            if abstract:
                if len(abstract) > 500:
                    abstract = abstract[:500] + "..."
                parts.append(f"Abstract: {abstract}")

            output_parts.append("\n".join(parts))

        return "\n".join(output_parts)

    @kernel_function(
        name="get_pubmed_full_text",
        description=(
            "Get the full article text for a specific PubMed article by PMID. "
            "Use this when you need the complete article content, not just the abstract."
        ),
    )
    async def get_full_text(
        self,
        pmid: Annotated[str, "PubMed ID (e.g., '31041627' or 'PMC9953887')"],
    ) -> Annotated[str, "Full article text or error message"]:
        """Retrieve full text for a specific article.
        
        Args:
            pmid: PubMed ID
            
        Returns:
            Full article text or error message
        """
        async with self._get_client() as client:
            try:
                data = await client.get(f"/article/{pmid}/full_text")
            except BuiltSimpleAPIError as e:
                return f"Error fetching full text for PMID {pmid}: {e.message}"

        if not data.get("has_full_text") and not data.get("full_text"):
            return f"Full text not available for PMID {pmid}"

        title = clean_text(data.get("title", ""))
        full_text = clean_text(data.get("full_text", ""))
        
        output_parts = []
        if title:
            output_parts.append(f"Title: {title}")
        output_parts.append(f"\nFull Text ({len(full_text)} characters):\n")
        output_parts.append(full_text)
        
        return "\n".join(output_parts)


class BuiltSimpleArxivPlugin:
    """Semantic Kernel plugin for searching ArXiv via Built-Simple API.
    
    This plugin provides access to 2.7M+ preprints in physics, mathematics,
    computer science, and machine learning from ArXiv.
    
    Features:
        - Semantic search over preprint database
        - Access to cutting-edge research before peer review
        - Categories in physics, math, CS, ML, statistics, and more
    
    Example:
        >>> kernel = Kernel()
        >>> kernel.add_plugin(BuiltSimpleArxivPlugin(), plugin_name="arxiv")
    """

    BASE_URL = "https://arxiv.built-simple.ai"

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
    ):
        """Initialize the ArXiv plugin.
        
        Args:
            base_url: Override the default API URL
            api_key: Optional API key for higher rate limits
            timeout: Request timeout in seconds (default: 30)
        """
        self._base_url = base_url or self.BASE_URL
        self._api_key = api_key
        self._timeout = timeout

    def _get_client(self) -> BuiltSimpleClient:
        """Create a new client instance."""
        return BuiltSimpleClient(
            base_url=self._base_url,
            api_key=self._api_key,
            timeout=self._timeout,
        )

    @kernel_function(
        name="search_arxiv",
        description=(
            "Search ArXiv for preprints in physics, mathematics, computer science, "
            "statistics, electrical engineering, machine learning, and AI. "
            "Returns paper titles, authors, abstracts, and ArXiv IDs. "
            "Best for: cutting-edge AI/ML research, theoretical physics, pure math, "
            "algorithms, neural networks, and emerging research before peer review."
        ),
    )
    async def search_arxiv(
        self,
        query: Annotated[str, "Search query describing the research topic"],
        limit: Annotated[int, "Maximum number of results to return (1-20)"] = 5,
    ) -> Annotated[str, "Formatted search results with paper details"]:
        """Search ArXiv and return formatted results.
        
        Args:
            query: Natural language search query
            limit: Maximum results (1-20)
            
        Returns:
            Formatted string with paper titles, abstracts, and metadata
        """
        limit = max(1, min(limit, 20))  # Clamp between 1-20

        async with self._get_client() as client:
            try:
                data = await client.get(
                    "/api/search",
                    params={"q": query, "limit": limit},
                )
            except BuiltSimpleAPIError as e:
                return f"Error searching ArXiv: {e.message}"

        results = data.get("results", [])
        if not results:
            return f"No ArXiv results found for: {query}"

        output_parts = [f"Found {len(results)} ArXiv results for '{query}':\n"]

        for i, result in enumerate(results, 1):
            parts = [f"\n--- Result {i} ---"]
            
            title = clean_text(result.get("title"))
            if title:
                parts.append(f"Title: {title}")
            
            authors = result.get("authors")
            if authors:
                if isinstance(authors, list):
                    author_str = ", ".join(authors[:5])
                    if len(authors) > 5:
                        author_str += f" (+{len(authors) - 5} more)"
                else:
                    author_str = str(authors)
                parts.append(f"Authors: {author_str}")
            
            year = result.get("year")
            if year:
                parts.append(f"Year: {year}")
            
            arxiv_id = result.get("arxiv_id")
            if arxiv_id:
                parts.append(f"ArXiv ID: {arxiv_id}")
                parts.append(f"URL: https://arxiv.org/abs/{arxiv_id}")
                parts.append(f"PDF: https://arxiv.org/pdf/{arxiv_id}.pdf")
            
            categories = result.get("categories")
            if categories:
                if isinstance(categories, list):
                    categories = ", ".join(categories)
                parts.append(f"Categories: {categories}")
            
            abstract = clean_text(result.get("abstract"))
            if abstract:
                if len(abstract) > 500:
                    abstract = abstract[:500] + "..."
                parts.append(f"Abstract: {abstract}")

            output_parts.append("\n".join(parts))

        return "\n".join(output_parts)


class BuiltSimpleWikipediaPlugin:
    """Semantic Kernel plugin for searching Wikipedia via Built-Simple API.
    
    This plugin provides semantic search over Wikipedia articles,
    useful for general knowledge queries and factual information.
    
    Features:
        - Semantic vector search over Wikipedia
        - Rich article content with metadata
        - Fast response times
    
    Example:
        >>> kernel = Kernel()
        >>> kernel.add_plugin(BuiltSimpleWikipediaPlugin(), plugin_name="wikipedia")
    """

    BASE_URL = "https://wikipedia.built-simple.ai"

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
    ):
        """Initialize the Wikipedia plugin.
        
        Args:
            base_url: Override the default API URL
            api_key: Optional API key for higher rate limits
            timeout: Request timeout in seconds (default: 30)
        """
        self._base_url = base_url or self.BASE_URL
        self._api_key = api_key
        self._timeout = timeout

    def _get_client(self) -> BuiltSimpleClient:
        """Create a new client instance."""
        return BuiltSimpleClient(
            base_url=self._base_url,
            api_key=self._api_key,
            timeout=self._timeout,
        )

    @kernel_function(
        name="search_wikipedia",
        description=(
            "Search Wikipedia for general knowledge and factual information. "
            "Returns article titles and content summaries. "
            "Best for: definitions, historical facts, biographical info, "
            "scientific concepts, places, events, and general reference."
        ),
    )
    async def search_wikipedia(
        self,
        query: Annotated[str, "Search query describing what you want to learn about"],
        limit: Annotated[int, "Maximum number of results to return (1-20)"] = 5,
    ) -> Annotated[str, "Formatted search results with article content"]:
        """Search Wikipedia and return formatted results.
        
        Args:
            query: Natural language search query
            limit: Maximum results (1-20)
            
        Returns:
            Formatted string with article titles and content
        """
        limit = max(1, min(limit, 20))  # Clamp between 1-20

        async with self._get_client() as client:
            try:
                # Try POST endpoint first
                data = await client.post(
                    "/hybrid-search",
                    data={"query": query, "limit": limit},
                )
            except BuiltSimpleAPIError:
                try:
                    # Fallback to GET endpoint
                    data = await client.get(
                        "/api/search",
                        params={"q": query, "limit": limit},
                    )
                except BuiltSimpleAPIError as e:
                    return f"Error searching Wikipedia: {e.message}"

        results = data.get("results", [])
        if not results:
            return f"No Wikipedia results found for: {query}"

        output_parts = [f"Found {len(results)} Wikipedia results for '{query}':\n"]

        for i, result in enumerate(results, 1):
            parts = [f"\n--- Result {i} ---"]
            
            title = clean_text(result.get("title"))
            if title:
                parts.append(f"Title: {title}")
                url = result.get("url") or f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
                parts.append(f"URL: {url}")
            
            # Handle various content field names
            content = clean_text(
                result.get("content") or
                result.get("text") or
                result.get("extract") or
                result.get("summary", "")
            )
            if content:
                if len(content) > 800:
                    content = content[:800] + "..."
                parts.append(f"Content: {content}")
            
            categories = result.get("categories")
            if categories:
                if isinstance(categories, list):
                    categories = ", ".join(categories[:5])
                parts.append(f"Categories: {categories}")

            output_parts.append("\n".join(parts))

        return "\n".join(output_parts)


class BuiltSimpleResearchPlugin:
    """Combined Semantic Kernel plugin for all Built-Simple research APIs.
    
    This plugin provides unified access to PubMed, ArXiv, and Wikipedia
    through a single plugin instance. Useful when you want comprehensive
    research coverage with one plugin registration.
    
    Example:
        >>> kernel = Kernel()
        >>> kernel.add_plugin(BuiltSimpleResearchPlugin(), plugin_name="research")
    """

    def __init__(
        self,
        pubmed_url: Optional[str] = None,
        arxiv_url: Optional[str] = None,
        wikipedia_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
    ):
        """Initialize the combined research plugin.
        
        Args:
            pubmed_url: Override PubMed API URL
            arxiv_url: Override ArXiv API URL
            wikipedia_url: Override Wikipedia API URL
            api_key: Optional API key for higher rate limits
            timeout: Request timeout in seconds (default: 30)
        """
        self._pubmed = BuiltSimplePubMedPlugin(
            base_url=pubmed_url,
            api_key=api_key,
            timeout=timeout,
        )
        self._arxiv = BuiltSimpleArxivPlugin(
            base_url=arxiv_url,
            api_key=api_key,
            timeout=timeout,
        )
        self._wikipedia = BuiltSimpleWikipediaPlugin(
            base_url=wikipedia_url,
            api_key=api_key,
            timeout=timeout,
        )

    @kernel_function(
        name="search_pubmed",
        description=(
            "Search PubMed for peer-reviewed biomedical and life sciences literature. "
            "Best for: medical research, clinical studies, drug research, genomics."
        ),
    )
    async def search_pubmed(
        self,
        query: Annotated[str, "Search query for biomedical literature"],
        limit: Annotated[int, "Maximum results (1-20)"] = 5,
    ) -> Annotated[str, "Formatted PubMed search results"]:
        """Search PubMed."""
        return await self._pubmed.search_pubmed(query, limit)

    @kernel_function(
        name="search_arxiv",
        description=(
            "Search ArXiv for preprints in physics, math, CS, ML, and AI. "
            "Best for: cutting-edge research, AI/ML papers, theoretical work."
        ),
    )
    async def search_arxiv(
        self,
        query: Annotated[str, "Search query for preprints"],
        limit: Annotated[int, "Maximum results (1-20)"] = 5,
    ) -> Annotated[str, "Formatted ArXiv search results"]:
        """Search ArXiv."""
        return await self._arxiv.search_arxiv(query, limit)

    @kernel_function(
        name="search_wikipedia",
        description=(
            "Search Wikipedia for general knowledge and factual information. "
            "Best for: definitions, history, biographies, concepts."
        ),
    )
    async def search_wikipedia(
        self,
        query: Annotated[str, "Search query for general knowledge"],
        limit: Annotated[int, "Maximum results (1-20)"] = 5,
    ) -> Annotated[str, "Formatted Wikipedia search results"]:
        """Search Wikipedia."""
        return await self._wikipedia.search_wikipedia(query, limit)

    @kernel_function(
        name="search_all_sources",
        description=(
            "Search PubMed, ArXiv, and Wikipedia simultaneously for comprehensive "
            "research coverage. Use for interdisciplinary topics or when you need "
            "both peer-reviewed papers and general knowledge."
        ),
    )
    async def search_all_sources(
        self,
        query: Annotated[str, "Search query to run across all sources"],
        limit_per_source: Annotated[int, "Maximum results per source (1-10)"] = 3,
    ) -> Annotated[str, "Combined results from all sources"]:
        """Search all sources simultaneously.
        
        Args:
            query: Search query
            limit_per_source: Max results per source (1-10)
            
        Returns:
            Combined formatted results from PubMed, ArXiv, and Wikipedia
        """
        limit = max(1, min(limit_per_source, 10))
        
        # Run searches (could be parallelized with asyncio.gather in future)
        pubmed_results = await self._pubmed.search_pubmed(query, limit)
        arxiv_results = await self._arxiv.search_arxiv(query, limit)
        wiki_results = await self._wikipedia.search_wikipedia(query, limit)
        
        return (
            f"=== PubMed (Biomedical) ===\n{pubmed_results}\n\n"
            f"=== ArXiv (Preprints) ===\n{arxiv_results}\n\n"
            f"=== Wikipedia (General) ===\n{wiki_results}"
        )
