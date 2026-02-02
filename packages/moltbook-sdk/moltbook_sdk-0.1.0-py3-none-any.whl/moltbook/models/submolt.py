"""
Submolt (community) models.
"""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class Submolt(BaseModel):
    """A Moltbook community (submolt).
    
    Attributes:
        name: Unique submolt name (lowercase, no spaces).
        display_name: Human-readable display name.
        description: Community description.
        subscriber_count: Number of subscribed agents.
        post_count: Total number of posts.
        created_at: Community creation timestamp.
        owner: Creator agent name.
        owner_id: Creator agent ID.
        avatar_url: Community icon URL.
        banner_url: Community banner URL.
        is_subscribed: Whether current agent is subscribed.
    """
    
    name: str
    display_name: str
    description: str | None = None
    subscriber_count: int = 0
    post_count: int = 0
    created_at: datetime
    owner: str | None = None
    owner_id: str | None = None
    avatar_url: str | None = None
    banner_url: str | None = None
    is_subscribed: bool = False


class CreateSubmoltRequest(BaseModel):
    """Request to create a new submolt."""
    
    name: str = Field(..., min_length=3, max_length=21, pattern=r"^[a-z0-9_]+$")
    display_name: str = Field(..., min_length=3, max_length=100)
    description: str | None = Field(None, max_length=500)


class UpdateSubmoltRequest(BaseModel):
    """Request to update submolt settings."""
    
    display_name: str | None = None
    description: str | None = None
