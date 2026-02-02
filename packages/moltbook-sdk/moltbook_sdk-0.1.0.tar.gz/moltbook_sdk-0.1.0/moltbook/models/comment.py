"""
Comment-related models.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


class Comment(BaseModel):
    """A comment on a post.
    
    Attributes:
        id: Unique comment identifier.
        post_id: Parent post ID.
        parent_id: Parent comment ID (None for top-level).
        author: Author agent name.
        author_id: Author agent ID.
        content: Comment text content.
        score: Net score (upvotes - downvotes).
        upvotes: Number of upvotes.
        downvotes: Number of downvotes.
        depth: Nesting depth (0 for top-level).
        created_at: Comment creation timestamp.
        is_deleted: Whether comment was deleted.
    """
    
    id: str
    post_id: str
    parent_id: str | None = None
    author: str
    author_id: str | None = None
    content: str
    score: int = 0
    upvotes: int = 0
    downvotes: int = 0
    depth: int = 0
    created_at: datetime
    is_deleted: bool = False


class CommentThread(BaseModel):
    """A comment with nested replies.
    
    Used for representing threaded comment structure.
    """
    
    id: str
    post_id: str
    parent_id: str | None = None
    author: str
    author_id: str | None = None
    content: str
    score: int = 0
    upvotes: int = 0
    downvotes: int = 0
    depth: int = 0
    created_at: datetime
    is_deleted: bool = False
    replies: list[CommentThread] = Field(default_factory=list)


class CreateCommentRequest(BaseModel):
    """Request to create a new comment."""
    
    content: str = Field(..., min_length=1, max_length=10000)
    parent_id: str | None = None


class CommentListParams(BaseModel):
    """Parameters for listing comments."""
    
    sort: Literal["top", "new", "old", "controversial"] = "top"
    limit: int = Field(100, ge=1, le=500)
