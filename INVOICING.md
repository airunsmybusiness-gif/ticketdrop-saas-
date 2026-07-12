# PDF Invoices

TicketDrop generates clean, branded PDF invoices from completed tickets — professional
enough to email straight to a customer. Each company gets its own colors, name, rates,
tax, and invoice numbering, with no code changes.

---

## What you get
- A **one-click PDF** built from your "Ready for Invoice" tickets, grouped by customer.
- **Your branding**: the PDF header, table, and total use your company color and name (from Settings).
- **Line items** for each ticket: date, ticket #, description (product), volume (m³) and/or hours, rate, amount.
- **Subtotal, tax (e.g. GST), and total**, plus your footer/terms.
- **Sequential invoice numbers** per company (e.g. `RICK-2026-0001`), recorded in an `invoices` table.

See `sample_invoice.pdf` in this repo for an example of the output.

---

## How to use it (in the app)
1. Sign in as **AR** or **Admin**.
2. **Settings → Company** (Admin): set your **Rate per m³**, **Rate per hour**, **Tax rate**, tax label,
   invoice number prefix, and terms. (You only do this once; you can override rates per-invoice later.)
3. **AR / Billing → Create Invoice**:
   - Pick a **customer** (only customers with tickets marked *Ready for Invoice* appear).
   - Confirm or override the rates. The **Subtotal / Tax / Total** preview updates live.
   - Click **Generate PDF Invoice**, then **Download**. (By default the tickets are marked *Invoiced* so they won't be billed twice — untick the box if you want to keep them open.)

> Tickets reach "Ready for Invoice" through the normal flow: driver submits ticket → AR
> **Verifies** it → AR marks it **Ready for Invoice**.

---

## Installing the needed package
The only new dependency is **ReportLab** (pure Python — no system libraries, so it "just works" on Railway/Render).

- **On Railway/Render:** nothing to do — it's already in `requirements.txt` and installs automatically on deploy.
- **On your own computer (for local testing):**
  ```
  pip install reportlab
  ```
- **Database:** the invoice fields and `invoices` table are included in `schema.sql`. If you set up
  your database before this feature existed, just re-run `schema.sql` in Supabase — it only adds the
  new bits and is safe to re-run.

---

## Customizing per company
- **Rates, tax, prefix, terms, color, name** → all in **Settings → Company**. No code needed.
- **A second company** automatically gets its own branding and its own invoice number sequence.

## Changing the invoice *look* (optional, for the technically curious)
Everything about the layout lives in one function: `render_invoice_pdf()` in
`services/invoice.py`. The colors, the column headings, and the footer text are all near the
top of that function and clearly labeled. You do **not** need to touch the database code to
restyle the PDF — `render_invoice_pdf` takes a plain dictionary, so you can preview changes by
running it with sample data.
