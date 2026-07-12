"""Professional PDF invoice generation (ReportLab — pure Python, no system libraries).

Two layers, kept separate so it's easy to test and maintain:

  render_invoice_pdf(data)      -> bytes   # pure layout, takes a plain dict, no database
  generate_invoice_pdf(company_id, ticket_ids, ...) -> saves an invoice row + returns PDF

A non-developer changing the look only needs to touch render_invoice_pdf: the colors,
the column headings, and the footer text are all near the top of that function.
"""
import io
import logging
from datetime import date, timedelta

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable,
)
from reportlab.lib.enums import TA_RIGHT, TA_LEFT

from db import fetch_one, fetch_all, execute_returning

log = logging.getLogger("ticketdrop.invoice")


# ----------------------------------------------------------------- helpers
def _money(x):
    return f"${float(x or 0):,.2f}"


def _brand_color(hexstr):
    try:
        return colors.HexColor(hexstr or "#8B5CF6")
    except Exception:
        return colors.HexColor("#8B5CF6")


# ----------------------------------------------------------------- pure renderer
def render_invoice_pdf(data) -> bytes:
    """Build the PDF from a plain dict. No database access — easy to test.

    Expected keys:
      company: {name, address, phone, primary_color}
      invoice_number, invoice_date (date), due_date (date)
      customer_name
      line_items: [{date, ticket, description, qty, unit, rate, amount}]
      subtotal, tax, tax_label, tax_rate, total, terms
    """
    company = data.get("company", {})
    brand = _brand_color(company.get("primary_color"))
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        leftMargin=0.7 * inch, rightMargin=0.7 * inch,
        topMargin=0.6 * inch, bottomMargin=0.7 * inch,
        title=f"Invoice {data.get('invoice_number','')}",
    )
    styles = getSampleStyleSheet()
    normal = ParagraphStyle("n", parent=styles["Normal"], fontSize=9, leading=13)
    small = ParagraphStyle("s", parent=styles["Normal"], fontSize=8, leading=11, textColor=colors.HexColor("#6B7280"))
    right = ParagraphStyle("r", parent=normal, alignment=TA_RIGHT)
    label = ParagraphStyle("l", parent=small, textColor=colors.HexColor("#9CA3AF"))
    story = []

    # ---- header band: company name (left) + big INVOICE (right) ----
    name_style = ParagraphStyle("co", parent=styles["Title"], fontSize=22, textColor=colors.white, leading=24)
    inv_style = ParagraphStyle("iv", parent=styles["Title"], fontSize=22, textColor=colors.white,
                               alignment=TA_RIGHT, leading=24)
    header = Table(
        [[Paragraph(company.get("name", "Company"), name_style),
          Paragraph("INVOICE", inv_style)]],
        colWidths=[3.9 * inch, 3.0 * inch],
    )
    header.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), brand),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
    ]))
    story.append(header)
    story.append(Spacer(1, 14))

    # ---- company contact (left) + invoice meta (right) ----
    contact_bits = []
    if company.get("address"):
        contact_bits.append(company["address"])
    if company.get("phone"):
        contact_bits.append(company["phone"])
    contact_para = Paragraph("<br/>".join(contact_bits) or "&nbsp;", small)

    meta = Table([
        [Paragraph("Invoice #", label), Paragraph(str(data.get("invoice_number", "")), right)],
        [Paragraph("Date", label), Paragraph(data["invoice_date"].strftime("%b %d, %Y"), right)],
        [Paragraph("Due", label), Paragraph(data["due_date"].strftime("%b %d, %Y"), right)],
    ], colWidths=[0.9 * inch, 1.7 * inch])
    meta.setStyle(TableStyle([
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
    ]))
    top = Table([[contact_para, meta]], colWidths=[4.3 * inch, 2.6 * inch])
    top.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(top)
    story.append(Spacer(1, 16))

    # ---- bill to ----
    story.append(Paragraph("BILL TO", label))
    story.append(Paragraph(f"<b>{data.get('customer_name') or 'Customer'}</b>", normal))
    story.append(Spacer(1, 14))

    # ---- line items table ----
    head = ["Date", "Ticket #", "Description", "Qty", "Unit", "Rate", "Amount"]
    rows = [head]
    for li in data.get("line_items", []):
        rows.append([
            li.get("date", ""),
            li.get("ticket", ""),
            li.get("description", ""),
            f"{float(li.get('qty', 0)):,.2f}",
            li.get("unit", ""),
            _money(li.get("rate", 0)),
            _money(li.get("amount", 0)),
        ])
    tbl = Table(rows, colWidths=[0.85 * inch, 0.85 * inch, 2.5 * inch, 0.6 * inch, 0.5 * inch, 0.8 * inch, 0.9 * inch],
                repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), brand),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("ALIGN", (3, 0), (-1, -1), "RIGHT"),
        ("ALIGN", (4, 0), (4, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F4F4F6")]),
        ("LINEBELOW", (0, -1), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 10))

    # ---- totals block (right aligned) ----
    tax_label = data.get("tax_label", "Tax")
    tax_rate = data.get("tax_rate", 0)
    totals = Table([
        ["Subtotal", _money(data.get("subtotal", 0))],
        [f"{tax_label} ({float(tax_rate):g}%)", _money(data.get("tax", 0))],
        ["Total", _money(data.get("total", 0))],
    ], colWidths=[1.4 * inch, 1.1 * inch], hAlign="RIGHT")
    totals.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LINEABOVE", (0, 2), (-1, 2), 1, brand),
        ("FONTNAME", (0, 2), (-1, 2), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, 2), (-1, 2), brand),
        ("FONTSIZE", (0, 2), (-1, 2), 12),
        ("TOPPADDING", (0, 2), (-1, 2), 6),
    ]))
    story.append(totals)
    story.append(Spacer(1, 26))

    # ---- footer / terms ----
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#E5E7EB")))
    story.append(Spacer(1, 6))
    if data.get("terms"):
        story.append(Paragraph(data["terms"], small))
    story.append(Paragraph(f"Thank you for your business — {company.get('name','')}", small))

    doc.build(story)
    return buf.getvalue()


