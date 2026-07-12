// GET → one invoice with company details and per-ticket line items,
// for the printable invoice page.
import { NextResponse } from "next/server";
import { db } from "@/lib/db";
import { getDriverSession } from "@/lib/session";
import { handleWithParams, requireId, ApiError } from "@/lib/api";

export const dynamic = "force-dynamic";

export const GET = handleWithParams<{ id: string }>("billing_invoice_get", async (_req, params) => {
  const s = await getDriverSession();
  if (!s) throw new ApiError(401, "Not signed in");
  if (s.role === "driver") throw new ApiError(403, "Office access only");

  const invId = requireId(params.id, "Invoice");
  const inv = await db().query(
    `SELECT id, invoice_number, customer_name, ticket_ids, subtotal, tax, total,
            notes, created_at
     FROM invoices WHERE id = $1 AND company_id = $2`,
    [invId, s.company_id]
  );
  if (inv.rows.length === 0) throw new ApiError(404, "Invoice not found");
  const invoice = inv.rows[0];

  // Rates were stored on the invoice notes at creation (rate_m3=..;rate_hr=..)
  const rateM3 = Number(/rate_m3=([\d.]+)/.exec(invoice.notes ?? "")?.[1] ?? 0);
  const rateHr = Number(/rate_hr=([\d.]+)/.exec(invoice.notes ?? "")?.[1] ?? 0);

  const [company, tickets] = await Promise.all([
    db().query(
      `SELECT name, address, phone, tax_rate, tax_label, invoice_terms
       FROM companies WHERE id = $1`,
      [s.company_id]
    ),
    db().query(
      `SELECT id, ticket_number, ticket_date, customer_name, operator_name,
              actual_volume, hours_charged,
              (SELECT product FROM loads WHERE loads.id = tickets.load_id) AS product
       FROM tickets WHERE company_id = $1 AND id = ANY($2)
       ORDER BY ticket_date, id`,
      [s.company_id, invoice.ticket_ids ?? []]
    ),
  ]);

  return NextResponse.json({
    invoice,
    company: company.rows[0] ?? {},
    tickets: tickets.rows,
    rates: { rate_per_m3: rateM3, rate_per_hour: rateHr },
  });
});
