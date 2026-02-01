from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from pypipackagestats.core.constants import DATE_ISO_FORMAT_LENGTH

@dataclass(frozen=True)
class ProjectMetadata:
    name: str
    version: str
    repository_url: str
    author: str
    author_url: str

@dataclass(frozen=True)
class PackageInfo:
    name: str
    version: str
    description: Optional[str] = None
    author: Optional[str] = None
    license: Optional[str] = None
    home_page: Optional[str] = None
    pypi_url: Optional[str] = None
    upload_time: Optional[str] = None

@dataclass(frozen=True)
class DownloadStats:
    last_day: int = 0
    last_week: int = 0
    last_month: int = 0
    last_180d: int = 0

@dataclass(frozen=True)
class CategoryBreakdown:
    category: str
    downloads: int
    percentage: float

@dataclass(frozen=True)
class PackageStats:
    package_info: PackageInfo
    downloads: DownloadStats
    python_versions: List[CategoryBreakdown]
    operating_systems: List[CategoryBreakdown]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON."""
        return {
            "package": {
                "name": self.package_info.name,
                "version": self.package_info.version,
                "upload_time": self.package_info.upload_time[:DATE_ISO_FORMAT_LENGTH] if self.package_info.upload_time else None,
                "description": self.package_info.description,
                "author": self.package_info.author,
                "license": self.package_info.license,
                "home_page": self.package_info.home_page,
                "pypi_url": self.package_info.pypi_url,
            },
            "downloads": {
                "last_day": self.downloads.last_day,
                "last_week": self.downloads.last_week,
                "last_month": self.downloads.last_month,
                "last_180d": self.downloads.last_180d,
            },
            "python_versions": [
                {"version": pv.category, "downloads": pv.downloads, "percentage": pv.percentage}
                for pv in self.python_versions
            ],
            "operating_systems": [
                {"os": os.category, "downloads": os.downloads, "percentage": os.percentage}
                for os in self.operating_systems
            ],
        }
