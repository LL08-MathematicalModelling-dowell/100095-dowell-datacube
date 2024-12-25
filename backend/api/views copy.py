import datetime
import asyncio
import logging

from bson import ObjectId
from datetime import datetime

from django.conf import settings
from django.shortcuts import render

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from api.serializers import (
    AddCollectionPOSTSerializer,
    GetCollectionsSerializer,
    AddDatabasePOSTSerializer,
    GetMetadataSerializer,
    InputDeleteSerializer,
    InputGetSerializer,
    InputPostSerializer,
    InputPutSerializer,
    DropDatabaseSerializer,
    ListDatabaseSerializer,
)
from asgiref.sync import async_to_sync


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
    Provides modular, flexible, and efficient handling of collection creation.
    """
    serializer_class = AddDatabasePOSTSerializer

    def post(self, request, *args, **kwargs):
        try:
            # Validate request data
            serializer = AddDatabasePOSTSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data

            # Extract database and collections information
            db_name = validated_data.get('db_name', '').lower()
            product_name = validated_data.get('product_name', '').lower() if validated_data.get('product_name') else None
            collections = validated_data.get('collections', [])

            # Ensure at least one collection with fields is specified
            if not collections and product_name != "living lab admin":
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

            # Insert metadata and initialize the database
            self.insert_metadata(db_name, collections)

            if product_name == "living lab admin":
                asyncio.run(self.create_collections_for_living_lab(db_name))
            else:
                asyncio.run(self.create_collections_in_db(db_name, collections))

            return Response(
                {"success": True, "message": f"Database '{db_name}' and collections created successfully."},
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            logger.error(f"Error creating database: {e}", exc_info=True)
            return Response(
                {"success": False, "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def check_database_exists(self, db_name):
        """Check if the database already exists in metadata or cache."""
        if db_name in metadata_cache:
            return True

        metadata_coll = settings.METADATA_COLLECTION
        if metadata_coll.find_one({"database_name": db_name}):
            metadata_cache[db_name] = True
            return True
        return False

    def insert_metadata(self, db_name, collections):
        """Insert metadata for the new database, including collections and fields."""
        metadata_coll = settings.METADATA_COLLECTION

        total_fields = sum(len(coll["fields"]) for coll in collections)
        metadata = {
            "database_name": db_name,
            "collections_metadata": [
                {"name": coll["name"], "fields": coll["fields"]} for coll in collections
            ],
            "number_of_collections": len(collections),
            "number_of_fields": total_fields
        }
        metadata_coll.insert_one(metadata)
        metadata_cache[db_name] = True

    async def create_collections_in_db(self, db_name, collections):
        """Create specified collections with fields in the MongoDB database."""
        cluster = settings.MONGODB_CLIENT
        db = cluster[db_name]
        for coll in collections:
            collection_name = coll["name"]
            await asyncio.to_thread(db.create_collection, collection_name)
            logger.info(f"Created collection '{collection_name}' in database '{db_name}'.")

            # Initialize each collection with an empty document containing the specified fields
            sample_doc = {field: None for field in coll["fields"]}
            await asyncio.to_thread(db[collection_name].insert_one, sample_doc)
            logger.info(f"Inserted sample document with fields {coll['fields']} into collection '{collection_name}'.")

    async def create_collections_for_living_lab(self, db_name):
        """
        Creates collections and inserts documents for the "living lab admin" product.
        - Collections 1 to 1000 will each have 1 document.
        - Collections 1001 to 10000 will each have 1000 documents.
        """
        cluster = settings.MONGODB_CLIENT
        db = cluster[db_name]

        # Create collections 1 to 1000, each with 1 document
        for i in range(1, 1001):
            collection_name = f"collection_{i}"
            await asyncio.to_thread(db.create_collection, collection_name)
            await asyncio.to_thread(db[collection_name].insert_one, {"data": f"document_{i}"})
            logger.info(f"Created collection '{collection_name}' with 1 document in database '{db_name}'.")

        # Create collections 1001 to 10000, each with 1000 documents
        for i in range(1001, 10001):
            collection_name = f"collection_{i}"
            await asyncio.to_thread(db.create_collection, collection_name)
            
            # Create a batch of 1000 documents for efficiency
            documents = [{"data": f"document_{j}"} for j in range(1, 1001)]
            await asyncio.to_thread(db[collection_name].insert_many, documents)
            logger.info(f"Created collection '{collection_name}' with 1000 documents in database '{db_name}'.")

        # Update metadata for Living Lab Admin collections
        metadata_coll = settings.METADATA_COLLECTION
        living_lab_metadata = [
            {"name": f"collection_{i}", "fields": ["data"]} for i in range(1, 10001)
        ]
        await asyncio.to_thread(metadata_coll.update_one,
                                {"database_name": db_name},
                                {"$set": {"collections_metadata": living_lab_metadata}})



class DataCrudView(APIView):
    """
    A view for handling CRUD operations on MongoDB collections with metadata validation.
    """

    def get_serializer_class(self):
        """Returns the serializer class based on the request method."""
        if self.request.method == 'GET':
            return InputGetSerializer
        elif self.request.method == 'POST':
            return InputPostSerializer
        elif self.request.method == 'PUT':
            return InputPutSerializer
        elif self.request.method == 'DELETE':
            return InputDeleteSerializer

    def get(self, request, *args, **kwargs):
        """Handles GET requests to fetch data from a specified MongoDB collection."""
        return async_to_sync(self.async_get)(request, *args, **kwargs)

    async def async_get(self, request, *args, **kwargs):
        """Asynchronous method to handle the logic for GET requests."""
        try:
            serializer = InputGetSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data

            database = data.get('db_name')
            coll = data.get('coll_name')
            filters = self.convert_object_id(data.get('filters', {}))
            limit = data.get('limit', 50)
            offset = data.get('offset', 0)

            # Exclude soft-deleted documents by default
            filters['is_deleted'] = filters.get('is_deleted', False)

            await self.validate_database_and_collection(database, coll)
            result = await self.fetch_data_from_collection(database, coll, filters, limit, offset)

            msg = "Data found!" if result else "No data exists for this query/collection"
            return Response({"success": True, "message": msg, "data": result}, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error in GET request: {e}")
            return Response({"success": False, "message": str(e), "data": []}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, *args, **kwargs):
        """Handles POST requests to insert new data into a specified MongoDB collection."""
        return async_to_sync(self.async_post)(request, *args, **kwargs)
    
    async def async_post(self, request, *args, **kwargs):
        """Asynchronous method to handle the logic for POST."""
        try:
            serializer = InputPostSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data

            database = data.get('db_name')
            coll = data.get('coll_name')
            documents_to_insert = data.get('data')

            # Ensure documents_to_insert is a list, even if a single document is provided
            if isinstance(documents_to_insert, dict):
                documents_to_insert = [documents_to_insert]

            # Validate fields in each document and set `is_deleted` to False by default
            valid_fields = await self.validate_database_and_collection(database, coll)
            for document in documents_to_insert:
                await self.check_fields_exist(document, valid_fields)
                document['is_deleted'] = False

                # Add insert timestamp and operation log for each document
                insert_date_time = datetime.utcnow()
                document.update({
                    f"{key}_operation": {
                        "insert_date_time": [insert_date_time],
                        "is_deleted": False,
                    } for key in document.keys()
                })

            # Insert documents into the collection
            collection = settings.MONGODB_CLIENT[database][coll]
            if len(documents_to_insert) > 1:
                result = await asyncio.to_thread(collection.insert_many, documents_to_insert)
                inserted_ids = [str(id) for id in result.inserted_ids]
            else:
                result = await asyncio.to_thread(collection.insert_one, documents_to_insert[0])
                inserted_ids = [str(result.inserted_id)]

            return Response(
                {"success": True, "message": "Documents inserted successfully!", "data": {"inserted_ids": inserted_ids}},
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            logger.error(f"Error in POST request: {e}")
            return Response({"success": False, "message": str(e), "data": []}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        """Handles PUT requests to update or replace data in a MongoDB collection."""
        return async_to_sync(self.async_put)(request, *args, **kwargs)

    async def async_put(self, request, *args, **kwargs):
        """Asynchronous method to handle the logic for PUT requests."""
        try:
            serializer = InputPutSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data

            database = data.get('db_name')
            coll = data.get('coll_name')
            operation = data.get('operation')
            filter_data = self.convert_object_id(data.get('query'))
            update_data = data.get('update_data', {})

            # Validate database and collection, check fields
            valid_fields = await self.validate_database_and_collection(database, coll)
            await self.check_fields_exist(update_data, valid_fields)

            # Insert update timestamp and log operation for each updated field
            update_date_time = datetime.utcnow()
            update_data_with_log = {
                key: value for key, value in update_data.items()
            }
            update_data_with_log.update({
                f"{key}_operation": {
                    "update_date_time": [update_date_time],
                    "is_deleted": False
                } for key in update_data.keys()
            })

            # Perform update or replace based on the operation
            collection = settings.MONGODB_CLIENT[database][coll]
            if operation == 'update':
                result = await asyncio.to_thread(
                    collection.update_one, filter_data, {'$set': update_data_with_log}
                )
            elif operation == 'replace':
                result = await asyncio.to_thread(
                    collection.replace_one, filter_data, update_data_with_log
                )

            # Check if the document was modified
            if result.modified_count == 0:
                return Response(
                    {"success": False, "message": "No document found or updated"},
                    status=status.HTTP_404_NOT_FOUND
                )

            return Response({"success": True, "message": "Document updated successfully"}, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error in PUT request: {e}")
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        """Handles DELETE requests to remove or soft-delete documents from a MongoDB collection."""
        return async_to_sync(self.async_delete)(request, *args, **kwargs)

    async def async_delete(self, request, *args, **kwargs):
        """Asynchronous method to handle the logic for DELETE requests."""
        try:
            serializer = InputDeleteSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data

            database = data.get('db_name')
            coll = data.get('coll_name')
            operation = data.get('operation')
            filter_data = self.convert_object_id(data.get('query'))

            # Validate database and collection
            await self.validate_database_and_collection(database, coll)

            # Perform soft delete (mark as deleted) or hard delete
            collection = settings.MONGODB_CLIENT[database][coll]
            if operation == 'soft_delete':
                # Set `is_deleted` to True and add deletion timestamp
                delete_date_time = datetime.utcnow()
                update_result = await asyncio.to_thread(
                    collection.update_one, filter_data, {'$set': {'is_deleted': True, 'deleted_at': delete_date_time}}
                )
                if update_result.modified_count == 0:
                    return Response(
                        {"success": False, "message": "No document found to soft delete"},
                        status=status.HTTP_404_NOT_FOUND
                    )
                message = "Document soft-deleted successfully"
            elif operation == 'delete':
                delete_result = await asyncio.to_thread(collection.delete_one, filter_data)
                if delete_result.deleted_count == 0:
                    return Response(
                        {"success": False, "message": "No document found to delete"},
                        status=status.HTTP_404_NOT_FOUND
                    )
                message = "Document deleted successfully"

            return Response({"success": True, "message": message}, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error in DELETE request: {e}")
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    async def fetch_data_from_collection(self, database, coll, filters, limit=50, offset=0):
        """Fetches data from the specified collection with filters, limit, and offset."""
        cluster = settings.MONGODB_CLIENT
        collection = cluster[database][coll]
        

        query = collection.find(filters).skip(offset).limit(limit)
        result = await asyncio.to_thread(lambda: list(query))

        for doc in result:
            doc['_id'] = str(doc['_id'])
        return result

    async def validate_database_and_collection(self, database, coll):
        """Validates if the specified database and collection exist with defined fields."""
        metadata_coll = settings.METADATA_COLLECTION
        mongo_db = await asyncio.to_thread(metadata_coll.find_one, {"database_name": database})
        
        if not mongo_db:
            raise ValueError(f"Database '{database}' does not exist in Datacube")
        
        collections_metadata = {coll["name"]: coll["fields"] for coll in mongo_db.get("collections_metadata", [])}
        
        if coll not in collections_metadata:
            raise ValueError(f"Collection '{coll}' does not exist in Datacube database")
        
        return collections_metadata[coll]

    def convert_object_id(self, filters):
        """Converts 'id' and '_id' keys in filters to ObjectId."""
        for key, value in filters.items():
            if key in ["id", "_id"]:
                try:
                    filters[key] = ObjectId(value)
                except Exception as ex:
                    pass
                    logger.warning(f"ObjectId conversion error: {ex}")
        return filters

    async def check_fields_exist(self, data, valid_fields):
        """Ensures only defined fields are present in the request data."""
        for field in data.keys():
            if field not in valid_fields:
                raise ValueError(f"Invalid field '{field}' for this collection")


class ListCollectionsView(APIView):
    """
    API view to list all collections for a given database in Datacube.
    """

    def get(self, request, *args, **kwargs):
        try:
            if not request.data:
                return Response(
                    {"success": False, "message": "Request data is required", "data": []},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate request data using serializer
            serializer = GetCollectionsSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data

            # Extract database name
            database = data.get('db_name', "").lower()

            if not database:
                return Response(
                    {"success": False, "message": "Database name is required", "data": []},
                    status=status.HTTP_400_BAD_REQUEST
                )

            metadata_record = asyncio.run(self.get_metadata_record(database))
            if not metadata_record:
                return Response(
                    {"success": False, "message": f"Database '{database}' does not exist in Datacube", "data": []},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            collections = metadata_record.get('collection_names', []) or metadata_record.get('collections_metadata', [])

            if type(collections[0]) == dict:
                collections = [coll["name"] for coll in collections]

            if not collections:
                return Response(
                    {"success": False, "message": f"No collections found for database '{database}'", "data": []},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            actual_collections = asyncio.run(self.get_actual_collections(database))
            
            missing_in_db = set(collections) - set(actual_collections)

            # Log any discrepancies
            if missing_in_db:
                pass
                logger.warning(f"Collections in metadata but missing in MongoDB: {', '.join(missing_in_db)}")

            return Response(
                {"success": True, "message": "Collections found!", "data": collections},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(f"Error listing collections for database '{data.get('db_name', 'unknown')}': {e}")
            return Response(
                {"success": False, "message": str(e), "data": []},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_metadata_record(self, database):
        return await asyncio.to_thread(settings.METADATA_COLLECTION.find_one, {"database_name": database})

    async def get_actual_collections(self, database):
        cluster = settings.MONGODB_CLIENT
        db = cluster[database]
        return await asyncio.to_thread(db.list_collection_names)


class AddCollectionView(APIView):
    """
    API view to handle adding new collections with defined document fields to an existing database.
    """
    serializer_class = AddCollectionPOSTSerializer

    def post(self, request, *args, **kwargs):
        try:
            # Validate the request data
            serializer = AddCollectionPOSTSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data

            # Extract database name and collections
            db_name = data.get('db_name').lower()
            collections = data.get('collections', [])

            # Check if the database exists
            if not self.check_database_exists(db_name):
                return Response(
                    {"success": False, "message": f"Database '{db_name}' does not exist in Datacube"},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Validate and filter collections
            existing_collections, duplicates = self.validate_collections(db_name, collections)
            if duplicates:
                return Response(
                    {"success": False, "message": f"Collections '{', '.join(duplicates)}' already exist"},
                    status=status.HTTP_409_CONFLICT
                )

            # Update metadata with new collections and fields
            new_collections = [coll for coll in collections if coll["name"] not in existing_collections]
            asyncio.run(self.update_metadata(db_name, new_collections))
            asyncio.run(self.create_collections_in_db(db_name, new_collections))

            return Response(
                {"success": True, "message": f"Collections '{', '.join([coll['name'] for coll in new_collections])}' created successfully"},
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            logger.error(f"Error adding collections: {e}", exc_info=True)
            return Response(
                {"success": False, "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def check_database_exists(self, db_name):
        """Check if the database exists in the metadata collection."""
        metadata_coll = settings.METADATA_COLLECTION
        return bool(metadata_coll.find_one({"database_name": db_name}))

    def validate_collections(self, db_name, collections):
        """
        Validate and filter collections for the specified database.
        Returns existing collections and duplicates.
        """
        metadata = settings.METADATA_COLLECTION.find_one({"database_name": db_name})
        existing_collections = set(metadata.get("collection_names", []))
        duplicates = [coll["name"] for coll in collections if coll["name"] in existing_collections]

        # Optionally, calculate total fields for reporting
        total_fields = sum(len(coll["fields"]) for coll in collections if coll["name"] not in existing_collections)

        return existing_collections, duplicates


    async def update_metadata(self, db_name, new_collections):
        """Update metadata with the new collections and their fields."""
        metadata_coll = settings.METADATA_COLLECTION
        total_fields = 0

        for coll in new_collections:
            collection_name = coll["name"]
            fields = coll["fields"]
            total_fields += len(fields)

            # Add new collection metadata
            await asyncio.to_thread(metadata_coll.update_one,
                                    {"database_name": db_name},
                                    {"$addToSet": {
                                        "collection_names": collection_name,
                                        "collections_metadata": {"name": collection_name, "fields": fields}
                                    }})

        # Update number_of_collections and number_of_fields
        await asyncio.to_thread(metadata_coll.update_one,
                                {"database_name": db_name},
                                {
                                    "$inc": {"number_of_collections": len(new_collections), "number_of_fields": total_fields}
                                })


    async def create_collections_in_db(self, db_name, new_collections):
        """Create new collections in the MongoDB database."""
        cluster = settings.MONGODB_CLIENT
        db = cluster[db_name]
        for coll in new_collections:
            collection_name = coll["name"]
            await asyncio.to_thread(db.create_collection, collection_name)
            logger.info(f"Created collection '{collection_name}' in database '{db_name}'.")


class DropDatabaseView(APIView):
    """
    API view to safely drop a specified database with confirmation.
    """
    serializer_class = DropDatabaseSerializer

    def delete(self, request, *args, **kwargs):
        """
        Deletes a database only if the confirmation matches the database name.
        Removes all collections, documents, and metadata associated with the database.
        """
        serializer = DropDatabaseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        db_name = validated_data.get('db_name', '').lower()
        confirmation = validated_data.get('confirmation', '').lower()

        if db_name != confirmation:
            return Response(
                {"success": False, "message": "Confirmation does not match database name"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Check if the database exists
            db_exists = asyncio.run(self.check_database_exists(db_name))
            if not db_exists:
                return Response(
                    {"success": False, "message": f"Database '{db_name}' does not exist"},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Clean up metadata and drop collections
            asyncio.run(self.delete_database_and_metadata(db_name))

            return Response(
                {"success": True, "message": f"Database '{db_name}' and associated metadata dropped successfully"},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(f"Error dropping database '{db_name}': {e}")
            return Response(
                {"success": False, "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def check_database_exists(self, db_name):
        """Check if the database exists in MongoDB."""
        cluster = settings.MONGODB_CLIENT
        return await asyncio.to_thread(lambda: db_name in cluster.list_database_names())

    async def delete_database_and_metadata(self, db_name):
        """Remove metadata and drop all collections within the database."""
        cluster = settings.MONGODB_CLIENT
        metadata_db = cluster["datacube_metadata"]
        metadata_coll = metadata_db["metadata_collection"]

        # Delete metadata
        await asyncio.to_thread(metadata_coll.delete_one, {"database_name": db_name})

        # Drop collections and the database
        database = cluster[db_name]
        for coll_name in await asyncio.to_thread(database.list_collection_names):
            await asyncio.to_thread(database[coll_name].drop)

        # Drop the database itself
        await asyncio.to_thread(lambda: cluster.drop_database(db_name))


class ListDatabasesView(APIView):
    """
    API view to list all databases in the MongoDB cluster, with optional pagination, filtering, and metadata.
    """
    serializer_class = ListDatabaseSerializer

    def get(self, request, *args, **kwargs):
        try:
            # Validate request data using serializer
            serializer = ListDatabaseSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data

            # Pagination and filtering parameters
            page = validated_data.get('page', 1)
            page_size = validated_data.get('page_size', 10)
            filter_term = validated_data.get('filter', '')

            # Run async functions within asyncio.run()
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
            print(f"Error listing databases: {e}")
            return Response(
                {"success": False, "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def list_database_names(self, filter_term):
        cluster = settings.MONGODB_CLIENT
        db_names = await asyncio.to_thread(cluster.list_database_names)
        if filter_term:
            db_names = [db for db in db_names if filter_term.lower() in db.lower()]
        return db_names

    async def get_database_metadata(self, db_names):
        cluster = settings.MONGODB_CLIENT
        # metadata_coll = cluster["datacube_metadata"]["metadata_collection"]
        db_info = []
        for db_name in db_names:
            num_collections = await asyncio.to_thread(lambda: len(cluster[db_name].list_collection_names()))
            # metadata = await asyncio.to_thread(lambda: metadata_coll.find_one({"database_name": db_name}))
            db_info.append({
                "name": db_name,
                "num_collections": num_collections,
                # "metadata": metadata or "No metadata available"
            })
        return db_info



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

