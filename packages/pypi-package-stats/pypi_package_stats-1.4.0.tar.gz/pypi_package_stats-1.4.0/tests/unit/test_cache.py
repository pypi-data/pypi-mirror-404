"""Tests for cache functionality."""
import threading
import pytest
from pathlib import Path
from pypipackagestats.core.cache import (
    get_cache_dir,
    get_cache,
    clear_cache,
    get_cache_info,
)


class TestCacheDirectory:
    """Test cache directory functions."""
    
    def test_get_cache_dir_returns_correct_path(self):
        """Test get_cache_dir returns correct path."""
        cache_dir = get_cache_dir()
        assert isinstance(cache_dir, Path)
        assert "pypipackagestats" in str(cache_dir)
    
    def test_cache_directory_creation(self):
        """Test cache directory creation."""
        cache_dir = get_cache_dir()
        assert cache_dir.exists()
        assert cache_dir.is_dir()
    
    def test_cache_directory_exists_check(self):
        """Test cache directory exists check."""
        cache_dir = get_cache_dir()
        # Should exist after calling get_cache_dir
        assert cache_dir.exists()


class TestCacheInstance:
    """Test cache instance functions."""
    
    def test_get_cache_returns_singleton_instance(self):
        """Test get_cache returns singleton instance."""
        cache1 = get_cache()
        cache2 = get_cache()
        assert cache1 is cache2
    
    def test_thread_safe_singleton_initialization(self):
        """Test thread-safe singleton initialization."""
        caches = []
        
        def get_cache_instance():
            caches.append(get_cache())
        
        threads = [threading.Thread(target=get_cache_instance) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All should be the same instance
        assert len(caches) == 5
        assert all(cache is caches[0] for cache in caches)
    
    def test_cache_instance_reuse(self):
        """Test cache instance reuse."""
        cache1 = get_cache()
        clear_cache()
        cache2 = get_cache()
        # Should still be the same instance
        assert cache1 is cache2


class TestCacheOperations:
    """Test cache operations."""
    
    def test_clear_cache_removes_all_entries(self):
        """Test clear_cache removes all entries."""
        cache = get_cache()
        cache.set("test_key", "test_value")
        assert len(cache) > 0
        
        clear_cache()
        assert len(cache) == 0
    
    def test_get_cache_info_returns_correct_size(self):
        """Test get_cache_info returns correct size."""
        clear_cache()
        cache = get_cache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        info = get_cache_info()
        assert info["size"] == 2
    
    def test_get_cache_info_returns_correct_cache_directory(self):
        """Test get_cache_info returns correct cache directory."""
        info = get_cache_info()
        assert "cache_dir" in info
        assert "pypipackagestats" in info["cache_dir"]
        assert "api_cache" in info["cache_dir"]
    
    def test_cache_info_with_empty_cache(self):
        """Test cache info with empty cache."""
        clear_cache()
        info = get_cache_info()
        assert info["size"] == 0
    
    def test_cache_info_with_populated_cache(self):
        """Test cache info with populated cache."""
        clear_cache()
        cache = get_cache()
        for i in range(5):
            cache.set(f"key{i}", f"value{i}")
        
        info = get_cache_info()
        assert info["size"] == 5


class TestCacheThreadSafety:
    """Test thread safety of cache operations."""
    
    def test_concurrent_cache_access(self):
        """Test concurrent cache access."""
        clear_cache()
        cache = get_cache()
        
        def add_to_cache(start, count):
            for i in range(count):
                cache.set(f"key_{start}_{i}", f"value_{start}_{i}")
        
        threads = [
            threading.Thread(target=add_to_cache, args=(i * 10, 10))
            for i in range(5)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Should have 50 entries
        assert len(cache) == 50
    
    def test_cache_operations_from_multiple_threads(self):
        """Test cache operations from multiple threads."""
        clear_cache()
        cache = get_cache()
        results = []
        
        def cache_operation(thread_id):
            cache.set(f"key_{thread_id}", f"value_{thread_id}")
            value = cache.get(f"key_{thread_id}")
            results.append(value)
        
        threads = [threading.Thread(target=cache_operation, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(results) == 10
        assert all(f"value_{i}" in results for i in range(10))
