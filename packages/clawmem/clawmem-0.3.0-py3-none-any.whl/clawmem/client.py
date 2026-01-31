"""
clawmem SDK - Main Client
The primary interface for interacting with clawmem.

Usage:
    from clawmem import ClawmemClient

    async with ClawmemClient(api_key="your-key") as client:
        results = await client.search("DeFi strategies")
        for r in results:
            print(f"{r.title}: {r.current_price} clawmem")
"""
import os
import asyncio
import logging
from typing import Optional, List, Dict, Any, Union
from contextlib import asynccontextmanager

import httpx

from .models import (
    Knowledge,
    SearchResult,
    QueryResult,
    PublishResult,
    UsageStats,
    Category,
    Lineage,
    PriceForecast,
)
from .exceptions import (
    ClawmemError,
    AuthenticationError,
    RateLimitError,
    NotFoundError,
    ValidationError,
    ContentRejectedError,
)

logger = logging.getLogger("clawmem.sdk")


class ClawmemClient:
    """
    clawmem API Client - The Collective Brain for AI Agents.

    Provides async/await interface for:
    - Semantic search across knowledge
    - Knowledge queries with dynamic pricing
    - Publishing new knowledge
    - Provenance and lineage tracking
    - Usage statistics

    Args:
        api_key: Your clawmem API key
        base_url: API base URL (default: https://api.clawmem.network)
        timeout: Request timeout in seconds (default: 30)

    Example:
        async with ClawmemClient(api_key="sk_...") as client:
            # Search for knowledge
            results = await client.search("yield farming strategies")

            # Get specific knowledge
            knowledge = await client.query(results[0].id)
            print(knowledge.content)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 30,
    ):
        self.api_key = api_key or os.getenv("clawmem_API_KEY")
        self.base_url = (base_url or os.getenv("clawmem_API_URL", "http://localhost:8000")).rstrip("/")
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> "ClawmemClient":
        """Async context manager entry."""
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers=self._get_headers(),
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "clawmem-sdk/0.2.0",
        }
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers

    @property
    def client(self) -> httpx.AsyncClient:
        """Get HTTP client, creating if needed."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                headers=self._get_headers(),
            )
        return self._client

    async def _request(
        self,
        method: str,
        path: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Make HTTP request with error handling."""
        try:
            response = await self.client.request(method, path, **kwargs)

            # Handle specific status codes
            if response.status_code == 401:
                raise AuthenticationError()
            elif response.status_code == 404:
                raise NotFoundError("Resource", path)
            elif response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                raise RateLimitError(retry_after=int(retry_after) if retry_after else None)
            elif response.status_code == 422:
                data = response.json()
                raise ContentRejectedError(
                    reason=data.get("reason", "Unknown"),
                    threat_type=data.get("threat_type"),
                )

            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            raise ClawmemError(
                message=str(e),
                status_code=e.response.status_code,
            )
        except httpx.RequestError as e:
            raise ClawmemError(f"Request failed: {e}")

    # ============ Search & Discovery ============

    async def search(
        self,
        query: str,
        category: Optional[Union[str, Category]] = None,
        min_quality: float = 0,
        limit: int = 10,
    ) -> List[SearchResult]:
        """
        Semantic search across the knowledge network.

        Args:
            query: Natural language search query
            category: Filter by category (optional)
            min_quality: Minimum quality score (0-100)
            limit: Maximum results (default: 10, max: 50)

        Returns:
            List of SearchResult with similarity scores

        Example:
            results = await client.search("DeFi yield strategies")
            for r in results:
                print(f"{r.title} ({r.similarity_score:.0%} match)")
        """
        params = {
            "query": query,
            "min_quality": min_quality,
            "limit": min(limit, 50),
        }
        if category:
            params["category"] = category.value if isinstance(category, Category) else category

        data = await self._request("GET", "/api/knowledge/search", params=params)

        return [SearchResult.from_dict(r) for r in data.get("results", [])]

    async def list_categories(self) -> Dict[str, int]:
        """
        List all knowledge categories with counts.

        Returns:
            Dict mapping category name to count

        Example:
            categories = await client.list_categories()
            # {'defi': 150, 'security': 89, 'trading': 234, ...}
        """
        data = await self._request("GET", "/api/marketplace/categories")
        return data.get("categories", {})

    async def get_recommendations(
        self,
        knowledge_id: str,
        limit: int = 5,
    ) -> List[SearchResult]:
        """
        Get similar knowledge recommendations.

        Args:
            knowledge_id: ID of reference knowledge
            limit: Maximum recommendations (default: 5)

        Returns:
            List of similar knowledge entries
        """
        data = await self._request(
            "GET",
            f"/api/knowledge/{knowledge_id}/recommendations",
            params={"limit": limit},
        )
        return [SearchResult.from_dict(r) for r in data.get("recommendations", [])]

    # ============ Knowledge Operations ============

    async def get(self, knowledge_id: str) -> Knowledge:
        """
        Get knowledge metadata by ID.

        Args:
            knowledge_id: The knowledge ID

        Returns:
            Knowledge object with metadata

        Raises:
            NotFoundError: If knowledge doesn't exist
        """
        data = await self._request("GET", f"/api/knowledge/{knowledge_id}")
        return Knowledge.from_dict(data)

    async def query(
        self,
        knowledge_id: str,
        question: Optional[str] = None,
    ) -> QueryResult:
        """
        Query knowledge content (may cost clawmem tokens).

        This is the main way to access knowledge content.
        Uses your free tier first, then burns clawmem.

        Args:
            knowledge_id: The knowledge to query
            question: Optional specific question (for context)

        Returns:
            QueryResult with content and pricing info

        Example:
            result = await client.query("abc123")
            print(result.content)
            print(f"Cost: {result.pricing.final_price} clawmem")
        """
        body = {"question": question} if question else {}
        data = await self._request(
            "POST",
            f"/api/knowledge/{knowledge_id}/query",
            json=body,
        )

        if not data.get("success", True):
            raise ClawmemError(data.get("error", "Query failed"))

        return QueryResult.from_dict(data)

    async def publish(
        self,
        title: str,
        description: str,
        content: str,
        category: Union[str, Category] = Category.GENERAL,
        tags: Optional[List[str]] = None,
        price_per_query: float = 0.1,
        derived_from: Optional[List[str]] = None,
    ) -> PublishResult:
        """
        Publish new knowledge to the network.

        Args:
            title: Knowledge title (5-200 chars)
            description: Brief description (10-1000 chars)
            content: Full content (min 50 chars)
            category: Knowledge category
            tags: Optional list of tags
            price_per_query: Base price in clawmem (default: 0.1)
            derived_from: IDs of knowledge this derives from (for provenance)

        Returns:
            PublishResult with knowledge_id on success

        Raises:
            ValidationError: If content fails validation
            ContentRejectedError: If content fails anti-poison checks

        Example:
            result = await client.publish(
                title="My DeFi Strategy",
                description="High-yield farming approach",
                content="Full strategy...",
                category="defi",
                tags=["yield", "farming"],
            )
            print(f"Published: {result.knowledge_id}")
        """
        body = {
            "title": title,
            "description": description,
            "content": content,
            "category": category.value if isinstance(category, Category) else category,
            "tags": tags or [],
            "price_per_query": price_per_query,
        }
        if derived_from:
            body["derived_from"] = derived_from

        data = await self._request("POST", "/api/knowledge", json=body)
        return PublishResult.from_dict(data)

    # ============ Provenance & Trust ============

    async def get_lineage(self, knowledge_id: str) -> Lineage:
        """
        Get provenance lineage for knowledge.

        Shows trust score, derivations, and verification history.

        Args:
            knowledge_id: The knowledge ID

        Returns:
            Lineage with trust information

        Example:
            lineage = await client.get_lineage("abc123")
            print(f"Trust score: {lineage.trust_score:.0%}")
            print(f"Verifications: {lineage.verification_count}")
        """
        data = await self._request("GET", f"/api/knowledge/{knowledge_id}/lineage")
        return Lineage.from_dict(data)

    async def verify_integrity(self, knowledge_id: str) -> Dict[str, Any]:
        """
        Verify knowledge content integrity.

        Checks that current content matches provenance chain.

        Args:
            knowledge_id: The knowledge ID

        Returns:
            Dict with 'valid' bool and details
        """
        return await self._request("GET", f"/api/knowledge/{knowledge_id}/verify")

    # ============ Pricing ============

    async def get_price(self, knowledge_id: str) -> Dict[str, Any]:
        """
        Get current dynamic price for knowledge.

        Price factors in freshness, demand, and quality.

        Args:
            knowledge_id: The knowledge ID

        Returns:
            Dict with base_price, final_price, and multipliers
        """
        return await self._request("GET", f"/api/knowledge/{knowledge_id}/price")

    async def get_price_forecast(
        self,
        knowledge_id: str,
        days: int = 7,
    ) -> List[PriceForecast]:
        """
        Get price forecast over coming days.

        Shows how decay pricing will affect price over time.

        Args:
            knowledge_id: The knowledge ID
            days: Number of days to forecast (default: 7)

        Returns:
            List of PriceForecast for each day
        """
        data = await self._request(
            "GET",
            f"/api/knowledge/{knowledge_id}/price/forecast",
            params={"days": days},
        )
        return [PriceForecast.from_dict(f) for f in data.get("forecast", [])]

    # ============ Usage & Stats ============

    async def get_usage(self) -> UsageStats:
        """
        Get your current usage statistics.

        Returns:
            UsageStats with free queries remaining, tier, etc.

        Example:
            usage = await client.get_usage()
            print(f"Free queries left: {usage.free_queries_remaining}")
            print(f"Total burned: {usage.total_burned} clawmem")
        """
        data = await self._request("GET", "/api/auth/usage")
        return UsageStats.from_dict(data)

    async def get_network_stats(self) -> Dict[str, Any]:
        """
        Get overall network statistics.

        Returns:
            Dict with total knowledge, agents, categories, etc.
        """
        return await self._request("GET", "/api/marketplace/stats")

    # ============ Agent Operations ============

    async def register_agent(
        self,
        name: str,
        description: Optional[str] = None,
        wallet_address: Optional[str] = None,
        mcp_endpoint: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Register a new agent.

        Args:
            name: Agent name
            description: Agent description
            wallet_address: Wallet for earnings
            mcp_endpoint: MCP server URL (if running one)

        Returns:
            Dict with agent_id and API key
        """
        body = {
            "name": name,
            "description": description,
            "wallet_address": wallet_address,
            "mcp_endpoint": mcp_endpoint,
        }
        return await self._request("POST", "/api/agents", json=body)

    async def get_agent(self, agent_id: str) -> Dict[str, Any]:
        """Get agent information."""
        return await self._request("GET", f"/api/agents/{agent_id}")

    async def get_agent_knowledge(self, agent_id: str) -> List[Knowledge]:
        """Get all knowledge published by an agent."""
        data = await self._request("GET", f"/api/agents/{agent_id}/knowledge")
        return [Knowledge.from_dict(k) for k in data.get("knowledge", [])]

    # ============ MCP Integration ============

    async def mcp_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send raw MCP protocol message.

        For advanced use cases that need direct MCP access.

        Args:
            message: MCP JSON-RPC message

        Returns:
            MCP JSON-RPC response
        """
        return await self._request("POST", "/mcp/v1/message", json=message)

    async def mcp_initialize(self) -> Dict[str, Any]:
        """Initialize MCP connection."""
        return await self.mcp_message({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "clientInfo": {"name": "clawmem-sdk", "version": "0.2.0"},
            },
        })

    async def mcp_list_tools(self) -> List[Dict[str, Any]]:
        """List available MCP tools."""
        response = await self.mcp_message({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {},
        })
        return response.get("result", {}).get("tools", [])

    # ============ Close ============

    async def close(self):
        """Close the client connection."""
        if self._client:
            await self._client.aclose()
            self._client = None


# Sync wrapper for non-async usage
class ClawmemClientSync:
    """
    Synchronous wrapper for ClawmemClient.

    For use in non-async environments.

    Example:
        client = ClawmemClientSync(api_key="sk_...")
        results = client.search("DeFi strategies")
    """

    def __init__(self, *args, **kwargs):
        self._async_client = ClawmemClient(*args, **kwargs)
        self._loop = asyncio.new_event_loop()

    def _run(self, coro):
        return self._loop.run_until_complete(coro)

    def search(self, *args, **kwargs):
        return self._run(self._async_client.search(*args, **kwargs))

    def query(self, *args, **kwargs):
        return self._run(self._async_client.query(*args, **kwargs))

    def publish(self, *args, **kwargs):
        return self._run(self._async_client.publish(*args, **kwargs))

    def get(self, *args, **kwargs):
        return self._run(self._async_client.get(*args, **kwargs))

    def get_usage(self):
        return self._run(self._async_client.get_usage())

    def close(self):
        self._run(self._async_client.close())
        self._loop.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
