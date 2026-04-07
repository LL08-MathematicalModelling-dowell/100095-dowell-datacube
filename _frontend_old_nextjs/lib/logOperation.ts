// lib/logOperation.ts
import { prisma } from "@/prisma/client";
import { OperationType, ResourceType } from "@prisma/client";

/**
 * logOperation now takes an optional `count` (defaulting to 1).
 */
export async function logOperation(
  userId: string,
  type: OperationType,
  resourceType: ResourceType,
  resourceId: string,
  count = 1
) {
  return prisma.operationLog.create({
    data: { userId, type, resourceType, resourceId, count },
  });
}
