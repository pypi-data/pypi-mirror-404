# Constants
DEFAULT_CACHE_TTL = 3600  # Default cache TTL in seconds (1 hour)
TOP_PYTHON_VERSIONS_COUNT = 5  # Number of top Python versions to display
TOP_OS_COUNT = 4  # Number of top operating systems to display
DATE_ISO_FORMAT_LENGTH = 10  # Length of ISO date format string (YYYY-MM-DD)

# API URLs
PYPI_API = "https://pypi.org/pypi/{pkg}/json"
STATS_API = "https://pypistats.org/api/packages/{pkg}/"

# Request configuration
REQUEST_RETRY_MAX_TRIES = 4
REQUEST_RETRY_BACKOFF_FACTOR = 1
REQUEST_RETRY_STATUS_FORCELIST = [429, 500, 502, 503, 504]
REQUEST_RETRY_ALLOWED_METHODS = ["GET"]
REQUEST_TIMEOUT = (2, 10)  # (connect_timeout, read_timeout) in seconds
