import { auth } from "@/auth";
import { prisma } from "@/prisma/client";
import crypto from "crypto";
import { headers } from "next/headers";

export const getUserId = async () => {
  // Attempt to retrieve the user ID from the authenticated session
  const session = await auth();

  if (session?.user?.email) {
    const user = await prisma.user.findUnique({
      where: { email: session.user.email },
    });
    return user?.id;
  }
  // If no session, check for API key in the request headers
  const headersList = await headers();
  const apiKey = headersList.get("datacube-key") as string | undefined;

  if (apiKey) {
    // Hash the provided API key using SHA-256
    const hashedApiKey = crypto
      .createHash("sha256")
      .update(apiKey)
      .digest("hex");

    // Find the API key in the database
    const apiKeyRecord = await prisma.apiKey.findUnique({
      where: { key: hashedApiKey },
    });
    if (apiKeyRecord) {
      // If found, return the associated user ID
      return apiKeyRecord.userId;
    }
  }
  return null;
};
