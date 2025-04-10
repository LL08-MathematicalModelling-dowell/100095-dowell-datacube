"""
This module contains views for handling database and
collection operations in the Datacube API.
"""

import os
import re
import asyncio
import logging
import json

from bson.objectid import InvalidId, ObjectId
from django.conf import settings
from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.views import APIView
from tenacity import retry, stop_after_attempt, wait_exponential
# from rest_framework.permissions import IsAuthenticated

from api.helpers import get_metadata_record
from api.serializers import (AddCollectionPOSTSerializer,
                             AddDatabasePOSTSerializer,
                             AsyncPostDocumentSerializer,
                             JSonImportSerializer,
    )
# from .models import Metadata





# Use the custom logger
logger = logging.getLogger('database_operations')

# Cache for database and collection validation
db_cache = {}
# Cache metadata to minimize database queries
metadata_cache = {}


def api_home(request):
    """
    View to render the home page listing all available API endpoints, descriptions, request bodies, and example responses.
    """
    from .api_home_data import apis

    return render(request, 'api_home.html', {'apis': apis})


class CreateDatabaseView(APIView):
    """
    API view to create a new database with specified collections and fields.
    Ensures atomicity and handles all-or-nothing transactions.
    """
    serializer_class = AddDatabasePOSTSerializer

    def post(self, request):
        """
        Handle POST request to create a new database with collections.
        
        Args:
            request: HTTP request containing database and collection details
            
        Returns:
            Response: Created database details or error message
        """
        try:
            # Validate request data
            serializer = AddDatabasePOSTSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data

            # Extract database name and collections
            db_name = validated_data.get('db_name', '').lower()
            collections = validated_data.get('collections', [])

            # Ensure at least one collection with fields is specified
            if not collections:
                return Response(
                    {"success": False, "message": "At least one collection with fields must be specified"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check if the database already exists
            if self.check_database_exists(db_name):
                return Response(
                    {"success": False, "message": f"Database '{db_name}' already exists!"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Start an atomic transaction
            cluster = settings.MONGODB_CLIENT
            session = cluster.start_session()
            session.start_transaction()

            try:
                # Insert metadata and initialize the database
                db_metadata = self.insert_metadata(db_name, collections, session)
                collection_metadata = asyncio.run(self.create_collections_in_db(db_metadata, collections, session))
                session.commit_transaction()

                response_data = {
                    "success": True,
                    "message": f"Database '{db_name}' and collections created successfully.",
                    "database": {
                        "name": db_metadata.get("database_name"),
                        "id": str(db_metadata.get("_id"))
                    },
                    "collections": collection_metadata
                }

                return Response(response_data, status=status.HTTP_201_CREATED)

            except (ValidationError, InvalidId, asyncio.TimeoutError) as inner_exception:
                session.abort_transaction()
                logger.error(f"Transaction aborted due to error: {inner_exception}", exc_info=True)
                self.rollback_collections(cluster[db_name], [coll['name'] for coll in collections])
                raise inner_exception

            finally:
                session.end_session()

        except (ValidationError, InvalidId) as e:
            logger.error(f"Validation error: {e}", exc_info=True)
            return Response(
                {"success": False, "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except asyncio.TimeoutError as e:
            logger.error(f"Timeout error: {e}", exc_info=True)
            return Response(
                {"success": False, "message": "Operation timed out"},
                status=status.HTTP_504_GATEWAY_TIMEOUT
            )

    def check_database_exists(self, db_name):
        """Check if the database already exists in metadata."""
        metadata_coll = settings.METADATA_COLLECTION
        return bool(metadata_coll.find_one({"database_name": db_name}))

    def insert_metadata(self, db_name, collections, session):
        """Insert metadata for the new database, including collections and fields."""
        metadata_coll = settings.METADATA_COLLECTION

        metadata = {
            "database_name": db_name,
            "collections": [
                {
                    "name": coll["name"],
                    "fields": [
                        {"name": field["name"], "type": field.get("type", "string")} for field in coll["fields"]
                    ]
                } for coll in collections
            ],
            "number_of_collections": len(collections),
        }
        result = metadata_coll.insert_one(metadata, session=session)
        metadata["_id"] = result.inserted_id
        return metadata

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=5))
    async def create_collections_in_db(self, db_metadata, collections, session):
        """Create specified collections with fields in the MongoDB database."""
        cluster = settings.MONGODB_CLIENT
        db = cluster[db_metadata["database_name"]]
        collection_metadata = []

        for coll in collections:
            collection_name = coll["name"]
            await asyncio.to_thread(db.create_collection, collection_name, session=session)
            logger.info(
                f"Created collection '{collection_name}' in database '{db_metadata['database_name']}'."
            )

            # Initialize each collection with an empty document containing the specified fields
            sample_doc = {field["name"]: None for field in coll["fields"]}
            result = await asyncio.to_thread(db[collection_name].insert_one, sample_doc, session=session)

            collection_metadata.append({
                "name": collection_name,
                "id": str(result.inserted_id),
                "fields": [
                    {"name": field["name"], "type": field.get("type", "string")} for field in coll["fields"]
                ]
            })

            logger.info(f"Inserted sample document with fields {[field['name'] for field in coll['fields']]} into collection '{collection_name}'.")

        return collection_metadata

    def rollback_collections(self, db, created_collections):
        """Rollback partially created collections."""
        for coll_name in created_collections:
            db.drop_collection(coll_name)
            logger.info(f"Rolled back collection '{coll_name}'")



'''
# # DONE
# class CreateDatabaseView(APIView):
#     """API view to create a new database and collections."""
#     permission_classes = [IsAuthenticated]
    
#     def post(self, request):
#         """
#         Handle POST request to create a new database and its collections.
#         """
#         data = request.data
#         db_name = data.get("db_name", "").lower()
#         collections = data.get("collections", [])

#         if not db_name or not collections:
#             return Response(
#                 {"success": False, "message": "Database name and collections are required."},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
        
#         # Get the user object from the API key (using the middleware)
#         user = request.user

#         try:
#             # Fetch or create the user's metadata
#             metadata, created = Metadata.objects.get_or_create(user_id=user.id)

#             # Check if the database already exists in the user's metadata
#             if db_name in metadata.databases:
#                 return Response(
#                     {"success": False, "message": f"Database '{db_name}' already exists in your account."},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )

#             # Start MongoDB operations (using old method)
#             cluster = settings.MONGODB_CLIENT
#             # db = cluster[db_name]

#             # Check if the database exists, create it if it doesn't exist
#             if db_name not in cluster.list_database_names():
#                 cluster[db_name].command("create")
#                 logger.info(f"Created database '{db_name}'.")

#             db = cluster[db_name]

#             # Create collections and their metadata
#             collection_metadata = []
#             for collection in collections:
#                 collection_name = collection.get("name")
#                 if collection_name not in db.list_collection_names():
#                     db.create_collection(collection_name)
#                     logger.info(f"Created collection '{collection_name}' in database '{db_name}'.")

#                     # Initialize the collection with sample data
#                     sample_doc = {field["name"]: None for field in collection.get("fields", [])}
#                     db[collection_name].insert_one(sample_doc)

#                     # Store collection metadata
#                     collection_metadata.append({
#                         "name": collection_name,
#                         "fields": collection.get("fields", [])
#                     })

#             # Update metadata (databases and collections)
#             metadata.databases.append(db_name)
#             metadata.collections.extend(collection_metadata)
#             metadata.number_of_databases += 1
#             metadata.number_of_collections += len(collections)
#             metadata.save()

#             return Response(
#                 {
#                     "success": True,
#                     "message": f"Database '{db_name}' and collections created successfully.",
#                     "database": db_name,
#                     "collections": collection_metadata
#                 },
#                 status=status.HTTP_201_CREATED
#             )

#         except Exception as e:
#             logger.error(f"Error creating database and collections: {e}", exc_info=True)
#             return Response(
#                 {"success": False, "message": str(e)},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )
'''


class AddCollectionView(APIView):
    """
    API view to handle adding new collections with defined document fields to an existing database.
    Ensures atomicity: all-or-nothing behavior for collection addition.
    """
    serializer_class = AddCollectionPOSTSerializer

    def post(self, request, *args, **kwargs):
        """
        Handles the POST request to add new collections to a specified database.
        Args:
            request (Request): The HTTP request object.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        Returns:
            Response: A Response object containing the result of the operation.
        Raises:
            Exception: If any error occurs during the process.
        The method performs the following steps:
        1. Validates the request data using AddCollectionPOSTSerializer.
        2. Extracts the database ID and collections from the validated data.
        3. Checks if the specified database exists.
        4. Starts an atomic transaction.
        5. Validates and filters the collections to be added.
        6. Adds new collections to the database metadata and the database itself.
        7. Commits the transaction if successful.
        8. Returns a success response with the details of the added collections and updated database metadata.
        9. Aborts the transaction and rolls back changes if any error occurs during the process.
        """
        
        try:
            # Validate the request data
            serializer = AddCollectionPOSTSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data

            # Extract database ID and collections
            database_id = data.get('database_id')
            collections = data.get('collections', [])

            # Check if the database exists
            db_metadata = self.check_database_exists(database_id)
            if not db_metadata:
                return Response(
                    {"success": False, "message": f"Database with ID '{database_id}' does not exist in Datacube"},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Start an atomic transaction
            cluster = settings.MONGODB_CLIENT
            session = cluster.start_session()
            session.start_transaction()

            try:
                # Validate and filter collections
                existing_collections, duplicates = self.validate_collections(db_metadata, collections)
                if duplicates:
                    session.abort_transaction()
                    return Response(
                        {"success": False, "message": f"Collections '{', '.join(duplicates)}' already exist"},
                        status=status.HTTP_409_CONFLICT
                    )

                # Add new collections to metadata and database
                new_collections = [coll for coll in collections if coll["name"] not in existing_collections]
                self.update_metadata(db_metadata, new_collections, session)
                collection_metadata = asyncio.run(self.create_collections_in_db(db_metadata, new_collections, session))

                # Commit the transaction
                session.commit_transaction()

                response_data = {
                    "success": True,
                    "message": f"Collections '{', '.join([coll['name'] for coll in new_collections])}' created successfully",
                    "collections": collection_metadata,
                    "database": {
                        "total_collections": len(db_metadata.get("collections", [])) + len(new_collections),
                        "total_fields": sum(len(coll["fields"]) for coll in db_metadata.get("collections", [])) + sum(len(coll["fields"]) for coll in new_collections)
                    }
                }

                return Response(response_data, status=status.HTTP_201_CREATED)

            except Exception as inner_exception:
                # Abort transaction on failure
                session.abort_transaction()
                logger.error(f"Transaction aborted due to error: {inner_exception}", exc_info=True)
                self.rollback_collections(cluster[db_metadata['database_name']], [coll['name'] for coll in new_collections])
                raise inner_exception

            finally:
                session.end_session()

        except Exception as e:
            logger.error(f"Error adding collections: {e}", exc_info=True)
            return Response(
                {"success": False, "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def check_database_exists(self, database_id):
        """Check if the database exists in the metadata collection."""
        metadata_coll = settings.METADATA_COLLECTION
        return metadata_coll.find_one({"_id": ObjectId(database_id)})

    def validate_collections(self, db_metadata, collections):
        """
        Validate and filter collections for the specified database.
        Returns existing collections and duplicates.
        """
        existing_collections = set(coll["name"] for coll in db_metadata.get("collections", []))
        duplicates = [coll["name"] for coll in collections if coll["name"] in existing_collections]

        for coll in collections:
            if len(coll["name"]) > 100:
                raise ValidationError(f"Collection name '{coll['name']}' exceeds maximum allowed length of 100 characters.")
            field_names = [field["name"] for field in coll["fields"]]
            if len(field_names) != len(set(field_names)):
                raise ValidationError(f"Duplicate field names detected in collection '{coll['name']}'. Fields must be unique.")

        return existing_collections, duplicates

    def update_metadata(self, db_metadata, new_collections, session):
        """Update metadata with the new collections and their fields."""
        metadata_coll = settings.METADATA_COLLECTION

        for coll in new_collections:
            collection_name = coll["name"]
            fields = [
                {"name": field["name"], "type": field.get("type", "string")} for field in coll["fields"]
            ]

            # Add new collection metadata
            metadata_coll.update_one(
                {"_id": db_metadata["_id"]},
                {
                    "$addToSet": {
                        "collections": {"name": collection_name, "fields": fields}
                    },
                    "$inc": {"number_of_collections": 1, "number_of_fields": len(fields)}
                },
                session=session
            )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=5))
    async def create_collections_in_db(self, db_metadata, new_collections, session):
        """Create new collections in the MongoDB database."""
        cluster = settings.MONGODB_CLIENT
        db = cluster[db_metadata["database_name"]]
        collection_metadata = []

        for coll in new_collections:
            collection_name = coll["name"]
            await asyncio.to_thread(db.create_collection, collection_name, session=session)
            logger.info(f"Created collection '{collection_name}' in database '{db_metadata['database_name']}'.")

            # Initialize each collection with an empty document containing the specified fields
            sample_doc = {field["name"]: None for field in coll["fields"]}
            result = await asyncio.to_thread(db[collection_name].insert_one, sample_doc, session=session)

            collection_metadata.append({
                "name": collection_name,
                "id": str(result.inserted_id),
                "fields": [
                    {"name": field["name"], "type": field.get("type", "string")} for field in coll["fields"]
                ]
            })

            logger.info(f"Inserted sample document with fields {[field['name'] for field in coll['fields']]} into collection '{collection_name}'.")

        return collection_metadata

    def rollback_collections(self, db, created_collections):
        """Rollback partially created collections."""
        for coll_name in created_collections:
            db.drop_collection(coll_name)
            logger.info(f"Rolled back collection '{coll_name}'")


class DataCrudView(APIView):
    """
    DataCrudView is a Django REST framework API view that provides CRUD operations for MongoDB collections.
    It handles HTTP POST, GET, PUT, and DELETE requests asynchronously.
    Methods:
        post(request, *args, **kwargs):
        get(request, *args, **kwargs):
            Handle GET requests asynchronously.
        put(request, *args, **kwargs):
            Handle PUT requests asynchronously.
        delete(request, *args, **kwargs):
            Handle DELETE requests asynchronously.
        async_post(request):
        async_get(request):
        async_put(request):
        async_delete(request):
        validate_collection(database_id, collection_name):
        get_collection_by_name(database_id, collection_name):
        convert_object_id(filters):
            Convert string ObjectIds in filters to actual ObjectId instances.
    """

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests asynchronously.

        Args:
            request: The HTTP request object.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            The result of the asynchronous post method.
        """
        return asyncio.run(self.async_post(request))

    def get(self, request, *args, **kwargs):
        """ Handle GET requests asynchronously. """
        return asyncio.run(self.async_get(request))

    def put(self, request, *args, **kwargs):
        return asyncio.run(self.async_put(request))

    def delete(self, request, *args, **kwargs):
        """
        Handle the DELETE request to delete a resource.
        This method runs the asynchronous delete operation using asyncio.run.
        Args:
            request: The HTTP request object.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        Returns:
            The result of the asynchronous delete operation.
        """

        return asyncio.run(self.async_delete(request))

    async def async_post(self, request):
        """
        Handle asynchronous POST requests to insert documents into a MongoDB collection.
        Args:
            request (Request): The request object containing the data to be inserted.
        Returns:
            Response: A response object indicating the success or failure of the operation.
        Raises:
            Exception: If there is an error during the database operation.
        The request data should include:
            - database_id (str): The ID of the database.
            - collection_name (str): The name of the collection.
            - data (list): A list of documents to be inserted.
        The response will include:
            - success (bool): Whether the operation was successful.
            - message (str): A message indicating the result of the operation.
            - inserted_ids (list): A list of IDs of the inserted documents (if successful).
        """

        serializer = AsyncPostDocumentSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"success": False, "message": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        validated_data = serializer.validated_data
        database_id = validated_data["database_id"]
        collection_name = validated_data["collection_name"]
        documents = validated_data["data"]

        try:
            # Fetch the collection object
            collection = await self.get_collection_by_name(database_id, collection_name)
            session = await asyncio.to_thread(settings.MONGODB_CLIENT.start_session)

            with session:
                session.start_transaction()
                try:
                    # Insert documents
                    result = await asyncio.to_thread(
                        collection.insert_many, documents, session=session
                    )
                    session.commit_transaction()
                except Exception as e:
                    session.abort_transaction()
                    raise e

            return Response(
                {
                    "success": True,
                    "message": "Documents inserted successfully",
                    "inserted_ids": [str(id) for id in result.inserted_ids]
                },
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            logger.error("Error in POST operation: %s", e)
            return Response(
                {"success": False, "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
    async def async_get(self, request):
        """
        Asynchronously handles GET requests to fetch data from a specified collection in the database.

        Args:
            request (Request): The request object containing query parameters.

        Returns:
            Response: A response object containing the fetched data, pagination details, and success status.

        Query Parameters:
            - database_id (str): The ID of the database to query.
            - collection_name (str): The name of the collection to query.
            - filters (str, optional): JSON string of filters to apply to the query. Defaults to "{}".
            - page (int, optional): The page number to return. Defaults to 1.
            - page_size (int, optional): The maximum number of records to return per page. Defaults to 50.

        Response:
            - success (bool): Indicates whether the data was fetched successfully.
            - message (str): A message describing the result of the operation.
            - data (list): A list of documents fetched from the collection.
            - pagination (dict): Pagination details including total records, current page, and page size.
        
        Raises:
            Exception: If an error occurs during the GET operation.
        """
        try:
            # Extract query parameters with default values
            data = request.query_params
            database_id = data.get("database_id")
            collection_name = data.get("collection_name")
            filters = data.get("filters", "{}")
            page = int(data.get("page", 1))       # Use 'page' parameter for pagination
            page_size = int(data.get("page_size", 50))  # Use 'page_size' for limiting results

            if page < 1 or page_size < 1:
                raise ValueError("Page and page_size must be positive integers")
            if not database_id or not collection_name:
                raise ValueError("Database ID and collection name are required")

            # Load filters safely
            filters = self.load_filters(filters)


            # Validate database and collection names
            valid_fields = await self.validate_collection(database_id, collection_name)
            
            # Filter valid fields and ensure 'is_deleted' is included
            filters = {key: value for key, value in filters.items() if key in valid_fields or key == "is_deleted"}
            filters["is_deleted"] = filters.get("is_deleted", False)


            # Access collection and perform database operations
            collection = await self.get_collection_by_name(database_id, collection_name)
            total_count = await asyncio.to_thread(collection.count_documents, filters)

            # Calculate pagination values
            start = (page - 1) * page_size
            cursor = collection.find(filters).skip(start).limit(page_size)
            results = await asyncio.to_thread(list, cursor)

            # Convert ObjectId to string for JSON serialization
            self.convert_ids_to_string(results)

            # Prepare paginated response
            return Response({
                "success": True,
                "message": "Data fetched successfully" if results else "No data found",
                "data": results,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total_count,
                    "total_pages": (total_count // page_size) + (1 if total_count % page_size > 0 else 0)
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error in GET operation: {e}")
            return Response({"success": False, "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def load_filters(self, filters):
        """
        Safely load and parse filter parameters from a JSON string.
        
        Args:
            filters (str): JSON string of filters.

        Returns:
            dict: Parsed filters as a dictionary.
        """
        try:
            filters = json.loads(filters)
        except json.JSONDecodeError:
            filters = {}
        return self.convert_object_id(filters)

    def convert_ids_to_string(self, results):
        """
        Convert MongoDB ObjectId to string for JSON serialization.

        Args:
            results (list): List of documents fetched from the database.

        Returns:
            None: Results are modified in place.
        """
        for doc in results:
            doc["_id"] = str(doc["_id"])

    # async def async_get(self, request):
    #     """
    #     Asynchronously handles GET requests to fetch data from a specified collection in the database.
    #     Args:
    #         request (Request): The request object containing query parameters.
    #     Returns:
    #         Response: A response object containing the fetched data, pagination details, and success status.
    #     Query Parameters:
    #         - database_id (str): The ID of the database to query.
    #         - collection_name (str): The name of the collection to query.
    #         - filters (str, optional): JSON string of filters to apply to the query. Defaults to "{}".
    #         - limit (int, optional): The maximum number of records to return. Defaults to 50.
    #         - offset (int, optional): The number of records to skip. Defaults to 0.
    #     Response:
    #         - success (bool): Indicates whether the data was fetched successfully.
    #         - message (str): A message describing the result of the operation.
    #         - data (list): A list of documents fetched from the collection.
    #         - pagination (dict): Pagination details including total records, current page, and page size.
    #     Raises:
    #         Exception: If an error occurs during the GET operation.
    #     """

    #     try:
    #         data = request.query_params
    #         database_id = data.get("database_id")
    #         collection_name = data.get("collection_name")
            
    #         import json

    #         filters = data.get("filters", "{}")
    #         if isinstance(filters, str):
    #             try:
    #                 filters = json.loads(filters)
    #             except json.JSONDecodeError:
    #                 filters = {}
    #         filters = self.convert_object_id(filters)

    #         limit = int(data.get("limit", 50))
    #         offset = int(data.get("offset", 0))

    #         valid_fields = await self.validate_collection(database_id, collection_name)
    #         filters = {key: value for key, value in filters.items() if key in valid_fields or key == "is_deleted"}

    #         filters["is_deleted"] = filters.get("is_deleted", False)
    #         collection = await self.get_collection_by_name(database_id, collection_name)
    #         total_count = await asyncio.to_thread(collection.count_documents, filters)

    #         cursor = collection.find(filters).skip(offset).limit(limit)
    #         results = await asyncio.to_thread(list, cursor)
    #         for doc in results:
    #             doc["_id"] = str(doc["_id"])

    #         return Response({
    #             "success": True,
    #             "message": "Data fetched successfully" if results else "No data found",
    #             "data": results,
    #             "pagination": {
    #                 "total_records": total_count,
    #                 "current_page": (offset // limit) + 1,
    #                 "page_size": limit
    #             }
    #         }, status=status.HTTP_200_OK)

    #     except Exception as e:
    #         logger.error(f"Error in GET operation: {e}")
    #         return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    async def async_put(self, request):
        """
        Asynchronous PUT method to update documents in a MongoDB collection.
        Args:
            request (Request): The request object containing the data for the update operation.
        Returns:
            Response: A response object indicating the success or failure of the update operation.
        Raises:
            ValueError: If any of the fields in the update data are invalid.
            Exception: If any error occurs during the update operation.
        The request data should contain the following keys:
            - database_id (str): The ID of the database.
            - collection_name (str): The name of the collection.
            - filters (dict): The filters to select the documents to be updated.
            - update_data (dict): The data to update the selected documents with.
        The method performs the following steps:
            1. Extracts the data from the request.
            2. Validates the fields in the update data.
            3. Retrieves the collection by name.
            4. Starts a MongoDB session and transaction.
            5. Updates the documents in the collection.
            6. Commits the transaction if successful, otherwise aborts the transaction.
            7. Returns a response indicating the number of documents updated or an error message.
        """

        try:
            data = request.data
            database_id = data.get("database_id")
            collection_name = data.get("collection_name")
            filters = self.convert_object_id(data.get("filters", {}))
            updates = data.get("update_data", {})

            valid_fields = await self.validate_collection(database_id, collection_name)
            invalid_fields = [key for key in updates if key not in valid_fields]
            if invalid_fields:
                raise ValueError(f"Invalid fields: {', '.join(invalid_fields)}")

            collection = await self.get_collection_by_name(database_id, collection_name)
            session = await asyncio.to_thread(settings.MONGODB_CLIENT.start_session)
            with session:
                session.start_transaction()
                try:
                    result = await asyncio.to_thread(collection.update_many, filters, {"$set": updates}, session=session)
                    session.commit_transaction()
                except Exception as e:
                    session.abort_transaction()
                    raise e

            return Response({
                "success": True,
                "message": f"{result.modified_count} documents updated successfully"
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error in PUT operation: {e}")
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    async def async_delete(self, request):
        """
        Asynchronously deletes documents from a MongoDB collection based on provided filters.
        Args:
            request (Request): The request object containing the data for the delete operation.
        Returns:
            Response: A response object containing the success status and a message.
        Raises:
            Exception: If an error occurs during the delete operation.
        Request Data:
            - database_id (str): The ID of the database.
            - collection_name (str): The name of the collection.
            - filters (dict, optional): The filters to apply for selecting documents to delete. Defaults to an empty dict.
            - soft_delete (bool, optional): If True, performs a soft delete by setting `is_deleted` to True. If False, performs a hard delete. Defaults to True.
        Response:
            - success (bool): Indicates whether the operation was successful.
            - message (str): A message describing the result of the operation.
        """

        try:
            data = request.data
            database_id = data.get("database_id")
            collection_name = data.get("collection_name")
            filters = self.convert_object_id(data.get("filters", {}))
            soft_delete = data.get("soft_delete", True)

            collection = await self.get_collection_by_name(database_id, collection_name)
            session = await asyncio.to_thread(settings.MONGODB_CLIENT.start_session)
            with session:
                session.start_transaction()
                try:
                    if soft_delete:
                        result = await asyncio.to_thread(collection.update_many, filters, {"$set": {"is_deleted": True}}, session=session)
                        message = f"{result.modified_count} documents soft-deleted successfully"
                    else:
                        result = await asyncio.to_thread(collection.delete_many, filters, session=session)
                        message = f"{result.deleted_count} documents hard-deleted successfully"
                    session.commit_transaction()
                except Exception as e:
                    session.abort_transaction()
                    raise e

            return Response({
                "success": True,
                "message": message
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error in DELETE operation: {e}")
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    async def validate_collection(self, database_id, collection_name):
        """
        Validate the existence of a collection within a specified database and return its field names.
        Args:
            database_id (str): The ID of the database to validate.
            collection_name (str): The name of the collection to validate.
        Returns:
            list: A list of field names in the specified collection.
        Raises:
            ValueError: If the database with the given ID does not exist.
            ValueError: If the collection with the given name does not exist in the specified database.
        """
        metadata_coll = settings.METADATA_COLLECTION
        db_metadata = await asyncio.to_thread(metadata_coll.find_one, {"_id": ObjectId(database_id)})


        if not db_metadata:
            raise ValueError(f"Database with ID '{database_id}' does not exist.")
        
        try:
            coll_metadata = next((coll for coll in db_metadata["collections_metadata"] if coll["name"] == collection_name), None)
        except Exception:
            coll_metadata = next((coll for coll in db_metadata["collections"] if coll["name"] == collection_name), None)

        if not coll_metadata:
            raise ValueError(f"Collection '{collection_name}' does not exist in the specified database.")
    
        try:
            return [field["name"] for field in coll_metadata["fields"]]
        except Exception:
            return [field for field in coll_metadata["fields"]]

    async def get_collection_by_name(self, database_id, collection_name):
        """
        Retrieve a MongoDB collection by its name from a specified database.
        Args:
            database_id (str): The ID of the database to search within.
            collection_name (str): The name of the collection to retrieve.
        Returns:
            Collection: The MongoDB collection object.
        Raises:
            ValueError: If the database with the specified ID does not exist.
            ValueError: If the collection with the specified name does not exist in the database.
        """

        metadata_coll = settings.METADATA_COLLECTION
        db_metadata = await asyncio.to_thread(metadata_coll.find_one, {"_id": ObjectId(database_id)})

        if not db_metadata:
            raise ValueError(f"Database with ID '{database_id}' does not exist.")

        try:
            if not any(coll["name"] == collection_name for coll in db_metadata["collections_metadata"]):
                raise ValueError(f"Collection '{collection_name}' does not exist in the specified database.")
        except Exception:
            if not any(coll["name"] == collection_name for coll in db_metadata["collections"]):
                raise ValueError(f"Collection '{collection_name}' does not exist in the specified database.")

        return settings.MONGODB_CLIENT[db_metadata["database_name"]][collection_name]

    def convert_object_id(self, filters):
        """Convert string ObjectIds in filters to actual ObjectId instances."""
        for key, value in filters.items():
            if key in ["_id", "id"] and isinstance(value, str):
                try:
                    filters[key] = ObjectId(value)
                except Exception as e:
                    logger.warning(f"Invalid ObjectId format for key '{key}': {value}. Error: {e}")
                    pass
        return filters


# DONE
class ListDatabasesView(APIView):
    """
    API view to list all databases in the MongoDB cluster, with optional pagination, filtering, and metadata.
    """

    def get(self, request, *args, **kwargs):
        """
        Handles GET requests to list databases with pagination and filtering.
        """
        try:
            # Extract pagination and filtering parameters
            page = int(request.query_params.get("page", 1))
            page_size = int(request.query_params.get("page_size", 50))
            filter_term = request.query_params.get("filter", "")

            # Fetch database metadata including IDs
            db_list = asyncio.run(self.get_database_metadata_from_metadata_collection(filter_term))

            # Pagination logic
            start = (page - 1) * page_size
            end = start + page_size
            paginated_dbs = db_list[start:end]

            # Fetch metadata for each paginated database
            db_info = asyncio.run(self.get_database_metadata(paginated_dbs))

            # Prepare paginated response
            return Response(
                {
                    "success": True,
                    "message": "Databases listed successfully",
                    "data": db_info,
                    "pagination": {
                        "page": page,
                        "page_size": page_size,
                        "total": len(db_list)
                    }
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"success": False, "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_database_metadata_from_metadata_collection(self, filter_term):
        """Fetch all database metadata including ID and name from the metadata collection."""
        metadata_coll = settings.METADATA_COLLECTION

        # Fetch database metadata from the metadata collection
        dbs = await asyncio.to_thread(lambda: list(metadata_coll.find({}, {"_id": 1, "database_name": 1})))

        # Apply filtering
        if filter_term:
            dbs = [db for db in dbs if filter_term.lower() in db["database_name"].lower()]

        # Convert ObjectId to string for serialization
        return [{"id": str(db["_id"]), "name": db["database_name"]} for db in dbs]

    async def get_database_metadata(self, db_list):
        """Fetch metadata for each database, including collection counts."""
        cluster = settings.MONGODB_CLIENT
        db_info = []

        # Fetch metadata for each database
        for db in db_list:
            try:
                num_collections = await asyncio.to_thread(lambda: len(cluster[db["name"]].list_collection_names()))
                db_info.append({
                    "id": db["id"],  # Ensure the ID is included
                    "name": db["name"],
                    "num_collections": num_collections
                })
            except Exception:
                db_info.append({
                    "id": db["id"],
                    "name": db["name"],
                    "num_collections": "Error fetching metadata"
                })
        return db_info


class ListCollectionsView(APIView):
    """
    API view to list all collections for a given database in Datacube using database ID.
    """

    def get(self, request, *args, **kwargs):
        """ Handle GET requests to list collections for a specified database. """
        try:
            # Extract database ID from query parameters
            database_id = request.query_params.get("database_id", "").strip()

            if not database_id:
                return Response(
                    {"success": False, "message": "Database ID is required", "data": []},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Ensure database_id is a valid ObjectId
            try:
                database_id = ObjectId(database_id)
            except Exception:
                return Response(
                    {"success": False, "message": "Invalid Database ID format"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Fetch metadata record for the specified database ID
            metadata_record = asyncio.run(self.get_metadata_record(database_id))
            if not metadata_record:
                return Response(
                    {
                        "success": False,
                        "message": f"Database with ID '{database_id}' does not exist in Datacube",
                        "data": []
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

            # Get actual collections from MongoDB
            actual_collections = asyncio.run(self.get_actual_collections_and_number_documents(metadata_record["database_name"]))

            if not actual_collections:
                return Response(
                    {
                        "success": False,
                        "message": f"No collections found for database with ID '{database_id}'",
                        "data": []
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

            return Response(
                {
                    "success": True,
                    "message": "Collections found!",
                    "collections": actual_collections
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"success": False, "message": str(e), "data": []},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_metadata_record(self, database_id):
        """Fetch metadata record for a given database ID."""
        metadata_coll = settings.METADATA_COLLECTION

        # Ensure database_id is a valid query format
        metadata_record = await asyncio.to_thread(lambda: metadata_coll.find_one({"_id": database_id}))

        return metadata_record

    async def get_actual_collections_and_number_documents(self, database_name):
        """Fetch the actual list of collections from MongoDB."""
        try:
            cluster = settings.MONGODB_CLIENT
            db = cluster[database_name]
            collections = await asyncio.to_thread(db.list_collection_names)
            collection_info = []

            for coll_name in collections:
                collection = db[coll_name]
                num_documents = await asyncio.to_thread(collection.count_documents, {})
                collection_info.append({"name": coll_name, "num_documents": num_documents})

            return collection_info

        except Exception as e:
            return []


class DropDatabaseView(APIView):
    """
    API view to safely drop a specified database with confirmation.
    Uses database ID for identification and ensures atomic operations.
    """

    def delete(self, request, *args, **kwargs):
        """
        Deletes a database only if the confirmation matches the database ID.
        Removes all collections, documents, and metadata associated with the database.
        """
        try:
            # Validate the request data
            database_id = request.data.get("database_id", "").strip()
            confirmation = request.data.get("confirmation", "").strip()

            if not database_id or not confirmation:
                return Response(
                    {"success": False, "message": "Database ID and confirmation are required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Ensure database_id is a valid ObjectId
            try:
                database_id = ObjectId(database_id)
            except InvalidId:
                return Response(
                    {"success": False, "message": "Invalid Database ID format"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check if the database exists
            metadata_record = asyncio.run(get_metadata_record(database_id))
            if not metadata_record:
                return Response(
                    {"success": False, "message": f"Database with ID '{database_id}' does not exist"},
                    status=status.HTTP_404_NOT_FOUND
                )

            db_name = metadata_record.get("database_name")

            # Ensure confirmation matches the database name
            if db_name.lower() != confirmation.lower():
                return Response(
                    {"success": False, "message": "Confirmation does not match database name"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Drop database and metadata in an atomic transaction
            dropped_collections_count = asyncio.run(self.drop_database_and_metadata(database_id, db_name))

            return Response(
                {
                    "success": True,
                    "message": f"Database '{db_name}' and associated metadata dropped successfully",
                    "details": {
                        "dropped_collections": dropped_collections_count
                    }
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(f"Error dropping database with ID '{request.data.get('database_id', 'unknown')}': {e}")
            return Response(
                {"success": False, "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def drop_database_and_metadata(self, database_id, db_name):
        """Remove metadata and drop the database and all its collections."""
        cluster = settings.MONGODB_CLIENT
        metadata_coll = settings.METADATA_COLLECTION
        dropped_collections_count = 0

        # Start an atomic transaction
        session = await asyncio.to_thread(cluster.start_session)
        with session:
            session.start_transaction()
            try:
                # Delete metadata
                await asyncio.to_thread(metadata_coll.delete_one, {"_id": database_id})

                # Drop collections and the database
                database = cluster[db_name]
                collections = await asyncio.to_thread(database.list_collection_names)
                for coll_name in collections:
                    await asyncio.to_thread(database[coll_name].drop)
                    dropped_collections_count += 1

                # Drop the database itself
                await asyncio.to_thread(lambda: cluster.drop_database(db_name))

                session.commit_transaction()
                logger.info(f"Database '{db_name}' dropped successfully with {dropped_collections_count} collections.")
                return dropped_collections_count

            except Exception as e:
                session.abort_transaction()
                logger.error(f"Error during transaction for dropping database '{db_name}': {e}")
                raise e


class DropCollectionsView(APIView):
    """
    API view to safely drop specified collections from a database.
    Uses database ID and collection names for identification and ensures atomic operations.
    """

    def delete(self, request, *args, **kwargs):
        """
        Deletes specified collections from a database.
        Requires database ID and a list of collection names.
        """
        try:
            # Validate the request data
            database_id = request.data.get("database_id", "").strip()
            collection_names = request.data.get("collection_names", [])

            if not database_id or not collection_names:
                return Response(
                    {"success": False, "message": "Database ID and collection names are required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Ensure database_id is a valid ObjectId
            try:
                database_id = ObjectId(database_id)
            except InvalidId:
                return Response(
                    {"success": False, "message": "Invalid Database ID format"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check if the database exists
            metadata_record = asyncio.run(get_metadata_record(database_id))
            if not metadata_record:
                return Response(
                    {"success": False, "message": f"Database with ID '{database_id}' does not exist"},
                    status=status.HTTP_404_NOT_FOUND
                )

            db_name = metadata_record.get("database_name")

            # Validate collection names
            existing_collections = [coll["name"] for coll in metadata_record.get("collections", [])]
            invalid_collections = set(collection_names) - set(existing_collections)
            if invalid_collections:
                return Response(
                    {
                        "success": False,
                        "message": f"The following collections do not exist in the database: {', '.join(invalid_collections)}",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Drop specified collections in an atomic transaction
            response_details = asyncio.run(self.drop_collections(database_id, db_name, collection_names))

            return Response(
                {
                    "success": True,
                    "message": f"Specified collections dropped successfully from database '{db_name}'",
                    "details": response_details,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Error dropping collections for database with ID '{request.data.get('database_id', 'unknown')}': {e}")
            return Response(
                {"success": False, "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    async def drop_collections(self, database_id, db_name, collection_names):
        """Remove specified collections from the database and update metadata."""
        cluster = settings.MONGODB_CLIENT
        metadata_coll = settings.METADATA_COLLECTION
        dropped_collections = []
        failed_collections = []

        # Start an atomic transaction
        session = await asyncio.to_thread(cluster.start_session)
        with session:
            session.start_transaction()
            try:
                # Drop collections from the database
                database = cluster[db_name]
                for coll_name in collection_names:
                    try:
                        if coll_name in await asyncio.to_thread(database.list_collection_names):
                            await asyncio.to_thread(database[coll_name].drop)
                            dropped_collections.append(coll_name)
                        else:
                            failed_collections.append(coll_name)
                    except Exception as e:
                        logger.error(f"Error dropping collection '{coll_name}': {e}")
                        failed_collections.append(coll_name)

                # Update metadata to remove dropped collections
                await asyncio.to_thread(
                    metadata_coll.update_one,
                    {"_id": database_id},
                    {"$pull": {"collections": {"name": {"$in": dropped_collections}}}},
                )

                session.commit_transaction()
                logger.info(f"Collections dropped successfully from database '{db_name}': {dropped_collections}")
                return {
                    "dropped_collections": dropped_collections,
                    "failed_collections": failed_collections,
                }

            except Exception as e:
                session.abort_transaction()
                logger.error(f"Error during transaction for dropping collections from database '{db_name}': {e}")
                raise e

    # async def drop_collections(self, database_id, db_name, collection_names):
    #     """Remove specified collections from the database and update metadata."""
    #     cluster = settings.MONGODB_CLIENT
    #     metadata_coll = settings.METADATA_COLLECTION
    #     dropped_collections_count = 0

    #     # Start an atomic transaction
    #     session = await asyncio.to_thread(cluster.start_session)
    #     with session:
    #         session.start_transaction()
    #         try:
    #             # Drop collections from the database
    #             database = cluster[db_name]
    #             for coll_name in collection_names:
    #                 if coll_name in await asyncio.to_thread(database.list_collection_names):
    #                     await asyncio.to_thread(database[coll_name].drop)
    #                     dropped_collections_count += 1

    #             # Update metadata to remove dropped collections
    #             await asyncio.to_thread(
    #                 metadata_coll.update_one,
    #                 {"_id": database_id},
    #                 {"$pull": {"collections": {"name": {"$in": collection_names}}}}
    #             )

    #             session.commit_transaction()
    #             logger.info(f"Collections '{', '.join(collection_names)}' dropped successfully from database '{db_name}'.")
    #             return dropped_collections_count

    #         except Exception as e:
    #             session.abort_transaction()
    #             logger.error(f"Error during transaction for dropping collections from database '{db_name}': {e}")
    #             raise e


class GetMetadataView(APIView):
    """
    API View to fetch metadata of a specific database using database ID as a query parameter.
    """

    def get(self, request, *args, **kwargs):
        """
        Handles GET requests to fetch metadata for a given database ID.
        Args:
            request (Request): The HTTP request object.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        Returns:
            Response: A DRF Response object containing the metadata or an error message.
        Raises:
            Exception: If an error occurs while fetching metadata.
        Responses:
            200 OK: If metadata is successfully fetched.
            400 Bad Request: If the database ID is missing or invalid.
            404 Not Found: If no metadata is found for the given database ID.
            500 Internal Server Error: If an error occurs while fetching metadata.
        """

        try:
            # Extract database ID from query parameters
            database_id = request.query_params.get("database_id", "").strip()

            if not database_id:
                return Response(
                    {"success": False, "message": "Database ID is required."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate database ID
            try:
                database_id = ObjectId(database_id)
            except InvalidId:
                return Response(
                    {"success": False, "message": "Invalid Database ID format."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Fetch metadata from the metadata collection
            metadata_coll = settings.METADATA_COLLECTION
            metadata = metadata_coll.find_one({"_id": database_id})

            if not metadata:
                return Response(
                    {"success": False, "message": f"No metadata found for database with ID '{database_id}'."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Convert ObjectId to string in the metadata
            metadata = self.convert_objectid_to_str(metadata)

            return Response(
                {"success": True, "data": metadata},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(f"Error fetching metadata for database ID '{database_id}': {e}", exc_info=True)
            return Response(
                {"success": False, "message": "An error occurred while fetching metadata."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def convert_objectid_to_str(self, data):
        """
        Recursively convert ObjectId instances to strings in the given data.
        """
        if isinstance(data, dict):
            return {k: self.convert_objectid_to_str(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.convert_objectid_to_str(item) for item in data]
        elif isinstance(data, ObjectId):
            return str(data)
        else:
            return data


class HealthCheck(APIView):
    """
    HealthCheck API view to check the server status.
    Methods:
        get(request):
            Handles GET requests to check if the server is running.
            Returns a JSON response with the server status.
            - If the server is running, returns HTTP 200 OK with a success message.
            - If there is an exception, returns HTTP 500 Internal Server Error with an error message.
    """
        
    def get(self, request, *args, **kwargs):
        """
        Handles GET requests to check server status.
        Args:
            request (Request): The HTTP request object.
        Returns:
            Response: A JSON response indicating whether the server is running fine or down, 
                      along with the appropriate HTTP status code.
        """

        try:
            return Response({
                "success": True,
                "message": "Server is running fine"
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "success": False,
                "message": f"Server is down for {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



def sanitize_collection_name(name):
    """
    Sanitize the provided collection name to be MongoDB compliant.
    Replaces non-word characters with underscores and converts the result to lowercase.
    """
    return re.sub(r"\W+", "_", name).lower()


class DatabaseMixin:
    """
    A mixin that provides common helper methods for working with the database metadata
    and collections.
    """

    def check_database_exists(self, database_id):
        """
        Check if the database exists in the metadata collection.
        Returns the metadata record if found, else None.
        """
        metadata_coll = settings.METADATA_COLLECTION
        try:
            db_obj_id = ObjectId(database_id)
        except InvalidId:
            raise ValueError("Invalid Database ID format")
        return metadata_coll.find_one({"_id": db_obj_id})

    async def create_collection_if_not_exists(self, db, collection_name):
        """
        Check if the collection exists in the given database.
        If not, create it, update the metadata with an empty fields list, and return the collection.
        """
        # List existing collection names in a thread to avoid blocking
        existing_collections = await asyncio.to_thread(db.list_collection_names)
        if collection_name not in existing_collections:
            # Create the collection in the database.
            await asyncio.to_thread(db.create_collection, collection_name)
            
            # Update the metadata for the database by adding the new collection.
            # Here, we assume that the metadata document is identified by the "database_name".
            # You can adjust the filtering criteria if necessary.
            metadata_coll = settings.METADATA_COLLECTION
            await asyncio.to_thread(
                metadata_coll.update_one,
                {"database_name": db.name},
                {
                    "$addToSet": {"collections": {"name": collection_name, "fields": []}},
                    "$inc": {"number_of_collections": 1}
                }
            )
            logger.info(f"Collection '{collection_name}' created in database '{db.name}' and metadata updated.")
        return db[collection_name]




class ImportDataView(APIView, DatabaseMixin):
    """
    API view to import data into a MongoDB collection from a JSON file.
    If no collection name is provided, a sanitized version of the JSON file name is used.
    If the collection does not exist, it is created.
    """

    def get_serializer_class(self, request, *args, **kwargs):
        """
        Returns the serializer class for the import data view.
        This can be overridden in subclasses to provide different serializers.
        """
        if request.method == "POST":
            return JSonImportSerializer
        return None


    def post(self, request, *args, **kwargs):
        """
        Handles POST requests to import data into a MongoDB collection from a JSON file. 
        """
        try:
            serializer = JSonImportSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            # Extract validated data.
            database_id = serializer.validated_data.get("database_id")
            collection_name = serializer.validated_data.get("collection_name")
            json_file = serializer.validated_data.get("json_file")

            # If no collection name is provided, generate one from the JSON file name.
            if not collection_name:
                filename = os.path.basename(getattr(json_file, "name", str(json_file)))
                name, _ = os.path.splitext(filename)
                collection_name = sanitize_collection_name(name)

            # Check if the database exists.
            try:
                db_metadata = self.check_database_exists(database_id)
            except ValueError as ve:
                return Response(
                    {"success": False, "message": str(ve)},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not db_metadata:
                return Response(
                    {
                        "success": False,
                        "message": f"Database with ID '{database_id}' does not exist"
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

            # Get the actual MongoDB database handle.
            db_name = db_metadata.get("database_name")
            db = settings.MONGODB_CLIENT[db_name]

            # Use the helper to get (or create) the collection.
            collection = asyncio.run(self.create_collection_if_not_exists(db, collection_name))

            # Read the JSON file.
            if hasattr(json_file, "read"):
                file_content = json_file.read()
                data = json.loads(file_content)
            else:
                with open(json_file, "r") as file:
                    data = json.load(file)

            inserted_count = self.insert_data_into_collection(collection, data)

            return Response(
                {
                    "success": True,
                    "message": f"{inserted_count} documents imported successfully into '{collection_name}'"
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Error importing data: {e}", exc_info=True)
            return Response(
                {"success": False, "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def insert_data_into_collection(self, collection, data):
        """
        Insert data into the specified MongoDB collection.
        If the data is not a list, it will be wrapped into a list.
        """
        if not isinstance(data, list):
            data = [data]

        # Run asynchronous insertion in a synchronous manner.
        result = asyncio.run(self.insert_data(collection, data))
        return len(result.inserted_ids) if result and result.inserted_ids else 0

    async def insert_data(self, collection, data):
        """
        Asynchronously insert data into the MongoDB collection.
        """
        try:
            result = await asyncio.to_thread(collection.insert_many, data)
            return result
        except Exception as e:
            logger.error(f"Error inserting data into collection: {e}", exc_info=True)
            raise e
