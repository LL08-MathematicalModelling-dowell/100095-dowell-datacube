# APIClient Documentation

## Overview

The `APIClient` is a TypeScript library designed to provide an easy and consistent interface for interacting with a backend API for database and collection management. It includes methods for CRUD operations, collection management, and metadata retrieval.

---

## Installation

Install the package via npm or yarn:

```bash
npm install datacubenp
```

or

```bash
yarn add datacubenp
```

---

## Initialization

To start using the APIClient, you need an API key for authentication. Import and initialize the client as shown below:

```typescript
import { APIClient } from "datacubenp";

const API_KEY = "your_api_key";
const client = new APIClient(API_KEY);
```

---

## Methods Overview

### Database Management

#### `createDatabase(payload: CreateDatabasePayload): Promise<any>`
Create a new database with specified collections.

```typescript
const payload = {
  dbName: "test_db",
  collections: [
    { name: "users", fields: [{ name: "username", type: "string" }] },
  ],
};

const response = await client.createDatabase(payload);
console.log(response);
```

#### `dropDatabase(databaseId: string): Promise<any>`
Delete a specified database.

```typescript
const response = await client.dropDatabase("database_id");
console.log(response);
```

### Collection Management

#### `createCollection(payload: CreateCollectionPayload): Promise<any>`
Add collections to an existing database.

```typescript
const payload = {
  databaseId: "database_id",
  collections: [
    {
      name: "products",
      fields: [
        { name: "productName", type: "string" },
        { name: "price", type: "number" },
      ],
    },
  ],
};

const response = await client.createCollection(payload);
console.log(response);
```

#### `listCollections(databaseId: string): Promise<any>`
Retrieve all collections within a specific database.

```typescript
const response = await client.listCollections("database_id");
console.log(response);
```

#### `dropCollections(payload: { databaseId: string; collectionNames: string[] }): Promise<any>`
Remove specific collections from a database.

```typescript
const payload = {
  databaseId: "database_id",
  collectionNames: ["users", "products"],
};

const response = await client.dropCollections(payload);
console.log(response);
```

### CRUD Operations

#### `create(payload: CrudPayload): Promise<any>`
Insert new documents into a collection.

```typescript
const payload = {
  databaseId: "database_id",
  collectionName: "users",
  data: { username: "johndoe", email: "john@example.com" },
};

const response = await client.create(payload);
console.log(response);
```

#### `read(payload: ReadPayload): Promise<any>`
Retrieve documents from a collection.

```typescript
const payload = {
  databaseId: "database_id",
  collectionName: "users",
  filters: { username: "johndoe" },
  limit: 10,
  offset: 0,
};

const response = await client.read(payload);
console.log(response);
```

#### `update(payload: UpdatePayload): Promise<any>`
Update existing documents in a collection.

```typescript
const payload = {
  databaseId: "database_id",
  collectionName: "users",
  filters: { username: "johndoe" },
  updateData: { email: "new_email@example.com" },
};

const response = await client.update(payload);
console.log(response);
```

#### `delete(payload: DeletePayload): Promise<any>`
Delete documents from a collection.

```typescript
const payload = {
  databaseId: "database_id",
  collectionName: "users",
  filters: { username: "johndoe" },
  softDelete: true,
};

const response = await client.delete(payload);
console.log(response);
```

### Metadata

#### `get_metadata(payload: { database_id: string }): Promise<any>`
Retrieve metadata for a specific database.

```typescript
const response = await client.get_metadata({ database_id: "database_id" });
console.log(response);
```

---

## Error Handling

All API errors throw exceptions that can be caught and handled gracefully. The library provides two main exception classes:

- `APIError`: Raised for API-specific issues such as authentication failures or server errors.
- `ValidationError`: Raised for input validation issues.

```typescript
try {
  const response = await client.createDatabase({
    dbName: "invalid_db",
    collections: [],
  });
} catch (error) {
  if (error instanceof ValidationError) {
    console.error("Validation Error: ", error.message);
  } else if (error instanceof APIError) {
    console.error("API Error: ", error.message);
  } else {
    console.error("Unexpected Error: ", error);
  }
}
```

---

## Testing

The library includes comprehensive unit tests to validate its functionality. Use the following command to run the tests:

```bash
npx jest client.test.ts
```

---

## Contributing

Contributions are welcome! Please follow these steps to contribute:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Write unit tests for your changes.
4. Submit a pull request with a detailed description of your changes.

---

## License

This library is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.
