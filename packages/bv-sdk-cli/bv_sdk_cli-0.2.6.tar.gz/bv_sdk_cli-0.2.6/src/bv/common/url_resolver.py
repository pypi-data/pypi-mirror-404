"""URL resolution utilities for Bot Velocity platform.

This module provides a single source of truth for URL resolution across
all Bot Velocity components. The BaseUrlResolver normalizes frontend URLs
and derives API base URLs automatically.

Canonical rules:
- Frontend base URL: https://<host>
- Backend API base URL: https://<host>/api
- No component should hardcode ports or full API URLs
- /api suffix is automatically derived
"""

from __future__ import annotations


class BaseUrlResolver:
    """Resolves API base URL from frontend base URL.
    
    This utility ensures consistent URL handling across all Bot Velocity
    components. It accepts a frontend base URL, normalizes it, and
    derives the API base URL by appending /api.
    
    Usage:
        resolver = BaseUrlResolver("https://cloud.botvelocity.com")
        print(resolver.frontend_base)  # https://cloud.botvelocity.com
        print(resolver.api_base)       # https://cloud.botvelocity.com/api
        
        # Also handles URLs with trailing slashes or /api suffix
        resolver = BaseUrlResolver("https://example.com/api/")
        print(resolver.frontend_base)  # https://example.com
        print(resolver.api_base)       # https://example.com/api
    """
    
    def __init__(self, frontend_url: str) -> None:
        """Initialize the resolver with a frontend URL.
        
        Args:
            frontend_url: The frontend base URL. Can include trailing slashes
                         or /api suffix which will be normalized.
                         
        Raises:
            ValueError: If the URL is empty or invalid.
        """
        if not frontend_url or not frontend_url.strip():
            raise ValueError("Frontend URL cannot be empty")
        self._frontend_url = self._normalize(frontend_url)
    
    @staticmethod
    def _normalize(url: str) -> str:
        """Normalize URL: strip trailing slashes and /api suffix.
        
        Args:
            url: The URL to normalize.
            
        Returns:
            Normalized URL without trailing slashes or /api suffix.
        """
        url = url.strip().rstrip("/")
        # Remove /api suffix if present (case-insensitive check)
        if url.lower().endswith("/api"):
            url = url[:-4]
        return url.rstrip("/")
    
    @property
    def frontend_base(self) -> str:
        """Get normalized frontend base URL.
        
        Returns:
            The frontend base URL without trailing slashes or /api suffix.
        """
        return self._frontend_url
    
    @property
    def api_base(self) -> str:
        """Get API base URL (frontend + /api).
        
        Returns:
            The API base URL with /api suffix.
        """
        return f"{self._frontend_url}/api"
    
    def resolve_endpoint(self, path: str) -> str:
        """Resolve a full API endpoint URL.
        
        Args:
            path: The API path (with or without leading slash).
                  Should NOT include /api prefix.
                  
        Returns:
            Full URL for the API endpoint.
            
        Example:
            resolver.resolve_endpoint("runner/heartbeat")
            # Returns: https://cloud.botvelocity.com/api/runner/heartbeat
        """
        path = path.lstrip("/")
        return f"{self.api_base}/{path}"
    
    def __repr__(self) -> str:
        return f"BaseUrlResolver(frontend_base={self._frontend_url!r}, api_base={self.api_base!r})"
    
    def __str__(self) -> str:
        return self._frontend_url


def normalize_url(url: str) -> str:
    """Convenience function to normalize a URL.
    
    Strips trailing slashes and removes /api suffix if present.
    
    Args:
        url: The URL to normalize.
        
    Returns:
        Normalized URL.
    """
    return BaseUrlResolver._normalize(url)


def derive_api_url(frontend_url: str) -> str:
    """Convenience function to derive API URL from frontend URL.
    
    Args:
        frontend_url: The frontend base URL.
        
    Returns:
        API base URL with /api suffix.
    """
    return BaseUrlResolver(frontend_url).api_base
