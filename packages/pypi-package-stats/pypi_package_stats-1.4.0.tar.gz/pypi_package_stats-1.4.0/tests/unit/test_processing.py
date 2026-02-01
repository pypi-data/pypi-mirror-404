"""Tests for data processing functions."""
import pytest
from datetime import date, timedelta
from pypipackagestats.core.processing import (
    process_package_info,
    process_download_stats,
    process_category_breakdown,
)
from pypipackagestats.core.models import PackageInfo, DownloadStats, CategoryBreakdown


class TestProcessPackageInfo:
    """Test process_package_info function."""
    
    def test_with_complete_package_data(self):
        """Test with complete package data."""
        data = {
            "info": {
                "name": "test-package",
                "version": "1.0.0",
                "summary": "Test package",
                "author": "Test Author",
                "license": "MIT",
                "home_page": "https://example.com",
                "package_url": "https://pypi.org/project/test-package/",
            },
            "releases": {
                "1.0.0": [{"upload_time": "2024-01-15T10:30:00"}]
            }
        }
        result = process_package_info(data)
        assert isinstance(result, PackageInfo)
        assert result.name == "test-package"
        assert result.version == "1.0.0"
        assert result.description == "Test package"
        assert result.author == "Test Author"
        assert result.license == "MIT"
        assert result.home_page == "https://example.com"
    
    def test_with_missing_optional_fields(self):
        """Test with missing optional fields."""
        data = {
            "info": {
                "name": "test-package",
                "version": "1.0.0",
            }
        }
        result = process_package_info(data)
        assert result.name == "test-package"
        assert result.version == "1.0.0"
        assert result.description is None
        assert result.author is None
        assert result.license is None
    
    def test_with_empty_info_dict(self):
        """Test with empty info dict."""
        data = {"info": {}}
        result = process_package_info(data)
        assert result.name == ""
        assert result.version == ""
    
    def test_author_extraction_author_field(self):
        """Test author extraction (author field)."""
        data = {
            "info": {
                "name": "test",
                "version": "1.0.0",
                "author": "Test Author",
            }
        }
        result = process_package_info(data)
        assert result.author == "Test Author"
    
    def test_author_extraction_author_email_fallback(self):
        """Test author extraction (author_email fallback)."""
        data = {
            "info": {
                "name": "test",
                "version": "1.0.0",
                "author_email": "test@example.com",
            }
        }
        result = process_package_info(data)
        assert result.author == "test@example.com"
    
    def test_home_page_extraction_home_page_field(self):
        """Test home_page extraction (home_page field)."""
        data = {
            "info": {
                "name": "test",
                "version": "1.0.0",
                "home_page": "https://example.com",
            }
        }
        result = process_package_info(data)
        assert result.home_page == "https://example.com"
    
    def test_home_page_extraction_project_url_fallback(self):
        """Test home_page extraction (project_url fallback)."""
        data = {
            "info": {
                "name": "test",
                "version": "1.0.0",
                "project_url": "https://github.com/test/repo",
            }
        }
        result = process_package_info(data)
        assert result.home_page == "https://github.com/test/repo"
    
    def test_home_page_extraction_project_urls_homepage_fallback(self):
        """Test home_page extraction (project_urls.Homepage fallback)."""
        data = {
            "info": {
                "name": "test",
                "version": "1.0.0",
                "project_urls": {
                    "Homepage": "https://example.com"
                }
            }
        }
        result = process_package_info(data)
        assert result.home_page == "https://example.com"
    
    def test_upload_time_extraction(self):
        """Test upload_time extraction."""
        data = {
            "info": {
                "name": "test",
                "version": "1.0.0",
            },
            "releases": {
                "1.0.0": [{"upload_time": "2024-01-15T10:30:00"}]
            }
        }
        result = process_package_info(data)
        assert result.upload_time == "2024-01-15T10:30:00"
    
    def test_with_none_values(self):
        """Test with None values."""
        data = {
            "info": {
                "name": "test",
                "version": "1.0.0",
                "author": None,
                "license": None,
            }
        }
        result = process_package_info(data)
        assert result.author is None
        assert result.license is None
    
    def test_with_empty_strings(self):
        """Test with empty strings."""
        data = {
            "info": {
                "name": "",
                "version": "",
                "author": "",
            }
        }
        result = process_package_info(data)
        assert result.name == ""
        assert result.version == ""
        assert result.author is None  # get_at returns None for empty strings


