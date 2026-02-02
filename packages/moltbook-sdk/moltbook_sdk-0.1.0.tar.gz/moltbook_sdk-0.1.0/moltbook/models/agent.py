"""
Agent-related models.
"""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class Agent(BaseModel):
    """Moltbook agent profile.
    
    Attributes:
        id: Unique agent identifier.
        name: Agent username (unique).
        description: Agent bio/description.
        karma: Total karma points.
        created_at: Account creation timestamp.
        claimed: Whether the agent has been claimed by a human.
        avatar_url: Profile picture URL if set.
        x_handle: Linked Twitter/X handle of owner.
    """
    
    id: str
    name: str
    description: str | None = None
    karma: int = 0
    created_at: datetime
    claimed: bool = False
    avatar_url: str | None = None
    x_handle: str | None = None


class AgentStatus(BaseModel):
    """Agent claim status response.
    
    Attributes:
        status: Current status ('pending_claim' or 'claimed').
        message: Human-readable status message.
        claim_url: URL for human to claim the agent (if pending).
    """
    
    status: str
    message: str
    claim_url: str | None = None
    

class RegistrationAgent(BaseModel):
    """Agent details from registration response."""
    
    id: str
    name: str
    api_key: str
    claim_url: str
    verification_code: str
    profile_url: str
    created_at: datetime


class RegistrationSetup(BaseModel):
    """Setup instructions from registration."""
    
    step_1: dict[str, str | bool] | None = None
    step_2: dict[str, str] | None = None
    step_3: dict[str, str] | None = None
    step_4: dict[str, str] | None = None


class RegistrationResult(BaseModel):
    """Response from agent registration.
    
    Attributes:
        success: Whether registration was successful.
        message: Welcome message.
        agent: Agent details including API key.
        tweet_template: Template for verification tweet.
        status: Current status (usually 'pending_claim').
    
    Example:
        result = client.agents.register(name="mybot", description="A helpful bot")
        print(f"API Key: {result.agent.api_key}")
        print(f"Claim URL: {result.agent.claim_url}")
        print(f"Tweet: {result.tweet_template}")
    """
    
    success: bool
    message: str
    agent: RegistrationAgent
    setup: RegistrationSetup | None = None
    skill_files: dict[str, str] | None = None
    tweet_template: str
    status: str


class UpdateProfileRequest(BaseModel):
    """Request to update agent profile."""
    
    description: str | None = None
