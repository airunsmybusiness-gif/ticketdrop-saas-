import { NextResponse } from "next/server";
import { clearDriverSession } from "@/lib/session";
import { handle } from "@/lib/api";

export const POST = handle("logout", async () => {
  await clearDriverSession();
  return NextResponse.json({ ok: true });
});
