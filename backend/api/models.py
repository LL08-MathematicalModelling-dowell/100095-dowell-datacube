import uuid
from datetime import datetime
from mongoengine import Document, fields

class Metadata(Document):
    """Metadata collection tracking all user databases and collections."""
    id = fields.UUIDField(primary_key=True, default=uuid.uuid4)
    user_id = fields.UUIDField()
    number_of_databases = fields.IntField(default=0)
    number_of_collections = fields.IntField(default=0)
    created_at = fields.DateTimeField(default=datetime.utcnow)
    updated_at = fields.DateTimeField(default=datetime.utcnow)
    
    databases = fields.ListField(fields.DictField(), default=[])
    collections = fields.ListField(fields.DictField(), default=[])

    def __str__(self):
        return f"Metadata for User {self.user_id}"

    def to_dict(self):
        return {
            "id": str(self.id),
            "user": str(self.user_id),
            "number_of_databases": self.number_of_databases,
            "number_of_collections": self.number_of_collections,
            "created_at": str(self.created_at),
            "updated_at": str(self.updated_at),
            "databases": self.databases,
            "collections": self.collections,
        }

    def add_database(self, database_name, database_id, number_of_collections, database_description, created_at, updated_at, last_accessed):
        """Add a new database entry to metadata."""
        new_db = {
            "id": database_id,
            "name": database_name,
            "number_of_collections": number_of_collections,
            "description": database_description,
            "created_at": created_at,
            "updated_at": updated_at,
            "last_accessed": last_accessed
        }
        self.databases.append(new_db)
        self.number_of_databases += 1
        self.save()

    def remove_database(self, database_id):
        """Remove a database entry from metadata."""
        self.databases = [db for db in self.databases if db["id"] != database_id]
        self.number_of_databases -= 1
        self.save()
    

