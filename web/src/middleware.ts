import { NextRequest, NextResponse } from "next/server";

const COOKIE_NAME = "neuronote_session";

// These paths are always accessible regardless of auth state.
const PUBLIC_PREFIXES = ["/login", "/api/auth/login", "/api/auth/logout"];

async function computeToken(password: string, secret: string): Promise<string> {
  const enc = new TextEncoder();
  const key = await crypto.subtle.importKey(
    "raw",
    enc.encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const sig = await crypto.subtle.sign("HMAC", key, enc.encode(password));
  return Array.from(new Uint8Array(sig))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

export async function middleware(req: NextRequest): Promise<NextResponse> {
  const appPassword = process.env.APP_PASSWORD;

  // Auth disabled (local dev or user hasn't set a password).
  if (!appPassword) {
    return NextResponse.next();
  }

  const { pathname } = req.nextUrl;

  // Always allow public paths through.
  if (PUBLIC_PREFIXES.some((prefix) => pathname.startsWith(prefix))) {
    return NextResponse.next();
  }

  const secret = process.env.SESSION_SECRET || appPassword;
  const expectedToken = await computeToken(appPassword, secret);
  const cookieValue = req.cookies.get(COOKIE_NAME)?.value;

  if (cookieValue === expectedToken) {
    return NextResponse.next();
  }

  // Redirect to login, preserving the intended destination.
  const loginUrl = new URL("/login", req.url);
  loginUrl.searchParams.set("next", pathname);
  return NextResponse.redirect(loginUrl);
}

export const config = {
  // Run on all routes except Next.js internals and static files.
  matcher: ["/((?!_next/static|_next/image|favicon.ico|robots.txt).*)"],
};
