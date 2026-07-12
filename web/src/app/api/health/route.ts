// GET /api/health — for uptime monitors (e.g. UptimeRobot, free).
// Returns 200 when the app AND the database are reachable, 503 otherwise.
import { NextResponse } from "next/server";
import { dbPing } from "@/lib/db";
import { handle } from "@/lib/api";

export const dynamic = "force-dynamic";

export const GET = handle("health", async () => {
  const db = await dbPing();
  const body = { ok: db.ok, db: { ok: db.ok, ms: db.ms }, time: new Date().toISOString() };
  return NextResponse.json(body, { status: db.ok ? 200 : 503 });
});
