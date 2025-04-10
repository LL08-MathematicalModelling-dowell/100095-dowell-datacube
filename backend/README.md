# DatacubeV2 API Documentation

## Overview

Welcome to the **DatacubeV2 API** documentation! This API provides powerful database and collection management features for handling structured and unstructured data using MongoDB.

With **DatacubeV2**, you can:

- Create, read, update, and delete databases and collections.
- Perform CRUD operations on documents.
- Implement seamless database scaling with efficient data handling.

## Table of Contents

- [Getting Started](#getting-started)
- [API Base URL](#api-base-url)
- [Authentication](#authentication)
- [API Endpoints](#api-endpoints)
  - [Health Check](#health-check)
  - [Database Management](#database-management)
  - [Allowed Data Types](#allowed-data-types)
  - [Collection Management](#collection-management)
  - [CRUD Operations](#crud-operations)
- [Error Handling](#error-handling)
- [Contributing](#contributing)
- [License](#license)

---

## Getting Started

To start using the **DatacubeV2 API**, ensure you have the following:

- **An active API key** (if required for authentication)
- **Postman or cURL** for testing API requests
- **Python 3.7+** (for integrating into Python applications)
- **MongoDB instance** (if required for local database operations)

### Installation

If you plan to integrate this API into your application, ensure you have Python and the necessary libraries installed:

```bash
pip install requests
```

---

## API Base URL

All API requests should be made to the following base URL:

```
https://datacube.uxlivinglab.online/api/
```

Make sure you include this base URL when making requests to specific endpoints.

---

## Authentication

If authentication is required, include your API key in the request header as follows:

```http
Authorization: Bearer YOUR_API_KEY
```

Replace `YOUR_API_KEY` with your actual API key.

---

## API Endpoints

### Health Check

Check if the server is running:

```bash
curl -X GET https://datacube.uxlivinglab.online/health_check/
```

**Response:**

```json
{
  "success": true,
  "message": "Server is running fine"
}
```

### Database Management

#### Allowed Data Types:

1. "string" - Textual data
2. "number" - Numeric data
3. "object" - Embedded document
4. "array" - List of values
5. "boolean" - True/False
6. "date" - ISO 8601 date
7. "null" - Null value
8. "binary" - Binary data
9. "objectid" - ObjectId
10. "decimal128" - High-precision decimal
11. "regex" - Regular expression
12. "timestamp" - Timestamp

#### Create a Database

```bash
curl -X POST https://datacube.uxlivinglab.online/api/create_database/ \
    -H "Content-Type: application/json" \
    -d '{
        "db_name": "example_db",
        "collections": [
            {
                "name": "users",
                "fields": [
                    {"name": "username", "type": "string"},
                    {"name": "age", "type": "number"}
                ]
            }
        ]
    }'
```

### Collection Management

#### Add Collections

```bash
curl -X POST https://datacube.uxlivinglab.online/api/add_collection/ \
    -H "Content-Type: application/json" \
    -d '{
        "database_id": "your_database_id",
        "collections": [
            {
                "name": "products",
                "fields": [
                    {"name": "product_id", "type": "string"},
                    {"name": "price", "type": "number"}
                ]
            }
        ]
    }'
```

### CRUD Operations

#### Create Documents

```bash
curl -X POST https://datacube.uxlivinglab.online/api/crud/ \
    -H "Content-Type: application/json" \
    -d '{
        "database_id": "your_database_id",
        "collection_name": "users",
        "data": [
            {
                "username": "john_doe",
                "age": 30
            }
        ]
    }'
```

#### Read Documents

```bash
curl -X GET "https://datacube.uxlivinglab.online/api/crud?database_id=your_database_id&collection_name=users&filters={\"age\":{\"$gt\":25}}&limit=50&offset=0"
```

#### Update Documents

```bash
curl -X PUT https://datacube.uxlivinglab.online/api/crud/ \
    -H "Content-Type: application/json" \
    -d '{
        "database_id": "your_database_id",
        "collection_name": "users",
        "filters": {"username": "john_doe"},
        "update_data": {"age": 38}
    }'
```

#### Delete Documents

```bash
curl -X DELETE https://datacube.uxlivinglab.online/api/crud/ \
    -H "Content-Type: application/json" \
    -d '{
        "database_id": "your_database_id",
        "collection_name": "users",
        "filters": {"username": "john_doe"},
        "soft_delete": true
    }'
```

---

## Error Handling

All API responses include a success status and a message. Errors return appropriate HTTP status codes.

Example:

```json
{
  "success": false,
  "message": "Database with ID 'xyz' does not exist"
}
```

### Common Errors:

| Status Code | Meaning                                      |
| ----------- | -------------------------------------------- |
| 400         | Bad Request (Invalid parameters)             |
| 401         | Unauthorized (Invalid API key)               |
| 404         | Not Found (Database or Collection not found) |
| 500         | Internal Server Error (Server issues)        |

---

## Contributing

We welcome contributions! To contribute:

1. Fork the repository.
2. Create a new branch (`feature-branch`).
3. Make your changes and commit them.
4. Push to your fork and create a Pull Request.

---

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

---

## Contact

For support or inquiries, reach out via:

- 📧 Email: ...
- 📌 Website: [DatacubeV2](https://datacube.uxlivinglab.online)
