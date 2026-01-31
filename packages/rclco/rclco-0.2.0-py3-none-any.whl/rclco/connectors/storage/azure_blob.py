"""Azure Blob Storage connector."""

import io
from typing import BinaryIO

import polars as pl

from rclco.core.exceptions import StorageError, ConfigurationError
from rclco.core.logging import get_logger

logger = get_logger("connectors.storage.azure_blob")


class AzureBlobConnector:
    """Connector for Azure Blob Storage.

    Provides methods for uploading, downloading, and listing blobs
    in an Azure Storage container. Supports Polars DataFrames
    natively for parquet files.

    Example:
        connector = AzureBlobConnector(
            account_url="https://myaccount.blob.core.windows.net",
            container="mycontainer",
            credential="sas-token-or-key"
        )

        # List blobs
        files = connector.list_blobs("data/")

        # Download a DataFrame
        df = connector.download_dataframe("data/sales.parquet")

        # Upload a DataFrame
        connector.upload_dataframe("output/results.parquet", df)

        # Clean up
        connector.close()
    """

    def __init__(
        self,
        account_url: str,
        container: str,
        credential: str,
    ):
        """Initialize the Azure Blob Storage connector.

        Args:
            account_url: Storage account URL (e.g., "https://myaccount.blob.core.windows.net")
            container: Container name
            credential: SAS token or storage account key
        """
        try:
            from azure.storage.blob import ContainerClient
        except ImportError as e:
            raise ConfigurationError(
                "azure-storage-blob not installed. Run: pip install azure-storage-blob"
            ) from e

        self._account_url = account_url
        self._container = container

        try:
            self._container_client = ContainerClient(
                account_url=account_url,
                container_name=container,
                credential=credential,
            )
            logger.debug(f"Connected to blob container: {container}")
        except Exception as e:
            raise StorageError(f"Failed to connect to blob storage: {e}") from e

    def close(self) -> None:
        """Close the container client."""
        if self._container_client:
            self._container_client.close()
            logger.debug("Closed blob storage connection")

    def __enter__(self) -> "AzureBlobConnector":
        """Enter context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager."""
        self.close()

    def list_blobs(self, prefix: str = "") -> list[str]:
        """List blobs in the container.

        Args:
            prefix: Optional prefix to filter blobs (e.g., "data/2024/")

        Returns:
            List of blob names matching the prefix
        """
        try:
            blobs = self._container_client.list_blobs(name_starts_with=prefix)
            blob_names = [blob.name for blob in blobs]
            logger.debug(f"Listed {len(blob_names)} blobs with prefix '{prefix}'")
            return blob_names
        except Exception as e:
            raise StorageError(f"Failed to list blobs: {e}") from e

    def download(self, blob_name: str) -> bytes:
        """Download a blob as bytes.

        Args:
            blob_name: Name of the blob to download

        Returns:
            Blob contents as bytes
        """
        try:
            blob_client = self._container_client.get_blob_client(blob_name)
            data = blob_client.download_blob().readall()
            logger.debug(f"Downloaded blob: {blob_name} ({len(data)} bytes)")
            return data
        except Exception as e:
            raise StorageError(f"Failed to download blob '{blob_name}': {e}") from e

    def upload(
        self,
        blob_name: str,
        data: bytes | BinaryIO,
        overwrite: bool = True,
    ) -> None:
        """Upload data to a blob.

        Args:
            blob_name: Name for the blob
            data: Data to upload (bytes or file-like object)
            overwrite: Whether to overwrite existing blob (default: True)
        """
        try:
            blob_client = self._container_client.get_blob_client(blob_name)
            blob_client.upload_blob(data, overwrite=overwrite)
            logger.debug(f"Uploaded blob: {blob_name}")
        except Exception as e:
            raise StorageError(f"Failed to upload blob '{blob_name}': {e}") from e

    def delete(self, blob_name: str) -> None:
        """Delete a blob.

        Args:
            blob_name: Name of the blob to delete
        """
        try:
            blob_client = self._container_client.get_blob_client(blob_name)
            blob_client.delete_blob()
            logger.debug(f"Deleted blob: {blob_name}")
        except Exception as e:
            raise StorageError(f"Failed to delete blob '{blob_name}': {e}") from e

    def exists(self, blob_name: str) -> bool:
        """Check if a blob exists.

        Args:
            blob_name: Name of the blob

        Returns:
            True if the blob exists, False otherwise
        """
        try:
            blob_client = self._container_client.get_blob_client(blob_name)
            return blob_client.exists()
        except Exception as e:
            raise StorageError(f"Failed to check blob existence: {e}") from e

    def download_dataframe(self, blob_name: str) -> pl.DataFrame:
        """Download a parquet file as a Polars DataFrame.

        Args:
            blob_name: Name of the parquet blob

        Returns:
            Polars DataFrame
        """
        data = self.download(blob_name)
        try:
            df = pl.read_parquet(io.BytesIO(data))
            logger.debug(f"Loaded DataFrame from {blob_name}: {df.shape}")
            return df
        except Exception as e:
            raise StorageError(f"Failed to parse parquet from '{blob_name}': {e}") from e

    def upload_dataframe(
        self,
        blob_name: str,
        df: pl.DataFrame,
        overwrite: bool = True,
    ) -> None:
        """Upload a Polars DataFrame as a parquet file.

        Args:
            blob_name: Name for the blob (should end with .parquet)
            df: Polars DataFrame to upload
            overwrite: Whether to overwrite existing blob (default: True)
        """
        try:
            buffer = io.BytesIO()
            df.write_parquet(buffer)
            buffer.seek(0)
            self.upload(blob_name, buffer, overwrite=overwrite)
            logger.debug(f"Uploaded DataFrame to {blob_name}: {df.shape}")
        except StorageError:
            raise
        except Exception as e:
            raise StorageError(f"Failed to upload DataFrame to '{blob_name}': {e}") from e

    def download_csv(self, blob_name: str, **kwargs) -> pl.DataFrame:
        """Download a CSV file as a Polars DataFrame.

        Args:
            blob_name: Name of the CSV blob
            **kwargs: Additional arguments passed to pl.read_csv

        Returns:
            Polars DataFrame
        """
        data = self.download(blob_name)
        try:
            df = pl.read_csv(io.BytesIO(data), **kwargs)
            logger.debug(f"Loaded CSV from {blob_name}: {df.shape}")
            return df
        except Exception as e:
            raise StorageError(f"Failed to parse CSV from '{blob_name}': {e}") from e

    def upload_csv(
        self,
        blob_name: str,
        df: pl.DataFrame,
        overwrite: bool = True,
    ) -> None:
        """Upload a Polars DataFrame as a CSV file.

        Args:
            blob_name: Name for the blob (should end with .csv)
            df: Polars DataFrame to upload
            overwrite: Whether to overwrite existing blob (default: True)
        """
        try:
            buffer = io.BytesIO()
            df.write_csv(buffer)
            buffer.seek(0)
            self.upload(blob_name, buffer, overwrite=overwrite)
            logger.debug(f"Uploaded CSV to {blob_name}: {df.shape}")
        except StorageError:
            raise
        except Exception as e:
            raise StorageError(f"Failed to upload CSV to '{blob_name}': {e}") from e
