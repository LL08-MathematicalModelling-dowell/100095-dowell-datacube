// Create Database fron SDK Response ><><><><><>> :
create_database_response = {
  success: True,
  message: "Database 'test_db_from_sdk' and collections created successfully.",
  database: { name: "test_db_from_sdk", id: "677967f14498f63691764217" },
  collections: [
    {
      name: "users",
      id: "677967f24498f63691764218",
      fields: [{ name: "username", type: "string" }],
    },
  ],
};

// Create Collection fron SDK Response ><><><><><>> :
create_collection_response = {
  success: True,
  message: "Collections 'City' created successfully",
  collections: [
    {
      name: "City",
      id: "6779a9560b4dcf4165ddc043",
      fields: [
        { name: "name", type: "string" },
        { name: "zipcode", type: "string" },
      ],
    },
  ],
  database: { total_collections: 2, total_fields: 3 },
};

// Add Document fron SDK Response ><><><><><>> :
add_document_response = {
  success: True,
  message: "Documents inserted successfully",
  inserted_ids: ["6779c429d04a9c8acc05033b"],
};

// Read Document fron SDK Response ><><><><><>> :
data_read_response = {
  success: True,
  message: "Data fetched successfully",
  data: [
    {
      _id: "6779c429d04a9c8acc05033b",
      name: "City",
      zipcode: "12345",
      is_deleted: False,
    },
  ],
  pagination: { total_records: 1, current_page: 1, page_size: 50 },
};
