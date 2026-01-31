"""SharePoint connector using Office365-REST-Python-Client."""

from typing import BinaryIO

from rclco.core.exceptions import StorageError, ConfigurationError, AuthenticationError
from rclco.core.logging import get_logger

logger = get_logger("connectors.microsoft.sharepoint")


class SharePointConnector:
    """Connector for SharePoint Online file operations.

    Uses Office365-REST-Python-Client for SharePoint API access.
    Authenticates using Azure AD application credentials (client ID and secret).

    Example:
        connector = SharePointConnector(
            site_url="https://company.sharepoint.com/sites/Data",
            client_id="your-app-client-id",
            client_secret="your-client-secret",
            tenant_id="your-tenant-id"
        )

        # List files
        files = connector.list_files("Shared Documents/Reports")

        # Download a file
        content = connector.download_file("Shared Documents/Reports/Q4.xlsx")

        # Upload a file
        connector.upload_file("Shared Documents/Outputs", "results.csv", data)
    """

    def __init__(
        self,
        site_url: str,
        client_id: str,
        client_secret: str,
        tenant_id: str,
    ):
        """Initialize the SharePoint connector.

        Args:
            site_url: SharePoint site URL (e.g., "https://company.sharepoint.com/sites/Data")
            client_id: Azure AD application client ID
            client_secret: Azure AD application client secret
            tenant_id: Azure AD tenant ID
        """
        try:
            from office365.sharepoint.client_context import ClientContext
            from office365.runtime.auth.client_credential import ClientCredential
        except ImportError as e:
            raise ConfigurationError(
                "Office365-REST-Python-Client not installed. "
                "Run: pip install Office365-REST-Python-Client"
            ) from e

        self._site_url = site_url

        try:
            credentials = ClientCredential(client_id, client_secret)
            self._ctx = ClientContext(site_url).with_credentials(credentials)

            # Test the connection by getting web info
            web = self._ctx.web
            self._ctx.load(web)
            self._ctx.execute_query()

            logger.debug(f"Connected to SharePoint site: {web.properties['Title']}")
        except Exception as e:
            if "unauthorized" in str(e).lower() or "401" in str(e):
                raise AuthenticationError(
                    f"Failed to authenticate to SharePoint. "
                    f"Check client_id, client_secret, and tenant_id. Error: {e}"
                ) from e
            raise StorageError(f"Failed to connect to SharePoint: {e}") from e

    def list_files(self, folder_path: str) -> list[dict]:
        """List files in a SharePoint folder.

        Args:
            folder_path: Path to the folder (e.g., "Shared Documents/Reports")

        Returns:
            List of dictionaries with file information:
            - name: File name
            - path: Full server-relative path
            - size: File size in bytes
            - modified: Last modified datetime
        """
        try:
            folder = self._ctx.web.get_folder_by_server_relative_path(folder_path)
            files = folder.files
            self._ctx.load(files)
            self._ctx.execute_query()

            result = []
            for file in files:
                result.append({
                    "name": file.properties.get("Name"),
                    "path": file.properties.get("ServerRelativeUrl"),
                    "size": file.properties.get("Length"),
                    "modified": file.properties.get("TimeLastModified"),
                })

            logger.debug(f"Listed {len(result)} files in {folder_path}")
            return result

        except Exception as e:
            raise StorageError(f"Failed to list files in '{folder_path}': {e}") from e

    def list_folders(self, folder_path: str) -> list[dict]:
        """List subfolders in a SharePoint folder.

        Args:
            folder_path: Path to the parent folder

        Returns:
            List of dictionaries with folder information:
            - name: Folder name
            - path: Full server-relative path
        """
        try:
            folder = self._ctx.web.get_folder_by_server_relative_path(folder_path)
            folders = folder.folders
            self._ctx.load(folders)
            self._ctx.execute_query()

            result = []
            for f in folders:
                result.append({
                    "name": f.properties.get("Name"),
                    "path": f.properties.get("ServerRelativeUrl"),
                })

            logger.debug(f"Listed {len(result)} folders in {folder_path}")
            return result

        except Exception as e:
            raise StorageError(f"Failed to list folders in '{folder_path}': {e}") from e

    def download_file(self, file_path: str) -> bytes:
        """Download a file from SharePoint.

        Args:
            file_path: Server-relative path to the file
                      (e.g., "Shared Documents/Reports/Q4.xlsx")

        Returns:
            File contents as bytes
        """
        try:
            from office365.sharepoint.files.file import File

            file = File.open_binary(self._ctx, file_path)

            if hasattr(file, 'content'):
                content = file.content
            else:
                # Fallback for different library versions
                content = file

            logger.debug(f"Downloaded file: {file_path} ({len(content)} bytes)")
            return content

        except Exception as e:
            raise StorageError(f"Failed to download file '{file_path}': {e}") from e

    def upload_file(
        self,
        folder_path: str,
        file_name: str,
        content: bytes | BinaryIO,
    ) -> str:
        """Upload a file to SharePoint.

        Args:
            folder_path: Path to the destination folder
                        (e.g., "Shared Documents/Outputs")
            file_name: Name for the uploaded file
            content: File content as bytes or file-like object

        Returns:
            Server-relative URL of the uploaded file
        """
        try:
            # Get the target folder
            folder = self._ctx.web.get_folder_by_server_relative_path(folder_path)

            # Handle file-like objects
            if hasattr(content, 'read'):
                content = content.read()

            # Upload the file
            file = folder.upload_file(file_name, content).execute_query()

            file_url = file.properties.get("ServerRelativeUrl", f"{folder_path}/{file_name}")
            logger.debug(f"Uploaded file: {file_url}")
            return file_url

        except Exception as e:
            raise StorageError(
                f"Failed to upload file '{file_name}' to '{folder_path}': {e}"
            ) from e

    def delete_file(self, file_path: str) -> None:
        """Delete a file from SharePoint.

        Args:
            file_path: Server-relative path to the file
        """
        try:
            file = self._ctx.web.get_file_by_server_relative_path(file_path)
            file.delete_object()
            self._ctx.execute_query()
            logger.debug(f"Deleted file: {file_path}")

        except Exception as e:
            raise StorageError(f"Failed to delete file '{file_path}': {e}") from e

    def file_exists(self, file_path: str) -> bool:
        """Check if a file exists in SharePoint.

        Args:
            file_path: Server-relative path to the file

        Returns:
            True if the file exists, False otherwise
        """
        try:
            file = self._ctx.web.get_file_by_server_relative_path(file_path)
            self._ctx.load(file)
            self._ctx.execute_query()
            return file.properties.get("Exists", False)

        except Exception:
            return False

    def create_folder(self, folder_path: str) -> str:
        """Create a folder in SharePoint.

        Args:
            folder_path: Path for the new folder
                        (e.g., "Shared Documents/NewFolder")

        Returns:
            Server-relative URL of the created folder
        """
        try:
            # Get parent folder path and new folder name
            parts = folder_path.rsplit("/", 1)
            if len(parts) == 2:
                parent_path, folder_name = parts
            else:
                parent_path = ""
                folder_name = folder_path

            parent_folder = self._ctx.web.get_folder_by_server_relative_path(parent_path)
            new_folder = parent_folder.folders.add(folder_name)
            self._ctx.execute_query()

            folder_url = new_folder.properties.get("ServerRelativeUrl", folder_path)
            logger.debug(f"Created folder: {folder_url}")
            return folder_url

        except Exception as e:
            raise StorageError(f"Failed to create folder '{folder_path}': {e}") from e
