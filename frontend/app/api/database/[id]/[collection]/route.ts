// app/api/database/[id]/collections/[collection]/route.ts
import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import client from "@/lib/mongodb";
import { prisma } from "@/prisma/client";
import { getUserId } from "@/lib/getUserId";
import { logOperation } from "@/lib/logOperation";
import { ObjectId } from "mongodb";
import { OperationType, ResourceType } from "@prisma/client";

// — Zod schemas —
const getQuerySchema = z.object({
  page: z
    .string()
    .optional()
    .transform((v) => parseInt(v || "1")),
  pageSize: z
    .string()
    .optional()
    .transform((v) => parseInt(v || "10")),
  filters: z.string().optional(),
});

const postSchema = z.object({
  data: z.union([z.record(z.any()), z.array(z.record(z.any()))]),
});

const putSchema = z.object({
  data: z.record(z.any()).refine((d) => d._id, "Missing _id"),
});

const deleteSchema = z.object({
  documentId: z.string().min(1),
});

// — Helper to find real DB name for user —
async function getDatabaseName(userId: string, databaseId: string) {
  const dbMeta = await prisma.databaseMetadata.findFirst({
    where: { id: databaseId, metadata: { userId } },
  });
  return dbMeta?.name;
}

// — GET documents —
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string; collection: string }> }
) {
  const { id: databaseId, collection: collName } = await params;
  let mongoClient;

  try {
    const userId = await getUserId();
    if (!userId)
      return NextResponse.json(
        { success: false, message: "Unauthorized" },
        { status: 401 }
      );

    // parse pagination + filters
    const query = getQuerySchema.safeParse({
      page: request.nextUrl.searchParams.get("page"),
      pageSize: request.nextUrl.searchParams.get("pageSize"),
      filters: request.nextUrl.searchParams.get("filters"),
    });
    if (!query.success) {
      return NextResponse.json(
        { success: false, message: "Invalid query" },
        { status: 400 }
      );
    }
    const { page, pageSize, filters } = query.data;
    const filterObj = filters ? JSON.parse(filters) : {};

    // verify DB ownership
    const dbName = await getDatabaseName(userId, databaseId);
    if (!dbName)
      return NextResponse.json(
        { success: false, message: "DB not found" },
        { status: 404 }
      );

    // fetch from Mongo
    mongoClient = await client.connect();
    const coll = mongoClient.db(dbName).collection(collName);
    const total = await coll.countDocuments(filterObj);
    const docs = await coll
      .find(filterObj)
      .skip((page - 1) * pageSize)
      .limit(pageSize)
      .toArray();

    // log each READ
    await Promise.all(
      docs.map((d) =>
        logOperation(
          userId,
          OperationType.READ,
          ResourceType.DOCUMENT,
          d._id.toString(),
          1
        )
      )
    );

    return NextResponse.json({
      success: true,
      data: docs,
      pagination: { page, pageSize, total },
    });
  } catch (e) {
    console.error("GET docs error", e);
    return NextResponse.json(
      { success: false, message: "Server error" },
      { status: 500 }
    );
  } finally {
    await client.close();
  }
}

// — POST create doc(s) —
export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string; collection: string }> }
) {
  const { id: databaseId, collection: collName } = await params;
  let mongoClient;

  try {
    const userId = await getUserId();
    if (!userId)
      return NextResponse.json(
        { success: false, message: "Unauthorized" },
        { status: 401 }
      );

    const { data } = postSchema.parse(await request.json());
    const dbName = await getDatabaseName(userId, databaseId);
    if (!dbName)
      return NextResponse.json(
        { success: false, message: "DB not found" },
        { status: 404 }
      );

    mongoClient = await client.connect();
    const coll = mongoClient.db(dbName).collection(collName);
    let result;

    if (Array.isArray(data)) {
      result = await coll.insertMany(data);
      // one log entry, count = insertedCount
      await logOperation(
        userId,
        OperationType.WRITE,
        ResourceType.DOCUMENT,
        collName,
        result.insertedCount
      );
      return NextResponse.json(
        {
          success: true,
          message: "Bulk insert OK",
          insertedCount: result.insertedCount,
        },
        { status: 201 }
      );
    } else {
      result = await coll.insertOne(data);
      await logOperation(
        userId,
        OperationType.WRITE,
        ResourceType.DOCUMENT,
        result.insertedId.toString(),
        1
      );
      return NextResponse.json(
        {
          success: true,
          message: "Insert OK",
          insertedId: result.insertedId.toString(),
        },
        { status: 201 }
      );
    }
  } catch (e) {
    console.error("POST doc error", e);
    if (e instanceof z.ZodError) {
      return NextResponse.json(
        { success: false, errors: e.errors },
        { status: 400 }
      );
    }
    return NextResponse.json(
      { success: false, message: "Server error" },
      { status: 500 }
    );
  } finally {
    await client.close();
  }
}

