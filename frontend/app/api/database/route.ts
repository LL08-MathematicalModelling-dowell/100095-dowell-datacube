// app/api/database/route.ts
import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import client from "@/lib/mongodb";
import { prisma } from "@/prisma/client";
import { getUserId } from "@/lib/getUserId";
import { logOperation } from "@/lib/logOperation";
import { OperationType, Prisma, ResourceType } from "@prisma/client";

// POST body schema
const createDbSchema = z.object({
  dbName: z
    .string()
    .min(1)
    .transform((s) => s.toLowerCase()),
  description: z.string().optional(),
  collections: z
    .array(
      z.object({
        name: z.string().min(1),
        fields: z.array(z.string()).optional().default([]),
      })
    )
    .nonempty("At least one collection is required"),
});

export async function POST(request: NextRequest) {
  let mongoClient;
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
    const body = await request.json();
    const parsed = createDbSchema.safeParse(body);
    if (!parsed.success) {
      return NextResponse.json(
        { success: false, errors: parsed.error.errors },
        { status: 400 }
      );
    }
    const { dbName: name, description, collections } = parsed.data;
    const fullName = `${userId}_${name}`;

    // 3) Connect Mongo
    mongoClient = await client.connect();

    // 4) Ensure Metadata row
    let meta = await prisma.metadata.findUnique({ where: { userId } });
    if (!meta) {
      meta = await prisma.metadata.create({ data: { userId } });
    }

    // 5) Prevent dup
    const exists = await prisma.databaseMetadata.findFirst({
      where: { metadataId: meta.id, name: fullName },
    });
    if (exists) {
      return NextResponse.json(
        { success: false, message: `Database '${name}' already exists.` },
        { status: 400 }
      );
    }

    // 6) Create Mongo DB + collections
    const db = mongoClient.db(fullName);
    for (const col of collections) {
      await db.createCollection(col.name);
    }

    // 7) Create Prisma records
    const dbMeta = await prisma.databaseMetadata.create({
      data: {
        name: fullName,
        description: description ?? "",
        metadata: { connect: { id: meta.id } },
      },
    });
    await prisma.collectionMetadata.createMany({
      data: collections.map((c) => ({
        name: c.name,
        fields: c.fields,
        databaseMetadataId: dbMeta.id,
      })),
    });

    // 8) Log write on the newly created database
    await logOperation(userId, OperationType.WRITE, ResourceType.DB, dbMeta.id);

    return NextResponse.json(
      {
        success: true,
        database: { id: dbMeta.id, name },
        collections: collections.map((c) => ({
          name: c.name,
          fields: c.fields,
        })),
      },
      { status: 201 }
    );
  } catch (err) {
    console.error("POST /api/database error:", err);
    return NextResponse.json(
      { success: false, message: "Internal Server Error" },
      { status: 500 }
    );
  } finally {
    if (mongoClient) await client.close();
  }
}

export async function GET(request: NextRequest) {
  try {
    // 1) Auth
    const userId = await getUserId();
    if (!userId) {
      return NextResponse.json(
        { success: false, message: "Unauthorized" },
        { status: 401 }
      );
    }

    // 2) Paging + filter
    const q = request.nextUrl.searchParams;
    const page = Math.max(1, Number(q.get("page") ?? 1));
    const pageSize = Math.min(100, Number(q.get("pageSize") ?? 10));
    const filterTerm = q.get("filter")?.toLowerCase() ?? "";

    // 3) Fetch user‐metadata
    const meta = await prisma.metadata.findUnique({ where: { userId } });
    if (!meta) {
      return NextResponse.json(
        { success: true, data: [], pagination: { page, pageSize, total: 0 } },
        { status: 200 }
      );
    }

    // 4) Name filter
    const nameFilter: Prisma.StringFilter | undefined = filterTerm
      ? { contains: `${userId}_${filterTerm}`, mode: "insensitive" }
      : undefined;

    // 5) Query DBs + total
    const [items, total] = await Promise.all([
      prisma.databaseMetadata.findMany({
        where: { metadataId: meta.id, name: nameFilter },
        include: { collections: true },
        orderBy: { createdAt: "desc" },
        skip: (page - 1) * pageSize,
        take: pageSize,
      }),
      prisma.databaseMetadata.count({
        where: { metadataId: meta.id, name: nameFilter },
      }),
    ]);

    // 6) Bump accessCount
    await Promise.all(
      items.map((db) =>
        prisma.databaseMetadata.update({
          where: { id: db.id },
          data: { accessCount: { increment: 1 } },
        })
      )
    );

    // 7) Log read for each database returned
    await Promise.all(
      items.map((db) =>
        logOperation(userId, OperationType.READ, ResourceType.DB, db.id)
      )
    );

    // 8) Shape response
    const data = items.map((db) => ({
      id: db.id,
      name: db.name.replace(`${userId}_`, ""),
      description: db.description,
      createdAt: db.createdAt.toISOString(),
      numCollections: db.collections.length,
    }));

    return NextResponse.json(
      { success: true, data, pagination: { page, pageSize, total } },
      { status: 200 }
    );
  } catch (err) {
    console.error("GET /api/database error:", err);
    return NextResponse.json(
      { success: false, message: "Internal Server Error" },
      { status: 500 }
    );
  }
}
