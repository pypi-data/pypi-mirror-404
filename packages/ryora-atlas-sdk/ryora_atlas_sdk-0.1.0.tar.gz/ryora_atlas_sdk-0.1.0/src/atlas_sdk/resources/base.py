"""Base classes and protocols for resource abstractions.

This module provides the foundational building blocks for the resource pattern:
- HTTPClientProtocol: Interface for HTTP operations (dependency injection)
- Resource: Base class for all resource wrappers with refresh/save/delete support
- ResourceManager: Base class for resource managers providing get/list operations
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Generic,
    Protocol,
    TypeVar,
    cast,
    runtime_checkable,
)
from uuid import UUID

import httpx
from pydantic import BaseModel

if TYPE_CHECKING:
    pass


# Type variable for Pydantic model types
ModelT = TypeVar("ModelT", bound=BaseModel)

# Type variable for Resource types (used in ResourceManager)
ResourceT = TypeVar("ResourceT", bound="Resource[Any]")


@runtime_checkable
class HTTPClientProtocol(Protocol):
    """Protocol defining the HTTP interface for resource operations.

    This protocol enables dependency injection, allowing resource classes
    to be tested independently of the actual HTTP client implementation.

    Implementations must provide:
    - `_request()`: Make an HTTP request with retry logic and instrumentation
    - `_raise_for_status()`: Raise appropriate Atlas error for failed responses

    Example:
        class MockHTTPClient:
            async def _request(self, method: str, url: str, **kwargs) -> httpx.Response:
                # Return mock response
                ...

            def _raise_for_status(self, response: httpx.Response) -> None:
                response.raise_for_status()
    """

    async def _request(
        self, method: str, url: str, request_id: str | None = None, **kwargs: Any
    ) -> httpx.Response:
        """Make an HTTP request.

        Args:
            method: HTTP method (GET, POST, PATCH, DELETE, etc.)
            url: URL path (relative to base_url)
            request_id: Optional request ID for distributed tracing
            **kwargs: Additional arguments passed to the HTTP client

        Returns:
            The HTTP response object.
        """
        ...

    def _raise_for_status(self, response: httpx.Response) -> None:
        """Raise appropriate Atlas error if response indicates failure.

        Args:
            response: The HTTP response to check.

        Raises:
            AtlasAPIError: (or appropriate subclass) if response indicates error.
        """
        ...


class Resource(ABC, Generic[ModelT]):
    """Base class for all resource wrappers.

    A Resource wraps a Pydantic model and provides bound methods for:
    - `refresh()`: Re-fetch the resource from the server
    - `save()`: Persist local changes to the server
    - `delete()`: Delete the resource from the server

    Resource instances expose the underlying model's fields as read-only
    attributes for convenient access. Field access is automatically delegated
    to the underlying Pydantic model via `__getattr__`.

    Args:
        data: The Pydantic model data for this resource.
        client: The HTTP client protocol for making requests.

    Example:
        deployment = await client.deployments.get(deployment_id)

        # Access model fields directly (delegated to _data)
        print(deployment.name)
        print(deployment.status)

        # Modify and save
        deployment.data.name = "new-name"
        await deployment.save()

        # Refresh from server
        await deployment.refresh()

        # Delete
        await deployment.delete()
    """

    # Fields on the underlying model that should be delegated via __getattr__.
    # Subclasses can extend this set if needed. If empty, all model fields
    # are delegated.
    _delegated_fields: frozenset[str] = frozenset()

    def __init__(self, data: ModelT, client: HTTPClientProtocol) -> None:
        """Initialize the resource.

        Args:
            data: The Pydantic model data for this resource.
            client: The HTTP client protocol for making requests.
        """
        self._data = data
        self._client = client

    def __getattr__(self, name: str) -> Any:
        """Delegate attribute access to the underlying Pydantic model.

        This enables convenient access to model fields without defining
        explicit properties for each field. Fields are accessed as read-only
        attributes on the resource.

        Args:
            name: The attribute name to look up.

        Returns:
            The value of the attribute from the underlying model.

        Raises:
            AttributeError: If the attribute does not exist on the model.
        """
        # Only delegate if the attribute exists on _data
        # Note: __getattr__ is only called when the attribute is not found
        # through normal means, so we don't need to check for _data/_client
        if hasattr(self._data, name):
            return getattr(self._data, name)
        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'"
        )

    @property
    def data(self) -> ModelT:
        """Get the underlying Pydantic model data.

        Returns:
            The raw Pydantic model instance.
        """
        return self._data

    @property
    def id(self) -> UUID:
        """Get the unique identifier for this resource.

        Returns:
            The UUID of this resource.
        """
        # All Resource subclasses have models with an 'id' field of type UUID
        return cast("UUID", self._data.id)  # type: ignore[attr-defined]

    @abstractmethod
    async def refresh(self) -> None:
        """Re-fetch this resource from the server.

        Updates the internal data with the latest state from the server.

        Raises:
            AtlasNotFoundError: If the resource no longer exists.
            AtlasAPIError: If the request fails.
        """
        ...

    @abstractmethod
    async def save(self) -> None:
        """Persist local changes to the server.

        Updates the server with any changes made to the resource data.

        Raises:
            AtlasValidationError: If the update data is invalid.
            AtlasNotFoundError: If the resource no longer exists.
            AtlasAPIError: If the request fails.
        """
        ...

    @abstractmethod
    async def delete(self) -> None:
        """Delete this resource from the server.

        After deletion, the resource should not be used further.

        Raises:
            AtlasNotFoundError: If the resource does not exist.
            AtlasAPIError: If the request fails.
        """
        ...

    def __repr__(self) -> str:
        """Return a string representation of the resource."""
        class_name = self.__class__.__name__
        return f"<{class_name} id={self.id}>"


class ResourceManager(Generic[ResourceT, ModelT], ABC):
    """Base class for resource managers providing common get/list operations.

    ResourceManager provides a consistent pattern for managing collections of
    resources with type-safe get and list operations. Subclasses configure
    the manager by setting class attributes and can override or extend behavior.

    Class Attributes:
        _resource_class: The Resource subclass to wrap returned data.
        _model_class: The Pydantic model class for parsing responses.
        _base_path: The API path prefix (e.g., "/api/v1/deployments").

    Args:
        client: The HTTP client protocol for making requests.

    Example:
        class DeploymentsResource(ResourceManager[Deployment, DeploymentRead]):
            _resource_class = Deployment
            _model_class = DeploymentRead
            _base_path = "/api/v1/deployments"

            async def list(self, *, environment: str | None = None, ...) -> list[Deployment]:
                params = self._build_list_params(limit=limit, offset=offset)
                if environment:
                    params["environment"] = environment
                return await self._list(params=params)
    """

    # Class attributes to be set by subclasses
    _resource_class: ClassVar[type[Resource[Any]]]
    _model_class: ClassVar[type[BaseModel]]
    _base_path: ClassVar[str]

    def __init__(self, client: HTTPClientProtocol) -> None:
        """Initialize the resource manager.

        Args:
            client: The HTTP client protocol for making requests.
        """
        self._client = client

    async def get(self, resource_id: UUID) -> ResourceT:
        """Get a resource by ID.

        Args:
            resource_id: The UUID of the resource to retrieve.

        Returns:
            The resource instance.

        Raises:
            AtlasNotFoundError: If the resource does not exist.
            AtlasAPIError: If the request fails.
        """
        resp = await self._client._request("GET", f"{self._base_path}/{resource_id}")
        self._client._raise_for_status(resp)
        data = self._model_class.model_validate(resp.json())
        return cast(ResourceT, self._resource_class(data, self._client))

    async def _list(
        self,
        *,
        path: str | None = None,
        params: dict[str, Any] | None = None,
    ) -> list[ResourceT]:
        """Internal helper for list operations.

        Subclasses should call this from their public list() method after
        building the appropriate parameters.

        Args:
            path: Optional custom API path. Defaults to _base_path.
            params: Query parameters for filtering/pagination.

        Returns:
            List of resource instances.

        Raises:
            AtlasAPIError: If the request fails.
        """
        resp = await self._client._request(
            "GET", path or self._base_path, params=params or {}
        )
        self._client._raise_for_status(resp)
        return [
            cast(
                ResourceT,
                self._resource_class(
                    self._model_class.model_validate(item), self._client
                ),
            )
            for item in resp.json()
        ]

    @staticmethod
    def _build_list_params(
        *,
        limit: int = 100,
        offset: int = 0,
        **extra: Any,
    ) -> dict[str, Any]:
        """Build standard pagination parameters.

        Args:
            limit: Maximum number of results to return. Defaults to 100.
            offset: Number of results to skip. Defaults to 0.
            **extra: Additional parameters to include.

        Returns:
            Dict of query parameters with None values filtered out.
        """
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        for key, value in extra.items():
            if value is not None:
                params[key] = value
        return params
