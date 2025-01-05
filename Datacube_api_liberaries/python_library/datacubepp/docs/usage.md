# Usage Guide for `APIClient`

## Overview

The `APIClient` package allows seamless interaction with a backend API for managing databases, collections, and their associated CRUD operations. This guide provides step-by-step instructions for using the client and leveraging its powerful capabilities.

---

## Table of Contents

1. [Installation](#installation)
2. [Initialization](#initialization)
3. [Method Descriptions](#method-descriptions)
4. [Examples](#examples)
5. [Error Handling](#error-handling)

---

## Installation

You can install the `APIClient` package using `pip`:

```bash
pip install datacubepp
```

---

## Initialization

To get started, import and initialize the `APIClient` with your API key:

```python
from datacubepp.client import APIClient

# Initialize the client
client = APIClient(api_key="your_api_key")
```

---

## Method Descriptions

### Database Operations

#### `create_database`

Create a new database with specified collections.

```python
response = client.create_database(
    db_name="my_database",
    collections=[
        {"name": "users", "fields": [{"name": "username", "type": "string"}]}
    ]
)
```

#### `list_databases`

Retrieve a list of all available databases.

```python
response = client.list_databases()
```

### Collection Operations

#### `create_collection`

Add collections to an existing database.

```python
response = client.create_collection(
    database_id="your_database_id",
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
```

#### `list_collections`

Retrieve a list of collections in a specified database.

```python
response = client.list_collections(database_id="your_database_id")
```

### CRUD Operations

#### `create`

Insert documents into a collection.

```python
response = client.create(
    database_id="your_database_id",
    collection_name="users",
    data={"username": "johndoe", "email": "john@example.com"}
)
```

#### `read`

Fetch documents from a collection.

```python
response = client.read(
    database_id="your_database_id",
    collection_name="users",
    filters={"username": "johndoe"},
    limit=10
)
```

#### `update`

Update documents in a collection.

```python
response = client.update(
    database_id="your_database_id",
    collection_name="users",
    filters={"username": "johndoe"},
    update_data={"email": "new_email@example.com"}
)
```

#### `delete`

Delete documents from a collection.

```python
response = client.delete(
    database_id="your_database_id",
    collection_name="users",
    filters={"username": "johndoe"},
    soft_delete=True
)
```

### Metadata

#### `get_metadata`

Retrieve metadata for a specific database.

```python
response = client.get_metadata(database_id="your_database_id")
```

---

## Examples

### Create a Database

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

### Add a Collection

```python
response = client.create_collection(
    database_id="your_database_id",
    collections=[
        {
            "name": "orders",
            "fields": [
                {"name": "order_id", "type": "string"},
                {"name": "amount", "type": "number"}
            ]
        }
    ]
)
print(response)
```

### Insert a Document

```python
response = client.create(
    database_id="your_database_id",
    collection_name="orders",
    data={"order_id": "12345", "amount": 250}
)
print(response)
```

### Retrieve Documents

```python
response = client.read(
    database_id="your_database_id",
    collection_name="orders",
    filters={"order_id": "12345"},
    limit=5
)
print(response)
```

### Update a Document

```python
response = client.update(
    database_id="your_database_id",
    collection_name="orders",
    filters={"order_id": "12345"},
    update_data={"amount": 300}
)
print(response)
```

### Delete a Document

```python
response = client.delete(
    database_id="your_database_id",
    collection_name="orders",
    filters={"order_id": "12345"},
    soft_delete=True
)
print(response)
```

---

## Error Handling

The `APIClient` raises custom exceptions for better debugging and validation. These include:

- `ValidationError`: Raised for invalid inputs.
- `APIError`: Raised for API-level errors.

Example:

```python
try:
    response = client.create(
        database_id="invalid_id",
        collection_name="users",
        data={"username": "johndoe"}
    )
except ValidationError as ve:
    print(f"Validation Error: {ve}")
except APIError as ae:
    print(f"API Error: {ae}")
```

---
