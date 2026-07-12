import { NextResponse } from "next/server";
import { clearDriverSession } from "@/lib/session";

export async function POST() {
  await clearDriverSession();
  return NextResponse.json({ ok: true });
}
