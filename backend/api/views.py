import asyncio
import logging

from rest_framework import status
from tenacity import retry, stop_after_attempt, wait_exponential

from django.conf import settings
from django.shortcuts import render
from rest_framework.views import APIView
from api.helpers import get_metadata_record
from rest_framework.response import Response
from bson.objectid import ObjectId, InvalidId
from rest_framework.serializers import ValidationError

from api.serializers import (
    AddCollectionPOSTSerializer,
    AddDatabasePOSTSerializer,
    GetMetadataSerializer,
)


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

    def post(self, request, *args, **kwargs):
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

                # Commit the transaction
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

            except Exception as inner_exception:
                # Abort transaction on failure
                session.abort_transaction()
                logger.error(f"Transaction aborted due to error: {inner_exception}", exc_info=True)
                self.rollback_collections(cluster[db_name], [coll['name'] for coll in collections])
                raise inner_exception

            finally:
                session.end_session()

        except Exception as e:
            logger.error(f"Error creating database: {e}", exc_info=True)
            return Response(
                {"success": False, "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
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


class AddCollectionView(APIView):
    """
    API view to handle adding new collections with defined document fields to an existing database.
    Ensures atomicity: all-or-nothing behavior for collection addition.
    """
    serializer_class = AddCollectionPOSTSerializer

    def post(self, request, *args, **kwargs):
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
    A streamlined view for CRUD operations on MongoDB collections using names with metadata validation.
    """

    def post(self, request, *args, **kwargs):
        return asyncio.run(self.async_post(request))

    def get(self, request, *args, **kwargs):
        return asyncio.run(self.async_get(request))

    def put(self, request, *args, **kwargs):
        return asyncio.run(self.async_put(request))

    def delete(self, request, *args, **kwargs):
        return asyncio.run(self.async_delete(request))

    async def async_post(self, request):
        try:
            data = request.data
            database_id = data.get("database_id")
            collection_name = data.get("collection_name")
            documents = data.get("data")

            if isinstance(documents, dict):
                documents = [documents]

            valid_fields = await self.validate_collection(database_id, collection_name)

            for doc in documents:
                invalid_fields = [key for key in doc if key not in valid_fields]
                if invalid_fields:
                    raise ValueError(f"Invalid fields: {', '.join(invalid_fields)}")

                doc["is_deleted"] = False

            collection = await self.get_collection_by_name(database_id, collection_name)
            session = await asyncio.to_thread(settings.MONGODB_CLIENT.start_session)
            with session:
                session.start_transaction()
                try:
                    result = await asyncio.to_thread(collection.insert_many, documents, session=session)
                    session.commit_transaction()
                except Exception as e:
                    session.abort_transaction()
                    raise e

            return Response({
                "success": True,
                "message": "Documents inserted successfully",
                "inserted_ids": [str(id) for id in result.inserted_ids]
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error in POST operation: {e}")
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
    async def async_get(self, request):
        try:
            data = request.query_params
            database_id = data.get("database_id")
            collection_name = data.get("collection_name")
            
            import json
            filters = data.get("filters", "{}")
            if isinstance(filters, str):
                try:
                    filters = json.loads(filters)
                except json.JSONDecodeError:
                    filters = {}
            filters = self.convert_object_id(filters)

            limit = int(data.get("limit", 50))
            offset = int(data.get("offset", 0))

            valid_fields = await self.validate_collection(database_id, collection_name)
            filters = {key: value for key, value in filters.items() if key in valid_fields or key == "is_deleted"}

            filters["is_deleted"] = filters.get("is_deleted", False)
            collection = await self.get_collection_by_name(database_id, collection_name)
            total_count = await asyncio.to_thread(collection.count_documents, filters)

            cursor = collection.find(filters).skip(offset).limit(limit)
            results = await asyncio.to_thread(list, cursor)
            for doc in results:
                doc["_id"] = str(doc["_id"])

            return Response({
                "success": True,
                "message": "Data fetched successfully" if results else "No data found",
                "data": results,
                "pagination": {
                    "total_records": total_count,
                    "current_page": (offset // limit) + 1,
                    "page_size": limit
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error in GET operation: {e}")
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    async def async_put(self, request):
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
        metadata_coll = settings.METADATA_COLLECTION
        db_metadata = await asyncio.to_thread(metadata_coll.find_one, {"_id": ObjectId(database_id)})

        if not db_metadata:
            raise ValueError(f"Database with ID '{database_id}' does not exist.")

        coll_metadata = next((coll for coll in db_metadata["collections"] if coll["name"] == collection_name), None)

        if not coll_metadata:
            raise ValueError(f"Collection '{collection_name}' does not exist in the specified database.")

        return [field["name"] for field in coll_metadata["fields"]]

    async def get_collection_by_name(self, database_id, collection_name):
        metadata_coll = settings.METADATA_COLLECTION
        db_metadata = await asyncio.to_thread(metadata_coll.find_one, {"_id": ObjectId(database_id)})

        if not db_metadata:
            raise ValueError(f"Database with ID '{database_id}' does not exist.")

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
        return filters


class ListDatabasesView(APIView):
    """
    API view to list all databases in the MongoDB cluster, with optional pagination, filtering, and metadata.
    """

    def get(self, request, *args, **kwargs):
        try:
            # Extract pagination and filtering parameters from query params
            page = int(request.query_params.get("page", 1))
            page_size = int(request.query_params.get("page_size", 10))
            filter_term = request.query_params.get("filter", "")

            # Run async functions to fetch database names and metadata
            db_names = asyncio.run(self.list_database_names(filter_term))

            # Pagination logic
            start = (page - 1) * page_size
            end = start + page_size
            paginated_dbs = db_names[start:end]

            # Fetch metadata for each paginated database
            db_info = asyncio.run(self.get_database_metadata(paginated_dbs))

            # Prepare paginated response with metadata
            return Response(
                {
                    "success": True,
                    "message": "Databases listed successfully",
                    "data": db_info,
                    "pagination": {
                        "page": page,
                        "page_size": page_size,
                        "total": len(db_names)
                    }
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(f"Error listing databases: {e}")
            return Response(
                {"success": False, "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def list_database_names(self, filter_term):
        """Fetch all database names, optionally filtered by a term."""
        cluster = settings.MONGODB_CLIENT

        # Fetch all database names
        db_names = await asyncio.to_thread(cluster.list_database_names)
        if filter_term:
            db_names = [db for db in db_names if filter_term.lower() in db.lower()]
        return db_names

    async def get_database_metadata(self, db_names):
        """Fetch metadata for each database, including collection counts."""
        cluster = settings.MONGODB_CLIENT
        db_info = []

        # Fetch metadata for each database
        for db_name in db_names:
            try:
                num_collections = await asyncio.to_thread(lambda: len(cluster[db_name].list_collection_names()))
                db_info.append({
                    "name": db_name,
                    "num_collections": num_collections
                })
            except Exception as e:
                logger.warning(f"Error fetching metadata for database '{db_name}': {e}")
                db_info.append({
                    "name": db_name,
                    "num_collections": "Error fetching metadata"
                })
        return db_info


class ListCollectionsView(APIView):
    """
    API view to list all collections for a given database in Datacube using database ID.
    """

    def get(self, request, *args, **kwargs):
        try:
            # Extract database ID from query parameters
            database_id = request.query_params.get("database_id", "").strip()

            if not database_id:
                return Response(
                    {"success": False, "message": "Database ID is required", "data": []},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Fetch metadata record for the specified database ID
            metadata_record = asyncio.run(get_metadata_record(database_id))
            if not metadata_record:
                return Response(
                    {"success": False, "message": f"Database with ID '{database_id}' does not exist in Datacube", "data": []},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Retrieve collection names from metadata
            collections = metadata_record.get('collections', [])
            collections = [coll["name"] for coll in collections] if collections else []

            if not collections:
                return Response(
                    {"success": False, "message": f"No collections found for database with ID '{database_id}'", "data": []},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Fetch actual collections in the database
            actual_collections = asyncio.run(self.get_actual_collections(metadata_record["database_name"]))
            missing_in_db = set(collections) - set(actual_collections)

            # Log any discrepancies
            if missing_in_db:
                logger.warning(f"Collections in metadata but missing in MongoDB: {', '.join(missing_in_db)}")

            return Response(
                {
                    "success": True,
                    "message": "Collections found!",
                    "data": collections
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(f"Error listing collections for database with ID '{request.query_params.get('database_id', 'unknown')}': {e}")
            return Response(
                {"success": False, "message": str(e), "data": []},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_actual_collections(self, database_name):
        """Fetch the actual list of collections from the database."""
        try:
            cluster = settings.MONGODB_CLIENT
            db = cluster[database_name]
            return await asyncio.to_thread(db.list_collection_names)
        except Exception as e:
            logger.error(f"Error fetching actual collections for database '{database_name}': {e}")
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


    async def drop_collections(self, database_id, db_name, collection_names):
        """Remove specified collections from the database and update metadata."""
        cluster = settings.MONGODB_CLIENT
        metadata_coll = settings.METADATA_COLLECTION
        dropped_collections_count = 0

        # Start an atomic transaction
        session = await asyncio.to_thread(cluster.start_session)
        with session:
            session.start_transaction()
            try:
                # Drop collections from the database
                database = cluster[db_name]
                for coll_name in collection_names:
                    if coll_name in await asyncio.to_thread(database.list_collection_names):
                        await asyncio.to_thread(database[coll_name].drop)
                        dropped_collections_count += 1

                # Update metadata to remove dropped collections
                await asyncio.to_thread(
                    metadata_coll.update_one,
                    {"_id": database_id},
                    {"$pull": {"collections": {"name": {"$in": collection_names}}}}
                )

                session.commit_transaction()
                logger.info(f"Collections '{', '.join(collection_names)}' dropped successfully from database '{db_name}'.")
                return dropped_collections_count

            except Exception as e:
                session.abort_transaction()
                logger.error(f"Error during transaction for dropping collections from database '{db_name}': {e}")
                raise e


class GetMetadataView(APIView):
    """
    API View to fetch metadata of a specific database.
    """
    serialiser_class = GetMetadataSerializer

    def get(self, request, *args, **kwargs):
        try:
            serializer = GetMetadataSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            # Extract database name from query parameters
            db_name = serializer.validated_data.get('db_name', '').lower()

            if not db_name:
                return Response(
                    {"success": False, "message": "Database name is required."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Fetch metadata from the metadata collection
            metadata_coll = settings.METADATA_COLLECTION
            metadata = metadata_coll.find_one({"database_name": db_name})

            if not metadata:
                return Response(
                    {"success": False, "message": f"No metadata found for database '{db_name}'."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Convert ObjectId to string in the metadata
            metadata = self.convert_objectid_to_str(metadata)

            return Response(
                {"success": True, "data": metadata},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(f"Error fetching metadata for database '{db_name}': {e}", exc_info=True)
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
    def get(self, request):
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

