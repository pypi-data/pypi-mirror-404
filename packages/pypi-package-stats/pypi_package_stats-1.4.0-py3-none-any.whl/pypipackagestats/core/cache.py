from pathlib import Path
from typing import Dict, Any, Optional
import platformdirs
import diskcache
import threading

_cache_instance: Optional[diskcache.Cache] = None
_cache_lock = threading.Lock()

def get_cache_dir() -> Path:
    """Get cache directory."""
    cache_dir = Path(platformdirs.user_cache_dir("pypipackagestats"))
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir

def get_cache() -> diskcache.Cache:
    """Get cache instance - thread-safe singleton with lazy initialization."""
    global _cache_instance
    if _cache_instance is None:
        with _cache_lock:
            if _cache_instance is None:
                cache_dir = get_cache_dir() / "api_cache"
                _cache_instance = diskcache.Cache(cache_dir)
    return _cache_instance

def clear_cache() -> None:
    """Clear all cached data."""
    get_cache().clear()

def get_cache_info() -> Dict[str, Any]:
    """Get cache information."""
    cache = get_cache()
    return {
        "size": len(cache),
        "cache_dir": str(get_cache_dir() / "api_cache"),
    }
