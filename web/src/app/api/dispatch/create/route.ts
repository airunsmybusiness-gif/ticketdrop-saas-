// POST → create a new job order. With a driver it goes out as ASSIGNED;
// without one it sits on the board as REQUESTED until someone assigns it.
// Same status names and audit history as the Streamlit app.
import { NextResponse } from "next/server";
import { db } from "@/lib/db";
import { getDriverSession } from "@/lib/session";
import { HAZARD_ITEMS } from "@/lib/hazards";
import { handle, readJson, requireString, optionalString, ApiError } from "@/lib/api";
import { log } from "@/lib/log";

export const POST = handle("dispatch_create", async (req, { requestId }) => {
  const s = await getDriverSession();
  if (!s) throw new ApiError(401, "Not signed in");
  if (s.role === "driver") throw new ApiError(403, "Office access only");

  const b = await readJson(req);
  const customer = requireString(b.customer, "Customer", 200);
  const pickup = requireString(b.pickup, "Pickup location", 300);
  const delivery = requireString(b.delivery, "Delivery location", 300);
  const product = optionalString(b.product, "Product", 200);
  const truck = optionalString(b.truck, "Truck", 100);
  const trailer = optionalString(b.trailer, "Trailer", 100);
  const notes = optionalString(b.notes, "Notes", 1000);
  const estVolume =
    b.estimated_volume === undefined || b.estimated_volume === null || b.estimated_volume === ""
      ? null
      : (() => {
          const n = Number(b.estimated_volume);
          if (!isFinite(n) || n < 0 || n > 100000)
            throw new ApiError(400, "Estimated volume must be a positive number");
          return n;
        })();

  const valid = new Set<string>(HAZARD_ITEMS);
  const hazards = (Array.isArray(b.hazards) ? b.hazards : [])
    .filter((h): h is string => typeof h === "string" && valid.has(h));

  // Optional driver: verify they belong to this company before assigning.
  let driverId: number | null = null;
  if (b.driver_id !== undefined && b.driver_id !== null && b.driver_id !== "") {
    const id = Number(b.driver_id);
    if (!Number.isInteger(id) || id <= 0) throw new ApiError(400, "Driver is invalid");
    const d = await db().query(
      `SELECT id FROM users
       WHERE id = $1 AND company_id = $2 AND role = 'driver' AND active = TRUE`,
      [id, s.company_id]
    );
    if (d.rows.length === 0) throw new ApiError(400, "That driver doesn't exist");
    driverId = id;
  }

  const status = driverId ? "ASSIGNED" : "REQUESTED";
  const client = await db().connect();
  try {
    await client.query("BEGIN");
    const { rows } = await client.query(
      `INSERT INTO loads (company_id, customer, pickup_location, delivery_location,
                          driver_id, truck, trailer, product, estimated_volume,
                          hazards, notes, status, created_by)
       VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13) RETURNING id`,
      [s.company_id, customer, pickup, delivery, driverId, truck, trailer,
       product, estVolume, hazards.length ? hazards : null, notes, status, s.user_id]
    );
    const loadId = rows[0].id;
    await client.query(
      `INSERT INTO load_status_history
         (load_id, new_status, changed_by, changed_by_name, reason)
       VALUES ($1, $2, $3, $4, $5)`,
      [loadId, status, s.user_id, s.name,
       driverId ? "Load request sent" : "Job order created — awaiting driver"]
    );
    await client.query("COMMIT");
    log.info("load_created", {
      requestId, load_id: loadId, status, driver_id: driverId,
      hazards: hazards.length, by: s.name,
    });
    return NextResponse.json({ ok: true, load_id: loadId, status });
  } catch (e) {
    await client.query("ROLLBACK").catch(() => {});
    throw e;
  } finally {
    client.release();
  }
});
