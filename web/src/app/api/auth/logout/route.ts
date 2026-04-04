import { cookies } from "next/headers";
import { NextResponse } from "next/server";

const COOKIE_NAME = "neuronote_session";

export async function POST(): Promise<NextResponse> {
  const cookieStore = await cookies();
  cookieStore.delete(COOKIE_NAME);
  return NextResponse.json({ ok: true });
}
