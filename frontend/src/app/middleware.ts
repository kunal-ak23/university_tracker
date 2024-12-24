import { auth } from "@/auth"
import { NextResponse } from "next/server";


export default auth((req) => {

  const isAuthenticated = !!req.auth;
  const isAdmin = req.auth?.user?.role === 'admin';

  return NextResponse.next();
})

 
// Optionally, don't invoke Middleware on some paths
export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
}