class TestProcessDownloadStats:
    """Test process_download_stats function."""
    
    def test_with_complete_recent_stats(self):
        """Test with complete recent stats."""
        recent = {
            "last_day": 1000,
            "last_week": 7000,
            "last_month": 30000,
        }
        overall = [
            {"date": "2024-01-01", "downloads": 500},
            {"date": "2024-01-02", "downloads": 600},
        ]
        result = process_download_stats(recent, overall)
        assert isinstance(result, DownloadStats)
        assert result.last_day == 1000
        assert result.last_week == 7000
        assert result.last_month == 30000
        assert result.last_180d == 1100  # 500 + 600
    
    def test_with_missing_fields_should_default_to_zero(self):
        """Test with missing fields (should default to 0)."""
        recent = {}
        overall = []
        result = process_download_stats(recent, overall)
        assert result.last_day == 0
        assert result.last_week == 0
        assert result.last_month == 0
        assert result.last_180d == 0
    
    def test_last_180d_calculation_from_overall_stats(self):
        """Test last_180d calculation from overall stats."""
        recent = {}
        overall = [
            {"date": "2024-01-01", "downloads": 100},
            {"date": "2024-01-02", "downloads": 200},
            {"date": "2024-01-03", "downloads": 300},
        ]
        result = process_download_stats(recent, overall)
        assert result.last_180d == 600  # 100 + 200 + 300
    
    def test_with_empty_overall_stats_list(self):
        """Test with empty overall stats list."""
        recent = {"last_day": 100}
        overall = []
        result = process_download_stats(recent, overall)
        assert result.last_180d == 0
    
    def test_with_zero_downloads(self):
        """Test with zero downloads."""
        recent = {
            "last_day": 0,
            "last_week": 0,
            "last_month": 0,
        }
        overall = [{"date": "2024-01-01", "downloads": 0}]
        result = process_download_stats(recent, overall)
        assert result.last_day == 0
        assert result.last_180d == 0
    
    def test_with_large_download_numbers(self):
        """Test with large download numbers."""
        recent = {
            "last_day": 1000000,
            "last_week": 7000000,
            "last_month": 30000000,
        }
        overall = [{"date": "2024-01-01", "downloads": 5000000}]
        result = process_download_stats(recent, overall)
        assert result.last_day == 1000000
        assert result.last_180d == 5000000
    
    def test_with_missing_downloads_field_in_overall_stats(self):
        """Test with missing downloads field in overall stats."""
        recent = {}
        overall = [
            {"date": "2024-01-01"},
            {"date": "2024-01-02", "downloads": 100},
        ]
        result = process_download_stats(recent, overall)
        assert result.last_180d == 100  # Only one entry has downloads


