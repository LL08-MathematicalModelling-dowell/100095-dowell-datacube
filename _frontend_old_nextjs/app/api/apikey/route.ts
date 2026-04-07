import { prisma } from "@/prisma/client";
import crypto from "crypto";
import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";

// ----- GET: Fetch API Keys -----
export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const email = searchParams.get("userId");
  if (!email) {
    return NextResponse.json({ error: "User ID is required" }, { status: 400 });
  }
  // Validate email format
  const emailSchema = z.string().email();
  const emailValidation = emailSchema.safeParse(email);
  if (!emailValidation.success) {
    return NextResponse.json(
      { error: "Invalid email format" },
      { status: 400 }
    );
  }
  // get user id from email
  const user = await prisma.user.findFirst({
    where: { email: email },
  });
  if (!user) {
    return NextResponse.json({ error: "User not found" }, { status: 404 });
  }
  const userId = user.id;

  try {
    const apiKeys = await prisma.apiKey.findMany({
      where: { userId },
      select: {
        id: true,
        description: true,
        createdAt: true,
        expiresAt: true,
        lastUsed: true,
        // key: true, // This is the hashed version
      },
    });

    //  return empty if no keys found
    if (apiKeys.length === 0) {
      return NextResponse.json({ apiKeys: [] }, { status: 200 });
    }

    return NextResponse.json(
      {
        apiKeys: apiKeys.map((key) => ({
          id: key.id,
          description: key.description,
          createdAt: key.createdAt,
          expiresAt: key.expiresAt,
          lastUsed: key.lastUsed,
        })),
      },
      { status: 200 }
    );
  } catch (error) {
    console.error("Error fetching API keys:", error);
    return NextResponse.json(
      { error: "Internal Server Error" },
      { status: 500 }
    );
  }
}

// ----- POST: Create a New API Key -----
const createApiKeySchema = z.object({
  userId: z.string().email(),
  description: z.string(),
  expiresAt: z.string(),
});

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const parsed = createApiKeySchema.safeParse(body);
    if (!parsed.success) {
      return NextResponse.json({ error: parsed.error.errors }, { status: 400 });
    }
    const { userId: userEmail, description, expiresAt } = parsed.data;
    // get user id from email
    const user = await prisma.user.findFirst({
      where: { email: userEmail },
    });
    if (!user) {
      return NextResponse.json({ error: "User not found" }, { status: 404 });
    }
    const userId = user.id;

    // Generate a plain-text API key.
    const plainKey = crypto.randomBytes(16).toString("hex");
    const hashedKey = crypto
      .createHash("sha256")
      .update(plainKey)
      .digest("hex");

    const apiKey = await prisma.apiKey.create({
      data: {
        userId,
        description,
        expiresAt: expiresAt,
        createdAt: new Date(),
        isActive: true,
        key: hashedKey, // only the hashed key is stored.
      },
    });

    return NextResponse.json(
      {
        apiKey: {
          id: apiKey.id,
          description: apiKey.description,
          createdAt: apiKey.createdAt,
          expiresAt: apiKey.expiresAt,
          lastUsed: apiKey.lastUsed,
          // key: plainKey, // return the plain key for immediate use
          plainKey: plainKey,
        },
      },
      { status: 201 }
    );
  } catch (error) {
    console.error("Error creating API key:", error);
    return NextResponse.json(
      { error: "Internal Server Error" },
      { status: 500 }
    );
  }
}

// ----- PUT: Update an Existing API Key -----
const updateApiKeySchema = z.object({
  userId: z.string().email(),
  apiKeyId: z.string(),
  description: z.string(),
});

export async function PUT(request: NextRequest) {
  try {
    const body = await request.json();
    const parsed = updateApiKeySchema.safeParse(body);
    if (!parsed.success) {
      return NextResponse.json({ error: parsed.error.errors }, { status: 400 });
    }
    const { userId: userEmail, apiKeyId, description } = parsed.data;
    // get user id from email
    const user = await prisma.user.findFirst({
      where: { email: userEmail },
    });
    if (!user) {
      return NextResponse.json({ error: "User not found" }, { status: 404 });
    }
    const userId = user.id;

    // Ensure the key belongs to the user.
    const existing = await prisma.apiKey.findFirst({
      where: { id: apiKeyId, userId },
    });
    if (!existing) {
      return NextResponse.json(
        { error: "API Key not found or unauthorized" },
        { status: 404 }
      );
    }
    const updated = await prisma.apiKey.update({
      where: { id: apiKeyId },
      data: { description },
    });
    return NextResponse.json(
      {
        apiKey: {
          id: updated.id,
          description: updated.description,
          createdAt: updated.createdAt,
          expiresAt: updated.expiresAt,
          lastUsed: updated.lastUsed,
        },
      },
      { status: 200 }
    );
  } catch (error) {
    console.error("Error updating API key:", error);
    return NextResponse.json(
      { error: "Internal Server Error" },
      { status: 500 }
    );
  }
}

// ----- DELETE: Remove an API Key -----
const deleteApiKeySchema = z.object({
  userId: z.string().email(),
  apiKeyId: z.string(),
});

export async function DELETE(request: NextRequest) {
  try {
    const body = await request.json();
    const parsed = deleteApiKeySchema.safeParse(body);
    if (!parsed.success) {
      return NextResponse.json({ error: parsed.error.errors }, { status: 400 });
    }
    const { userId: userEmail, apiKeyId } = parsed.data;
    // get user id from email
    const user = await prisma.user.findFirst({
      where: { email: userEmail },
    });
    if (!user) {
      return NextResponse.json({ error: "User not found" }, { status: 404 });
    }
    const userId = user.id;

    const existing = await prisma.apiKey.findFirst({
      where: { id: apiKeyId, userId },
    });
    if (!existing) {
      return NextResponse.json(
        { error: "API Key not found or unauthorized" },
        { status: 404 }
      );
    }
    await prisma.apiKey.delete({
      where: { id: apiKeyId },
    });
    return NextResponse.json(
      { message: "API Key deleted successfully." },
      { status: 200 }
    );
  } catch (error) {
    console.error("Error deleting API key:", error);
    return NextResponse.json(
      { error: "Internal Server Error" },
      { status: 500 }
    );
  }
}
