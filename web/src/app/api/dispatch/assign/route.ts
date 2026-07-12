// POST { load_id, driver_id } → assign (or re-assign) a driver to a load
// that is REQUESTED or was DECLINED. Sends it to the driver as ASSIGNED.
import { NextResponse } from "next/server";
import { db } from "@/lib/db";
import { getDriverSession } from "@/lib/session";
import { handle, readJson, requireId, ApiError } from "@/lib/api";
import { log } from "@/lib/log";

export const POST = handle("dispatch_assign", async (req, { requestId }) => {
  const s = await getDriverSession();
  if (!s) throw new ApiError(401, "Not signed in");
  if (s.role === "driver") throw new ApiError(403, "Office access only");

  const b = await readJson(req);
  const loadId = requireId(b.load_id, "Load");
  const driverId = requireId(b.driver_id, "Driver");

  const d = await db().query(
    `SELECT id, name FROM users
     WHERE id = $1 AND company_id = $2 AND role = 'driver' AND active = TRUE`,
    [driverId, s.company_id]
  );
  if (d.rows.length === 0) throw new ApiError(400, "That driver doesn't exist");

  const client = await db().connect();
  try {
    await client.query("BEGIN");
    const { rows } = await client.query(
      `SELECT status FROM loads WHERE id = $1 AND company_id = $2 FOR UPDATE`,
      [loadId, s.company_id]
    );
    if (rows.length === 0) throw new ApiError(404, "Load not found");
    const from = rows[0].status;
    if (from !== "REQUESTED" && from !== "DECLINED")
      throw new ApiError(409, `Load is ${from} — only unassigned or declined loads can be assigned`);

    await client.query(
      `UPDATE loads SET driver_id = $1, status = 'ASSIGNED',
                        status_changed_at = NOW(), status_changed_by = $2,
                        updated_at = NOW()
       WHERE id = $3`,
      [driverId, s.user_id, loadId]
    );
    await client.query(
      `INSERT INTO load_status_history
         (load_id, old_status, new_status, changed_by, changed_by_name, reason)
       VALUES ($1, $2, 'ASSIGNED', $3, $4, $5)`,
      [loadId, from, s.user_id, s.name, `Assigned to ${d.rows[0].name}`]
    );
    await client.query("COMMIT");
    log.info("load_assigned", { requestId, load_id: loadId, driver_id: driverId, by: s.name });
    return NextResponse.json({ ok: true });
  } catch (e) {
    await client.query("ROLLBACK").catch(() => {});
    throw e;
  } finally {
    client.release();
  }
});
