"""Public API for PyPI Package Stats."""

import threading
from typing import Optional
from requests.exceptions import HTTPError, RequestException
from pypipackagestats.core.client import PyPIClient
from pypipackagestats.core.models import PackageStats
from pypipackagestats.core.processing import process_package_info, process_download_stats, process_category_breakdown
from pypipackagestats.core.exceptions import PackageNotFoundError, APIError, PyPIStatsError
from pypipackagestats.core.constants import TOP_PYTHON_VERSIONS_COUNT, TOP_OS_COUNT

# Thread-local storage for client reuse
_thread_local = threading.local()

def get_package_stats(
    package_name: str,
    *,
    no_cache: bool = False,
    cache_ttl: Optional[int] = None,
) -> PackageStats:
    """
    Get PyPI package statistics (thread-safe).
    
    Args:
        package_name: Package name
        no_cache: Whether to disable caching (default: False). 
                  If True, sets cache_ttl=0 to disable caching.
        cache_ttl: Time-to-live for cache entries in seconds.
                  - Positive integer → cache with that TTL (seconds)
                  - 0 → disable caching completely
                  - None or omitted → use default (3600 seconds)
        
    Returns:
        PackageStats: Package statistics
        
    Raises:
        PackageNotFoundError: If package not found
        APIError: If API/network error
        ValueError: If invalid package name
        
    Example:
        >>> stats = get_package_stats("requests")
        >>> print(f"Downloads: {stats.downloads.last_month:,}")
        
    Thread Safety:
        This function is fully thread-safe and can be used safely
        in concurrent environments like ThreadPoolExecutor.
    """
    if not package_name or not package_name.strip():
        raise ValueError("Package name cannot be empty")
    
    package_name = package_name.strip().lower()
    
    # Convert no_cache to cache_ttl=0 for backward compatibility
    if no_cache:
        effective_cache_ttl = 0
    else:
        effective_cache_ttl = cache_ttl
    
    # Thread-safe client reuse - each thread gets its own client
    # Client is reused only if cache settings match
    cache_key = f"{effective_cache_ttl}"
    
    if (not hasattr(_thread_local, 'client') or 
        not hasattr(_thread_local, 'cache_key') or
        _thread_local.cache_key != cache_key):
        
        _thread_local.client = PyPIClient(cache_ttl=effective_cache_ttl)
        _thread_local.cache_key = cache_key
    
    client = _thread_local.client
    
    try:
        # Fetch all data
        package_data = client.get_package_info(package_name)
        recent_stats = client.get_recent_stats(package_name)
        overall_stats = client.get_overall_stats(package_name)
        python_stats = client.get_python_stats(package_name)
        system_stats = client.get_system_stats(package_name)
        
        # Process data
        return PackageStats(
            package_info=process_package_info(package_data),
            downloads=process_download_stats(recent_stats, overall_stats),
            python_versions=process_category_breakdown(python_stats, TOP_PYTHON_VERSIONS_COUNT),
            operating_systems=process_category_breakdown(system_stats, TOP_OS_COUNT),
        )
        
    except HTTPError as e:
        if e.response and e.response.status_code == 404:
            raise PackageNotFoundError(package_name) from e
        elif e.response and e.response.status_code == 429:
            retry_after = e.response.headers.get('Retry-After', '60')
            raise APIError(f"Rate limit exceeded. Retry after {retry_after} seconds", 429) from e
        else:
            status_code = e.response.status_code if e.response else None
            raise APIError(f"HTTP {status_code}: {str(e)}", status_code) from e
    
    except RequestException as e:
        raise APIError(f"Network error for {package_name}: {str(e)}") from e
    
    except Exception as e:
        raise PyPIStatsError(f"Unexpected error: {str(e)}") from e