# ----------------------------------------------------------------- DB-backed builder
def build_invoice_data(company_id, ticket_ids, rate_per_m3=None, rate_per_hour=None,
                       invoice_number="DRAFT", invoice_date=None):
    """Load company + tickets and compute line items/totals into the dict the
    renderer expects. Rates fall back to the company's saved defaults."""
    invoice_date = invoice_date or date.today()
    c = fetch_one(
        "SELECT name, address, phone, primary_color, rate_per_m3, rate_per_hour, "
        "tax_rate, tax_label, invoice_terms FROM companies WHERE id=:id",
        {"id": company_id},
    )
    company = {
        "name": c[0] if c else "Company", "address": c[1] if c else "",
        "phone": c[2] if c else "", "primary_color": c[3] if c else "#8B5CF6",
    }
    def_m3 = float(c[4] or 0) if c else 0
    def_hr = float(c[5] or 0) if c else 0
    tax_rate = float(c[6] or 0) if c else 0
    tax_label = (c[7] if c else "Tax") or "Tax"
    terms = (c[8] if c else "") or ""

    r_m3 = def_m3 if rate_per_m3 is None else float(rate_per_m3)
    r_hr = def_hr if rate_per_hour is None else float(rate_per_hour)

    rows = fetch_all(
        "SELECT id, ticket_number, ticket_date, customer_name, product_description, "
        "actual_volume, hours_charged, load_id FROM tickets "
        "WHERE company_id=:cid AND id = ANY(:ids) ORDER BY ticket_date, id",
        {"cid": company_id, "ids": list(ticket_ids)},
    )

    line_items, subtotal, customer_name = [], 0.0, None
    for tid, tnum, tdate, cust, product, vol, hours, load_id in rows:
        customer_name = customer_name or cust
        d = tdate.strftime("%b %d") if tdate else ""
        vol = float(vol or 0)
        hours = float(hours or 0)
        if vol > 0:
            amt = round(vol * r_m3, 2)
            subtotal += amt
            line_items.append({"date": d, "ticket": tnum or f"#{tid}",
                               "description": (product or "Fluid hauling")[:48],
                               "qty": vol, "unit": "m³", "rate": r_m3, "amount": amt})
        if hours > 0 and r_hr > 0:
            amt = round(hours * r_hr, 2)
            subtotal += amt
            line_items.append({"date": d, "ticket": tnum or f"#{tid}",
                               "description": "Hourly / standby time",
                               "qty": hours, "unit": "hr", "rate": r_hr, "amount": amt})
        if vol <= 0 and (hours <= 0 or r_hr <= 0):
            # nothing priced — still show the ticket so totals reconcile
            line_items.append({"date": d, "ticket": tnum or f"#{tid}",
                               "description": (product or "Hauling") + " (rate not set)",
                               "qty": 0, "unit": "", "rate": 0, "amount": 0})

    subtotal = round(subtotal, 2)
    tax = round(subtotal * tax_rate / 100.0, 2)
    total = round(subtotal + tax, 2)
    return {
        "company": company,
        "invoice_number": invoice_number,
        "invoice_date": invoice_date,
        "due_date": invoice_date + timedelta(days=30),
        "customer_name": customer_name,
        "line_items": line_items,
        "subtotal": subtotal, "tax": tax, "tax_label": tax_label,
        "tax_rate": tax_rate, "total": total, "terms": terms,
    }


def next_invoice_number(company_id):
    row = fetch_one("SELECT invoice_prefix FROM companies WHERE id=:id", {"id": company_id})
    prefix = (row[0] if row and row[0] else "INV-")
    n = fetch_one("SELECT COUNT(*) FROM invoices WHERE company_id=:id", {"id": company_id})
    seq = (n[0] if n else 0) + 1
    return f"{prefix}{date.today().year}-{seq:04d}"


def generate_invoice_pdf(company_id, ticket_ids, rate_per_m3=None, rate_per_hour=None,
                         user_id=None):
    """Assign an invoice number, record the invoice, and return the PDF.
    Returns (invoice_number, filename, pdf_bytes, data). Does NOT change ticket
    status — the caller decides when to mark tickets INVOICED."""
    number = next_invoice_number(company_id)
    data = build_invoice_data(company_id, ticket_ids, rate_per_m3, rate_per_hour,
                              invoice_number=number)
    pdf = render_invoice_pdf(data)
    execute_returning(
        "INSERT INTO invoices (company_id, invoice_number, customer_name, ticket_ids, "
        "subtotal, tax, total, created_by) "
        "VALUES (:cid, :num, :cust, :ids, :sub, :tax, :tot, :uid) RETURNING id",
        {"cid": company_id, "num": number, "cust": data["customer_name"],
         "ids": list(ticket_ids), "sub": data["subtotal"], "tax": data["tax"],
         "tot": data["total"], "uid": user_id},
    )
    filename = f"{number}.pdf".replace("/", "-")
    log.info("Generated invoice %s for company %s (%d tickets, %s)",
             number, company_id, len(list(ticket_ids)), data["total"])
    return number, filename, pdf, data
