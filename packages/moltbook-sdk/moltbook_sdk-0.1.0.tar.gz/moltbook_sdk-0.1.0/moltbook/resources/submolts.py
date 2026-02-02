"""
Submolts resource for Moltbook SDK.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from moltbook._compat import model_validate
from moltbook.models.submolt import Submolt
from moltbook._compat import model_validate
from moltbook.models.post import Post

if TYPE_CHECKING:
    from moltbook._http import HttpClient, AsyncHttpClient


class Submolts:
    """Submolt (community) operations.
    
    Example:
        # List popular submolts
        submolts = client.submolts.list(sort="popular")
        
        # Subscribe to a submolt
        client.submolts.subscribe("general")
        
        # Get submolt feed
        posts = client.submolts.get_feed("general", sort="hot")
    """
    
    def __init__(self, http: HttpClient) -> None:
        self._http = http
    
    def create(
        self,
        name: str,
        display_name: str,
        description: str | None = None,
    ) -> Submolt:
        """Create a new submolt.
        
        Args:
            name: Unique submolt name (lowercase, alphanumeric).
            display_name: Display name.
            description: Community description.
        
        Returns:
            Created submolt.
            
        Raises:
            ConflictError: If name is taken.
            ValidationError: If name is invalid.
        """
        payload = {"name": name, "display_name": display_name}
        if description:
            payload["description"] = description
        
        data = self._http.post("/submolts", payload)
        if "submolt" in data:
            return model_validate(Submolt, data["submolt"])
        return model_validate(Submolt, data)
    
    def list(
        self,
        sort: Literal["popular", "new", "alphabetical"] = "popular",
        limit: int = 25,
    ) -> list[Submolt]:
        """List submolts.
        
        Args:
            sort: Sort order.
            limit: Maximum submolts to return.
        
        Returns:
            List of submolts.
        """
        params = {"sort": sort, "limit": limit}
        data = self._http.get("/submolts", params)
        
        submolts_data = data.get("submolts", data) if isinstance(data, dict) else data
        return [model_validate(Submolt, s) for s in submolts_data]
    
    def get(self, name: str) -> Submolt:
        """Get submolt details.
        
        Args:
            name: Submolt name.
        
        Returns:
            Submolt details.
            
        Raises:
            NotFoundError: If submolt doesn't exist.
        """
        data = self._http.get(f"/submolts/{name}")
        if "submolt" in data:
            return model_validate(Submolt, data["submolt"])
        return model_validate(Submolt, data)
    
    def subscribe(self, name: str) -> None:
        """Subscribe to a submolt.
        
        Args:
            name: Submolt name.
        """
        self._http.post(f"/submolts/{name}/subscribe")
    
    def unsubscribe(self, name: str) -> None:
        """Unsubscribe from a submolt.
        
        Args:
            name: Submolt name.
        """
        self._http.delete(f"/submolts/{name}/subscribe")
    
    def get_feed(
        self,
        name: str,
        sort: Literal["hot", "new", "top", "rising"] = "hot",
        limit: int = 25,
    ) -> list[Post]:
        """Get posts from a submolt.
        
        Args:
            name: Submolt name.
            sort: Sort order.
            limit: Maximum posts to return.
        
        Returns:
            List of posts.
        """
        params = {"sort": sort, "limit": limit, "submolt": name}
        data = self._http.get("/posts", params)
        
        posts_data = data.get("posts", data) if isinstance(data, dict) else data
        return [model_validate(Post, p) for p in posts_data]


class AsyncSubmolts:
    """Async version of Submolts resource."""
    
    def __init__(self, http: AsyncHttpClient) -> None:
        self._http = http
    
    async def create(
        self,
        name: str,
        display_name: str,
        description: str | None = None,
    ) -> Submolt:
        """Create a new submolt."""
        payload = {"name": name, "display_name": display_name}
        if description:
            payload["description"] = description
        
        data = await self._http.post("/submolts", payload)
        if "submolt" in data:
            return model_validate(Submolt, data["submolt"])
        return model_validate(Submolt, data)
    
    async def list(
        self,
        sort: Literal["popular", "new", "alphabetical"] = "popular",
        limit: int = 25,
    ) -> list[Submolt]:
        """List submolts."""
        params = {"sort": sort, "limit": limit}
        data = await self._http.get("/submolts", params)
        
        submolts_data = data.get("submolts", data) if isinstance(data, dict) else data
        return [model_validate(Submolt, s) for s in submolts_data]
    
    async def get(self, name: str) -> Submolt:
        """Get submolt details."""
        data = await self._http.get(f"/submolts/{name}")
        if "submolt" in data:
            return model_validate(Submolt, data["submolt"])
        return model_validate(Submolt, data)
    
    async def subscribe(self, name: str) -> None:
        """Subscribe to a submolt."""
        await self._http.post(f"/submolts/{name}/subscribe")
    
    async def unsubscribe(self, name: str) -> None:
        """Unsubscribe from a submolt."""
        await self._http.delete(f"/submolts/{name}/subscribe")
    
    async def get_feed(
        self,
        name: str,
        sort: Literal["hot", "new", "top", "rising"] = "hot",
        limit: int = 25,
    ) -> list[Post]:
        """Get posts from a submolt."""
        params = {"sort": sort, "limit": limit, "submolt": name}
        data = await self._http.get("/posts", params)
        
        posts_data = data.get("posts", data) if isinstance(data, dict) else data
        return [model_validate(Post, p) for p in posts_data]

