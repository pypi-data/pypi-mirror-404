"""
Post-related models.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Any
from pydantic import BaseModel, Field, validator


class PostSubmolt(BaseModel):
    """Submolt info embedded in a post."""
    id: str
    name: str
    display_name: str | None = None


class PostAuthor(BaseModel):
    """Author info embedded in a post."""
    id: str
    name: str


class Post(BaseModel):
    """A Moltbook post.
    
    Attributes:
        id: Unique post identifier.
        title: Post title.
        content: Post text content (for text posts).
        url: External URL (for link posts).
        submolt: Community info (object with id, name).
        author: Author info (object with id, name).
        upvotes: Number of upvotes.
        downvotes: Number of downvotes.
        comment_count: Number of comments.
        created_at: Post creation timestamp.
    """
    
    id: str
    title: str
    content: str | None = None
    url: str | None = None
    submolt: PostSubmolt
    author: PostAuthor
    upvotes: int = 0
    downvotes: int = 0
    comment_count: int = 0
    created_at: datetime
    
    @property
    def score(self) -> int:
        """Net score (upvotes - downvotes)."""
        return self.upvotes - self.downvotes
    
    @property
    def submolt_name(self) -> str:
        """Get submolt name as string."""
        return self.submolt.name
    
    @property
    def author_name(self) -> str:
        """Get author name as string."""
        return self.author.name


class CreatePostRequest(BaseModel):
    """Request to create a new post.
    
    Either content or url must be provided, but not both.
    """
    
    submolt: str = Field(..., description="Target submolt name")
    title: str = Field(..., min_length=1, max_length=300)
    content: str | None = Field(None, max_length=40000)
    url: str | None = Field(None)


class PostListParams(BaseModel):
    """Parameters for listing posts."""
    
    sort: Literal["hot", "new", "top", "rising"] = "hot"
    limit: int = Field(25, ge=1, le=100)
    offset: int = 0
    submolt: str | None = None
    time_range: Literal["hour", "day", "week", "month", "year", "all"] | None = None
