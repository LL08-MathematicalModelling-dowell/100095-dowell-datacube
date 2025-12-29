from django.dispatch import Signal

# Define custom signals for 2025 event tracking
# These are fired whenever a significant tenant action occurs
post_import_signal = Signal()  # Arguments: [user_id, db_id, coll_name, count]
post_drop_signal = Signal()    # Arguments: [user_id, db_id, internal_name]
quota_reached_signal = Signal() # Arguments: [user_id, usage_bytes]
document_created_signal = Signal() # Arguments: [user_id, db_id, coll_name, inserted_ids]
document_deleted_signal = Signal() # Arguments: [user_id, db_id, coll_name, deleted_count]
