## Usage

### Installation

To install the `APIClient`, run:

```bash
pip install datacubepp
```

---

## Initialization

Initialize the `APIClient` by importing it and providing the required API key:

```python
from datacubepp.client import APIClient

# Initialize the APIClient
client = APIClient(api_key="your_api_key")
```

---

## Methods Overview

### Database Operations

- `create_database(db_name: str, collections: list[dict])`  
  Create a new database with collections.

- `list_databases()`  
  Retrieve a list of all databases.

### Collection Operations

- `create_collection(database_id: str, collections: list[dict])`  
  Add new collections to an existing database.

- `list_collections(database_id: str)`  
  List collections in a specified database.

### CRUD Operations

- `create(database_id: str, collection_name: str, data: dict)`  
  Insert documents into a collection.

- `read(database_id: str, collection_name: str, filters: dict = None, limit: int = 50, offset: int = 0)`  
  Fetch documents from a collection.

- `update(database_id: str, collection_name: str, filters: dict, update_data: dict)`  
  Update documents in a collection.

- `delete(database_id: str, collection_name: str, filters: dict, soft_delete: bool = True)`  
  Delete documents from a collection.

### Metadata

- `get_metadata(database_id: str)`  
  Retrieve metadata for a specified database.

---

## Examples

### Creating a Database

```python
response = client.create_database(
    db_name="example_db",
    collections=[
        {
            "name": "users",
            "fields": [
                {"name": "username", "type": "string"},
                {"name": "email", "type": "string"}
            ]
        }
    ]
)
print(response)
```

### Adding a Collection

```python
response = client.create_collection(
    database_id="677967f14498f63691764217",
    collections=[
        {
            "name": "products",
            "fields": [
                {"name": "product_name", "type": "string"},
                {"name": "price", "type": "number"}
            ]
        }
    ]
)
print(response)
```

### CRUD Operations

#### Create Documents

```python
response = client.create(
    database_id="677967f14498f63691764217",
    collection_name="users",
    data={"username": "johndoe", "email": "john@example.com"}
)
print(response)
```

#### Read Documents

```python
response = client.read(
    database_id="677967f14498f63691764217",
    collection_name="users",
    filters={"username": "johndoe"},
    limit=10
)
print(response)
```

#### Update Documents

```python
response = client.update(
    database_id="677967f14498f63691764217",
    collection_name="users",
    filters={"username": "johndoe"},
    update_data={"email": "new_email@example.com"}
)
print(response)
```

#### Delete Documents

```python
response = client.delete(
    database_id="677967f14498f63691764217",
    collection_name="users",
    filters={"username": "johndoe"},
    soft_delete=True
)
print(response)
```

---
