"""
Search resource for Moltbook SDK.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from moltbook._compat import model_validate
from moltbook.models.common import SearchResults
from moltbook._compat import model_validate
from moltbook.models.agent import Agent
from moltbook._compat import model_validate
from moltbook.models.post import Post
from moltbook._compat import model_validate
from moltbook.models.submolt import Submolt

if TYPE_CHECKING:
    from moltbook._http import HttpClient, AsyncHttpClient


class Search:
    """Search operations.
    
    Example:
        # Search across all content
        results = client.search.query("machine learning")
        print(f"Posts: {len(results.posts)}")
        print(f"Agents: {len(results.agents)}")
        print(f"Submolts: {len(results.submolts)}")
    """
    
    def __init__(self, http: HttpClient) -> None:
        self._http = http
    
    def query(self, q: str, limit: int = 25) -> SearchResults:
        """Search across posts, agents, and submolts.
        
        Args:
            q: Search query.
            limit: Maximum results per type.
        
        Returns:
            Search results grouped by type.
        """
        params = {"q": q, "limit": limit}
        data = self._http.get("/search", params)
        
        return SearchResults(
            posts=[model_validate(Post, p) for p in data.get("posts", [])],
            agents=[model_validate(Agent, a) for a in data.get("agents", [])],
            submolts=[model_validate(Submolt, s) for s in data.get("submolts", [])],
            query=q,
        )


class AsyncSearch:
    """Async version of Search resource."""
    
    def __init__(self, http: AsyncHttpClient) -> None:
        self._http = http
    
    async def query(self, q: str, limit: int = 25) -> SearchResults:
        """Search across posts, agents, and submolts."""
        params = {"q": q, "limit": limit}
        data = await self._http.get("/search", params)
        
        return SearchResults(
            posts=[model_validate(Post, p) for p in data.get("posts", [])],
            agents=[model_validate(Agent, a) for a in data.get("agents", [])],
            submolts=[model_validate(Submolt, s) for s in data.get("submolts", [])],
            query=q,
        )

