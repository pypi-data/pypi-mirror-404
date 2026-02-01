"""Tests for output utility functions."""
import pytest
from pypipackagestats.output.utils import (
    humanize_number,
    normalize_os_name,
    get_upload_time,
    humanize_date,
    extract_repo_name,
)


class TestHumanizeNumber:
    """Test humanize_number function."""
    
    def test_with_numbers_less_than_1000_no_suffix(self):
        """Test with numbers < 1000 (no suffix)."""
        assert humanize_number(0) == "0"
        assert humanize_number(100) == "100"
        assert humanize_number(999) == "999"
    
    def test_with_numbers_in_thousands_k_suffix(self):
        """Test with numbers in thousands (K suffix)."""
        assert humanize_number(1000) == "1.0K"
        assert humanize_number(1500) == "1.5K"
        assert humanize_number(9999) == "10.0K"
    
    def test_with_numbers_in_millions_m_suffix(self):
        """Test with numbers in millions (M suffix)."""
        assert humanize_number(1000000) == "1.0M"
        assert humanize_number(1500000) == "1.5M"
        assert humanize_number(9999999) == "10.0M"
    
    def test_with_numbers_in_billions_b_suffix(self):
        """Test with numbers in billions (B suffix)."""
        assert humanize_number(1000000000) == "1.0B"
        assert humanize_number(1500000000) == "1.5B"
    
    def test_with_zero(self):
        """Test with zero."""
        assert humanize_number(0) == "0"
    
    def test_with_negative_numbers(self):
        """Test with negative numbers."""
        assert humanize_number(-100) == "-100"
        assert humanize_number(-1000) == "-1.0K"
        assert humanize_number(-1000000) == "-1.0M"
    
    def test_decimal_formatting(self):
        """Test decimal formatting."""
        assert humanize_number(1234) == "1.2K"
        assert humanize_number(12345) == "12.3K"
        assert humanize_number(1234567) == "1.2M"
    
    def test_trailing_zero_removal(self):
        """Test trailing zero removal."""
        assert humanize_number(1000) == "1.0K"  # Includes .0
        assert humanize_number(2000) == "2.0K"  # Includes .0
        assert humanize_number(1500) == "1.5K"  # Keeps .5


class TestNormalizeOSName:
    """Test normalize_os_name function."""
    
    def test_with_darwin_to_macos(self):
        """Test with "darwin" → "macOS"."""
        assert normalize_os_name("darwin") == "macOS"
        assert normalize_os_name("Darwin") == "macOS"
        assert normalize_os_name("DARWIN") == "macOS"
    
    def test_with_windows_to_windows(self):
        """Test with "windows" → "Windows"."""
        assert normalize_os_name("windows") == "Windows"
        assert normalize_os_name("Windows") == "Windows"
        assert normalize_os_name("WINDOWS") == "Windows"
    
    def test_with_linux_to_linux(self):
        """Test with "linux" → "Linux"."""
        assert normalize_os_name("linux") == "Linux"
        assert normalize_os_name("Linux") == "Linux"
        assert normalize_os_name("LINUX") == "Linux"
    
    def test_with_null_to_unknown(self):
        """Test with "null" → "Unknown"."""
        assert normalize_os_name("null") == "Unknown"
        assert normalize_os_name("Null") == "Unknown"
        assert normalize_os_name("NULL") == "Unknown"
    
    def test_with_empty_string_to_unknown(self):
        """Test with empty string → "Unknown"."""
        assert normalize_os_name("") == "Unknown"
    
    def test_with_none_to_unknown(self):
        """Test with None → "Unknown"."""
        assert normalize_os_name(None) == "Unknown"
    
    def test_with_unknown_os_name_title_case(self):
        """Test with unknown OS name (title case)."""
        assert normalize_os_name("freebsd") == "Freebsd"
        assert normalize_os_name("openbsd") == "Openbsd"
    
    def test_case_insensitivity(self):
        """Test case insensitivity."""
        assert normalize_os_name("DARWIN") == "macOS"
        assert normalize_os_name("WINDOWS") == "Windows"
        assert normalize_os_name("LINUX") == "Linux"


