from django.dispatch import Signal

# 2026 Standard: Use explicit providing_args descriptions in docstrings
# (Note: providing_args is deprecated in Django code but still good for docs)

# Fired after a bulk JSON import
post_import_signal = Signal()  # args: [user_id, db_id, coll_name, count]

# Fired after a database is dropped
post_drop_signal = Signal()    # args: [user_id, db_id, internal_name]

# Fired when a user exceeds their 2026 storage quota
quota_reached_signal = Signal() # args: [user_id, usage_bytes, limit_bytes]

# Fired after individual CRUD operations
document_created_signal = Signal() # args: [user_id, db_id, coll_name, count]
document_deleted_signal = Signal() # args: [user_id, db_id, coll_name, count]
