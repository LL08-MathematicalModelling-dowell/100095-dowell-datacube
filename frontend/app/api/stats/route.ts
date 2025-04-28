// app/api/stats/route.ts
import { NextResponse } from "next/server";
import client from "@/lib/mongodb";
import { prisma } from "@/prisma/client";
import { getUserId } from "@/lib/getUserId";
import { OperationType, ResourceType } from "@prisma/client";
import { MongoClient } from "mongodb";

export const revalidate = 60;

interface StatsResponse {
  success: true;
  data: {
    databases: number;
    collections: number;
    documents: number;
    mostFrequentDb: string | null;
    mostFrequentCollection: string | null;
    readsPerDay: number[];
    writesPerDay: number[];
    readsPerMonth: number[];
    writesPerMonth: number[];
  };
}

function getLastNDays(n: number): Array<{ start: Date; end: Date }> {
  const now = new Date();
  return Array.from({ length: n }, (_, idx) => {
    const day = new Date(now);
    day.setDate(now.getDate() - (n - 1 - idx));
    day.setHours(0, 0, 0, 0);
    const next = new Date(day);
    next.setDate(day.getDate() + 1);
    return { start: day, end: next };
  });
}

function getLastNMonths(n: number): Array<{ start: Date; end: Date }> {
  const now = new Date();
  return Array.from({ length: n }, (_, idx) => {
    const mStart = new Date(
      now.getFullYear(),
      now.getMonth() - (n - 1 - idx),
      1
    );
    const mEnd = new Date(mStart);
    mEnd.setMonth(mStart.getMonth() + 1);
    return { start: mStart, end: mEnd };
  });
}

export async function GET() {
  let mongoClient: MongoClient;

  try {
    // 1) Authenticate
    const userId = await getUserId();
    if (!userId) {
      return NextResponse.json(
        { success: false, error: "Unauthorized" },
        { status: 401 }
      );
    }

    // 2) Core counts
    const [databases, collections] = await Promise.all([
      prisma.databaseMetadata.count({ where: { metadata: { userId } } }),
      prisma.collectionMetadata.count({
        where: { databaseMetadata: { metadata: { userId } } },
      }),
    ]);

    // 3) Real‐time document total
    mongoClient = await client.connect();
    const admin = mongoClient.db().admin();
    const allDbs = (await admin.listDatabases()).databases.map((d) => d.name);
    const userDbs = allDbs.filter((db) => db.startsWith(`${userId}_`));

    const docsPerDb = await Promise.all(
      userDbs.map(async (dbName) => {
        const colInfos = await mongoClient
          .db(dbName)
          .listCollections()
          .toArray();
        const counts = await Promise.all(
          colInfos.map((c) =>
            mongoClient.db(dbName).collection(c.name).countDocuments()
          )
        );
        return counts.reduce((sum, c) => sum + c, 0);
      })
    );
    const documents = docsPerDb.reduce((sum, d) => sum + d, 0);

    // 4) Daily & monthly read/write sums (_sum.count instead of count rows)
    const dayRanges = getLastNDays(7);
    const monthRanges = getLastNMonths(7);

    const readsPerDay = await Promise.all(
      dayRanges.map(async ({ start, end }) => {
        const agg = await prisma.operationLog.aggregate({
          _sum: { count: true },
          where: {
            userId,
            type: OperationType.READ,
            createdAt: { gte: start, lt: end },
          },
        });
        return agg._sum.count ?? 0;
      })
    );

    const writesPerDay = await Promise.all(
      dayRanges.map(async ({ start, end }) => {
        const agg = await prisma.operationLog.aggregate({
          _sum: { count: true },
          where: {
            userId,
            type: OperationType.WRITE,
            createdAt: { gte: start, lt: end },
          },
        });
        return agg._sum.count ?? 0;
      })
    );

    const readsPerMonth = await Promise.all(
      monthRanges.map(async ({ start, end }) => {
        const agg = await prisma.operationLog.aggregate({
          _sum: { count: true },
          where: {
            userId,
            type: OperationType.READ,
            createdAt: { gte: start, lt: end },
          },
        });
        return agg._sum.count ?? 0;
      })
    );

    const writesPerMonth = await Promise.all(
      monthRanges.map(async ({ start, end }) => {
        const agg = await prisma.operationLog.aggregate({
          _sum: { count: true },
          where: {
            userId,
            type: OperationType.WRITE,
            createdAt: { gte: start, lt: end },
          },
        });
        return agg._sum.count ?? 0;
      })
    );

    // 5) Most frequent DB (by sum of counts)
    const topDb = await prisma.operationLog.groupBy({
      by: ["resourceId"],
      where: {
        userId,
        resourceType: ResourceType.DB,
      },
      _sum: { count: true },
      orderBy: { _sum: { count: "desc" } },
      take: 1,
    });
    const mostFrequentDb = topDb[0]?.resourceId
      ? (
          await prisma.databaseMetadata.findUnique({
            where: { id: topDb[0].resourceId },
            select: { name: true },
          })
        )?.name.replace(`${userId}_`, "")
      : null;

    // 6) Most frequent Collection
    const topColl = await prisma.operationLog.groupBy({
      by: ["resourceId"],
      where: {
        userId,
        resourceType: ResourceType.COLLECTION,
      },
      _sum: { count: true },
      orderBy: { _sum: { count: "desc" } },
      take: 1,
    });
    const mostFrequentCollection = topColl[0]?.resourceId
      ? (
          await prisma.collectionMetadata.findUnique({
            where: { id: topColl[0].resourceId },
            select: { name: true },
          })
        )?.name
      : null;

    // 7) Return payload
    const payload: StatsResponse = {
      success: true,
      data: {
        databases,
        collections,
        documents,
        mostFrequentDb: mostFrequentDb ?? null,
        mostFrequentCollection: mostFrequentCollection ?? null,
        readsPerDay,
        writesPerDay,
        readsPerMonth,
        writesPerMonth,
      },
    };
    return NextResponse.json(payload, { status: 200 });
  } catch (err) {
    console.error("GET /api/stats error:", err);
    return NextResponse.json(
      { success: false, error: "Internal Server Error" },
      { status: 500 }
    );
  }
}
