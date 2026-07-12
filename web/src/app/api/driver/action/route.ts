// POST { load_id, action: "accept" | "decline" | "start", note? }
// Mirrors services/status.py: same status names, same allowed transitions,
// same load_status_history audit trail — so Streamlit and this app stay in sync.
import { NextResponse } from "next/server";
import { db } from "@/lib/db";
import { getDriverSession } from "@/lib/session";
import { handle, readJson, requireId, optionalString, ApiError } from "@/lib/api";
import { log } from "@/lib/log";

const TRANSITIONS: Record<string, { from: string; to: string; reason: string }> = {
  accept: { from: "ASSIGNED", to: "ACCEPTED", reason: "Driver acknowledged" },
  decline: { from: "ASSIGNED", to: "DECLINED", reason: "Declined by driver" },
  start: { from: "ACCEPTED", to: "IN_PROGRESS", reason: "Driver started" },
};

export const POST = handle("driver_action", async (req, { requestId }) => {
  const s = await getDriverSession();
  if (!s) throw new ApiError(401, "Not signed in");

  const body = await readJson(req);
  const loadId = requireId(body.load_id, "Load");
  const t = TRANSITIONS[String(body.action || "")];
  if (!t) throw new ApiError(400, "Unknown action");
  const note = optionalString(body.note, "Note", 500);

  const client = await db().connect();
  try {
    await client.query("BEGIN");
    // Lock the row; enforce ownership, company, and current status in one go.
    const { rows } = await client.query(
      `SELECT status FROM loads
       WHERE id = $1 AND company_id = $2 AND driver_id = $3 FOR UPDATE`,
      [loadId, s.company_id, s.user_id]
    );
    if (rows.length === 0) throw new ApiError(404, "Load not found");
    if (rows[0].status !== t.from) {
      throw new ApiError(409, `Load is ${rows[0].status}, can't ${body.action}`);
    }
    await client.query(
      `UPDATE loads SET status = $1, status_changed_at = NOW(),
                        status_changed_by = $2, updated_at = NOW() WHERE id = $3`,
      [t.to, s.user_id, loadId]
    );
    const reason = note ? `${t.reason} | Note: ${note}` : t.reason;
    await client.query(
      `INSERT INTO load_status_history
         (load_id, old_status, new_status, changed_by, changed_by_name, reason)
       VALUES ($1, $2, $3, $4, $5, $6)`,
      [loadId, t.from, t.to, s.user_id, s.name, reason]
    );
    await client.query("COMMIT");
    log.info("load_status_changed", {
      requestId, load_id: loadId, from: t.from, to: t.to, by: s.name,
    });
    return NextResponse.json({ ok: true, status: t.to });
  } catch (e) {
    await client.query("ROLLBACK").catch(() => {});
    throw e; // handle() logs and formats it
  } finally {
    client.release();
  }
});