// — PUT update one doc —
export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ id: string; collection: string }> }
) {
  const { id: databaseId, collection: collName } = await params;
  let mongoClient;

  try {
    const userId = await getUserId();
    if (!userId)
      return NextResponse.json(
        { success: false, message: "Unauthorized" },
        { status: 401 }
      );

    const { data } = putSchema.parse(await request.json());
    const { _id, ...upd } = data;
    const objId = new ObjectId(_id);
    const dbName = await getDatabaseName(userId, databaseId);
    if (!dbName)
      return NextResponse.json(
        { success: false, message: "DB not found" },
        { status: 404 }
      );

    mongoClient = await client.connect();
    const coll = mongoClient.db(dbName).collection(collName);
    const res = await coll.updateOne({ _id: objId }, { $set: upd });
    if (res.matchedCount === 0) {
      return NextResponse.json(
        { success: false, message: "Not found" },
        { status: 404 }
      );
    }

    // log one WRITE = 1 update
    await logOperation(
      userId,
      OperationType.WRITE,
      ResourceType.DOCUMENT,
      _id.toString(),
      1
    );

    return NextResponse.json({ success: true, message: "Updated OK" });
  } catch (e) {
    console.error("PUT doc error", e);
    if (e instanceof z.ZodError) {
      return NextResponse.json(
        { success: false, errors: e.errors },
        { status: 400 }
      );
    }
    return NextResponse.json(
      { success: false, message: "Server error" },
      { status: 500 }
    );
  } finally {
    await client.close();
  }
}

// — DELETE one doc —
export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ id: string; collection: string }> }
) {
  const { id: databaseId, collection: collName } = await params;
  let mongoClient;

  try {
    const userId = await getUserId();
    if (!userId)
      return NextResponse.json(
        { success: false, message: "Unauthorized" },
        { status: 401 }
      );

    const { documentId } = deleteSchema.parse(await request.json());
    const objId = new ObjectId(documentId);
    const dbName = await getDatabaseName(userId, databaseId);
    if (!dbName)
      return NextResponse.json(
        { success: false, message: "DB not found" },
        { status: 404 }
      );

    mongoClient = await client.connect();
    const coll = mongoClient.db(dbName).collection(collName);
    const res = await coll.deleteOne({ _id: objId });

    if (res.deletedCount === 0) {
      return NextResponse.json(
        { success: false, message: "Not found" },
        { status: 404 }
      );
    }

    // log one DELETE = deletedCount
    await logOperation(
      userId,
      OperationType.DELETE,
      ResourceType.DOCUMENT,
      documentId,
      res.deletedCount
    );

    return NextResponse.json({ success: true, message: "Deleted OK" });
  } catch (e) {
    console.error("DELETE doc error", e);
    if (e instanceof z.ZodError) {
      return NextResponse.json(
        { success: false, errors: e.errors },
        { status: 400 }
      );
    }
    return NextResponse.json(
      { success: false, message: "Server error" },
      { status: 500 }
    );
  } finally {
    await client.close();
  }
}

// // app/api/database/[id]/collections/[collection]/route.ts
// import { NextRequest, NextResponse } from "next/server";
// import { z } from "zod";
// import client from "@/lib/mongodb";
// import { prisma } from "@/prisma/client";
// import { getUserId } from "@/lib/getUserId";
// import { logOperation } from "@/lib/logOperation";
// import { ObjectId } from "mongodb";
// import { OperationType, ResourceType } from "@prisma/client";

// // Zod schemas
// const getQuerySchema = z.object({
//   page: z
//     .string()
//     .optional()
//     .transform((v) => parseInt(v || "1")),
//   pageSize: z
//     .string()
//     .optional()
//     .transform((v) => parseInt(v || "10")),
//   filters: z.string().optional(),
// });

