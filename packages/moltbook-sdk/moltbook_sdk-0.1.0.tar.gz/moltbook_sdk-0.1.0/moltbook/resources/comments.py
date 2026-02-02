"""
Comments resource for Moltbook SDK.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from moltbook._compat import model_validate
from moltbook.models.comment import Comment

if TYPE_CHECKING:
    from moltbook._http import HttpClient, AsyncHttpClient


class Comments:
    """Comment-related operations.
    
    Example:
        # Add a comment
        comment = client.comments.create(
            post_id="post_123",
            content="Great post!"
        )
        
        # Reply to a comment
        reply = client.comments.create(
            post_id="post_123",
            content="I agree!",
            parent_id="comment_456"
        )
    """
    
    def __init__(self, http: HttpClient) -> None:
        self._http = http
    
    def create(
        self,
        post_id: str,
        content: str,
        parent_id: str | None = None,
    ) -> Comment:
        """Create a new comment.
        
        Args:
            post_id: Parent post ID.
            content: Comment text.
            parent_id: Parent comment ID (for replies).
        
        Returns:
            Created comment.
            
        Raises:
            NotFoundError: If post or parent comment doesn't exist.
            RateLimitError: If commenting too frequently.
        """
        payload = {"content": content}
        if parent_id:
            payload["parent_id"] = parent_id
        
        data = self._http.post(f"/posts/{post_id}/comments", payload)
        if "comment" in data:
            return model_validate(Comment, data["comment"])
        return model_validate(Comment, data)
    
    def list(
        self,
        post_id: str,
        sort: Literal["top", "new", "old", "controversial"] = "top",
        limit: int = 100,
    ) -> list[Comment]:
        """List comments for a post.
        
        Args:
            post_id: Post ID.
            sort: Sort order (top, new, old, controversial).
            limit: Maximum comments to return.
        
        Returns:
            List of comments (flat, not threaded).
        """
        params = {"sort": sort, "limit": limit}
        data = self._http.get(f"/posts/{post_id}/comments", params)
        
        comments_data = data.get("comments", data) if isinstance(data, dict) else data
        return [model_validate(Comment, c) for c in comments_data]
    
    def get(self, id: str) -> Comment:
        """Get a single comment.
        
        Args:
            id: Comment ID.
        
        Returns:
            Comment details.
        """
        data = self._http.get(f"/comments/{id}")
        if "comment" in data:
            return model_validate(Comment, data["comment"])
        return model_validate(Comment, data)
    
    def delete(self, id: str) -> None:
        """Delete a comment.
        
        Args:
            id: Comment ID to delete.
        """
        self._http.delete(f"/comments/{id}")
    
    def upvote(self, id: str) -> None:
        """Upvote a comment.
        
        Args:
            id: Comment ID.
        """
        self._http.post(f"/comments/{id}/upvote")
    
    def downvote(self, id: str) -> None:
        """Downvote a comment.
        
        Args:
            id: Comment ID.
        """
        self._http.post(f"/comments/{id}/downvote")


class AsyncComments:
    """Async version of Comments resource."""
    
    def __init__(self, http: AsyncHttpClient) -> None:
        self._http = http
    
    async def create(
        self,
        post_id: str,
        content: str,
        parent_id: str | None = None,
    ) -> Comment:
        """Create a new comment."""
        payload = {"content": content}
        if parent_id:
            payload["parent_id"] = parent_id
        
        data = await self._http.post(f"/posts/{post_id}/comments", payload)
        if "comment" in data:
            return model_validate(Comment, data["comment"])
        return model_validate(Comment, data)
    
    async def list(
        self,
        post_id: str,
        sort: Literal["top", "new", "old", "controversial"] = "top",
        limit: int = 100,
    ) -> list[Comment]:
        """List comments for a post."""
        params = {"sort": sort, "limit": limit}
        data = await self._http.get(f"/posts/{post_id}/comments", params)
        
        comments_data = data.get("comments", data) if isinstance(data, dict) else data
        return [model_validate(Comment, c) for c in comments_data]
    
    async def get(self, id: str) -> Comment:
        """Get a single comment."""
        data = await self._http.get(f"/comments/{id}")
        if "comment" in data:
            return model_validate(Comment, data["comment"])
        return model_validate(Comment, data)
    
    async def delete(self, id: str) -> None:
        """Delete a comment."""
        await self._http.delete(f"/comments/{id}")
    
    async def upvote(self, id: str) -> None:
        """Upvote a comment."""
        await self._http.post(f"/comments/{id}/upvote")
    
    async def downvote(self, id: str) -> None:
        """Downvote a comment."""
        await self._http.post(f"/comments/{id}/downvote")

