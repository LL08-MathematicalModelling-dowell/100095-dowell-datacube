# Initialization Script / Migration
from django.conf import settings

def setup_telemetry_collections():
    db = settings.MONGODB_CLIENT["platform_ops"]
    # Create a Time Series collection for fine-grained activity tracking
    if "user_activity" not in db.list_collection_names():
        db.create_collection("user_activity", timeseries={
            "timeField": "timestamp",
            "metaField": "metadata", # stores {user_id, db_id, op_type}
            "granularity": "minutes"
        })
    # Create a standard collection for storage snapshots
    if "storage_snapshots" not in db.list_collection_names():
        db.create_collection("storage_snapshots")
