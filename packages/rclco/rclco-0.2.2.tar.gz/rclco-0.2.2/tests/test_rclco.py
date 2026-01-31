"""Tests for RCLCO library core functionality."""

import pytest

from rclco import __version__
from rclco.core.exceptions import (
    RCLCOError,
    ConfigurationError,
    ConnectionError,
    QueryError,
    AuthenticationError,
    APIError,
    StorageError,
)
from rclco.core.types import DatabaseConfig, APIConfig, BlobConfig, SharePointConfig


class TestVersion:
    """Tests for version string."""

    def test_version_is_string(self):
        """Test that version is a non-empty string."""
        assert isinstance(__version__, str)
        assert len(__version__) > 0


class TestExceptions:
    """Tests for custom exception hierarchy."""

    def test_rclco_error_is_base(self):
        """Test that RCLCOError is the base for all custom exceptions."""
        assert issubclass(ConfigurationError, RCLCOError)
        assert issubclass(ConnectionError, RCLCOError)
        assert issubclass(QueryError, RCLCOError)
        assert issubclass(AuthenticationError, RCLCOError)
        assert issubclass(APIError, RCLCOError)
        assert issubclass(StorageError, RCLCOError)

    def test_api_error_attributes(self):
        """Test that APIError captures status code and response body."""
        error = APIError("Request failed", status_code=404, response_body='{"error": "not found"}')
        assert error.status_code == 404
        assert error.response_body == '{"error": "not found"}'
        assert "Request failed" in str(error)

    def test_catching_all_rclco_errors(self):
        """Test that all custom exceptions can be caught with RCLCOError."""
        exceptions = [
            ConfigurationError("config error"),
            ConnectionError("connection error"),
            QueryError("query error"),
            AuthenticationError("auth error"),
            APIError("api error"),
            StorageError("storage error"),
        ]

        for exc in exceptions:
            with pytest.raises(RCLCOError):
                raise exc


class TestTypes:
    """Tests for configuration type classes."""

    def test_database_config(self):
        """Test DatabaseConfig dataclass."""
        config = DatabaseConfig(
            secret_name="my-connection-string",
            db_type="azure_sql",
            description="Test database",
        )
        assert config.secret_name == "my-connection-string"
        assert config.db_type == "azure_sql"
        assert config.description == "Test database"

    def test_api_config_hardcoded_url_with_key(self):
        """Test APIConfig with hardcoded URL and API key from Key Vault."""
        config = APIConfig(
            base_url="https://api.example.com",
            api_key_secret="api-key",
            description="Test API",
        )
        assert config.base_url == "https://api.example.com"
        assert config.base_url_secret is None
        assert config.api_key_secret == "api-key"

    def test_api_config_url_from_keyvault(self):
        """Test APIConfig with URL from Key Vault."""
        config = APIConfig(
            base_url_secret="internal-api-url",
            api_key_secret="internal-api-key",
            description="Internal API",
        )
        assert config.base_url is None
        assert config.base_url_secret == "internal-api-url"
        assert config.api_key_secret == "internal-api-key"

    def test_api_config_no_auth(self):
        """Test APIConfig with no authentication (public API)."""
        config = APIConfig(
            base_url="https://public-api.example.com",
            description="Public API",
        )
        assert config.base_url == "https://public-api.example.com"
        assert config.api_key_secret is None

    def test_api_config_requires_url(self):
        """Test that APIConfig requires at least one URL source."""
        with pytest.raises(ValueError, match="base_url.*base_url_secret"):
            APIConfig(
                api_key_secret="some-key",
                description="Invalid config",
            )

    def test_blob_config(self):
        """Test BlobConfig dataclass."""
        config = BlobConfig(
            account_url="https://myaccount.blob.core.windows.net",
            container="mycontainer",
            secret_name="storage-key",
            description="Test storage",
        )
        assert config.account_url == "https://myaccount.blob.core.windows.net"
        assert config.container == "mycontainer"

    def test_sharepoint_config(self):
        """Test SharePointConfig dataclass."""
        config = SharePointConfig(
            site_url="https://company.sharepoint.com/sites/Data",
            client_id="client-id",
            tenant_id="tenant-id",
            client_secret_name="sp-secret",
            description="Test SharePoint",
        )
        assert config.site_url == "https://company.sharepoint.com/sites/Data"
        assert config.client_id == "client-id"