// const postSchema = z.object({
//   data: z.union([z.record(z.any()), z.array(z.record(z.any()))]),
// });

// const putSchema = z.object({
//   data: z.record(z.any()).refine((d) => d._id, "Missing _id field"),
// });

// const deleteSchema = z.object({
//   documentId: z.string().min(1),
// });

// // Helper: fetch and verify the DB name for this user + databaseId
// async function getDatabaseName(userId: string, databaseId: string) {
//   const dbMeta = await prisma.databaseMetadata.findFirst({
//     where: { id: databaseId, metadata: { userId } },
//   });
//   return dbMeta?.name;
// }

// // GET documents with pagination & filters
// export async function GET(
//   request: NextRequest,
//   { params }: { params: Promise<{ id: string; collection: string }> }
// ) {
//   const { id: databaseId, collection: collectionName } = await params;
//   let mongoClient;

//   try {
//     // Auth
//     const userId = await getUserId();
//     if (!userId)
//       return NextResponse.json(
//         { success: false, message: "Unauthorized" },
//         { status: 401 }
//       );

//     // Query params
//     const query = getQuerySchema.safeParse({
//       page: request.nextUrl.searchParams.get("page"),
//       pageSize: request.nextUrl.searchParams.get("pageSize"),
//       filters: request.nextUrl.searchParams.get("filters"),
//     });
//     if (!query.success) {
//       return NextResponse.json(
//         { success: false, message: "Invalid query parameters" },
//         { status: 400 }
//       );
//     }
//     const { page, pageSize, filters } = query.data;
//     const filterObj = filters ? JSON.parse(filters) : {};

//     // Verify DB
//     const dbName = await getDatabaseName(userId, databaseId);
//     if (!dbName)
//       return NextResponse.json(
//         { success: false, message: "Database not found" },
//         { status: 404 }
//       );

//     // Connect Mongo
//     mongoClient = await client.connect();
//     const coll = mongoClient.db(dbName).collection(collectionName);

//     // Fetch & paginate
//     const total = await coll.countDocuments(filterObj);
//     const docs = await coll
//       .find(filterObj)
//       .skip((page - 1) * pageSize)
//       .limit(pageSize)
//       .toArray();

//     // Log read per document
//     await Promise.all(
//       docs.map((doc) =>
//         logOperation(
//           userId,
//           OperationType.READ,
//           ResourceType.DOCUMENT,
//           doc._id.toString()
//         )
//       )
//     );

//     return NextResponse.json(
//       {
//         success: true,
//         data: docs,
//         pagination: { page, pageSize, total },
//       },
//       { status: 200 }
//     );
//   } catch (err) {
//     console.error("GET docs error:", err);
//     return NextResponse.json(
//       { success: false, message: "Internal Server Error" },
//       { status: 500 }
//     );
//   } finally {
//     await client.close();
//   }
// }

// // POST create document(s)
// export async function POST(
//   request: NextRequest,
//   { params }: { params: Promise<{ id: string; collection: string }> }
// ) {
//   const { id: databaseId, collection: collectionName } = await params;
//   let mongoClient;

//   try {
//     const userId = await getUserId();
//     if (!userId)
//       return NextResponse.json(
//         { success: false, message: "Unauthorized" },
//         { status: 401 }
//       );

//     // Validate body
//     const { data } = postSchema.parse(await request.json());

//     // Verify DB
//     const dbName = await getDatabaseName(userId, databaseId);
//     if (!dbName)
//       return NextResponse.json(
//         { success: false, message: "Database not found" },
//         { status: 404 }
//       );

//     // Connect & insert
//     mongoClient = await client.connect();
//     const coll = mongoClient.db(dbName).collection(collectionName);
//     let result;

//     if (Array.isArray(data)) {
//       result = await coll.insertMany(data);
//       // Log each new doc
//       await Promise.all(
//         Object.values(result.insertedIds).map((id) =>
//           logOperation(
//             userId,
//             OperationType.WRITE,
//             ResourceType.DOCUMENT,
//             id.toString()
//           )
//         )
//       );
//     } else {
//       result = await coll.insertOne(data);
//       await logOperation(
//         userId,
//         OperationType.WRITE,
//         ResourceType.DOCUMENT,
//         result.insertedId.toString()
//       );
//     }

