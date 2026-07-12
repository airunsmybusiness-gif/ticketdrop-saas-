// POST — driver completes a load: creates the field ticket (hazards checklist,
// backup photo, notes, signature) and moves the load to COMPLETED.
// Writes the exact same tickets columns as the Streamlit driver form, so the
// existing AR review, field-ticket PDF, and invoicing all keep working.
import { NextResponse } from "next/server";
import { db } from "@/lib/db";
import { getDriverSession } from "@/lib/session";
import { HAZARD_ITEMS } from "@/lib/hazards";

const MAX_PHOTO_BYTES = 5 * 1024 * 1024; // 5 MB

type CompleteBody = {
  load_id?: number;
  ticket_number?: string;
  actual_volume?: number;
  hours?: number;
  hazards?: string[];
  hazard_notes?: string;
  notes?: string;
  signature?: string;
  photo_base64?: string; // data-URL or raw base64 (jpeg/png)
  photo_mime?: string;
};

export async function POST(req: Request) {
  const s = await getDriverSession();
  if (!s) return NextResponse.json({ error: "Not signed in" }, { status: 401 });

  let b: CompleteBody;
  try {
    b = await req.json();
  } catch {
    return NextResponse.json({ error: "Bad request" }, { status: 400 });
  }
  const loadId = Number(b.load_id);
  if (!loadId) return NextResponse.json({ error: "Missing load" }, { status: 400 });
  if (!b.ticket_number?.trim())
    return NextResponse.json({ error: "Ticket # is required" }, { status: 400 });
  if (!b.signature?.trim())
    return NextResponse.json({ error: "Signature is required" }, { status: 400 });
  if (!b.actual_volume || b.actual_volume <= 0)
    return NextResponse.json({ error: "Actual volume is required" }, { status: 400 });

  const valid = new Set<string>(HAZARD_ITEMS);
  const hazards = (b.hazards || []).filter((h) => valid.has(h));
  if (hazards.includes("Other (see notes)") && !b.hazard_notes?.trim())
    return NextResponse.json({ error: "Describe the 'Other' hazard in notes" }, { status: 400 });

  let photo: Buffer | null = null;
  let photoMime: string | null = null;
  if (b.photo_base64) {
    const m = b.photo_base64.match(/^data:(image\/(?:jpeg|png));base64,(.+)$/);
    const raw = m ? m[2] : b.photo_base64;
    photoMime = m ? m[1] : b.photo_mime || "image/jpeg";
    try {
      photo = Buffer.from(raw, "base64");
    } catch {
      return NextResponse.json({ error: "Photo could not be read" }, { status: 400 });
    }
    if (photo.length > MAX_PHOTO_BYTES)
      return NextResponse.json({ error: "Photo too large (max 5 MB)" }, { status: 400 });
  }

  const client = await db().connect();
  try {
    await client.query("BEGIN");
    const { rows } = await client.query(
      `SELECT status, customer, truck, trailer, pickup_location, delivery_location
       FROM loads WHERE id = $1 AND company_id = $2 AND driver_id = $3 FOR UPDATE`,
      [loadId, s.company_id, s.user_id]
    );
    if (rows.length === 0) {
      await client.query("ROLLBACK");
      return NextResponse.json({ error: "Load not found" }, { status: 404 });
    }
    if (rows[0].status !== "IN_PROGRESS") {
      await client.query("ROLLBACK");
      return NextResponse.json(
        { error: `Load is ${rows[0].status}, not in progress` },
        { status: 409 }
      );
    }
    const L = rows[0];

    const ticket = await client.query(
      `INSERT INTO tickets (company_id, load_id, ticket_number, ticket_date,
         operator_name, truck_number, trailer_number, customer_name,
         loaded_at, offloaded_at, actual_volume, hours_charged,
         hazards, hazard_notes, load_photo, load_photo_mime,
         driver_signature, signature_datetime, status)
       VALUES ($1,$2,$3,CURRENT_DATE,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,NOW(),'SUBMITTED')
       RETURNING id`,
      [s.company_id, loadId, b.ticket_number.trim(), s.name, L.truck, L.trailer,
       L.customer, L.pickup_location, L.delivery_location,
       b.actual_volume, b.hours || 0,
       hazards.length ? hazards : null, b.hazard_notes?.trim() || null,
       photo, photo ? photoMime : null, b.signature.trim()]
    );

    await client.query(
      `UPDATE loads SET status='COMPLETED', status_changed_at=NOW(),
                        status_changed_by=$1, updated_at=NOW() WHERE id=$2`,
      [s.user_id, loadId]
    );
    const reason = `Ticket #${b.ticket_number.trim()} submitted` +
      (b.notes?.trim() ? ` | Note: ${b.notes.trim()}` : "");
    await client.query(
      `INSERT INTO load_status_history
         (load_id, old_status, new_status, changed_by, changed_by_name, reason)
       VALUES ($1,'IN_PROGRESS','COMPLETED',$2,$3,$4)`,
      [loadId, s.user_id, s.name, reason]
    );
    await client.query("COMMIT");
    return NextResponse.json({ ok: true, ticket_id: ticket.rows[0].id });
  } catch (e) {
    await client.query("ROLLBACK");
    console.error("complete failed", e);
    return NextResponse.json({ error: "Could not save the ticket" }, { status: 500 });
  } finally {
    client.release();
  }
}
