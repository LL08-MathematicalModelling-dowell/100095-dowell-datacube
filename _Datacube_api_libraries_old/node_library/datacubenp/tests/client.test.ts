import { APIClient } from "../src";

describe("APIClient", () => {
  let client: APIClient;
  const API_KEY = "test_api_key";

  beforeEach(() => {
    client = new APIClient(API_KEY);
  });

  it("should create a database successfully", async () => {
    const payload = {
      dbName: "test_db",
      collections: [
        { name: "users", fields: [{ name: "username", type: "string" }] },
      ],
    };

    const response = await client.createDatabase(payload);

    expect(response.success).toBe(true);
    expect(response.message).toBe("Database created successfully.");
  });

  it("should list collections successfully", async () => {
    const databaseId = "677967f14498f63691764217";

    const response = await client.listCollections(databaseId);

    expect(response.success).toBe(true);
    expect(response.collections).toEqual(["users", "City"]);
  });

  it("should create a collection successfully", async () => {
    const payload = {
      databaseId: "677967f14498f63691764217",
      collections: [
        { name: "products", fields: [{ name: "productName", type: "string" }] },
      ],
    };

    const response = await client.createCollection(payload);

    expect(response.success).toBe(true);
    expect(response.message).toBe("Collection created successfully.");
  });

  it("should drop collections successfully", async () => {
    const payload = {
      databaseId: "677967f14498f63691764217",
      collectionNames: ["users", "products"],
    };

    const response = await client.dropCollections(payload);

    expect(response.success).toBe(true);
    expect(response.message).toBe("Collections dropped successfully.");
  });

  it("should drop a database successfully", async () => {
    const databaseId = "677967f14498f63691764217";

    const response = await client.dropDatabase(databaseId);

    expect(response.success).toBe(true);
    expect(response.message).toBe("Database dropped successfully.");
  });

  it("should create a document successfully", async () => {
    const payload = {
      databaseId: "677967f14498f63691764217",
      collectionName: "users",
      data: { username: "johndoe", email: "john@example.com" },
    };

    const response = await client.create(payload);

    expect(response.success).toBe(true);
    expect(response.message).toBe("Document created successfully.");
  });

  it("should read documents successfully", async () => {
    const payload = {
      databaseId: "677967f14498f63691764217",
      collectionName: "users",
      filters: { username: "johndoe" },
      limit: 10,
      offset: 0,
    };

    const response = await client.read(payload);

    expect(response.success).toBe(true);
    expect(response.data).toEqual([
      { username: "johndoe", email: "john@example.com" },
    ]);
  });

  it("should update documents successfully", async () => {
    const payload = {
      databaseId: "677967f14498f63691764217",
      collectionName: "users",
      filters: { username: "johndoe" },
      updateData: { email: "new_email@example.com" },
    };

    const response = await client.update(payload);

    expect(response.success).toBe(true);
    expect(response.message).toBe("Document updated successfully.");
  });

  it("should delete documents successfully", async () => {
    const payload = {
      databaseId: "677967f14498f63691764217",
      collectionName: "users",
      filters: { username: "johndoe" },
      softDelete: true,
    };

    const response = await client.delete(payload);

    expect(response.success).toBe(true);
    expect(response.message).toBe("Document deleted successfully.");
  });
});



// npx jest client.test.ts
