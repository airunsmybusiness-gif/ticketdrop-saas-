# Field Ticket PDFs

Every completed load can be exported as a professional, branded **field ticket PDF** —
suitable for official records or sending to the customer. It follows real oilfield
ticket conventions: branded header, load details, product & volumes, a **site & load
hazards checklist** with tick boxes, a **backup photo of the load**, and the driver's
completion/signature block.

See `sample_field_ticket.pdf` in this repo for an example.

---

## What's on the ticket
| Section | Contents |
|---------|----------|
| Header band | Company name + color (from Settings), ticket #, date, load #, customer ticket # |
| Load details | Customer, driver/operator, origin, destination, truck, trailer, arrive/depart times |
| Product & volumes | Product, placard, density, BS&W, estimated + actual volume (m³), hours |
| **Site & load hazards** | Two-column checklist with tick boxes — ticked items print filled in the brand color: H2S present · High pressure lines · Slippery surfaces / spills · Heavy equipment movement · Chemical / fluid exposure · Fire / explosion risk · Overhead power lines · Confined space · Lease road traffic · Overweight load risk · Other (with notes) |
| **Backup photo** | The load photo the driver attached at completion (framed); a clear "No photo attached" placeholder otherwise |
| Completion | Driver signature + signed-at time, notes |
| Footer | "{Company} — official field ticket record" |

The whole ticket fits on **one page** when a photo is attached.

---

## How it works in the app
1. **Driver completes a load** (Driver → My Active Load → Complete Field Ticket). The form now includes:
   - **Site & Load Hazards** — tick every hazard present (ticking *Other* requires a note), and
   - **Backup Photo of the Load** — take/upload one JPG or PNG.
2. After submitting, the driver can download the PDF anytime from **Driver → History → 📄 PDF**.
3. **AR** can download the same PDF while reviewing (**AR / Billing → Review Tickets → 📄 PDF**) to see the hazards and photo before verifying.

## Packages & setup
- **No new packages** — it uses ReportLab, already in `requirements.txt` from the invoice feature.
- **Database**: re-run `schema.sql` in Supabase once (safe/idempotent). It adds four columns to
  `tickets`: `hazards`, `hazard_notes`, `load_photo`, `load_photo_mime`. The photo is stored in
  the database itself, so there's nothing extra to configure.

## Customizing
- **Branding** (name, color, address, phone) comes from **Settings → Company** — each company's
  tickets automatically print in their color.
- **The hazards list** lives in one obvious place: `HAZARD_ITEMS` at the top of
  `services/field_ticket.py`. Add or remove a line there and both the driver form and the PDF
  update together.
- **The layout** is all in `render_field_ticket_pdf()` in the same file — colors and section
  titles are near the top. It takes a plain dictionary (no database), so it's easy to preview.
