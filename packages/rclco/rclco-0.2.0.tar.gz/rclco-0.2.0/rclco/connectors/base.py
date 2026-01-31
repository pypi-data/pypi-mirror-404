"""Abstract base classes for all connectors."""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class BaseConnector(ABC, Generic[T]):
    """Abstract base class for all synchronous connectors.

    This class provides a consistent interface for all data connectors,
    including context manager support for automatic resource cleanup.

    Type parameter T represents the primary return type of the connector
    (e.g., pl.DataFrame for databases, dict for APIs, bytes for storage).

    Example:
        class MyConnector(BaseConnector[dict]):
            def connect(self) -> None:
                self._client = create_client()

            def disconnect(self) -> None:
                self._client.close()

        # Usage with context manager
        with MyConnector() as conn:
            data = conn.fetch_data()
    """

    @abstractmethod
    def connect(self) -> None:
        """Establish connection to the data source.

        This method should initialize any clients, connections, or sessions
        needed to interact with the data source.

        Raises:
            ConnectionError: If the connection cannot be established
        """
        ...

    @abstractmethod
    def disconnect(self) -> None:
        """Close the connection and release resources.

        This method should clean up any open connections, close clients,
        and release any held resources. It should be safe to call even
        if connect() was never called or failed.
        """
        ...

    def __enter__(self) -> "BaseConnector[T]":
        """Enter the context manager, establishing the connection."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the context manager, closing the connection."""
        self.disconnect()


class AsyncBaseConnector(ABC, Generic[T]):
    """Abstract base class for all asynchronous connectors.

    This class provides a consistent interface for async data connectors,
    including async context manager support for automatic resource cleanup.

    Type parameter T represents the primary return type of the connector.

    Example:
        class MyAsyncConnector(AsyncBaseConnector[dict]):
            async def connect(self) -> None:
                self._client = await create_async_client()

            async def disconnect(self) -> None:
                await self._client.close()

        # Usage with async context manager
        async with MyAsyncConnector() as conn:
            data = await conn.fetch_data()
    """

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to the data source asynchronously.

        Raises:
            ConnectionError: If the connection cannot be established
        """
        ...

    @abstractmethod
    async def disconnect(self) -> None:
        """Close the connection and release resources asynchronously."""
        ...

    async def __aenter__(self) -> "AsyncBaseConnector[T]":
        """Enter the async context manager, establishing the connection."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the async context manager, closing the connection."""
        await self.disconnect()