class TestImports:
    """Tests for module imports."""

    def test_import_factory_functions(self):
        """Test that factory functions can be imported."""
        from rclco import get_database, get_api, get_storage, get_sharepoint

        assert callable(get_database)
        assert callable(get_api)
        assert callable(get_storage)
        assert callable(get_sharepoint)

    def test_import_list_functions(self):
        """Test that list functions can be imported."""
        from rclco import list_databases, list_apis, list_storage

        assert callable(list_databases)
        assert callable(list_apis)
        assert callable(list_storage)

    def test_import_connectors(self):
        """Test that connectors can be imported."""
        from rclco.connectors.database import AzureSQLConnector, PostgresConnector
        from rclco.connectors.api import RESTClient
        from rclco.connectors.storage import AzureBlobConnector
        from rclco.connectors.microsoft import SharePointConnector

        assert AzureSQLConnector is not None
        assert PostgresConnector is not None
        assert RESTClient is not None
        assert AzureBlobConnector is not None
        assert SharePointConnector is not None

    def test_import_exceptions(self):
        """Test that exceptions can be imported from main module."""
        from rclco import (
            RCLCOError,
            ConfigurationError,
            ConnectionError,
            QueryError,
            AuthenticationError,
            APIError,
            StorageError,
        )

        assert RCLCOError is not None
        assert ConfigurationError is not None


class TestListFunctions:
    """Tests for list functions."""

    def test_list_databases_returns_list(self):
        """Test that list_databases returns a list."""
        from rclco.databases import list_databases

        result = list_databases()
        assert isinstance(result, list)

    def test_list_apis_returns_list(self):
        """Test that list_apis returns a list."""
        from rclco.apis import list_apis

        result = list_apis()
        assert isinstance(result, list)

    def test_list_storage_returns_list(self):
        """Test that list_storage returns a list."""
        from rclco.storage import list_storage

        result = list_storage()
        assert isinstance(result, list)


class TestConfigurationErrors:
    """Tests for configuration error handling."""

    def test_get_database_unknown_raises(self):
        """Test that get_database raises for unknown database."""
        from rclco.databases import get_database

        with pytest.raises(ConfigurationError, match="Unknown database"):
            get_database("nonexistent_db")

    def test_get_api_unknown_raises(self):
        """Test that get_api raises for unknown API."""
        from rclco.apis import get_api

        with pytest.raises(ConfigurationError, match="Unknown API"):
            get_api("nonexistent_api")

    def test_get_storage_unknown_raises(self):
        """Test that get_storage raises for unknown storage."""
        from rclco.storage import get_storage

        with pytest.raises(ConfigurationError, match="Unknown storage"):
            get_storage("nonexistent_storage")


class TestRetry:
    """Tests for retry utility."""

    def test_retry_success_on_first_attempt(self):
        """Test that successful functions don't retry."""
        from rclco.utils.retry import retry

        call_count = 0

        @retry(max_attempts=3)
        def successful_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = successful_func()
        assert result == "success"
        assert call_count == 1

    def test_retry_on_failure(self):
        """Test that failing functions retry."""
        from rclco.utils.retry import retry

        call_count = 0

        @retry(max_attempts=3, base_delay=0.01)
        def failing_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Not yet")
            return "success"

        result = failing_then_success()
        assert result == "success"
        assert call_count == 3

    def test_retry_exhaustion(self):
        """Test that max retries raises the exception."""
        from rclco.utils.retry import retry

        @retry(max_attempts=2, base_delay=0.01)
        def always_fails():
            raise ValueError("Always fails")

        with pytest.raises(ValueError, match="Always fails"):
            always_fails()
