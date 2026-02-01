import requests
from typing import Optional

class PyPIStatsError(Exception):
    """Base exception for PyPI Stats."""
    pass

class PackageNotFoundError(PyPIStatsError):
    """Package not found on PyPI."""
    def __init__(self, package_name: str):
        super().__init__(f"Package '{package_name}' not found on PyPI")
        self.package_name = package_name

class APIError(PyPIStatsError):
    """API or network error."""
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code
