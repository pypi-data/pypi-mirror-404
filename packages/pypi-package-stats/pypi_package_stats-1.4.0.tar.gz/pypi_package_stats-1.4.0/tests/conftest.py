"""Shared fixtures and configuration for tests."""
import json
from pathlib import Path
import pytest
from unittest.mock import Mock, MagicMock
import responses
from pypipackagestats.core.cache import clear_cache, get_cache


@pytest.fixture(autouse=True)
def clear_cache_before_test():
    """Clear cache before each test."""
    clear_cache()
    yield
    clear_cache()


@pytest.fixture
def sample_data_dir():
    """Return path to sample data directory."""
    return Path(__file__).parent / "fixtures" / "sample_data"


@pytest.fixture
def package_info_data(sample_data_dir):
    """Load sample package info data."""
    with open(sample_data_dir / "package_info.json") as f:
        return json.load(f)


@pytest.fixture
def recent_stats_data(sample_data_dir):
    """Load sample recent stats data."""
    with open(sample_data_dir / "recent_stats.json") as f:
        return json.load(f)


@pytest.fixture
def overall_stats_data(sample_data_dir):
    """Load sample overall stats data."""
    with open(sample_data_dir / "overall_stats.json") as f:
        return json.load(f)


@pytest.fixture
def python_stats_data(sample_data_dir):
    """Load sample Python stats data."""
    with open(sample_data_dir / "python_stats.json") as f:
        return json.load(f)


@pytest.fixture
def system_stats_data(sample_data_dir):
    """Load sample system stats data."""
    with open(sample_data_dir / "system_stats.json") as f:
        return json.load(f)


@pytest.fixture
def mock_response():
    """Create a mock response object."""
    response = Mock()
    response.status_code = 200
    response.json.return_value = {}
    response.headers = {}
    return response


@pytest.fixture
def mock_session(mock_response):
    """Create a mock session object."""
    session = MagicMock()
    session.get.return_value = mock_response
    return session
