import { createHmac } from "crypto";
import { cookies } from "next/headers";
import { NextResponse } from "next/server";

const COOKIE_NAME = "neuronote_session";

export async function POST(req: Request): Promise<NextResponse> {
  const appPassword = process.env.APP_PASSWORD;

  // Auth disabled — nothing to validate.
  if (!appPassword) {
    return NextResponse.json({ ok: true });
  }

  let body: { password?: unknown };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid request" }, { status: 400 });
  }

  if (body.password !== appPassword) {
    return NextResponse.json({ error: "Invalid password" }, { status: 401 });
  }

  const secret = process.env.SESSION_SECRET || appPassword;
  const token = createHmac("sha256", secret).update(appPassword).digest("hex");

  const cookieStore = await cookies();
  cookieStore.set(COOKIE_NAME, token, {
    httpOnly: true,
    sameSite: "strict",
    path: "/",
    // No maxAge → browser session cookie (cleared when browser closes).
    secure: process.env.NODE_ENV === "production",
  });

  return NextResponse.json({ ok: true });
}
