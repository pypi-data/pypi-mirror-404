"""Agent Index SDK Client."""

from typing import Optional, Literal
import httpx

from .models import Agent, SearchResult, TrendingResult, HealthResult, AnalyticsResult
from .exceptions import AgentIndexError, TimeoutError, RateLimitError, NotFoundError


class AgentIndex:
    """
    Synchronous client for Agent Index API.
    
    The discovery layer for x402 AI agents.
    
    Example:
        >>> from agentindex import AgentIndex
        >>> 
        >>> client = AgentIndex()
        >>> 
        >>> # Search for crypto agents
        >>> results = client.search("crypto price")
        >>> for agent in results.results:
        ...     print(f"{agent.description} - ${agent.price_usd}/call")
        >>> 
        >>> # Get trending agents
        >>> trending = client.trending()
    """
    
    DEFAULT_BASE_URL = "https://api.theagentindex.app"
    DEFAULT_TIMEOUT = 10.0
    
    def __init__(
        self,
        base_url: str | None = None,
        timeout: float | None = None,
    ):
        """
        Initialize Agent Index client.
        
        Args:
            base_url: API base URL (default: https://api.theagentindex.app)
            timeout: Request timeout in seconds (default: 10.0)
        """
        self.base_url = base_url or self.DEFAULT_BASE_URL
        self.timeout = timeout or self.DEFAULT_TIMEOUT
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={
                "Accept": "application/json",
                "User-Agent": "agentindex-python/1.0.0",
            },
        )
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()
    
    def close(self):
        """Close the HTTP client."""
        self._client.close()
    
    def _request(self, method: str, path: str, params: dict | None = None) -> dict:
        """Make an HTTP request."""
        try:
            response = self._client.request(method, path, params=params)
            
            if response.status_code == 404:
                raise NotFoundError(f"Not found: {path}", status_code=404)
            elif response.status_code == 429:
                raise RateLimitError("Rate limit exceeded", status_code=429)
            elif response.status_code >= 400:
                raise AgentIndexError(
                    f"API error: {response.text}",
                    status_code=response.status_code,
                    response=response.text,
                )
            
            return response.json()
            
        except httpx.TimeoutException:
            raise TimeoutError("Request timed out")
        except httpx.RequestError as e:
            raise AgentIndexError(f"Request failed: {e}")
    
    def search(
        self,
        query: str,
        category: str | None = None,
        max_price: float | None = None,
        limit: int | None = None,
    ) -> SearchResult:
        """
        Search for x402 agents by keyword, category, or capability.
        
        Args:
            query: Search query (required)
            category: Filter by category (crypto, defi, ai, weather, news, oracle)
            max_price: Maximum price per call in USD
            limit: Number of results (default: 10, max: 50)
        
        Returns:
            SearchResult with matching agents
        
        Example:
            >>> results = client.search("weather forecast", category="weather")
            >>> print(f"Found {results.count} agents")
        """
        params = {"q": query}
        if category:
            params["category"] = category
        if max_price is not None:
            params["maxPrice"] = str(max_price)
        if limit is not None:
            params["limit"] = str(limit)
        
        data = self._request("GET", "/search", params=params)
        return SearchResult(**data)
    
    def trending(self) -> TrendingResult:
        """
        Get trending x402 agents based on usage.
        
        Returns:
            TrendingResult with trending agents
        
        Example:
            >>> trending = client.trending()
            >>> for agent in trending.trending[:5]:
            ...     print(agent.description)
        """
        data = self._request("GET", "/trending")
        return TrendingResult(**data)
    
    def health(self) -> HealthResult:
        """
        Check API health status.
        
        Returns:
            HealthResult with status information
        
        Example:
            >>> health = client.health()
            >>> print(f"Status: {health.status}")
        """
        data = self._request("GET", "/health")
        return HealthResult(**data)
    
    def recommend(
        self,
        use_case: str,
        max_price: float | None = None,
        limit: int | None = None,
    ) -> SearchResult:
        """
        Get AI-powered agent recommendations based on your use case.
        
        ⚡ Premium endpoint - requires x402 payment ($0.005/call)
        
        Args:
            use_case: Description of what you need
            max_price: Budget per call
            limit: Number of recommendations
        
        Returns:
            SearchResult with recommended agents
        
        Example:
            >>> recs = client.recommend(
            ...     use_case="I need real-time crypto prices for my trading bot",
            ...     max_price=0.02
            ... )
        """
        params = {"useCase": use_case}
        if max_price is not None:
            params["maxPrice"] = str(max_price)
        if limit is not None:
            params["limit"] = str(limit)
        
        data = self._request("GET", "/premium/recommend", params=params)
        return SearchResult(**data)
    
    def analytics(
        self,
        target: str | None = None,
        period: Literal["24h", "7d", "30d"] | None = None,
    ) -> AnalyticsResult:
        """
        Get detailed analytics on endpoint usage and trends.
        
        ⚡ Premium endpoint - requires x402 payment ($0.01/call)
        
        Args:
            target: Agent ID or category to analyze
            period: Time period (24h, 7d, 30d)
        
        Returns:
            AnalyticsResult with usage data
        
        Example:
            >>> analytics = client.analytics(target="crypto", period="7d")
            >>> print(f"Total calls: {analytics.total_calls}")
        """
        params = {}
        if target:
            params["target"] = target
        if period:
            params["period"] = period
        
        data = self._request("GET", "/premium/analytics", params=params)
        return AnalyticsResult(**data)
    
    def get(self, agent_id: str) -> Agent:
        """
        Get a specific agent by ID.
        
        Args:
            agent_id: Agent identifier
        
        Returns:
            Agent details
        
        Example:
            >>> agent = client.get("abc123")
            >>> print(agent.url)
        """
        data = self._request("GET", f"/agents/{agent_id}")
        return Agent(**data)


