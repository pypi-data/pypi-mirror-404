"""Custom exception hierarchy for RCLCO library."""


class RCLCOError(Exception):
    """Base exception for all RCLCO errors.

    All custom exceptions in this library inherit from this class,
    making it easy to catch any RCLCO-related error.

    Example:
        try:
            df = analytics_query("SELECT * FROM table")
        except RCLCOError as e:
            print(f"RCLCO error: {e}")
    """

    pass


class ConfigurationError(RCLCOError):
    """Raised when there is a configuration or credential error.

    This includes:
    - Missing or invalid Key Vault URL
    - Unknown database/API/storage alias
    - Missing secrets in Key Vault
    - Invalid connection string format
    """

    pass


class AuthenticationError(RCLCOError):
    """Raised when authentication fails.

    This typically occurs when:
    - User is not logged into Azure CLI (run `az login`)
    - Managed Identity is not configured correctly
    - Service principal credentials are invalid
    - Insufficient permissions to access Key Vault
    """

    pass


class ConnectionError(RCLCOError):
    """Raised when a connection to a data source fails.

    This includes:
    - Database connection failures
    - Network timeouts
    - Invalid hostnames or ports
    - SSL/TLS errors
    """

    pass


class QueryError(RCLCOError):
    """Raised when a database query fails.

    This includes:
    - SQL syntax errors
    - Table/column not found
    - Constraint violations
    - Query timeout
    """

    pass


class APIError(RCLCOError):
    """Raised when an API request fails.

    Attributes:
        status_code: HTTP status code if available
        response_body: Response body if available
    """

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_body: str | None = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class StorageError(RCLCOError):
    """Raised when a storage operation fails.

    This includes:
    - Blob not found
    - Permission denied
    - Container not found
    - Upload/download failures
    """

    pass
