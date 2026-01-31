"""
Agent Index Python SDK
The discovery layer for x402 AI agents

Usage:
    from agentindex import AgentIndex
    
    client = AgentIndex()
    results = client.search("crypto prices")
    
    for agent in results.results:
        print(f"{agent.description} - ${agent.price_usd}/call")
"""

from .client import AgentIndex, AsyncAgentIndex
from .models import Agent, SearchResult, TrendingResult, HealthResult, AnalyticsResult
from .exceptions import AgentIndexError

__version__ = "1.0.0"
__all__ = [
    "AgentIndex",
    "AsyncAgentIndex", 
    "Agent",
    "SearchResult",
    "TrendingResult",
    "HealthResult",
    "AnalyticsResult",
    "AgentIndexError",
]
