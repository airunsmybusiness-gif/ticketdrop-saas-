// POST { load_id, action: "accept" | "decline" | "start", note? }
// Mirrors services/status.py: same status names, same allowed transitions,
// same load_status_history audit trail — so Streamlit and this app stay in sync.
import { NextResponse } from "next/server";
import { db } from "@/lib/db";
import { getDriverSession } from "@/lib/session";

const TRANSITIONS: Record<string, { from: string; to: string; reason: string }> = {
  accept: { from: "ASSIGNED", to: "ACCEPTED", reason: "Driver acknowledged" },
  decline: { from: "ASSIGNED", to: "DECLINED", reason: "Declined by driver" },
  start: { from: "ACCEPTED", to: "IN_PROGRESS", reason: "Driver started" },
};

export async function POST(req: Request) {
  const s = await getDriverSession();
  if (!s) return NextResponse.json({ error: "Not signed in" }, { status: 401 });

  let body: { load_id?: number; action?: string; note?: string };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Bad request" }, { status: 400 });
  }
  const t = TRANSITIONS[body.action || ""];
  const loadId = Number(body.load_id);
  if (!t || !loadId) return NextResponse.json({ error: "Unknown action" }, { status: 400 });

  const client = await db().connect();
  try {
    await client.query("BEGIN");
    // Lock the row; enforce ownership, company, and current status in one go.
    const { rows } = await client.query(
      `SELECT status FROM loads
       WHERE id = $1 AND company_id = $2 AND driver_id = $3 FOR UPDATE`,
      [loadId, s.company_id, s.user_id]
    );
    if (rows.length === 0) {
      await client.query("ROLLBACK");
      return NextResponse.json({ error: "Load not found" }, { status: 404 });
    }
    if (rows[0].status !== t.from) {
      await client.query("ROLLBACK");
      return NextResponse.json(
        { error: `Load is ${rows[0].status}, can't ${body.action}` },
        { status: 409 }
      );
    }
    await client.query(
      `UPDATE loads SET status = $1, status_changed_at = NOW(),
                        status_changed_by = $2, updated_at = NOW() WHERE id = $3`,
      [t.to, s.user_id, loadId]
    );
    const reason = body.note ? `${t.reason} | Note: ${body.note}` : t.reason;
    await client.query(
      `INSERT INTO load_status_history
         (load_id, old_status, new_status, changed_by, changed_by_name, reason)
       VALUES ($1, $2, $3, $4, $5, $6)`,
      [loadId, t.from, t.to, s.user_id, s.name, reason]
    );
    await client.query("COMMIT");
    return NextResponse.json({ ok: true, status: t.to });
  } catch (e) {
    await client.query("ROLLBACK");
    console.error("driver action failed", e);
    return NextResponse.json({ error: "Could not update the load" }, { status: 500 });
  } finally {
    client.release();
  }
}
