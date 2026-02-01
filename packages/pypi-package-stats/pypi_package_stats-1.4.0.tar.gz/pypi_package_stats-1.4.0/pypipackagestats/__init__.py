"""PyPI Package Stats - Production-ready library for PyPI package statistics."""

from pypipackagestats.api import get_package_stats
from pypipackagestats.core.models import PackageStats
from pypipackagestats.core.exceptions import PyPIStatsError, PackageNotFoundError, APIError
from pypipackagestats.core.cache import clear_cache, get_cache_info

# Export main functionality
__all__ = [
    "get_package_stats",
    "clear_cache", 
    "get_cache_info",
    "PackageStats",
    "PyPIStatsError",
    "PackageNotFoundError", 
    "APIError",
]