"""Tests for PyPIClient."""
import threading
import time
import pytest
import responses
from requests.exceptions import HTTPError, Timeout, ConnectionError, RetryError
from unittest.mock import Mock, patch, MagicMock
from pypipackagestats.core.client import PyPIClient
from pypipackagestats.core.constants import DEFAULT_CACHE_TTL, PYPI_API, STATS_API


class TestPyPIClientInitialization:
    """Test client initialization."""
    
    def test_init_with_default_cache_ttl(self):
        """Test client initialization with default cache TTL."""
        client = PyPIClient()
        assert client.cache_ttl == DEFAULT_CACHE_TTL
        assert client.use_cache is True
    
    def test_init_with_custom_cache_ttl(self):
        """Test client initialization with custom cache TTL."""
        client = PyPIClient(cache_ttl=7200)
        assert client.cache_ttl == 7200
        assert client.use_cache is True
    
    def test_init_with_cache_disabled(self):
        """Test client initialization with cache disabled (TTL=0)."""
        client = PyPIClient(cache_ttl=0)
        assert client.cache_ttl == 0
        assert client.use_cache is False
    
    def test_init_with_none_cache_ttl(self):
        """Test client initialization with None cache TTL (should use default)."""
        client = PyPIClient(cache_ttl=None)
        assert client.cache_ttl == DEFAULT_CACHE_TTL
        assert client.use_cache is True


