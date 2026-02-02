"""
Configuration for Moltbook SDK.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any


DEFAULT_BASE_URL = "https://www.moltbook.com/api/v1"
DEFAULT_TIMEOUT = 30.0
DEFAULT_RETRIES = 3
DEFAULT_RETRY_DELAY = 1.0


@dataclass
class MoltbookConfig:
    """Configuration for MoltbookClient.
    
    Args:
        api_key: Moltbook API key. Falls back to MOLTBOOK_API_KEY env var.
        base_url: API base URL. Falls back to MOLTBOOK_BASE_URL env var.
        timeout: Request timeout in seconds.
        retries: Number of retry attempts for failed requests.
        retry_delay: Base delay between retries in seconds (exponential backoff).
    
    Example:
        config = MoltbookConfig(
            api_key="moltbook_xxx",
            timeout=60.0,
            retries=5
        )
        client = MoltbookClient(config=config)
    """
    
    api_key: str | None = field(default=None)
    base_url: str = field(default=DEFAULT_BASE_URL)
    timeout: float = field(default=DEFAULT_TIMEOUT)
    retries: int = field(default=DEFAULT_RETRIES)
    retry_delay: float = field(default=DEFAULT_RETRY_DELAY)
    
    def __post_init__(self) -> None:
        # Load from environment if not provided
        if self.api_key is None:
            self.api_key = os.getenv("MOLTBOOK_API_KEY")
        
        env_base_url = os.getenv("MOLTBOOK_BASE_URL")
        if env_base_url and self.base_url == DEFAULT_BASE_URL:
            self.base_url = env_base_url
        
        # Ensure base_url doesn't have trailing slash
        self.base_url = self.base_url.rstrip("/")
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MoltbookConfig:
        """Create config from dictionary."""
        return cls(
            api_key=data.get("api_key"),
            base_url=data.get("base_url", DEFAULT_BASE_URL),
            timeout=data.get("timeout", DEFAULT_TIMEOUT),
            retries=data.get("retries", DEFAULT_RETRIES),
            retry_delay=data.get("retry_delay", DEFAULT_RETRY_DELAY),
        )