class AsyncAgentIndex:
    """
    Asynchronous client for Agent Index API.
    
    Example:
        >>> import asyncio
        >>> from agentindex import AsyncAgentIndex
        >>> 
        >>> async def main():
        ...     async with AsyncAgentIndex() as client:
        ...         results = await client.search("crypto price")
        ...         print(results.results)
        >>> 
        >>> asyncio.run(main())
    """
    
    DEFAULT_BASE_URL = "https://api.theagentindex.app"
    DEFAULT_TIMEOUT = 10.0
    
    def __init__(
        self,
        base_url: str | None = None,
        timeout: float | None = None,
    ):
        self.base_url = base_url or self.DEFAULT_BASE_URL
        self.timeout = timeout or self.DEFAULT_TIMEOUT
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={
                "Accept": "application/json",
                "User-Agent": "agentindex-python/1.0.0",
            },
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, *args):
        await self.close()
    
    async def close(self):
        await self._client.aclose()
    
    async def _request(self, method: str, path: str, params: dict | None = None) -> dict:
        try:
            response = await self._client.request(method, path, params=params)
            
            if response.status_code == 404:
                raise NotFoundError(f"Not found: {path}", status_code=404)
            elif response.status_code == 429:
                raise RateLimitError("Rate limit exceeded", status_code=429)
            elif response.status_code >= 400:
                raise AgentIndexError(
                    f"API error: {response.text}",
                    status_code=response.status_code,
                    response=response.text,
                )
            
            return response.json()
            
        except httpx.TimeoutException:
            raise TimeoutError("Request timed out")
        except httpx.RequestError as e:
            raise AgentIndexError(f"Request failed: {e}")
    
    async def search(
        self,
        query: str,
        category: str | None = None,
        max_price: float | None = None,
        limit: int | None = None,
    ) -> SearchResult:
        """Search for agents. See AgentIndex.search for details."""
        params = {"q": query}
        if category:
            params["category"] = category
        if max_price is not None:
            params["maxPrice"] = str(max_price)
        if limit is not None:
            params["limit"] = str(limit)
        
        data = await self._request("GET", "/search", params=params)
        return SearchResult(**data)
    
    async def trending(self) -> TrendingResult:
        """Get trending agents. See AgentIndex.trending for details."""
        data = await self._request("GET", "/trending")
        return TrendingResult(**data)
    
    async def health(self) -> HealthResult:
        """Check API health. See AgentIndex.health for details."""
        data = await self._request("GET", "/health")
        return HealthResult(**data)
    
    async def recommend(
        self,
        use_case: str,
        max_price: float | None = None,
        limit: int | None = None,
    ) -> SearchResult:
        """Get recommendations. See AgentIndex.recommend for details."""
        params = {"useCase": use_case}
        if max_price is not None:
            params["maxPrice"] = str(max_price)
        if limit is not None:
            params["limit"] = str(limit)
        
        data = await self._request("GET", "/premium/recommend", params=params)
        return SearchResult(**data)
    
    async def analytics(
        self,
        target: str | None = None,
        period: Literal["24h", "7d", "30d"] | None = None,
    ) -> AnalyticsResult:
        """Get analytics. See AgentIndex.analytics for details."""
        params = {}
        if target:
            params["target"] = target
        if period:
            params["period"] = period
        
        data = await self._request("GET", "/premium/analytics", params=params)
        return AnalyticsResult(**data)
    
    async def get(self, agent_id: str) -> Agent:
        """Get agent by ID. See AgentIndex.get for details."""
        data = await self._request("GET", f"/agents/{agent_id}")
        return Agent(**data)


# LangChain integration
def create_langchain_tool(client: AgentIndex | None = None):
    """
    Create a LangChain-compatible tool for agent discovery.
    
    Example:
        >>> from agentindex import create_langchain_tool
        >>> from langchain.agents import AgentExecutor
        >>> 
        >>> tool = create_langchain_tool()
        >>> # Add to your LangChain agent
    """
    from langchain.tools import StructuredTool
    from pydantic import BaseModel as LCBaseModel, Field as LCField
    
    class SearchInput(LCBaseModel):
        query: str = LCField(description="What capability are you looking for?")
        category: str | None = LCField(
            default=None,
            description="Filter by category: crypto, defi, ai, weather, news, oracle"
        )
        max_price: float | None = LCField(
            default=None, 
            description="Maximum price per call in USD"
        )
    
    index_client = client or AgentIndex()
    
    def search_agents(query: str, category: str | None = None, max_price: float | None = None) -> str:
        result = index_client.search(query, category=category, max_price=max_price)
        agents = result.results[:5]
        return "\n".join([
            f"- {a.description} ({a.url}) - ${a.price_usd}/call, Health: {a.health}"
            for a in agents
        ])
    
    return StructuredTool.from_function(
        func=search_agents,
        name="agent_index_search",
        description="Search for x402 AI agents that can perform specific tasks. Use this to find APIs and services your AI can pay for.",
        args_schema=SearchInput,
    )


# Convenience function
def search(query: str, **kwargs) -> list[Agent]:
    """
    Quick search for agents.
    
    Example:
        >>> from agentindex import search
        >>> agents = search("crypto prices", category="defi")
    """
    with AgentIndex() as client:
        result = client.search(query, **kwargs)
        return result.results
