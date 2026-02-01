import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import threading
from typing import Dict, Any, Optional
from nestedutils import get_at
from pypipackagestats.core.cache import get_cache
from pypipackagestats.core.constants import (
    DEFAULT_CACHE_TTL,
    PYPI_API,
    STATS_API,
    REQUEST_RETRY_MAX_TRIES,
    REQUEST_RETRY_BACKOFF_FACTOR,
    REQUEST_RETRY_STATUS_FORCELIST,
    REQUEST_RETRY_ALLOWED_METHODS,
    REQUEST_TIMEOUT,
)

class PyPIClient:
    """Thread-safe PyPI API client."""
    
    def __init__(self, cache_ttl: Optional[int] = DEFAULT_CACHE_TTL):
        """
        Initialize PyPI client with persistent disk cache.
        
        Args:
            cache_ttl: Time-to-live for cache entries in seconds.
                      - Positive integer → cache with that TTL (seconds)
                      - 0 → disable caching completely
                      - None or omitted → use default (3600 seconds)
        """
        self.cache_ttl = (cache_ttl or DEFAULT_CACHE_TTL) if cache_ttl != 0 else 0
        self.use_cache = cache_ttl != 0
        self._local = threading.local()
    
    def _get_session(self) -> requests.Session:
        """Get thread-local session."""
        if not hasattr(self._local, 'session'):
            session = requests.Session()
            retry = Retry(
                total=REQUEST_RETRY_MAX_TRIES,  # Total retries (covers connection and read errors)
                status_forcelist=REQUEST_RETRY_STATUS_FORCELIST,
                backoff_factor=REQUEST_RETRY_BACKOFF_FACTOR,
                respect_retry_after_header=True,
                allowed_methods=REQUEST_RETRY_ALLOWED_METHODS,  # Only retry GET requests
            )
            adapter = HTTPAdapter(max_retries=retry)
            session.mount("https://", adapter)
            session.mount("http://", adapter)
            self._local.session = session
        return self._local.session
    
    def __del__(self) -> None:
        """Cleanup on object destruction."""
        if hasattr(self, '_local') and hasattr(self._local, 'session'):
            try:
                self._local.session.close()
            except Exception:
                pass  # Ignore errors during cleanup
    
    def _cached_get(self, url: str) -> Dict[str, Any]:
        """Get URL with caching - let diskcache handle thread safety."""
        if not self.use_cache:
            response = self._get_session().get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.json()
        
        cache = get_cache()
        cache_key = f"url:{url}"
        
        # diskcache handles thread safety internally
        cached_data = cache.get(cache_key, default=None)
        if cached_data is not None:
            return cached_data
        
        # Fetch from API
        response = self._get_session().get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        
        # Store in cache - diskcache handles locking
        if 200 <= response.status_code < 300:
            cache.set(cache_key, data, expire=self.cache_ttl)
        
        return data
    
    def get_package_info(self, package: str) -> dict:
        """Fetch package metadata from PyPI"""
        url = PYPI_API.format(pkg=package.lower())
        return self._cached_get(url)
    
    def get_recent_stats(self, package: str) -> dict:
        """Get recent download stats"""
        url = STATS_API.format(pkg=package.lower()) + "recent"
        return get_at(self._cached_get(url), "data", default={})
    
    def get_overall_stats(self, package: str) -> list:
        """Get overall stats (180 days)"""
        url = STATS_API.format(pkg=package.lower()) + "overall?mirrors=false"
        return get_at(self._cached_get(url), "data", default=[])
    
    def get_python_stats(self, package: str) -> list:
        """Get Python version breakdown"""
        url = STATS_API.format(pkg=package.lower()) + "python_minor"
        return get_at(self._cached_get(url), "data", default=[])
    
    def get_system_stats(self, package: str) -> list:
        """Get OS breakdown"""
        url = STATS_API.format(pkg=package.lower()) + "system"
        return get_at(self._cached_get(url), "data", default=[])

