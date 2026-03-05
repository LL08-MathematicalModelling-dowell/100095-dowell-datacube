# api/tasks.py
from celery import shared_task
from django.conf import settings
from datetime import datetime
from api.services.metadata_service import MetadataService

@shared_task
def collect_storage_metrics():
    """Background task to snapshot DB and Collection sizes for all users."""
    client = settings.MONGODB_CLIENT
    platform_db = client["platform_ops"]
    
    # We use a system-level metadata service to get all databases
    all_meta = MetadataService.get_all_registered_databases() 
    
    for meta in all_meta:
        db_name = meta["dbName"]
        user_id = meta["ownerId"]
        
        # 1. Get Database Stats
        db_stats = client[db_name].command("dbStats")
        
        # 2. Get Collection Stats
        coll_stats = []
        for coll in client[db_name].list_collection_names():
            c_stat = client[db_name].command("collStats", coll)
            coll_stats.append({
                "name": coll,
                "size_bytes": c_stat["size"],
                "storage_bytes": c_stat["storageSize"]
            })
            
        # 3. Save Snapshot
        platform_db["storage_snapshots"].insert_one({
            "timestamp": datetime.utcnow(),
            "user_id": user_id,
            "db_id": meta["_id"],
            "total_size": db_stats["dataSize"],
            "storage_size": db_stats["storageSize"],
            "collections": coll_stats
        })



# api/tasks.py addition
@shared_task
def downsample_telemetry():
    """
    Moves old raw data into 'Daily' buckets to keep frontend charts fast.
    Runs once every 24 hours.
    """
    db = settings.MONGODB_CLIENT["platform_ops"]
    yesterday = datetime.utcnow() - timedelta(days=1)
    
    # Aggregate yesterday's data into a single summary document per user/db
    pipeline = [
        {"$match": {"timestamp": {"$lt": datetime.utcnow(), "$gte": yesterday}}},
        {"$group": {
            "_id": {
                "user_id": "$metadata.user_id",
                "db_id": "$metadata.db_id"
            },
            "total_reads": {"$sum": {"$cond": [{"$eq": ["$metadata.method", "GET"]}, 1, 0]}},
            "total_writes": {"$sum": {"$cond": [{"$in": ["$metadata.method", ["POST", "PUT", "DELETE"]]}, 1, 0]}},
            "avg_latency": {"$avg": "$latency_ms"}
        }}
    ]
    
    results = list(db["user_activity"].aggregate(pipeline))
    if results:
        for record in results:
            db["daily_summaries"].insert_one({
                "date": yesterday.replace(hour=0, minute=0, second=0, microsecond=0),
                "user_id": record["_id"]["user_id"],
                "db_id": record["_id"]["db_id"],
                "metrics": record
            })



@shared_task
def update_usage_stats_task(user_id, db_id, count):
    """Updates the 'platform_ops' time-series log for a bulk action."""
    db = settings.MONGODB_CLIENT["platform_ops"]
    db["user_activity"].insert_one({
        "timestamp": datetime.utcnow(),
        "metadata": {
            "user_id": user_id,
            "db_id": db_id,
            "op_type": "BULK_IMPORT"
        },
        "count": count,
        "latency_ms": 0 # Not a request latency, but a volume log
    })

@shared_task
def cleanup_dropped_db_telemetry(db_id):
    """Hard delete telemetry data for a database that no longer exists."""
    db = settings.MONGODB_CLIENT["platform_ops"]
    # Remove storage snapshots and raw activity for the dropped DB
    db["storage_snapshots"].delete_many({"db_id": db_id})
    db["user_activity"].delete_many({"metadata.db_id": db_id})




