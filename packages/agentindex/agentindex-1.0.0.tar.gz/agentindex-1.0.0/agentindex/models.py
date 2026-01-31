"""Data models for Agent Index SDK."""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


class Agent(BaseModel):
    """Represents an x402 agent/endpoint."""
    
    id: str = Field(description="Unique identifier")
    url: str = Field(description="Endpoint URL")
    domain: str = Field(description="Domain name")
    description: str = Field(description="Description of capabilities")
    price_usd: float = Field(alias="priceUsd", description="Price per call in USD")
    category: str = Field(description="Category")
    health: Literal["healthy", "degraded", "down", "unknown"] = Field(
        description="Health status"
    )
    tier: Literal["A", "B", "C", "D"] = Field(description="Quality tier")
    score: int = Field(description="Trust score (0-100)")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional metadata")
    
    class Config:
        populate_by_name = True


class SearchResult(BaseModel):
    """Search results from Agent Index."""
    
    count: int = Field(description="Total matching agents")
    results: List[Agent] = Field(description="Matching agents")
    took: Optional[int] = Field(default=None, description="Search duration in ms")


class TrendingResult(BaseModel):
    """Trending agents result."""
    
    trending: List[Agent] = Field(description="Trending agents")
    period: str = Field(description="Time period")


class HealthResult(BaseModel):
    """API health check result."""
    
    status: Literal["ok", "degraded", "down"] = Field(description="Service status")
    timestamp: str = Field(description="Check timestamp")
    version: Optional[str] = Field(default=None, description="API version")


class TopEndpoint(BaseModel):
    """Top endpoint in analytics."""
    
    url: str
    calls: int


class AnalyticsResult(BaseModel):
    """Analytics data result."""
    
    total_calls: int = Field(alias="totalCalls")
    unique_callers: int = Field(alias="uniqueCallers")
    revenue: float
    top_endpoints: List[TopEndpoint] = Field(alias="topEndpoints")
    period: str
    
    class Config:
        populate_by_name = True