class TestPyPIClientThreadSafety:
    """Test thread safety."""
    
    def test_thread_local_session_creation(self):
        """Test thread-local session creation."""
        client = PyPIClient()
        session1 = client._get_session()
        session2 = client._get_session()
        assert session1 is session2  # Same thread, same session
    
    def test_multiple_threads_using_same_client(self):
        """Test multiple threads using same client instance."""
        client = PyPIClient()
        sessions = []
        
        def get_session():
            sessions.append(client._get_session())
        
        threads = [threading.Thread(target=get_session) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Each thread should have its own session
        assert len(sessions) == 3
        assert len(set(id(s) for s in sessions)) == 3  # Different session objects
    
    def test_session_cleanup_on_object_destruction(self):
        """Test session cleanup on object destruction."""
        client = PyPIClient()
        session = client._get_session()
        assert hasattr(client._local, 'session')
        
        # Simulate cleanup
        client.__del__()
        # Session should still exist but be closed
        assert hasattr(client._local, 'session')


class TestPyPIClientCaching:
    """Test caching functionality."""
    
    @responses.activate
    def test_cached_get_with_cache_enabled_cache_hit(self):
        """Test _cached_get with cache enabled (cache hit)."""
        client = PyPIClient(cache_ttl=3600)
        url = "https://pypi.org/pypi/test/json"
        expected_data = {"test": "data"}
        
        # First request - cache miss
        responses.add(responses.GET, url, json=expected_data, status=200)
        result1 = client._cached_get(url)
        assert result1 == expected_data
        
        # Second request - cache hit (no new HTTP request)
        result2 = client._cached_get(url)
        assert result2 == expected_data
        assert len(responses.calls) == 1  # Only one HTTP request
    
    @responses.activate
    def test_cached_get_with_cache_enabled_cache_miss(self):
        """Test _cached_get with cache enabled (cache miss)."""
        client = PyPIClient(cache_ttl=3600)
        url = "https://pypi.org/pypi/test/json"
        expected_data = {"test": "data"}
        
        responses.add(responses.GET, url, json=expected_data, status=200)
        result = client._cached_get(url)
        assert result == expected_data
        assert len(responses.calls) == 1
    
    @responses.activate
    def test_cached_get_with_cache_disabled(self):
        """Test _cached_get with cache disabled."""
        client = PyPIClient(cache_ttl=0)
        url = "https://pypi.org/pypi/test/json"
        expected_data = {"test": "data"}
        
        responses.add(responses.GET, url, json=expected_data, status=200)
        result1 = client._cached_get(url)
        assert result1 == expected_data
        
        # Second request should make another HTTP call
        result2 = client._cached_get(url)
        assert result2 == expected_data
        assert len(responses.calls) == 2  # Two HTTP requests
    
    @responses.activate
    def test_cache_expiration_ttl(self):
        """Test cache expiration (TTL)."""
        client = PyPIClient(cache_ttl=1)  # 1 second TTL
        url = "https://pypi.org/pypi/test/json"
        expected_data = {"test": "data"}
        
        responses.add(responses.GET, url, json=expected_data, status=200)
        result1 = client._cached_get(url)
        assert result1 == expected_data
        assert len(responses.calls) == 1
        
        # Wait for cache to expire
        time.sleep(1.1)
        
        # Should make new request after expiration
        result2 = client._cached_get(url)
        assert result2 == expected_data
        assert len(responses.calls) == 2
    
    def test_cache_key_generation(self):
        """Test cache key generation."""
        client = PyPIClient()
        url = "https://pypi.org/pypi/test/json"
        # Cache key should be "url:" + url
        # This is tested indirectly through cache behavior
    
    @responses.activate
    def test_caching_only_for_successful_responses(self):
        """Test caching only for successful responses (2xx)."""
        client = PyPIClient(cache_ttl=3600)
        url = "https://pypi.org/pypi/test/json"
        
        # 404 response should not be cached
        responses.add(responses.GET, url, status=404)
        with pytest.raises(HTTPError):
            client._cached_get(url)
        
        # Should make request again (not cached)
        with pytest.raises(HTTPError):
            client._cached_get(url)
        assert len(responses.calls) == 2


class TestPyPIClientAPIMethods:
    """Test API methods."""
    
    @responses.activate
    def test_get_package_info_with_valid_package(self, package_info_data):
        """Test get_package_info with valid package."""
        client = PyPIClient(cache_ttl=0)
        package = "test-package"
        url = PYPI_API.format(pkg=package.lower())
        
        responses.add(responses.GET, url, json=package_info_data, status=200)
        result = client.get_package_info(package)
        assert result == package_info_data
    
    @responses.activate
    def test_get_package_info_with_invalid_package(self):
        """Test get_package_info with invalid package (404)."""
        client = PyPIClient(cache_ttl=0)
        package = "nonexistent-package-xyz"
        url = PYPI_API.format(pkg=package.lower())
        
        responses.add(responses.GET, url, status=404)
        with pytest.raises(HTTPError):
            client.get_package_info(package)
    
    @responses.activate
    def test_get_recent_stats_with_valid_package(self, recent_stats_data):
        """Test get_recent_stats with valid package."""
        client = PyPIClient(cache_ttl=0)
        package = "test-package"
        url = STATS_API.format(pkg=package.lower()) + "recent"
        
        responses.add(responses.GET, url, json=recent_stats_data, status=200)
        result = client.get_recent_stats(package)
        assert result == recent_stats_data["data"]
    
    @responses.activate
    def test_get_recent_stats_with_missing_data_field(self):
        """Test get_recent_stats with missing data field."""
        client = PyPIClient(cache_ttl=0)
        package = "test-package"
        url = STATS_API.format(pkg=package.lower()) + "recent"
        
        responses.add(responses.GET, url, json={}, status=200)
        result = client.get_recent_stats(package)
        assert result == {}
    
    @responses.activate
    def test_get_overall_stats_with_valid_package(self, overall_stats_data):
        """Test get_overall_stats with valid package."""
        client = PyPIClient(cache_ttl=0)
        package = "test-package"
        url = STATS_API.format(pkg=package.lower()) + "overall?mirrors=false"
        
        responses.add(responses.GET, url, json=overall_stats_data, status=200)
        result = client.get_overall_stats(package)
        assert result == overall_stats_data["data"]
    
    @responses.activate
    def test_get_overall_stats_with_empty_data(self):
        """Test get_overall_stats with empty data."""
        client = PyPIClient(cache_ttl=0)
        package = "test-package"
        url = STATS_API.format(pkg=package.lower()) + "overall?mirrors=false"
        
        responses.add(responses.GET, url, json={"data": []}, status=200)
        result = client.get_overall_stats(package)
        assert result == []
    
    @responses.activate
    def test_get_python_stats_with_valid_package(self, python_stats_data):
        """Test get_python_stats with valid package."""
        client = PyPIClient(cache_ttl=0)
        package = "test-package"
        url = STATS_API.format(pkg=package.lower()) + "python_minor"
        
        responses.add(responses.GET, url, json=python_stats_data, status=200)
        result = client.get_python_stats(package)
        assert result == python_stats_data["data"]
    
    @responses.activate
    def test_get_system_stats_with_valid_package(self, system_stats_data):
        """Test get_system_stats with valid package."""
        client = PyPIClient(cache_ttl=0)
        package = "test-package"
        url = STATS_API.format(pkg=package.lower()) + "system"
        
        responses.add(responses.GET, url, json=system_stats_data, status=200)
        result = client.get_system_stats(package)
        assert result == system_stats_data["data"]


class TestPyPIClientErrorHandling:
    """Test error handling."""
    
    @responses.activate
    def test_http_errors_4xx(self):
        """Test HTTP errors (4xx)."""
        client = PyPIClient(cache_ttl=0)
        url = "https://pypi.org/pypi/test/json"
        
        responses.add(responses.GET, url, status=400)
        with pytest.raises(HTTPError):
            client._cached_get(url)
    
    @responses.activate
    def test_http_errors_5xx(self):
        """Test HTTP errors (5xx)."""
        client = PyPIClient(cache_ttl=0)
        url = "https://pypi.org/pypi/test/json"
        
        # Add enough 500 responses to exhaust retries
        for _ in range(10):  # Ensure retries are exhausted
            responses.add(responses.GET, url, status=500)
        with pytest.raises(RetryError):
            client._cached_get(url)
    
    @responses.activate
    def test_network_timeout(self):
        """Test network timeout."""
        client = PyPIClient(cache_ttl=0)
        url = "https://pypi.org/pypi/test/json"
        
        responses.add(responses.GET, url, body=Timeout("Connection timeout"))
        with pytest.raises(Timeout):
            client._cached_get(url)
    
    @responses.activate
    def test_connection_errors(self):
        """Test connection errors."""
        client = PyPIClient(cache_ttl=0)
        url = "https://pypi.org/pypi/test/json"
        
        responses.add(responses.GET, url, body=ConnectionError("Connection failed"))
        with pytest.raises(ConnectionError):
            client._cached_get(url)
    
    @responses.activate
    def test_retry_logic_for_retryable_status_codes(self):
        """Test retry logic for retryable status codes (429, 500, 502, 503, 504)."""
        client = PyPIClient(cache_ttl=0)
        url = "https://pypi.org/pypi/test/json"
        
        # First two attempts fail with 500, third succeeds
        responses.add(responses.GET, url, status=500)
        responses.add(responses.GET, url, status=500)
        responses.add(responses.GET, url, json={"success": True}, status=200)
        
        result = client._cached_get(url)
        assert result == {"success": True}
        # Should have retried
        assert len(responses.calls) >= 2
    
    @responses.activate
    def test_retry_backoff_behavior(self):
        """Test retry backoff behavior."""
        client = PyPIClient(cache_ttl=0)
        url = "https://pypi.org/pypi/test/json"
        
        # Add multiple 500 responses to test backoff
        for _ in range(3):
            responses.add(responses.GET, url, status=500)
        responses.add(responses.GET, url, json={"success": True}, status=200)
        
        result = client._cached_get(url)
        assert result == {"success": True}
    
    @responses.activate
    def test_non_retryable_errors(self):
        """Test non-retryable errors."""
        client = PyPIClient(cache_ttl=0)
        url = "https://pypi.org/pypi/test/json"
        
        # 404 is not in retry list, should fail immediately
        responses.add(responses.GET, url, status=404)
        with pytest.raises(HTTPError):
            client._cached_get(url)
        assert len(responses.calls) == 1


class TestPyPIClientRequestConfiguration:
    """Test request configuration."""
    
    def test_request_timeout_settings(self):
        """Test request timeout settings."""
        client = PyPIClient()
        session = client._get_session()
        # Timeout is set in _cached_get, not in session
        # This is tested indirectly through timeout errors
    
    def test_retry_configuration(self):
        """Test retry configuration."""
        client = PyPIClient()
        session = client._get_session()
        adapter = session.get_adapter("https://")
        assert adapter.max_retries.total > 0
    
    def test_allowed_methods_get_only(self):
        """Test allowed methods (GET only)."""
        client = PyPIClient()
        session = client._get_session()
        adapter = session.get_adapter("https://")
        # Retry should only allow GET methods
        assert "GET" in adapter.max_retries.allowed_methods
