"""
Classes:
    APIClient: An asynchronous client for interacting with the API.
Methods:
    __init__(self, base_url: str = Config.BASE_URL, api_key: str | None = Config.API_KEY, mongodb_field_types: Optional[list] = None) -> None:
    _request(self, method: str, endpoint: str, **kwargs) -> dict:
    create_database(self, db_name: str, collections: list[dict]) -> dict:
        Create a new database with the specified collections.
    create_collection(self, database_id: str, collections: list[dict]) -> dict:
        Create new collections in the specified database.
    list_collections(self, database_id: str) -> dict:
        List all collections in the specified database.
    drop_collections(self, database_id: str, collection_names: list[str]) -> dict:
        Drop the specified collections from the database.
    drop_database(self, database_id: str) -> dict:
        Drop the specified database.
    create(self, database_id: str, collection_name: str, data: Union[dict, list[dict]]) -> dict:
        Create new documents in the specified collection.
    read(self, database_id: str, collection_name: str, filters: Optional[dict] = None, limit: int = 50, offset: int = 0) -> dict:
        Read documents from the specified collection.
    update(self, database_id: str, collection_name: str, filters: dict, update_data: dict) -> dict:
        Update documents in the specified collection.
    delete(self, database_id: str, collection_name: str, filters: dict, soft_delete: bool = True) -> dict:
        Delete documents from the specified collection.
    get_metadata(self, database_id: str) -> dict:
        Get metadata for the specified database.
    close(self):
        Close the HTTP client.

"""

import logging
from typing import Optional, Union

import httpx

from .endpoints import (CREATE_COLLECTION, CREATE_DATABASE, DATA_CRUD,
                        DROP_COLLECTIONS, DROP_DATABASE, GET_METADATA,
                        LIST_COLLECTIONS)
from .exceptions import APIError, ValidationError, map_status_code_to_exception
from .settings import Config
from .validators import (validate_collections, validate_database_name,
                         validate_object_id)

logger = logging.getLogger(__name__)


