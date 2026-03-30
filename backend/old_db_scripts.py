import sys
from datetime import datetime, timedelta
from pymongo import MongoClient
from bson.objectid import ObjectId

def get_unused_databases(uri, days=30):
    client = MongoClient(uri)
    db_names = client.list_database_names()
    
    unused_dbs = []
    threshold = datetime.now() - timedelta(days=days)
    
    for db_name in db_names:
        if db_name in ['admin', 'local', 'config']:
            continue
        
        db = client[db_name]
        last_activity = None
        
        for coll_name in db.list_collection_names():
            coll = db[coll_name]
            # Find the most recent document by _id descending
            recent_doc = coll.find_one(sort=[('_id', -1)])
            if recent_doc and '_id' in recent_doc and isinstance(recent_doc['_id'], ObjectId):
                ts = recent_doc['_id'].generation_time.replace(tzinfo=None)  # UTC to naive
                if last_activity is None or ts > last_activity:
                    last_activity = ts
        
        if last_activity is None or last_activity < threshold:
            unused_dbs.append(db_name)
    
    client.close()
    return unused_dbs

if __name__ == "__main__":
    DATABASE_URL= ""
    if len(sys.argv) < 2:
        print("Usage: python script.py <mongodb_uri> [days]")
        sys.exit(1)
    
    uri = sys.argv[1]
    days = 30
    if len(sys.argv) > 2:
        days = int(sys.argv[2])
    
    unused = get_unused_databases(uri, days)
    print("Unused databases (no inserts in the last {} days):".format(days))
    for db in unused:
        print(db)