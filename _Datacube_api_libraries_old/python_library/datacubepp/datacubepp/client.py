""" A client for interacting with the API. """

import logging
from typing import Optional, Union

import requests

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
    A client for interacting with the API.

    Attributes:
        base_url (str): The base URL of the API.
        api_key (str | None): The API key for authentication.
        session (requests.Session): The session object for HTTP requests.
        timeout (int): Timeout for requests in seconds.
    """

    def __init__(self, base_url: str = Config.BASE_URL,
                 api_key: str | None = Config.API_KEY,
                 MONGODB_FIELD_TYPES: list = Config.MONGODB_FIELD_TYPES
                 ) -> None:
        """
        Initialize the API client.

        Args:
            base_url (str): The base URL of the API.
            api_key (str | None): The API key for authentication.
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.session = requests.Session()
        self.timeout = 10
        self.MONGODB_FIELD_TYPES = MONGODB_FIELD_TYPES

    def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        """
        Make an HTTP request to the API.

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
            response = self.session.request(
                method, url, headers=headers, timeout=self.timeout, **kwargs
            )
        except requests.exceptions.RequestException as e:
            raise APIError(f"An error occurred while making a request: {e}") from e

        try:
            json_response = response.json()
        except ValueError as exc:
            raise APIError(
                "Invalid JSON response from the API.", 
                status_code=response.status_code
            ) from exc

        if not response.ok:
            raise map_status_code_to_exception(response.status_code, json_response)

        return json_response

    def create_database(self, db_name: str, collections: list[dict]) -> dict:
        """
        Create a new database.

        Args:
            db_name (str): The name of the database to create.
            collections (list[dict]): A list of collections with their fields.

        Returns:
            dict: The API response.

        Raises:
            ValidationError: If the database name or collections are invalid.
        """
        validate_database_name(db_name)
        validate_collections(collections)

        payload = {"db_name": db_name, "collections": collections}
        return self._request("POST", CREATE_DATABASE, json=payload)

    def create_collection(self, database_id: str, collections: list[dict]) -> dict:
        """
        Create a collection in the specified database.
        Args:
            database_id (str): The ID of the database where the collection will be created.
            collections (list[dict]): A list of dictionaries, each representing a collection to be created. 
                                      Each dictionary must have the following structure:
                                      - "name" (str): The name of the collection.
                                      - "fields" (list[dict]): A list of dictionaries, each representing a field in the collection.
                                        Each field dictionary must have:
                                        - "name" (str): The name of the field.
                                        - "type" (str, optional): The type of the field. Must be one of the valid MongoDB field types.
        Returns:
            dict: The response from the API request.
        Raises:
            ValidationError: If the database ID or collections structure is invalid.
        """
        
        # Validate the database ID
        validate_object_id(database_id)

        # Validate collections structure
        if not isinstance(collections, list) or not all(isinstance(c, dict) for c in collections):
            raise ValidationError("Collections must be a list of dictionaries.")

        for collection in collections:
            if "name" not in collection or not isinstance(collection["name"], str):
                raise ValidationError("Each collection must have a 'name' field as a non-empty string.")
            if "fields" not in collection or not isinstance(collection["fields"], list):
                raise ValidationError(f"Each collection must have a 'fields' field as a list.")
            for field in collection["fields"]:
                if "name" not in field or not isinstance(field["name"], str):
                    raise ValidationError("Each field must have a 'name' as a non-empty string.")
                if "type" in field and field["type"] not in self.MONGODB_FIELD_TYPES:
                    raise ValidationError(
                        f"Invalid field type '{field['type']}' in collection '{collection['name']}'."
                    )

        # Prepare the payload
        payload = {"database_id": database_id, "collections": collections}

        # Make the API request
        return self._request("POST", CREATE_COLLECTION, json=payload)

    def list_collections(self, database_id: str) -> dict:
        """
        List all collections in a database.

        Args:
            database_id (str): The ID of the database.

        Returns:
            dict: The API response.

        Raises:
            ValidationError: If the database ID is invalid.
        """
        validate_object_id(database_id)

        params = {"database_id": database_id}
        return self._request("GET", LIST_COLLECTIONS, params=params)

    def drop_collections(self, database_id: str, collection_names: list[str]) -> dict:
        """
        Drop collections from a database.

        Args:
            database_id (str): The ID of the database.
            collection_names (list[str]): The names of the collections to drop.

        Returns:
            dict: The API response.

        Raises:
            ValidationError: If the inputs are invalid.
        """
        validate_object_id(database_id)

        if not isinstance(collection_names, list)\
            or not all(isinstance(name, str)\
                for name in collection_names):
            raise ValidationError("Collection names must be a list of non-empty strings.")

        payload = {"database_id": database_id, "collection_names": collection_names}
        return self._request("DELETE", DROP_COLLECTIONS, json=payload)

    def drop_database(self, database_id: str) -> dict:
        """
        Drop a database.

        Args:
            database_id (str): The ID of the database to drop.

        Returns:
            dict: The API response.

        Raises:
            ValidationError: If the database ID is invalid.
        """
        validate_object_id(database_id)

        payload = {"database_id": database_id}
        return self._request("DELETE", DROP_DATABASE, json=payload)

    def create(self, database_id: str, collection_name: str, data: Union[dict, list[dict]]) -> dict:
        """
        Create documents in a collection.

        Args:
            database_id (str): The ID of the database.
            collection_name (str): The name of the collection.
            data (dict | list[dict]): The document(s) to create.

        Returns:
            dict: The API response.

        Raises:
            ValidationError: If the inputs are invalid.
        """
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
        return self._request("POST", DATA_CRUD, json=payload)

    def read(
            self, database_id: str,
            collection_name: str,
            filters: Optional[dict] = None,
            limit: int = 50,
            offset: int = 0
        ) -> dict:
        """
        Read documents from a collection.

        Args:
            database_id (str): The ID of the database.
            collection_name (str): The name of the collection.
            filters (Optional[dict]): Filters for querying documents.
            limit (int): The number of documents to retrieve.
            offset (int): The starting point for retrieval.

        Returns:
            dict: The API response.

        Raises:
            ValidationError: If the inputs are invalid.
        """
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
        return self._request("GET", DATA_CRUD, params=params)

    def update(self, database_id: str, collection_name: str, filters: dict, update_data: dict) -> dict:
        """
        Update documents in a collection.

        Args:
            database_id (str): The ID of the database.
            collection_name (str): The name of the collection.
            filters (dict): Filters for identifying documents to update.
            update_data (dict): The data to update the documents with.

        Returns:
            dict: The API response.

        Raises:
            ValidationError: If the inputs are invalid.
        """
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
        return self._request("PUT", DATA_CRUD, json=payload)

    def delete(self, database_id: str, collection_name: str, filters: dict, soft_delete: bool = True) -> dict:
        """
        Delete documents from a collection.

        Args:
            database_id (str): The ID of the database.
            collection_name (str): The name of the collection.
            filters (dict): Filters for identifying documents to delete.
            soft_delete (bool): Whether to perform a soft delete (default: True).

        Returns:
            dict: The API response.

        Raises:
            ValidationError: If the inputs are invalid.
        """
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
        return self._request("DELETE", DATA_CRUD, json=payload)

    def get_metadata(self, database_id: str) -> dict:
        """
        Get metadata for a database.

        Args:
            database_id (str): The ID of the database.

        Returns:
            dict: The API response.

        Raises:
            ValidationError: If the database ID is invalid.
        """
        validate_object_id(database_id)

        params = {"database_id": database_id}
        return self._request("GET", GET_METADATA, params=params)
