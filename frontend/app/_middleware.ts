import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { auth } from "@/auth";

const protectedRoutes = ["/dashboard"];

export default async function middleware(request: NextRequest) {
  const session = await auth();

  const { pathname } = request.nextUrl;
  console.log(
    "><>>>>>>>>>>>>>>>>>>>>>   PATHNAME ><>>>>>>>>>>>>>>>>>>  ",
    pathname
  );
  console.log(
    "><>>>>>>>>>>>>>>>>>>>>>   SESSION ><>>>>>>>>>>>>>>>>>>  ",
    session
  );
  console.log(
    "><>>>>>>>>>>>>>>>>>>>>>   REQUEST ><>>>>>>>>>>>>>>>>>>  ",
    request
  );
  console.log(
    "><>>>>>>>>>>>>>>>>>>>>>   REQUEST URL ><>>>>>>>>>>>>>>>>>>  ",
    request.url
  );

  const isProtected = protectedRoutes.some((route) =>
    pathname.startsWith(route)
  );

  if (isProtected && !session) {
    return NextResponse.redirect(new URL("/api/auth/signin", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*", "/api/auth/:path*"], // Adjust the matcher to include your auth routes
  // This will ensure the middleware runs for all routes under /dashboard and /api/auth

  // You can add more routes as needed
  // matcher: ["/dashboard/:path*", "/api/auth/:path*"],
};
