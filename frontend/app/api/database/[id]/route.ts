/* eslint-disable prefer-const */
// app/api/database/[id]/collections/route.ts
import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import client from "@/lib/mongodb";
import { prisma } from "@/prisma/client";
import { getUserId } from "@/lib/getUserId";
import { logOperation } from "@/lib/logOperation";
import type { MongoClient } from "mongodb";
import { OperationType, ResourceType } from "@prisma/client";

// Zod schemas
const collectionSchema = z.object({
  name: z.string().min(1),
  fields: z.array(z.string()).optional().default([]),
});

const updateSchema = z.object({
  oldName: z.string().min(1),
  newName: z.string().min(1).optional(),
  addFields: z.array(z.string()).optional(),
  removeFields: z.array(z.string()).optional(),
});

// Helper: fetch user’s DB name
async function getDatabaseName(userId: string, databaseId: string) {
  const dbMeta = await prisma.databaseMetadata.findFirst({
    where: { id: databaseId, metadata: { userId } },
  });
  return dbMeta?.name;
}

// GET: list collections with counts
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id: databaseId } = await params;
  let mongoClient: MongoClient | null = null;

  try {
    // 1) Auth
    const userId = await getUserId();
    if (!userId) {
      return NextResponse.json(
        { success: false, message: "Unauthorized" },
        { status: 401 }
      );
    }

    // 2) Fetch metadata + collections
    const dbMeta = await prisma.databaseMetadata.findFirst({
      where: { id: databaseId, metadata: { userId } },
      include: { collections: true },
    });
    if (!dbMeta) {
      return NextResponse.json(
        { success: false, message: "Database not found" },
        { status: 404 }
      );
    }

    // 3) Connect & verify Mongo DB exists
    mongoClient = await client.connect();
    const dbList = await mongoClient.db().admin().listDatabases();
    if (!dbList.databases.some((db) => db.name === dbMeta.name)) {
      return NextResponse.json(
        { success: false, message: "MongoDB DB missing" },
        { status: 404 }
      );
    }

    // 4) List and count
    const existingNames = (
      await mongoClient.db(dbMeta.name).listCollections().toArray()
    ).map((c) => c.name);

    const collectionsWithCount = await Promise.all(
      dbMeta.collections.map(async (col) => {
        const exists = existingNames.includes(col.name);
        const numDocuments = exists
          ? await mongoClient!
              .db(dbMeta.name)
              .collection(col.name)
              .countDocuments()
          : 0;
        return {
          id: col.id,
          name: col.name,
          fields: col.fields,
          numDocuments,
        };
      })
    );

    // 5) Log a READ on each collection
    await Promise.all(
      collectionsWithCount.map((col) =>
        logOperation(
          userId,
          OperationType.READ,
          ResourceType.COLLECTION,
          col.id
        )
      )
    );

    return NextResponse.json({
      success: true,
      collections: collectionsWithCount,
    });
  } catch (err) {
    console.error("GET collections error:", err);
    return NextResponse.json(
      { success: false, message: "Internal Server Error" },
      { status: 500 }
    );
  } finally {
    if (mongoClient) await client.close();
  }
}

// POST: create a new collection
export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id: databaseId } = await params;
  let mongoClient: MongoClient | null = null;
  let createdMeta: { id: string; name: string; fields: string[] } = {
    id: "",
    name: "",
    fields: [],
  };

  try {
    // 1) Auth
    const userId = await getUserId();
    if (!userId) {
      return NextResponse.json(
        { success: false, message: "Unauthorized" },
        { status: 401 }
      );
    }

    // 2) Validate input
    const parsed = collectionSchema.safeParse(await request.json());
    if (!parsed.success) {
      return NextResponse.json(
        { success: false, errors: parsed.error.errors },
        { status: 400 }
      );
    }
    const { name, fields } = parsed.data;

    // 3) Verify metadata
    const dbName = await getDatabaseName(userId, databaseId);
    if (!dbName) {
      return NextResponse.json(
        { success: false, message: "Database not found" },
        { status: 404 }
      );
    }

    // 4) Connect & check existing
    mongoClient = await client.connect();
    const mongoNames = (
      await mongoClient.db(dbName).listCollections().toArray()
    ).map((c) => c.name);

    const existsMeta = await prisma.collectionMetadata.findFirst({
      where: { name, databaseMetadataId: databaseId },
    });
    if (mongoNames.includes(name) || existsMeta) {
      return NextResponse.json(
        { success: false, message: "Collection exists" },
        { status: 409 }
      );
    }

    // 5) Create in a transaction
    const session = mongoClient.startSession();
    await session.withTransaction(async () => {
      await mongoClient!.db(dbName).createCollection(name, { session });
      createdMeta = await prisma.collectionMetadata.create({
        data: {
          name,
          fields,
          databaseMetadata: { connect: { id: databaseId } },
        },
      });
    });
    session.endSession();

    // 6) Log WRITE
    if (createdMeta && createdMeta.id) {
      await logOperation(
        userId,
        OperationType.WRITE,
        ResourceType.COLLECTION,
        createdMeta.id
      );
    }

    return NextResponse.json(
      { success: true, message: "Collection created", id: createdMeta?.id },
      { status: 201 }
    );
  } catch (err) {
    console.error("POST collections error:", err);
    return NextResponse.json(
      { success: false, message: "Internal Server Error" },
      { status: 500 }
    );
  } finally {
    if (mongoClient) await client.close();
  }
}

