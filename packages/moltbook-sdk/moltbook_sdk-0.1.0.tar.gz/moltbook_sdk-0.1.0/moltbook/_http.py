"""
Internal HTTP client wrapper for Moltbook SDK.

Handles authentication, rate limiting, retries, and error mapping.
"""

from __future__ import annotations

import time
from typing import Any, TypeVar

import httpx

from moltbook.config import MoltbookConfig
from moltbook.exceptions import (
    MoltbookError,
    AuthenticationError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
    RateLimitError,
    ConflictError,
    NetworkError,
    TimeoutError,
    ConfigurationError,
)
from moltbook.models.common import RateLimitInfo


T = TypeVar("T")


class HttpClient:
    """Internal HTTP client with authentication and retry logic.
    
    Not intended for direct use - use MoltbookClient instead.
    """
    
    def __init__(self, config: MoltbookConfig) -> None:
        self.config = config
        self._rate_limit_info: RateLimitInfo | None = None
        self._client: httpx.Client | None = None
    
    @property
    def client(self) -> httpx.Client:
        """Get or create httpx client."""
        if self._client is None:
            self._client = httpx.Client(
                base_url=self.config.base_url,
                timeout=self.config.timeout,
                headers=self._get_headers(),
            )
        return self._client
    
    def _get_headers(self) -> dict[str, str]:
        """Get request headers with authentication."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "moltbook-python-sdk/0.1.0",
        }
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        return headers
    
    def _parse_rate_limit_headers(self, response: httpx.Response) -> None:
        """Parse rate limit info from response headers."""
        try:
            limit = response.headers.get("X-RateLimit-Limit")
            remaining = response.headers.get("X-RateLimit-Remaining")
            reset = response.headers.get("X-RateLimit-Reset")
            
            if limit and remaining and reset:
                self._rate_limit_info = RateLimitInfo(
                    limit=int(limit),
                    remaining=int(remaining),
                    reset=int(reset),
                )
        except (ValueError, TypeError):
            pass  # Ignore parsing errors
    
    def _handle_error_response(self, response: httpx.Response) -> None:
        """Convert HTTP error response to appropriate exception."""
        try:
            data = response.json()
            message = data.get("error", response.reason_phrase)
            hint = data.get("hint")
        except Exception:
            message = response.reason_phrase or "Request failed"
            hint = None
        
        status = response.status_code
        
        if status == 400:
            raise ValidationError(message, hint=hint)
        elif status == 401:
            raise AuthenticationError(message, hint=hint)
        elif status == 403:
            raise ForbiddenError(message, hint=hint)
        elif status == 404:
            raise NotFoundError(message, hint=hint)
        elif status == 409:
            raise ConflictError(message, hint=hint)
        elif status == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            raise RateLimitError(message, retry_after=retry_after, hint=hint)
        elif status >= 500:
            raise MoltbookError(f"Server error: {message}", status_code=status, hint=hint)
        else:
            raise MoltbookError(message, status_code=status, hint=hint)
    
    def _request_with_retry(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make request with retry logic."""
        last_error: Exception | None = None
        
        for attempt in range(self.config.retries + 1):
            try:
                response = self.client.request(method, path, **kwargs)
                self._parse_rate_limit_headers(response)
                
                if response.is_success:
                    return response
                
                # Don't retry client errors except rate limits
                if 400 <= response.status_code < 500 and response.status_code != 429:
                    self._handle_error_response(response)
                
                # Retry on 429 and 5xx
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    if attempt < self.config.retries:
                        time.sleep(min(retry_after, 60))  # Cap at 60s
                        continue
                    self._handle_error_response(response)
                
                if response.status_code >= 500:
                    if attempt < self.config.retries:
                        delay = self.config.retry_delay * (2 ** attempt)
                        time.sleep(delay)
                        continue
                    self._handle_error_response(response)
                
                self._handle_error_response(response)
            
            except httpx.TimeoutException as e:
                last_error = e
                if attempt < self.config.retries:
                    delay = self.config.retry_delay * (2 ** attempt)
                    time.sleep(delay)
                    continue
                raise TimeoutError(str(e))
            
            except httpx.NetworkError as e:
                last_error = e
                if attempt < self.config.retries:
                    delay = self.config.retry_delay * (2 ** attempt)
                    time.sleep(delay)
                    continue
                raise NetworkError(str(e))
        
        if last_error:
            raise NetworkError(str(last_error))
        raise MoltbookError("Request failed after retries")
    
    def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make GET request."""
        response = self._request_with_retry("GET", path, params=params)
        return response.json()
    
    def post(self, path: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make POST request."""
        response = self._request_with_retry("POST", path, json=data)
        return response.json()
    
    def patch(self, path: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make PATCH request."""
        response = self._request_with_retry("PATCH", path, json=data)
        return response.json()
    
    def delete(self, path: str) -> dict[str, Any]:
        """Make DELETE request."""
        response = self._request_with_retry("DELETE", path)
        try:
            return response.json()
        except Exception:
            return {"success": True}
    
    def get_rate_limit_info(self) -> RateLimitInfo | None:
        """Get current rate limit info."""
        return self._rate_limit_info
    
    def is_rate_limited(self) -> bool:
        """Check if currently rate limited."""
        if self._rate_limit_info is None:
            return False
        return self._rate_limit_info.is_limited
    
    def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            self._client.close()
            self._client = None


class AsyncHttpClient:
    """Async version of HTTP client."""
    
    def __init__(self, config: MoltbookConfig) -> None:
        self.config = config
        self._rate_limit_info: RateLimitInfo | None = None
        self._client: httpx.AsyncClient | None = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async httpx client."""
        if self._client is None:
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "moltbook-python-sdk/0.1.0",
            }
            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"
            
            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                timeout=self.config.timeout,
                headers=headers,
            )
        return self._client
    
    def _parse_rate_limit_headers(self, response: httpx.Response) -> None:
        """Parse rate limit info from response headers."""
        try:
            limit = response.headers.get("X-RateLimit-Limit")
            remaining = response.headers.get("X-RateLimit-Remaining")
            reset = response.headers.get("X-RateLimit-Reset")
            
            if limit and remaining and reset:
                self._rate_limit_info = RateLimitInfo(
                    limit=int(limit),
                    remaining=int(remaining),
                    reset=int(reset),
                )
        except (ValueError, TypeError):
            pass
    
    def _handle_error_response(self, response: httpx.Response) -> None:
        """Convert HTTP error response to appropriate exception."""
        try:
            data = response.json()
            message = data.get("error", response.reason_phrase)
            hint = data.get("hint")
        except Exception:
            message = response.reason_phrase or "Request failed"
            hint = None
        
        status = response.status_code
        
        if status == 400:
            raise ValidationError(message, hint=hint)
        elif status == 401:
            raise AuthenticationError(message, hint=hint)
        elif status == 403:
            raise ForbiddenError(message, hint=hint)
        elif status == 404:
            raise NotFoundError(message, hint=hint)
        elif status == 409:
            raise ConflictError(message, hint=hint)
        elif status == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            raise RateLimitError(message, retry_after=retry_after, hint=hint)
        elif status >= 500:
            raise MoltbookError(f"Server error: {message}", status_code=status, hint=hint)
        else:
            raise MoltbookError(message, status_code=status, hint=hint)
    
    async def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make async GET request."""
        import asyncio
        
        client = await self._get_client()
        last_error: Exception | None = None
        
        for attempt in range(self.config.retries + 1):
            try:
                response = await client.get(path, params=params)
                self._parse_rate_limit_headers(response)
                
                if response.is_success:
                    return response.json()
                
                if 400 <= response.status_code < 500 and response.status_code != 429:
                    self._handle_error_response(response)
                
                if response.status_code in (429, 500, 502, 503, 504):
                    if attempt < self.config.retries:
                        delay = self.config.retry_delay * (2 ** attempt)
                        await asyncio.sleep(delay)
                        continue
                
                self._handle_error_response(response)
                
            except httpx.TimeoutException as e:
                last_error = e
                if attempt < self.config.retries:
                    await asyncio.sleep(self.config.retry_delay * (2 ** attempt))
                    continue
                raise TimeoutError(str(e))
            
            except httpx.NetworkError as e:
                last_error = e
                if attempt < self.config.retries:
                    await asyncio.sleep(self.config.retry_delay * (2 ** attempt))
                    continue
                raise NetworkError(str(e))
        
        if last_error:
            raise NetworkError(str(last_error))
        raise MoltbookError("Request failed")
    
    async def post(self, path: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make async POST request."""
        import asyncio
        
        client = await self._get_client()
        last_error: Exception | None = None
        
        for attempt in range(self.config.retries + 1):
            try:
                response = await client.post(path, json=data)
                self._parse_rate_limit_headers(response)
                
                if response.is_success:
                    return response.json()
                
                if 400 <= response.status_code < 500 and response.status_code != 429:
                    self._handle_error_response(response)
                
                if response.status_code in (429, 500, 502, 503, 504):
                    if attempt < self.config.retries:
                        await asyncio.sleep(self.config.retry_delay * (2 ** attempt))
                        continue
                
                self._handle_error_response(response)
                
            except (httpx.TimeoutException, httpx.NetworkError) as e:
                last_error = e
                if attempt < self.config.retries:
                    await asyncio.sleep(self.config.retry_delay * (2 ** attempt))
                    continue
        
        if last_error:
            raise NetworkError(str(last_error))
        raise MoltbookError("Request failed")
    
    async def patch(self, path: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make async PATCH request."""
        client = await self._get_client()
        response = await client.patch(path, json=data)
        self._parse_rate_limit_headers(response)
        if not response.is_success:
            self._handle_error_response(response)
        return response.json()
    
    async def delete(self, path: str) -> dict[str, Any]:
        """Make async DELETE request."""
        client = await self._get_client()
        response = await client.delete(path)
        self._parse_rate_limit_headers(response)
        if not response.is_success:
            self._handle_error_response(response)
        try:
            return response.json()
        except Exception:
            return {"success": True}
    
    def get_rate_limit_info(self) -> RateLimitInfo | None:
        """Get current rate limit info."""
        return self._rate_limit_info
    
    def is_rate_limited(self) -> bool:
        """Check if currently rate limited."""
        if self._rate_limit_info is None:
            return False
        return self._rate_limit_info.is_limited
    
    async def close(self) -> None:
        """Close the async HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
