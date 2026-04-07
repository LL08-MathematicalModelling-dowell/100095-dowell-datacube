// app/api/user/route.ts
import { getUserId } from "@/lib/getUserId";
import { prisma } from "@/prisma/client";
import { NextResponse } from "next/server";
// import { authOptions } from "@/lib/auth";
// import { getServerSession } from "next-auth/next";

// Name of the NextAuth cookie (may vary if you’ve customized it)
const SESSION_COOKIE_NAME = "next-auth.session-token";

export async function DELETE() {
  // 1) Attempt to get userId (via session or API key)
  const userId = await getUserId();
  if (!userId) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  // 2) In a transaction, delete all related data, then the user
  await prisma.$transaction([
    // Remove operation logs
    prisma.operationLog.deleteMany({ where: { userId } }),
    // Remove API keys
    prisma.apiKey.deleteMany({ where: { userId } }),
    // TODO: delete other user‑scoped tables, e.g.:
    // prisma.project.deleteMany({ where: { ownerId: userId } }),
    // prisma.session.deleteMany({ where: { userId } }),  // if you store sessions in Prisma
    // Finally delete the user
    prisma.user.delete({ where: { id: userId } }),
  ]);

  // 3) Build a 204 response and clear the NextAuth cookie
  const res = new NextResponse(null, { status: 204 });
  res.cookies.set({
    name: SESSION_COOKIE_NAME,
    value: "",
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: 0,
  });
  return res;
}