//     return NextResponse.json(
//       {
//         success: true,
//         message: "Document(s) created successfully.",
//         inserted:
//           Array.isArray(data) && "insertedIds" in result
//             ? Object.values(result.insertedIds)
//             : "insertedId" in result
//             ? result.insertedId
//             : null,
//       },
//       { status: 201 }
//     );
//   } catch (err) {
//     console.error("POST doc error:", err);
//     if (err instanceof z.ZodError) {
//       return NextResponse.json(
//         { success: false, errors: err.errors },
//         { status: 400 }
//       );
//     }
//     return NextResponse.json(
//       { success: false, message: "Internal Server Error" },
//       { status: 500 }
//     );
//   } finally {
//     await client.close();
//   }
// }

// // PUT update a single document
// export async function PUT(
//   request: NextRequest,
//   { params }: { params: Promise<{ id: string; collection: string }> }
// ) {
//   const { id: databaseId, collection: collectionName } = await params;
//   let mongoClient;

//   try {
//     const userId = await getUserId();
//     if (!userId)
//       return NextResponse.json(
//         { success: false, message: "Unauthorized" },
//         { status: 401 }
//       );

//     // Validate body
//     const { data } = putSchema.parse(await request.json());
//     const { _id, ...fieldsToUpdate } = data;
//     const objId = new ObjectId(_id);

//     // Verify DB
//     const dbName = await getDatabaseName(userId, databaseId);
//     if (!dbName)
//       return NextResponse.json(
//         { success: false, message: "Database not found" },
//         { status: 404 }
//       );

//     // Connect & update
//     mongoClient = await client.connect();
//     const coll = mongoClient.db(dbName).collection(collectionName);
//     const result = await coll.updateOne(
//       { _id: objId },
//       { $set: fieldsToUpdate }
//     );

//     if (result.matchedCount === 0) {
//       return NextResponse.json(
//         { success: false, message: "Document not found" },
//         { status: 404 }
//       );
//     }

//     // Log write
//     await logOperation(userId, OperationType.WRITE, ResourceType.DOCUMENT, _id);

//     return NextResponse.json(
//       { success: true, message: "Document updated successfully." },
//       { status: 200 }
//     );
//   } catch (err) {
//     console.error("PUT doc error:", err);
//     if (err instanceof z.ZodError) {
//       return NextResponse.json(
//         { success: false, errors: err.errors },
//         { status: 400 }
//       );
//     }
//     return NextResponse.json(
//       { success: false, message: "Internal Server Error" },
//       { status: 500 }
//     );
//   } finally {
//     await client.close();
//   }
// }

// // DELETE a document
// export async function DELETE(
//   request: NextRequest,
//   { params }: { params: Promise<{ id: string; collection: string }> }
// ) {
//   const { id: databaseId, collection: collectionName } = await params;
//   let mongoClient;

//   try {
//     const userId = await getUserId();
//     if (!userId)
//       return NextResponse.json(
//         { success: false, message: "Unauthorized" },
//         { status: 401 }
//       );

//     // Validate body
//     const { documentId } = deleteSchema.parse(await request.json());
//     const objId = new ObjectId(documentId);

//     // Verify DB
//     const dbName = await getDatabaseName(userId, databaseId);
//     if (!dbName)
//       return NextResponse.json(
//         { success: false, message: "Database not found" },
//         { status: 404 }
//       );

//     // Connect & delete
//     mongoClient = await client.connect();
//     const coll = mongoClient.db(dbName).collection(collectionName);
//     const result = await coll.deleteOne({ _id: objId });

//     if (result.deletedCount === 0) {
//       return NextResponse.json(
//         { success: false, message: "Document not found" },
//         { status: 404 }
//       );
//     }

//     // Log write
//     await logOperation(
//       userId,
//       OperationType.WRITE,
//       ResourceType.DOCUMENT,
//       documentId
//     );

//     return NextResponse.json(
//       { success: true, message: "Document deleted successfully." },
//       { status: 200 }
//     );
//   } catch (err) {
//     console.error("DELETE doc error:", err);
//     if (err instanceof z.ZodError) {
//       return NextResponse.json(
//         { success: false, errors: err.errors },
//         { status: 400 }
//       );
//     }
//     return NextResponse.json(
//       { success: false, message: "Internal Server Error" },
//       { status: 500 }
//     );
//   } finally {
//     await client.close();
//   }
// }
