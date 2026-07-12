// POST { ticket_id, action: "approve" | "dispute" }
// approve = SUBMITTED → VERIFIED → READY_FOR_INVOICE (one click for the
// office, two audit rows so the trail matches the Streamlit flow).
// dispute = SUBMITTED → DISPUTED.
import { NextResponse } from "next/server";
import { db } from "@/lib/db";
import { getDriverSession } from "@/lib/session";
import { handle, readJson, requireId, optionalString, ApiError } from "@/lib/api";
import { log } from "@/lib/log";

export const POST = handle("billing_review", async (req, { requestId }) => {
  const s = await getDriverSession();
  if (!s) throw new ApiError(401, "Not signed in");
  if (s.role === "driver") throw new ApiError(403, "Office access only");

  const b = await readJson(req);
  const ticketId = requireId(b.ticket_id, "Ticket");
  const action = String(b.action || "");
  const note = optionalString(b.note, "Note", 500);
  if (action !== "approve" && action !== "dispute")
    throw new ApiError(400, "Unknown action");

  const client = await db().connect();
  try {
    await client.query("BEGIN");
    const { rows } = await client.query(
      `SELECT status FROM tickets WHERE id = $1 AND company_id = $2 FOR UPDATE`,
      [ticketId, s.company_id]
    );
    if (rows.length === 0) throw new ApiError(404, "Ticket not found");
    if (rows[0].status !== "SUBMITTED")
      throw new ApiError(409, `Ticket is ${rows[0].status}, not awaiting review`);

    const steps =
      action === "approve"
        ? [["SUBMITTED", "VERIFIED", "Verified by office"],
           ["VERIFIED", "READY_FOR_INVOICE", "Marked ready for invoice"]]
        : [["SUBMITTED", "DISPUTED", note || "Needs review"]];

    for (const [from, to, reason] of steps) {
      await client.query(
        `UPDATE tickets SET status = $1, status_changed_at = NOW(),
                            status_changed_by = $2, updated_at = NOW()
         WHERE id = $3`,
        [to, s.user_id, ticketId]
      );
      await client.query(
        `INSERT INTO ticket_status_history
           (ticket_id, old_status, new_status, changed_by, changed_by_name, reason)
         VALUES ($1, $2, $3, $4, $5, $6)`,
        [ticketId, from, to, s.user_id, s.name, reason]
      );
    }
    await client.query("COMMIT");
    log.info("ticket_reviewed", { requestId, ticket_id: ticketId, action, by: s.name });
    return NextResponse.json({ ok: true });
  } catch (e) {
    await client.query("ROLLBACK").catch(() => {});
    throw e;
  } finally {
    client.release();
  }
});
