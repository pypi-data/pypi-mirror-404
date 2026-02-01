"""API clients for Built-Simple research APIs.

Low-level clients that fetch raw data from PubMed, ArXiv, and Wikipedia APIs.
"""

from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class APIConfig:
    """Configuration for Built-Simple API endpoints."""

    pubmed_url: str = "https://pubmed.built-simple.ai"
    arxiv_url: str = "https://arxiv.built-simple.ai"
    wikipedia_url: str = "https://wikipedia.built-simple.ai"
    timeout: float = 30.0


class BuiltSimpleAPI:
    """Low-level client for Built-Simple research APIs."""

    def __init__(self, config: APIConfig | None = None):
        """Initialize the API client.

        Args:
            config: Optional API configuration. Uses defaults if not provided.
        """
        self.config = config or APIConfig()
        self._client: httpx.Client | None = None

    @property
    def client(self) -> httpx.Client:
        """Lazy-initialize HTTP client."""
        if self._client is None:
            self._client = httpx.Client(timeout=self.config.timeout)
        return self._client

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            self._client.close()
            self._client = None

    def __enter__(self) -> "BuiltSimpleAPI":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def search_pubmed(
        self,
        query: str,
        limit: int = 10,
    ) -> dict[str, Any]:
        """Search PubMed for biomedical literature.

        Args:
            query: Search query string.
            limit: Maximum number of results (1-20).

        Returns:
            API response with query and results list.
        """
        limit = max(1, min(limit, 20))
        response = self.client.post(
            f"{self.config.pubmed_url}/hybrid-search",
            json={"query": query, "limit": limit},
        )
        response.raise_for_status()
        return response.json()

    def search_arxiv(
        self,
        query: str,
        limit: int = 10,
    ) -> dict[str, Any]:
        """Search ArXiv for preprints.

        Args:
            query: Search query string.
            limit: Maximum number of results (1-25).

        Returns:
            API response with query and results list.
        """
        limit = max(1, min(limit, 25))
        response = self.client.get(
            f"{self.config.arxiv_url}/api/search",
            params={"q": query, "limit": limit},
        )
        response.raise_for_status()
        return response.json()

    def search_wikipedia(
        self,
        query: str,
        limit: int = 10,
        category: str | None = None,
    ) -> dict[str, Any]:
        """Search Wikipedia for articles.

        Args:
            query: Search query string.
            limit: Maximum number of results (1-20).
            category: Optional category filter.

        Returns:
            API response with query and results list.
        """
        limit = max(1, min(limit, 20))
        payload: dict[str, Any] = {"query": query, "limit": limit}
        if category:
            payload["category"] = category

        response = self.client.post(
            f"{self.config.wikipedia_url}/api/search",
            json=payload,
        )
        response.raise_for_status()
        return response.json()

    def search_all(
        self,
        query: str,
        limit: int = 5,
        sources: list[str] | None = None,
    ) -> dict[str, dict[str, Any]]:
        """Search all sources and combine results.

        Args:
            query: Search query string.
            limit: Maximum results per source.
            sources: List of sources to search. Defaults to all.
                    Options: 'pubmed', 'arxiv', 'wikipedia'

        Returns:
            Dict mapping source name to API response.
        """
        sources = sources or ["pubmed", "arxiv", "wikipedia"]
        results: dict[str, dict[str, Any]] = {}

        if "pubmed" in sources:
            try:
                results["pubmed"] = self.search_pubmed(query, limit)
            except httpx.HTTPError as e:
                results["pubmed"] = {"error": str(e), "results": []}

        if "arxiv" in sources:
            try:
                results["arxiv"] = self.search_arxiv(query, limit)
            except httpx.HTTPError as e:
                results["arxiv"] = {"error": str(e), "results": []}

        if "wikipedia" in sources:
            try:
                results["wikipedia"] = self.search_wikipedia(query, limit)
            except httpx.HTTPError as e:
                results["wikipedia"] = {"error": str(e), "results": []}

        return results


class AsyncBuiltSimpleAPI:
    """Async client for Built-Simple research APIs."""

    def __init__(self, config: APIConfig | None = None):
        """Initialize the async API client."""
        self.config = config or APIConfig()
        self._client: httpx.AsyncClient | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Lazy-initialize async HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.config.timeout)
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> "AsyncBuiltSimpleAPI":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def search_pubmed(self, query: str, limit: int = 10) -> dict[str, Any]:
        """Async search PubMed."""
        limit = max(1, min(limit, 20))
        response = await self.client.post(
            f"{self.config.pubmed_url}/hybrid-search",
            json={"query": query, "limit": limit},
        )
        response.raise_for_status()
        return response.json()

    async def search_arxiv(self, query: str, limit: int = 10) -> dict[str, Any]:
        """Async search ArXiv."""
        limit = max(1, min(limit, 25))
        response = await self.client.get(
            f"{self.config.arxiv_url}/api/search",
            params={"q": query, "limit": limit},
        )
        response.raise_for_status()
        return response.json()

    async def search_wikipedia(
        self, query: str, limit: int = 10, category: str | None = None
    ) -> dict[str, Any]:
        """Async search Wikipedia."""
        limit = max(1, min(limit, 20))
        payload: dict[str, Any] = {"query": query, "limit": limit}
        if category:
            payload["category"] = category

        response = await self.client.post(
            f"{self.config.wikipedia_url}/api/search",
            json=payload,
        )
        response.raise_for_status()
        return response.json()

    async def search_all(
        self,
        query: str,
        limit: int = 5,
        sources: list[str] | None = None,
    ) -> dict[str, dict[str, Any]]:
        """Async search all sources."""
        import asyncio

        sources = sources or ["pubmed", "arxiv", "wikipedia"]
        results: dict[str, dict[str, Any]] = {}

        async def safe_search(name: str, coro: Any) -> tuple[str, dict[str, Any]]:
            try:
                return name, await coro
            except httpx.HTTPError as e:
                return name, {"error": str(e), "results": []}

        tasks = []
        if "pubmed" in sources:
            tasks.append(safe_search("pubmed", self.search_pubmed(query, limit)))
        if "arxiv" in sources:
            tasks.append(safe_search("arxiv", self.search_arxiv(query, limit)))
        if "wikipedia" in sources:
            tasks.append(safe_search("wikipedia", self.search_wikipedia(query, limit)))

        for name, result in await asyncio.gather(*tasks):
            results[name] = result

        return results
