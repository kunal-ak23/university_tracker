import { auth } from "@/auth"
import { NextResponse } from "next/server";


export default auth((req) => {
  console.log('req.auth', !!req.auth);

  const isAuthenticated = !!req.auth;
  const isAdmin = req.auth?.user?.role === 'admin';

  console.log('isAuthenticated', isAuthenticated);
  console.log('isAdmin', isAdmin);

  if (req.nextUrl.pathname.startsWith('/batches/')) {
    console.log('req.nextUrl.pathname', req.nextUrl.pathname);
  }

  return NextResponse.next();
})

 
// Optionally, don't invoke Middleware on some paths
export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
}