// app/api/reports/route.ts
import { NextResponse } from "next/server";
import client from "@/lib/mongodb";
import { prisma } from "@/prisma/client";
import { getUserId } from "@/lib/getUserId";
import { OperationType, ResourceType } from "@prisma/client";
import { MongoClient } from "mongodb";

export const revalidate = 60; // cache 60s

// last N days, [start, end)
function getLastNDays(n: number) {
  const now = new Date();
  return Array.from({ length: n }, (_, i) => {
    const start = new Date(now);
    start.setDate(now.getDate() - (n - 1 - i));
    start.setHours(0, 0, 0, 0);
    const end = new Date(start);
    end.setDate(start.getDate() + 1);
    return { start, end };
  });
}

// last N weeks (Mon–Sun), [start, end)
function getLastNWeeks(n: number) {
  const now = new Date();
  const dow = now.getDay() || 7;
  const monday = new Date(now);
  monday.setDate(now.getDate() - (dow - 1));
  monday.setHours(0, 0, 0, 0);

  return Array.from({ length: n }, (_, i) => {
    const start = new Date(monday);
    start.setDate(monday.getDate() - (n - 1 - i) * 7);
    const end = new Date(start);
    end.setDate(start.getDate() + 7);
    return { start, end };
  });
}

export async function GET() {
  let mongoClient: MongoClient | null = null;
  try {
    // 1) Auth
    const userId = await getUserId();
    if (!userId) {
      return NextResponse.json(
        { success: false, error: "Unauthorized" },
        { status: 401 }
      );
    }

    // 2) Live totalRecords
    mongoClient = await client.connect();
    const admin = mongoClient.db().admin();
    const allDbs = (await admin.listDatabases()).databases.map((d) => d.name);
    const myDbs = allDbs.filter((nm) => nm.startsWith(`${userId}_`));
    const docsPerDb = await Promise.all(
      myDbs.map(async (dbName) => {
        if (!mongoClient) {
          throw new Error("MongoClient is not initialized");
        }
        const cols = await mongoClient.db(dbName).listCollections().toArray();
        const counts = await Promise.all(
          cols.map(
            (c) =>
              mongoClient?.db(dbName).collection(c.name).countDocuments() ??
              (() => {
                throw new Error("MongoClient is not initialized");
              })()
          )
        );
        return counts.reduce((a, b) => a + b, 0);
      })
    );
    const totalRecords = docsPerDb.reduce((a, b) => a + b, 0);

    // 3) Records added/removed per week (sum of log.count)
    const weekRanges = getLastNWeeks(4);
    const recordsAddedPerWeek = await Promise.all(
      weekRanges.map(async ({ start, end }) => {
        const agg = await prisma.operationLog.aggregate({
          _sum: { count: true },
          where: {
            userId,
            type: OperationType.WRITE,
            resourceType: ResourceType.DOCUMENT,
            createdAt: { gte: start, lt: end },
          },
        });
        return agg._sum.count ?? 0;
      })
    );
    const recordsRemovedPerWeek = await Promise.all(
      weekRanges.map(async ({ start, end }) => {
        const agg = await prisma.operationLog.aggregate({
          _sum: { count: true },
          where: {
            userId,
            type: OperationType.DELETE,
            resourceType: ResourceType.DOCUMENT,
            createdAt: { gte: start, lt: end },
          },
        });
        return agg._sum.count ?? 0;
      })
    );

    // 4) 7‑day history of adds/removes and snapshot totalRecords
    const dayRanges = getLastNDays(7);
    const history = await Promise.all(
      dayRanges.map(async ({ start, end }) => {
        const addedAgg = await prisma.operationLog.aggregate({
          _sum: { count: true },
          where: {
            userId,
            type: OperationType.WRITE,
            resourceType: ResourceType.DOCUMENT,
            createdAt: { gte: start, lt: end },
          },
        });
        const removedAgg = await prisma.operationLog.aggregate({
          _sum: { count: true },
          where: {
            userId,
            type: OperationType.DELETE,
            resourceType: ResourceType.DOCUMENT,
            createdAt: { gte: start, lt: end },
          },
        });
        return {
          date: start.toISOString().slice(0, 10),
          totalRecords, // live snapshot
          recordsAdded: addedAgg._sum.count ?? 0,
          recordsRemoved: removedAgg._sum.count ?? 0,
        };
      })
    );

    // 5) Return payload
    return NextResponse.json(
      {
        success: true,
        data: {
          totalRecords,
          recordsAddedPerWeek,
          recordsRemovedPerWeek,
          history,
        },
      },
      { status: 200 }
    );
  } catch (err) {
    console.error("GET /api/reports error:", err);
    return NextResponse.json(
      { success: false, error: "Internal Server Error" },
      { status: 500 }
    );
  } finally {
    if (mongoClient) await mongoClient.close();
  }
}
