import { auth } from "@/auth"
import { NextResponse } from "next/server";
import { DEFAULT_REDIRECT_URL } from "./routes";

export default auth((req) => {
  const isAuthenticated = !!req.auth;
  console.log(req.auth);
  console.log(req.nextUrl.pathname);
  console.log(isAuthenticated);

  // Public paths that don't require authentication
  const publicPaths = ['/login', '/register', '/forgot-password', '/reset-password'];
  const isPublicPath = publicPaths.includes(req.nextUrl.pathname);

  // If the user is not authenticated and trying to access a protected route
  if (!isAuthenticated && !isPublicPath) {
    const loginUrl = new URL('/login', req.url);
    // Add the current path as a "from" parameter to redirect back after login
    loginUrl.searchParams.set('from', req.nextUrl.pathname);
    return NextResponse.redirect(loginUrl);
  }

  // If the user is authenticated and trying to access login/register pages
  if (isAuthenticated && isPublicPath) {
    return NextResponse.redirect(new URL(DEFAULT_REDIRECT_URL, req.url));
  }

  return NextResponse.next();
})

// Optionally, don't invoke Middleware on some paths
export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
}