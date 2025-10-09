# import sys
# from datetime import datetime, timedelta
# from pymongo import MongoClient
# import re
# from bson.timestamp import Timestamp

# def get_unused_databases(uri, days=30):
#     client = MongoClient(uri)
#     # Get list of database names
#     db_names = client.list_database_names()
    
#     # Access the oplog
#     local_db = client['local']
#     oplog = local_db['oplog.rs']
    
#     unused_dbs = []
#     now = datetime.now()
    
#     # Optionally, check oplog window
#     first_op = oplog.find_one(sort=[('ts', 1)])
#     if first_op:
#         first_ts = first_op['ts']
#         if isinstance(first_ts, Timestamp):
#             first_time = first_ts.as_datetime()
#             oplog_window = now - first_time
#             if oplog_window < timedelta(days=days):
#                 print(f"Warning: Oplog only covers {oplog_window.days} days, which is less than {days} days. Results may not be accurate for older databases.")
    
#     for db_name in db_names:
#         # Skip system databases
#         if db_name in ['admin', 'local', 'config']:
#             continue
        
#         # Find the most recent operation for this database
#         # ns format: db_name.collection_name
#         regex = re.compile(f'^{re.escape(db_name)}\\.')
#         last_op = oplog.find_one({'ns': regex}, sort=[('ts', -1)])
        
#         if last_op is None:
#             # No operations found in oplog for this db
#             unused_dbs.append(db_name)
#         else:
#             last_ts = last_op['ts']
#             if isinstance(last_ts, Timestamp):
#                 last_time = last_ts.as_datetime()
#                 if (now - last_time) > timedelta(days=days):
#                     unused_dbs.append(db_name)
    
#     client.close()
#     return unused_dbs

# if __name__ == "__main__":
#     DATABASE_URL="mongodb+srv://jacobdowell:HFzPobvOdqm3CwpT@cluster0.n2ih9.mongodb.net/"
#     if len(sys.argv) < 2:
#         print("Usage: python script.py <mongodb_uri> [days]")
#         sys.exit(1)
    
#     uri = sys.argv[1]
#     days = 30
#     if len(sys.argv) > 2:
#         days = int(sys.argv[2])
    
#     unused = get_unused_databases(uri, days)
#     print("Unused databases (no writes in the last {} days):".format(days))
#     for db in unused:
#         print(db)


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
    DATABASE_URL="mongodb+srv://jacobdowell:HFzPobvOdqm3CwpT@cluster0.n2ih9.mongodb.net/"
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