// PUT: rename collection / add or remove fields
export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id: databaseId } = await params;
  let mongoClient: MongoClient | null = null;

  try {
    // 1) Auth
    const userId = await getUserId();
    if (!userId) {
      return NextResponse.json(
        { success: false, message: "Unauthorized" },
        { status: 401 }
      );
    }

    // 2) Validate
    const parsed = updateSchema.safeParse(await request.json());
    if (!parsed.success) {
      return NextResponse.json(
        { success: false, errors: parsed.error.errors },
        { status: 400 }
      );
    }
    let { oldName, newName, addFields = [], removeFields = [] } = parsed.data;

    // 3) Load metadata
    const colMeta = await prisma.collectionMetadata.findFirst({
      where: {
        name: oldName,
        databaseMetadata: { id: databaseId, metadata: { userId } },
      },
    });
    if (!colMeta) {
      return NextResponse.json(
        { success: false, message: "Collection metadata not found" },
        { status: 404 }
      );
    }

    // 4) Verify DB
    const dbName = await getDatabaseName(userId, databaseId);
    if (!dbName) {
      return NextResponse.json(
        { success: false, message: "Database not found" },
        { status: 404 }
      );
    }

    // 5) Connect & check old collection
    mongoClient = await client.connect();
    const existingNames = (
      await mongoClient.db(dbName).listCollections().toArray()
    ).map((c) => c.name);
    if (!existingNames.includes(oldName)) {
      return NextResponse.json(
        { success: false, message: "MongoDB collection not found" },
        { status: 404 }
      );
    }

    // 6) Rename if requested
    if (newName && newName !== oldName) {
      if (existingNames.includes(newName)) {
        return NextResponse.json(
          { success: false, message: "New name already in use" },
          { status: 409 }
        );
      }
      await mongoClient.db(dbName).collection(oldName).rename(newName);
      await prisma.collectionMetadata.update({
        where: { id: colMeta.id },
        data: { name: newName },
      });
      oldName = newName;
    }

    // 7) Update fields list
    const current = new Set(colMeta.fields);
    addFields.forEach((f) => current.add(f));
    removeFields.forEach((f) => current.delete(f));
    const updatedFields = Array.from(current);

    await prisma.collectionMetadata.update({
      where: { id: colMeta.id },
      data: { fields: updatedFields },
    });

    // 8) Apply to existing documents
    const coll = mongoClient.db(dbName).collection(oldName);
    if (addFields.length) {
      const setObj = addFields.reduce((o, f) => ({ ...o, [f]: null }), {});
      await coll.updateMany({}, { $set: setObj });
    }
    if (removeFields.length) {
      const unsetObj = removeFields.reduce((o, f) => ({ ...o, [f]: "" }), {});
      await coll.updateMany({}, { $unset: unsetObj });
    }

    // 9) Log WRITE
    await logOperation(
      userId,
      OperationType.WRITE,
      ResourceType.COLLECTION,
      colMeta.id
    );

    return NextResponse.json({
      success: true,
      message: "Collection updated",
      updated: { name: oldName, fields: updatedFields },
    });
  } catch (err) {
    console.error("PUT collections error:", err);
    return NextResponse.json(
      { success: false, message: "Internal Server Error" },
      { status: 500 }
    );
  } finally {
    if (mongoClient) await client.close();
  }
}
