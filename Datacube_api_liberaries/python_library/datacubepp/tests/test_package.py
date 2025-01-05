""" Tests for the datacubepp package. """
from datacubepp.client import APIClient

API_KEY = "test_api_key"

client = APIClient(api_key=API_KEY)

# create_db_response = client.create_database("test_db_from_SDK", [
#     {"name": "users", "fields": [{"name": "username", "type": "string"}]}
# ])

# print(f"Create Database fron SDK Response ><><><><><>> : \n{create_db_response}")


# create_collection_response = client.create_collection(
#     database_id="677967f14498f63691764217",
#     collections= [
#         {
#             "name": "City",
#             "fields": [
#                 {"name": "name", "type": "string"},
#                 {"name": "zipcode", "type": "string"}
#             ]
#         }
#     ]
# )

# print(f"Create Collection fron SDK Response ><><><><><>> : \n{create_collection_response}")


# list_collections_response = client.list_collections(database_id="677967f14498f63691764217")

# print(f"List Collections fron SDK Response ><><><><><>> : \n{list_collections_response}")



# add_document_respoonse = client.create(
#     database_id="677967f14498f63691764217",
#     collection_name="City",
#     data={
#         "name": "City",
#         "zipcode": "12345"
#     }
# )

# print(f"Add Document fron SDK Response ><><><><><>> : \n{add_document_respoonse}")


document_read_response = client.read(database_id="677967f14498f63691764217", collection_name="City")

print(f"Read Document fron SDK Response ><><><><><>> : \n{document_read_response}")
