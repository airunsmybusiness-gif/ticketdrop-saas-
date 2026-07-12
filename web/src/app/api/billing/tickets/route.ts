// GET → everything the Billing page needs: tickets awaiting review,
// tickets ready to invoice (grouped client-side by customer), recent
// invoices, and the company's saved rates.
import { NextResponse } from "next/server";
import { db } from "@/lib/db";
import { getDriverSession } from "@/lib/session";
import { handle, ApiError } from "@/lib/api";

export const dynamic = "force-dynamic";

export const GET = handle("billing_tickets", async () => {
  const s = await getDriverSession();
  if (!s) throw new ApiError(401, "Not signed in");
  if (s.role === "driver") throw new ApiError(403, "Office access only");

  const cid = s.company_id;
  const [toReview, ready, invoices, company] = await Promise.all([
    db().query(
      `SELECT t.id, t.ticket_number, t.ticket_date, t.customer_name,
              t.operator_name, t.actual_volume, t.hours_charged,
              t.hazards, t.hazard_notes, t.driver_signature,
              t.load_id, l.pickup_location, l.delivery_location,
              l.product, (t.load_photo IS NOT NULL) AS has_photo
       FROM tickets t LEFT JOIN loads l ON l.id = t.load_id
       WHERE t.company_id = $1 AND t.status = 'SUBMITTED'
       ORDER BY t.created_at DESC`,
      [cid]
    ),
    db().query(
      `SELECT t.id, t.ticket_number, t.ticket_date, t.customer_name,
              t.actual_volume, t.hours_charged
       FROM tickets t
       WHERE t.company_id = $1 AND t.status = 'READY_FOR_INVOICE'
       ORDER BY t.customer_name, t.ticket_date`,
      [cid]
    ),
    db().query(
      `SELECT id, invoice_number, customer_name, subtotal, tax, total, created_at
       FROM invoices WHERE company_id = $1 ORDER BY id DESC LIMIT 25`,
      [cid]
    ),
    db().query(
      `SELECT rate_per_m3, rate_per_hour, tax_rate, tax_label
       FROM companies WHERE id = $1`,
      [cid]
    ),
  ]);

  const c = company.rows[0] ?? {};
  return NextResponse.json({
    to_review: toReview.rows,
    ready: ready.rows,
    invoices: invoices.rows,
    rates: {
      rate_per_m3: Number(c.rate_per_m3 ?? 0),
      rate_per_hour: Number(c.rate_per_hour ?? 0),
      tax_rate: Number(c.tax_rate ?? 0),
      tax_label: c.tax_label ?? "Tax",
    },
  });
});