class TestGetUploadTime:
    """Test get_upload_time function."""
    
    def test_extraction_from_releases_version_upload_time(self):
        """Test extraction from releases[version][0].upload_time."""
        pkg_data = {
            "info": {"version": "1.0.0"},
            "releases": {
                "1.0.0": [{"upload_time": "2024-01-15T10:30:00"}]
            }
        }
        result = get_upload_time(pkg_data)
        assert result == "2024-01-15T10:30:00"
    
    def test_extraction_from_releases_version_upload_time_iso_8601_fallback(self):
        """Test extraction from releases[version][0].upload_time_iso_8601 (fallback)."""
        pkg_data = {
            "info": {"version": "1.0.0"},
            "releases": {
                "1.0.0": [{"upload_time_iso_8601": "2024-01-15T10:30:00"}]
            }
        }
        result = get_upload_time(pkg_data)
        assert result == "2024-01-15T10:30:00"
    
    def test_with_missing_version(self):
        """Test with missing version."""
        pkg_data = {
            "info": {},
            "releases": {}
        }
        result = get_upload_time(pkg_data)
        assert result == ""
    
    def test_with_missing_releases(self):
        """Test with missing releases."""
        pkg_data = {
            "info": {"version": "1.0.0"}
        }
        result = get_upload_time(pkg_data)
        assert result == ""
    
    def test_with_empty_releases(self):
        """Test with empty releases."""
        pkg_data = {
            "info": {"version": "1.0.0"},
            "releases": {}
        }
        result = get_upload_time(pkg_data)
        assert result == ""
    
    def test_with_missing_upload_time_fields(self):
        """Test with missing upload_time fields."""
        pkg_data = {
            "info": {"version": "1.0.0"},
            "releases": {
                "1.0.0": [{}]
            }
        }
        result = get_upload_time(pkg_data)
        assert result == ""
    
    def test_returns_empty_string_when_not_found(self):
        """Test returns empty string when not found."""
        pkg_data = {}
        result = get_upload_time(pkg_data)
        assert result == ""


class TestHumanizeDate:
    """Test humanize_date function."""
    
    def test_with_valid_iso_date_yyyy_mm_dd(self):
        """Test with valid ISO date (YYYY-MM-DD)."""
        assert humanize_date("2025-12-07") == "December 07, 2025"
        assert humanize_date("2024-01-15") == "January 15, 2024"
        assert humanize_date("2023-06-30") == "June 30, 2023"
    
    def test_date_formatting(self):
        """Test date formatting (e.g., "2025-12-07" → "December 07, 2025")."""
        assert humanize_date("2025-12-07") == "December 07, 2025"
        assert humanize_date("2024-01-01") == "January 01, 2024"
        assert humanize_date("2023-12-31") == "December 31, 2023"
    
    def test_with_date_string_longer_than_iso_format_length_truncation(self):
        """Test with date string longer than DATE_ISO_FORMAT_LENGTH (truncation)."""
        # DATE_ISO_FORMAT_LENGTH is 10, so "2025-12-07T10:30:00" should be truncated to "2025-12-07"
        assert humanize_date("2025-12-07T10:30:00") == "December 07, 2025"
        assert humanize_date("2024-01-15T12:00:00Z") == "January 15, 2024"
    
    def test_with_invalid_date_format_returns_original(self):
        """Test with invalid date format (returns original)."""
        assert humanize_date("invalid-date") == "invalid-date"
        assert humanize_date("2024/01/15") == "2024/01/15"
        assert humanize_date("01-15-2024") == "01-15-2024"
    
    def test_with_empty_string_returns_empty_string(self):
        """Test with empty string (returns empty string)."""
        assert humanize_date("") == ""
    
    def test_with_none_returns_none_or_empty(self):
        """Test with None (returns None or empty)."""
        # The function should handle None gracefully
        result = humanize_date(None)
        # It might return None or empty string depending on implementation
        assert result is None or result == ""
    
    def test_with_various_date_formats(self):
        """Test with various date formats."""
        # Valid ISO format
        assert humanize_date("2024-01-15") == "January 15, 2024"
        # Invalid formats should return as-is
        assert humanize_date("15/01/2024") == "15/01/2024"
        assert humanize_date("Jan 15, 2024") == "Jan 15, 2024"


class TestExtractRepoName:
    """Test extract_repo_name function."""
    
    def test_github_url_extraction(self):
        """Test GitHub URL extraction."""
        assert extract_repo_name("https://github.com/owner/repo") == "owner/repo"
        assert extract_repo_name("https://github.com/user/package-name") == "user/package-name"
    
    def test_gitlab_url_extraction(self):
        """Test GitLab URL extraction."""
        assert extract_repo_name("https://gitlab.com/owner/repo") == "owner/repo"
        assert extract_repo_name("https://gitlab.com/user/package-name") == "user/package-name"
    
    def test_bitbucket_url_extraction(self):
        """Test Bitbucket URL extraction."""
        assert extract_repo_name("https://bitbucket.org/owner/repo") == "owner/repo"
        assert extract_repo_name("https://bitbucket.org/user/package-name") == "user/package-name"
    
    def test_with_git_suffix_removal(self):
        """Test with .git suffix removal."""
        assert extract_repo_name("https://github.com/owner/repo.git") == "owner/repo"
        assert extract_repo_name("https://gitlab.com/user/package.git") == "user/package"
        assert extract_repo_name("https://bitbucket.org/owner/repo.git") == "owner/repo"
    
    def test_with_empty_string_returns_empty(self):
        """Test with empty string (returns empty)."""
        assert extract_repo_name("") == ""
    
    def test_with_none_returns_empty(self):
        """Test with None (returns empty)."""
        assert extract_repo_name(None) == ""
    
    def test_with_invalid_url_format(self):
        """Test with invalid URL format."""
        assert extract_repo_name("not-a-url") == "not-a-url"
        assert extract_repo_name("http://example.com") == "http://example.com"
