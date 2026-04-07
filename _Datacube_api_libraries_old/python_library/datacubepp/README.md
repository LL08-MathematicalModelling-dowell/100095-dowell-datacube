# `APIClient` Project Documentation

## Overview

The `APIClient` is a Python library that simplifies interaction with a backend API for managing databases, collections, and their associated CRUD operations. This documentation provides an overview of the library, its features, installation steps, and usage examples.

---

## Table of Contents

1. [Features](#features)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Examples](#examples)
5. [Development](#development)
6. [Contributing](#contributing)
7. [License](#license)

---

## Features

- **Database Management:** Create, list, and delete databases.
- **Collection Management:** Add, list, and manage collections within databases.
- **CRUD Operations:** Perform create, read, update, and delete operations on documents within collections.
- **Validation:** Built-in input validation to ensure data integrity.
- **Error Handling:** Custom exceptions for streamlined debugging.

---

## Installation

To install the `APIClient`, use pip:

```bash
pip install datacubepp
```

---

## Quick Start

### Initialization

```python
from datacubepp.client import APIClient

# Initialize the client
client = APIClient(api_key="your_api_key")
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

## Development

### Setting Up

1. Clone the repository:

   ```bash
   git clone https://github.com/LL08-MathematicalModelling-dowell/100095-dowell-datacube.git
   ```

2. Navigate to the project directory:

   ```bash
   cd datacubepp
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

### Running Tests

Run tests using `pytest`:

```bash
pytest
```

Check code coverage:

```bash
pytest --cov=datacubepp
```

### Linting and Type Checking

Ensure your code adheres to standards:

```bash
black .
pylint datacubepp
mypy datacubepp
```

---

## Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository and create a new branch.
2. Make your changes and write tests for any new functionality.
3. Run the tests to ensure everything works correctly.
4. Submit a pull request with a clear description of your changes.

---

## License

This project is licensed under License. See the `LICENSE` file for details.
