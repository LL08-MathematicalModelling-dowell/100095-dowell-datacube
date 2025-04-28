/* eslint-disable @typescript-eslint/no-explicit-any */
// app/api/settings/route.ts
import { getUserId } from "@/lib/getUserId";
import { prisma } from "@/prisma/client";
import { NextRequest, NextResponse } from "next/server";

export async function GET() {
  const userId = await getUserId();
  if (!userId)
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const user = await prisma.user.findUnique({
    where: { id: userId },
    select: { settings: true },
  });
  return NextResponse.json({ success: true, settings: user?.settings || {} });
}

export async function PATCH(req: NextRequest) {
  const userId = await getUserId();
  if (!userId)
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const body = await req.json();
  // simple validation
  const { notifications, theme, language } = body;
  const updates: any = {};
  if (notifications) updates["settings.notifications"] = notifications;
  if (theme) updates["settings.theme"] = theme;
  if (language) updates["settings.language"] = language;

  const user = await prisma.user.update({
    where: { id: userId },
    data: {
      settings: {
        ...updates, // merges into JSON
      },
    },
  });
  return NextResponse.json({ success: true, settings: user.settings });
}
