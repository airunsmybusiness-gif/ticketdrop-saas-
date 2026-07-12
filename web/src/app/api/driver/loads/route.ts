// GET → the signed-in driver's loads: everything open plus today's completed.
import { NextResponse } from "next/server";
import { db } from "@/lib/db";
import { getDriverSession } from "@/lib/session";
import { handle, ApiError } from "@/lib/api";

export const dynamic = "force-dynamic";

export const GET = handle("driver_loads", async () => {
  const s = await getDriverSession();
  if (!s) throw new ApiError(401, "Not signed in");

  const { rows } = await db().query(
    `SELECT id, customer, pickup_location, delivery_location, truck, trailer,
            notes, status, created_at
     FROM loads
     WHERE company_id = $1 AND driver_id = $2
       AND (status IN ('ASSIGNED','ACCEPTED','IN_PROGRESS')
            OR (status = 'COMPLETED' AND DATE(status_changed_at) = CURRENT_DATE))
     ORDER BY CASE status
                WHEN 'IN_PROGRESS' THEN 0 WHEN 'ACCEPTED' THEN 1
                WHEN 'ASSIGNED' THEN 2 ELSE 3 END,
              created_at DESC`,
    [s.company_id, s.user_id]
  );
  return NextResponse.json({ driver: s.name, loads: rows });
});
