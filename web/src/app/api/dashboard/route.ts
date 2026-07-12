// GET → everything the dispatch dashboard needs in one call:
// summary stats, the live job board, and the driver list with assignments.
// Office roles only (dispatch / admin / ar).
import { NextResponse } from "next/server";
import { db } from "@/lib/db";
import { getDriverSession } from "@/lib/session";
import { handle, ApiError } from "@/lib/api";

export const dynamic = "force-dynamic";

export const GET = handle("dashboard", async () => {
  const s = await getDriverSession();
  if (!s) throw new ApiError(401, "Not signed in");
  if (s.role === "driver") throw new ApiError(403, "Office access only");

  const cid = s.company_id;
  const [company, stats, jobs, drivers] = await Promise.all([
    db().query(`SELECT name FROM companies WHERE id = $1`, [cid]),
    db().query(
      `SELECT
         COUNT(*) FILTER (WHERE status = 'ASSIGNED')                            AS pending,
         COUNT(*) FILTER (WHERE status IN ('ACCEPTED','IN_PROGRESS'))           AS active,
         COUNT(*) FILTER (WHERE status = 'COMPLETED'
                          AND DATE(status_changed_at) = CURRENT_DATE)           AS completed_today,
         (SELECT COUNT(*) FROM tickets t
           WHERE t.company_id = $1 AND t.status = 'SUBMITTED')                  AS tickets_to_review
       FROM loads WHERE company_id = $1`,
      [cid]
    ),
    db().query(
      `SELECT l.id, l.customer, l.pickup_location, l.delivery_location,
              l.truck, l.trailer, l.status, l.status_changed_at,
              u.name AS driver_name
       FROM loads l LEFT JOIN users u ON u.id = l.driver_id
       WHERE l.company_id = $1
         AND (l.status IN ('ASSIGNED','ACCEPTED','IN_PROGRESS')
              OR (l.status IN ('COMPLETED','DECLINED')
                  AND DATE(l.status_changed_at) = CURRENT_DATE))
       ORDER BY CASE l.status
                  WHEN 'ASSIGNED' THEN 0 WHEN 'IN_PROGRESS' THEN 1
                  WHEN 'ACCEPTED' THEN 2 ELSE 3 END,
                l.status_changed_at DESC
       LIMIT 60`,
      [cid]
    ),
    db().query(
      `SELECT u.id, u.name,
              l.id AS load_id, l.customer, l.status AS load_status
       FROM users u
       LEFT JOIN LATERAL (
         SELECT id, customer, status FROM loads
         WHERE driver_id = u.id AND company_id = $1
           AND status IN ('ASSIGNED','ACCEPTED','IN_PROGRESS')
         ORDER BY status_changed_at DESC LIMIT 1
       ) l ON TRUE
       WHERE u.company_id = $1 AND u.role = 'driver' AND u.active = TRUE
       ORDER BY u.name`,
      [cid]
    ),
  ]);

  return NextResponse.json({
    user: s.name,
    role: s.role,
    company: company.rows[0]?.name ?? "TicketDrop",
    stats: stats.rows[0],
    jobs: jobs.rows,
    drivers: drivers.rows,
    time: new Date().toISOString(),
  });
});
