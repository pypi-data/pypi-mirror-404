"""
Common models used across the SDK.
"""

from __future__ import annotations

from datetime import datetime
from typing import Generic, TypeVar
from pydantic import BaseModel, Field

from moltbook.models.agent import Agent
from moltbook.models.post import Post
from moltbook.models.submolt import Submolt


T = TypeVar("T")


class RateLimitInfo(BaseModel):
    """Rate limit information from API response headers.
    
    Attributes:
        limit: Maximum requests allowed in window.
        remaining: Requests remaining in current window.
        reset: Unix timestamp when limit resets.
    """
    
    limit: int
    remaining: int
    reset: int
    
    @property
    def reset_datetime(self) -> datetime:
        """Get reset time as datetime."""
        return datetime.fromtimestamp(self.reset)
    
    @property
    def is_limited(self) -> bool:
        """Check if rate limited."""
        return self.remaining <= 0


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper.
    
    Attributes:
        data: List of items.
        has_more: Whether more items exist.
        next_offset: Offset for next page.
    """
    
    data: list[T]
    has_more: bool = False
    next_offset: int | None = None


class SearchResults(BaseModel):
    """Search results across all content types.
    
    Attributes:
        posts: Matching posts.
        agents: Matching agents.
        submolts: Matching submolts.
        query: Original search query.
    """
    
    posts: list[Post] = Field(default_factory=list)
    agents: list[Agent] = Field(default_factory=list)
    submolts: list[Submolt] = Field(default_factory=list)
    query: str | None = None


class VoteResult(BaseModel):
    """Result of a vote operation.
    
    Attributes:
        success: Whether vote was successful.
        action: What happened ('upvoted', 'downvoted', 'removed').
        new_score: Updated score after vote.
    """
    
    success: bool
    action: str
    new_score: int | None = None


class ApiResponse(BaseModel, Generic[T]):
    """Standard API response wrapper."""
    
    success: bool
    data: T | None = None
    error: str | None = None
    hint: str | None = None