class TestProcessCategoryBreakdown:
    """Test process_category_breakdown function."""
    
    def test_with_valid_data_last_30_days(self):
        """Test with valid data (last 30 days)."""
        today = date.today()
        data = [
            {"category": "3.11", "date": today.isoformat(), "downloads": 1000},
            {"category": "3.10", "date": today.isoformat(), "downloads": 800},
        ]
        result = process_category_breakdown(data)
        assert len(result) == 2
        assert all(isinstance(r, CategoryBreakdown) for r in result)
    
    def test_filtering_by_date_only_last_30_days(self):
        """Test filtering by date (only last 30 days)."""
        today = date.today()
        old_date = (today - timedelta(days=31)).isoformat()
        recent_date = (today - timedelta(days=10)).isoformat()
        
        data = [
            {"category": "3.11", "date": old_date, "downloads": 1000},  # Should be filtered
            {"category": "3.10", "date": recent_date, "downloads": 800},  # Should be included
        ]
        result = process_category_breakdown(data)
        assert len(result) == 1
        assert result[0].category == "3.10"
    
    def test_aggregation_by_category(self):
        """Test aggregation by category."""
        today = date.today().isoformat()
        data = [
            {"category": "3.11", "date": today, "downloads": 100},
            {"category": "3.11", "date": today, "downloads": 200},
            {"category": "3.10", "date": today, "downloads": 150},
        ]
        result = process_category_breakdown(data)
        # Should aggregate 3.11: 100 + 200 = 300
        categories = {r.category: r.downloads for r in result}
        assert categories.get("3.11") == 300
        assert categories.get("3.10") == 150
    
    def test_sorting_by_downloads_descending(self):
        """Test sorting by downloads (descending)."""
        today = date.today().isoformat()
        data = [
            {"category": "3.10", "date": today, "downloads": 100},
            {"category": "3.11", "date": today, "downloads": 300},
            {"category": "3.9", "date": today, "downloads": 200},
        ]
        result = process_category_breakdown(data)
        downloads = [r.downloads for r in result]
        assert downloads == sorted(downloads, reverse=True)
    
    def test_limit_parameter(self):
        """Test limit parameter."""
        today = date.today().isoformat()
        data = [
            {"category": f"3.{i}", "date": today, "downloads": 1000 - i * 100}
            for i in range(8, 12)
        ]
        result = process_category_breakdown(data, limit=2)
        assert len(result) == 2
    
    def test_with_empty_data_list(self):
        """Test with empty data list."""
        result = process_category_breakdown([])
        assert result == []
    
    def test_with_data_older_than_30_days_should_be_filtered_out(self):
        """Test with data older than 30 days (should be filtered out)."""
        old_date = (date.today() - timedelta(days=31)).isoformat()
        data = [
            {"category": "3.11", "date": old_date, "downloads": 1000},
        ]
        result = process_category_breakdown(data)
        assert result == []
    
    def test_with_null_category_should_become_unknown(self):
        """Test with "null" category (should become "Unknown")."""
        today = date.today().isoformat()
        data = [
            {"category": "null", "date": today, "downloads": 100},
        ]
        result = process_category_breakdown(data)
        assert result[0].category == "Unknown"
    
    def test_percentage_calculation(self):
        """Test percentage calculation."""
        today = date.today().isoformat()
        data = [
            {"category": "3.11", "date": today, "downloads": 300},
            {"category": "3.10", "date": today, "downloads": 200},
        ]
        result = process_category_breakdown(data)
        # Total: 500, so 300/500 = 60%, 200/500 = 40%
        percentages = {r.category: r.percentage for r in result}
        assert percentages["3.11"] == 60.0
        assert percentages["3.10"] == 40.0
    
    def test_percentage_with_zero_total_downloads(self):
        """Test percentage with zero total downloads."""
        today = date.today().isoformat()
        data = [
            {"category": "3.11", "date": today, "downloads": 0},
        ]
        result = process_category_breakdown(data)
        assert result[0].percentage == 0.0
    
    def test_percentage_rounding_1_decimal_place(self):
        """Test percentage rounding (1 decimal place)."""
        today = date.today().isoformat()
        data = [
            {"category": "3.11", "date": today, "downloads": 1},
            {"category": "3.10", "date": today, "downloads": 3},
        ]
        result = process_category_breakdown(data)
        # 1/4 = 0.25 = 25.0%, 3/4 = 0.75 = 75.0%
        percentages = {r.category: r.percentage for r in result}
        assert percentages["3.11"] == 25.0
        assert percentages["3.10"] == 75.0
    
    def test_with_multiple_categories(self):
        """Test with multiple categories."""
        today = date.today().isoformat()
        data = [
            {"category": "3.11", "date": today, "downloads": 1000},
            {"category": "3.10", "date": today, "downloads": 800},
            {"category": "3.9", "date": today, "downloads": 600},
        ]
        result = process_category_breakdown(data)
        assert len(result) == 3
    
    def test_with_single_category(self):
        """Test with single category."""
        today = date.today().isoformat()
        data = [
            {"category": "3.11", "date": today, "downloads": 1000},
        ]
        result = process_category_breakdown(data)
        assert len(result) == 1
        assert result[0].percentage == 100.0
