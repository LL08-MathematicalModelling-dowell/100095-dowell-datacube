"""
This service orchestrates the creation of databases and collections by coordinating
between the MetadataService (for metadata) and CollectionService (for actual
database operations).
"""


from typing import List, Dict, Tuple
from api.utils.naming import generate_db_name
from api.services.metadata_service import MetadataService
from api.services.collection_service import CollectionService


class DatabaseService:
    """Service for managing virtual databases and their collections."""
    def __init__(self, user_id: str):
        """
        Initialize the service for a specific user.
        All operations will be scoped to this user_id.
        """
        if not user_id:
            raise ValueError("DatabaseService requires a valid user_id.")
            
        self.user_id = user_id
        # Instantiate MetadataService with the same user context
        self.meta_svc = MetadataService(user_id=user_id)

    async def create_database_with_collections(
        self,
        user_provided_name: str,
        collections: List[Dict],
        session=None
    ) -> Tuple[Dict, List[Dict]]:
        """
        High-level orchestration:
        1. Checks for naming collisions.
        2. Generates a unique internal namespace.
        3. Persists metadata record.
        4. Provisions physical MongoDB collections.
        """
        
        # Guard: Check existence before generating names or starting transactions
        if await self.meta_svc.exists_db(user_provided_name, session=session):
            raise ValueError(f"A database named '{user_provided_name}' already exists.")

        # Step 1: Generate the secure internal database name
        internal_db_name = generate_db_name(user_provided_name, self.user_id)

        # Step 2: Provision physical collections via CollectionService
        coll_svc = CollectionService(
            db_name=user_provided_name,
            user_id=self.user_id,
            internal_db_name=internal_db_name,
            new_db=True
        )

        names = [c["name"] for c in collections]
        
        # Step 3: Create physical collections
        coll_info = await coll_svc.create(names, session=session)

        # Step 4: Create metadata entry
        meta = await self.meta_svc.create_db_meta(
            user_provided_name=user_provided_name,
            internal_db_name=internal_db_name,
            collections=collections,
            session=session
        )

        return meta, coll_info # type: ignore

    async def add_collections_with_creation(
        self,
        database_id: str,
        new_cols: List[Dict],
        session=None
    ) -> List[Dict]:
        """
        Adds new collections to an existing database.
        Verified: Only proceeds if the bound user owns the target database.
        """
        # Step 1: Verification & Data Retrieval
        meta = await self.meta_svc.get_db(database_id)
        if not meta:
            raise PermissionError("Database not found or access denied.")
        
        # Enforce collections cap of 1000
        existing_col_count = len(meta.get("collections", []))
        if existing_col_count + len(new_cols) > 1000:
            raise ValueError("Adding these collections would exceed the limit of 1000 collections per database.")

        # internal_db_name = meta["dbName"]
        display_db_name = meta["displayName"]
        internal_db_name = meta["dbName"]
        # Step 2: Physical Creation
        coll_svc = CollectionService(
            user_id=self.user_id,
            db_name=display_db_name,
            internal_db_name=internal_db_name,
            new_db=False
        )
        names = [c["name"] for c in new_cols]

        # Step 3: Create physical collections        
        result = await coll_svc.create(names, session=session)

        # Step 4: Metadata Update only after successful physical creation
        # Filter only successfully created collections
        created_cols = [col for col in new_cols if any(res["name"] == col["name"] and res["created"] for res in result)]
        if len(created_cols) > 0:
            await self.meta_svc.add_collections(
                db_id=database_id,
                new_collections=created_cols,
                session=session
            )
        # Prepare formatted collection info for return
        formatted_cols = []
        for res in result:
            col_meta = next((col for col in new_cols if col["name"] == res["name"]), {})
            formatted_col = {
                "name": res["name"],
                "created": res["created"],
                "exists": res["exists"],
                "error": res["error"],
                "fields": col_meta.get("fields", [])
            }
            formatted_cols.append(formatted_col)  

        return formatted_cols