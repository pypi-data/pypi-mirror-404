"""HTTP client for Built-Simple research APIs.

Provides async HTTP client with retry logic and error handling.
"""

from typing import Any, Dict, List, Optional
import logging

import httpx

logger = logging.getLogger(__name__)


class BuiltSimpleAPIError(Exception):
    """Exception raised when Built-Simple API returns an error."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class BuiltSimpleClient:
    """Async HTTP client for Built-Simple research APIs.
    
    Provides connection pooling, automatic retries, and consistent
    error handling for all Built-Simple API endpoints.
    
    Attributes:
        base_url: Base URL for the API
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
    """

    DEFAULT_TIMEOUT = 30.0
    MAX_RETRIES = 3

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        """Initialize the client.
        
        Args:
            base_url: Base URL for the API (without trailing slash)
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds (default: 30)
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    def _get_headers(self) -> Dict[str, str]:
        """Get default headers for requests."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "semantic-kernel-builtsimple/0.1.0",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the async HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                headers=self._get_headers(),
            )
        return self._client

    async def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """Handle API response and extract JSON data.
        
        Args:
            response: The httpx Response object
            
        Returns:
            Parsed JSON response as a dictionary
            
        Raises:
            BuiltSimpleAPIError: If the API returns an error
        """
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            error_msg = f"API request failed: {e}"
            try:
                error_data = response.json()
                if "error" in error_data:
                    error_msg = f"API error: {error_data['error']}"
                elif "message" in error_data:
                    error_msg = f"API error: {error_data['message']}"
            except (ValueError, KeyError):
                pass
            raise BuiltSimpleAPIError(error_msg, response.status_code) from e
        
        try:
            return response.json()
        except ValueError as e:
            raise BuiltSimpleAPIError(
                f"Invalid JSON response: {response.text[:200]}"
            ) from e

    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make an async GET request to the API.
        
        Args:
            endpoint: API endpoint (will be appended to base_url)
            params: Optional query parameters
            
        Returns:
            Parsed JSON response
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        logger.debug(f"GET {url} params={params}")
        
        client = await self._get_client()
        
        last_error = None
        for attempt in range(self.MAX_RETRIES):
            try:
                response = await client.get(url, params=params)
                return await self._handle_response(response)
            except httpx.RequestError as e:
                last_error = e
                logger.warning(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt < self.MAX_RETRIES - 1:
                    continue
        
        raise BuiltSimpleAPIError(f"Request failed after {self.MAX_RETRIES} attempts: {last_error}")

    async def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make an async POST request to the API.
        
        Args:
            endpoint: API endpoint (will be appended to base_url)
            data: JSON body data
            params: Optional query parameters
            
        Returns:
            Parsed JSON response
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        logger.debug(f"POST {url} data={data}")
        
        client = await self._get_client()
        
        last_error = None
        for attempt in range(self.MAX_RETRIES):
            try:
                response = await client.post(url, json=data, params=params)
                return await self._handle_response(response)
            except httpx.RequestError as e:
                last_error = e
                logger.warning(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt < self.MAX_RETRIES - 1:
                    continue
        
        raise BuiltSimpleAPIError(f"Request failed after {self.MAX_RETRIES} attempts: {last_error}")

    async def close(self) -> None:
        """Close the HTTP client and release resources."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> "BuiltSimpleClient":
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()


def clean_text(text: Optional[str]) -> str:
    """Clean and normalize text content.
    
    Args:
        text: Raw text that may contain extra whitespace or be None
        
    Returns:
        Cleaned text string (empty string if input is None)
    """
    if text is None:
        return ""
    # Normalize whitespace while preserving paragraph structure
    lines = text.strip().split("\n")
    cleaned_lines = [" ".join(line.split()) for line in lines]
    return "\n".join(cleaned_lines)


def format_authors(authors: Any) -> str:
    """Format authors list into a readable string.
    
    Args:
        authors: Authors data (can be list, string, or None)
        
    Returns:
        Formatted author string
    """
    if authors is None:
        return ""
    if isinstance(authors, str):
        return authors
    if isinstance(authors, list):
        author_names = []
        for author in authors:
            if isinstance(author, dict):
                name = author.get("name") or author.get("full_name") or str(author)
                author_names.append(name)
            else:
                author_names.append(str(author))
        return ", ".join(author_names)
    return str(authors)