class APIClient:
    """
    An asynchronous client for interacting with the API.

    Attributes:
        base_url (str): The base URL of the API.
        api_key (str | None): The API key for authentication.
        client (httpx.AsyncClient): The async HTTP client for making requests.
        timeout (int): Timeout for requests in seconds.
    """

    def __init__(self, base_url: str = Config.BASE_URL,
                 api_key: str | None = Config.API_KEY,
                 mongodb_field_types: Optional[list] = None
                ) -> None:
        """
        Initialize the API client.

        Args:
            base_url (str): The base URL of the API.
            api_key (str | None): The API key for authentication.
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = 10
        self.mongodb_field_types = mongodb_field_types if mongodb_field_types is not None \
              else Config.MONGODB_FIELD_TYPES
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout)

    async def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        """
        Make an asynchronous HTTP request to the API.

        Args:
            method (str): The HTTP method (GET, POST, etc.).
            endpoint (str): The API endpoint.

        Returns:
            dict: The JSON response from the API.

        Raises:
            APIError: For general API errors.
        """
        url = f"{self.base_url}/{endpoint}"
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            response = await self.client.request(method, url, headers=headers, **kwargs)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise map_status_code_to_exception(response.status_code, response.json()) from e
        except httpx.RequestError as e:
            raise APIError(f"An error occurred while making a request: {e}") from e
        finally:
            self.close()

        try:
            return response.json()
        except ValueError as exc:
            raise APIError("Invalid JSON response from the API.", status_code=response.status_code) from exc

    async def create_database(self, db_name: str, collections: list[dict]) -> dict:
        """Create a new database with the specified collections."""
        validate_database_name(db_name)
        validate_collections(collections)

        payload = {"db_name": db_name, "collections": collections}
        return await self._request("POST", CREATE_DATABASE, json=payload)

    async def create_collection(self, database_id: str, collections: list[dict]) -> dict:
        """Create new collections in the specified database."""
        validate_object_id(database_id)
        validate_collections(collections)

        payload = {"database_id": database_id, "collections": collections}
        return await self._request("POST", CREATE_COLLECTION, json=payload)

    async def list_collections(self, database_id: str) -> dict:
        """List all collections in the specified database."""
        validate_object_id(database_id)

        params = {"database_id": database_id}
        return await self._request("GET", LIST_COLLECTIONS, params=params)

    async def drop_collections(self, database_id: str, collection_names: list[str]) -> dict:
        """Drop the specified collections from the database."""
        validate_object_id(database_id)

        if not isinstance(collection_names, list) or not all(isinstance(name, str) for name in collection_names):
            raise ValidationError("Collection names must be a list of non-empty strings.")

        payload = {"database_id": database_id, "collection_names": collection_names}
        return await self._request("DELETE", DROP_COLLECTIONS, json=payload)

    async def drop_database(self, database_id: str) -> dict:
        """Drop the specified database."""
        validate_object_id(database_id)

        payload = {"database_id": database_id}
        return await self._request("DELETE", DROP_DATABASE, json=payload)

    async def create(self, database_id: str, collection_name: str, data: Union[dict, list[dict]]) -> dict:
        """Create new documents in the specified collection."""
        validate_object_id(database_id)

        if not collection_name or not isinstance(collection_name, str):
            raise ValidationError("Collection name must be a non-empty string.")

        if isinstance(data, dict):
            data = [data]

        if not isinstance(data, list) or not all(isinstance(doc, dict) for doc in data):
            raise ValidationError("Data must be a dictionary or a list of dictionaries.")

        payload = {
            "database_id": database_id,
            "collection_name": collection_name,
            "data": data,
        }
        return await self._request("POST", DATA_CRUD, json=payload)

    async def read(self, database_id: str, collection_name: str, filters: Optional[dict] = None, limit: int = 50, offset: int = 0) -> dict:
        """Read documents from the specified collection."""
        validate_object_id(database_id)

        if not collection_name or not isinstance(collection_name, str):
            raise ValidationError("Collection name must be a non-empty string.")

        if filters and not isinstance(filters, dict):
            raise ValidationError("Filters must be a dictionary.")

        params = {
            "database_id": database_id,
            "collection_name": collection_name,
            "filters": filters,
            "limit": limit,
            "offset": offset
        }
        return await self._request("GET", DATA_CRUD, params=params)

    async def update(self, database_id: str, collection_name: str, filters: dict, update_data: dict) -> dict:
        """Update documents in the specified collection."""
        validate_object_id(database_id)

        if not collection_name or not isinstance(collection_name, str):
            raise ValidationError("Collection name must be a non-empty string.")

        if not filters or not isinstance(filters, dict):
            raise ValidationError("Filters must be a dictionary.")

        if not update_data or not isinstance(update_data, dict):
            raise ValidationError("Update data must be a dictionary.")

        payload = {
            "database_id": database_id,
            "collection_name": collection_name,
            "filters": filters,
            "update_data": update_data
        }
        return await self._request("PUT", DATA_CRUD, json=payload)

    async def delete(self, database_id: str, collection_name: str, filters: dict, soft_delete: bool = True) -> dict:
        """Delete documents from the specified collection."""
        validate_object_id(database_id)

        if not collection_name or not isinstance(collection_name, str):
            raise ValidationError("Collection name must be a non-empty string.")

        if not filters or not isinstance(filters, dict):
            raise ValidationError("Filters must be a dictionary.")

        payload = {
            "database_id": database_id,
            "collection_name": collection_name,
            "filters": filters,
            "soft_delete": soft_delete
        }
        return await self._request("DELETE", DATA_CRUD, json=payload)

    async def get_metadata(self, database_id: str) -> dict:
        """Get metadata for the specified database."""
        validate_object_id(database_id)

        params = {"database_id": database_id}
        return await self._request("GET", GET_METADATA, params=params)

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

