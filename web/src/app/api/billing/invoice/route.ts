// POST { ticket_ids, rate_per_m3?, rate_per_hour? } → create an invoice from
// READY_FOR_INVOICE tickets: sequential per-company number (same scheme as
// the Streamlit generator), line items from volume/hours × rates, tax from
// the company settings, tickets marked INVOICED with history.
import { NextResponse } from "next/server";
import { db } from "@/lib/db";
import { getDriverSession } from "@/lib/session";
import { handle, readJson, ApiError } from "@/lib/api";
import { log } from "@/lib/log";

export const POST = handle("billing_invoice_create", async (req, { requestId }) => {
  const s = await getDriverSession();
  if (!s) throw new ApiError(401, "Not signed in");
  if (s.role === "driver") throw new ApiError(403, "Office access only");

  const b = await readJson(req);
  const ids = (Array.isArray(b.ticket_ids) ? b.ticket_ids : [])
    .map(Number).filter((n) => Number.isInteger(n) && n > 0);
  if (ids.length === 0) throw new ApiError(400, "Pick at least one ticket");

  const num = (v: unknown, fallback: number) => {
    if (v === undefined || v === null || v === "") return fallback;
    const n = Number(v);
    if (!isFinite(n) || n < 0) throw new ApiError(400, "Rates must be positive numbers");
    return n;
  };

  const client = await db().connect();
  try {
    await client.query("BEGIN");
    const comp = await client.query(
      `SELECT rate_per_m3, rate_per_hour, tax_rate, tax_label, invoice_prefix
       FROM companies WHERE id = $1`,
      [s.company_id]
    );
    const c = comp.rows[0] ?? {};
    const rateM3 = num(b.rate_per_m3, Number(c.rate_per_m3 ?? 0));
    const rateHr = num(b.rate_per_hour, Number(c.rate_per_hour ?? 0));
    const taxRate = Number(c.tax_rate ?? 0);

    const { rows: tickets } = await client.query(
      `SELECT id, ticket_number, customer_name, actual_volume, hours_charged
       FROM tickets
       WHERE company_id = $1 AND id = ANY($2) AND status = 'READY_FOR_INVOICE'
       FOR UPDATE`,
      [s.company_id, ids]
    );
    if (tickets.length !== ids.length)
      throw new ApiError(409, "Some tickets are no longer ready to invoice — refresh and try again");

    let subtotal = 0;
    for (const t of tickets) {
      subtotal += Number(t.actual_volume ?? 0) * rateM3;
      subtotal += Number(t.hours_charged ?? 0) * rateHr;
    }
    subtotal = Math.round(subtotal * 100) / 100;
    const tax = Math.round(subtotal * taxRate) / 100;
    const total = Math.round((subtotal + tax) * 100) / 100;

    const { rows: cnt } = await client.query(
      `SELECT COUNT(*) AS n FROM invoices WHERE company_id = $1`,
      [s.company_id]
    );
    const seq = Number(cnt[0].n) + 1;
    const number = `${c.invoice_prefix || "INV-"}${new Date().getFullYear()}-${String(seq).padStart(4, "0")}`;

    const inv = await client.query(
      `INSERT INTO invoices (company_id, invoice_number, customer_name, ticket_ids,
                             subtotal, tax, total, notes, created_by)
       VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9) RETURNING id`,
      [s.company_id, number, tickets[0].customer_name, ids, subtotal, tax, total,
       `rate_m3=${rateM3};rate_hr=${rateHr}`, s.user_id]
    );

    for (const t of tickets) {
      await client.query(
        `UPDATE tickets SET status = 'INVOICED', invoiced_at = NOW(),
                            status_changed_at = NOW(), status_changed_by = $1,
                            updated_at = NOW()
         WHERE id = $2`,
        [s.user_id, t.id]
      );
      await client.query(
        `INSERT INTO ticket_status_history
           (ticket_id, old_status, new_status, changed_by, changed_by_name, reason)
         VALUES ($1, 'READY_FOR_INVOICE', 'INVOICED', $2, $3, $4)`,
        [t.id, s.user_id, s.name, `Invoice ${number}`]
      );
    }
    await client.query("COMMIT");
    log.info("invoice_created", {
      requestId, invoice_id: inv.rows[0].id, number, tickets: ids.length, total, by: s.name,
    });
    return NextResponse.json({ ok: true, invoice_id: inv.rows[0].id, number, total });
  } catch (e) {
    await client.query("ROLLBACK").catch(() => {});
    throw e;
  } finally {
    client.release();
  }
});
