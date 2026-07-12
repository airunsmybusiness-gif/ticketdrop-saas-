// POST — driver completes a load: creates the field ticket (hazards checklist,
// backup photo, notes, signature) and moves the load to COMPLETED.
// Writes the exact same tickets columns as the Streamlit driver form, so the
// existing AR review, field-ticket PDF, and invoicing all keep working.
import { NextResponse } from "next/server";
import { db } from "@/lib/db";
import { getDriverSession } from "@/lib/session";
import { HAZARD_ITEMS } from "@/lib/hazards";
import { handle, readJson, requireId, requireString, requireNumber, optionalString, ApiError } from "@/lib/api";
import { log } from "@/lib/log";

const MAX_PHOTO_BYTES = 5 * 1024 * 1024; // 5 MB

export const POST = handle("driver_complete", async (req, { requestId }) => {
  const s = await getDriverSession();
  if (!s) throw new ApiError(401, "Not signed in");

  const b = await readJson(req);
  const loadId = requireId(b.load_id, "Load");
  const ticketNumber = requireString(b.ticket_number, "Ticket #", 50);
  const signature = requireString(b.signature, "Signature", 120);
  const actualVolume = requireNumber(b.actual_volume, "Actual volume", { min: 0.01, max: 100000 });
  const hours = b.hours === undefined || b.hours === null || b.hours === ""
    ? 0 : requireNumber(b.hours, "Hours", { min: 0, max: 100 });
  const hazardNotes = optionalString(b.hazard_notes, "Hazard notes", 1000);
  const notes = optionalString(b.notes, "Notes", 1000);

  const valid = new Set<string>(HAZARD_ITEMS);
  const hazards = (Array.isArray(b.hazards) ? b.hazards : [])
    .filter((h): h is string => typeof h === "string" && valid.has(h));
  if (hazards.includes("Other (see notes)") && !hazardNotes)
    throw new ApiError(400, "Describe the 'Other' hazard in notes");

  let photo: Buffer | null = null;
  let photoMime: string | null = null;
  if (typeof b.photo_base64 === "string" && b.photo_base64) {
    const m = b.photo_base64.match(/^data:(image\/(?:jpeg|png));base64,(.+)$/);
    const raw = m ? m[2] : b.photo_base64;
    photoMime = m ? m[1] : (typeof b.photo_mime === "string" ? b.photo_mime : "image/jpeg");
    try {
      photo = Buffer.from(raw, "base64");
    } catch {
      throw new ApiError(400, "Photo could not be read");
    }
    if (photo.length > MAX_PHOTO_BYTES) throw new ApiError(400, "Photo too large (max 5 MB)");
  }

  const client = await db().connect();
  try {
    await client.query("BEGIN");
    const { rows } = await client.query(
      `SELECT status, customer, truck, trailer, pickup_location, delivery_location
       FROM loads WHERE id = $1 AND company_id = $2 AND driver_id = $3 FOR UPDATE`,
      [loadId, s.company_id, s.user_id]
    );
    if (rows.length === 0) throw new ApiError(404, "Load not found");
    if (rows[0].status !== "IN_PROGRESS")
      throw new ApiError(409, `Load is ${rows[0].status}, not in progress`);
    const L = rows[0];

    const ticket = await client.query(
      `INSERT INTO tickets (company_id, load_id, ticket_number, ticket_date,
         operator_name, truck_number, trailer_number, customer_name,
         loaded_at, offloaded_at, actual_volume, hours_charged,
         hazards, hazard_notes, load_photo, load_photo_mime,
         driver_signature, signature_datetime, status)
       VALUES ($1,$2,$3,CURRENT_DATE,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,NOW(),'SUBMITTED')
       RETURNING id`,
      [s.company_id, loadId, ticketNumber, s.name, L.truck, L.trailer,
       L.customer, L.pickup_location, L.delivery_location,
       actualVolume, hours,
       hazards.length ? hazards : null, hazardNotes,
       photo, photo ? photoMime : null, signature]
    );

    await client.query(
      `UPDATE loads SET status='COMPLETED', status_changed_at=NOW(),
                        status_changed_by=$1, updated_at=NOW() WHERE id=$2`,
      [s.user_id, loadId]
    );
    const reason = `Ticket #${ticketNumber} submitted` + (notes ? ` | Note: ${notes}` : "");
    await client.query(
      `INSERT INTO load_status_history
         (load_id, old_status, new_status, changed_by, changed_by_name, reason)
       VALUES ($1,'IN_PROGRESS','COMPLETED',$2,$3,$4)`,
      [loadId, s.user_id, s.name, reason]
    );
    await client.query("COMMIT");
    log.info("ticket_submitted", {
      requestId, load_id: loadId, ticket_id: ticket.rows[0].id,
      hazards: hazards.length, has_photo: Boolean(photo), by: s.name,
    });
    return NextResponse.json({ ok: true, ticket_id: ticket.rows[0].id });
  } catch (e) {
    await client.query("ROLLBACK").catch(() => {});
    throw e;
  } finally {
    client.release();
  }
});
