import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { auth } from "@/auth"; // Make sure your auth function is correct

const protectedRoutes = ["/dashboard"];

export async function middleware(request: NextRequest) {
  let session;
  try {
    session = await auth();
    console.log("Session:", session);
  } catch (error) {
    console.error("Auth error:", error);
    return NextResponse.redirect(new URL("/api/auth/signin", request.nextUrl)); // Fallback to signin on error
  }

  const { pathname } = request.nextUrl;

  const isProtected = protectedRoutes.some((route) =>
    pathname.startsWith(route)
  );

  if (isProtected && !session) {
    return NextResponse.redirect(new URL("/api/auth/signin", request.nextUrl));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*", "/api/auth/:path*"], // Adjust the matcher to include your auth routes
  // This will ensure the middleware runs for all routes under /dashboard and /api/auth

  // You can add more routes as needed
};
