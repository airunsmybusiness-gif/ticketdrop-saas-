"""Professional field/load ticket PDF (ReportLab — pure Python).

Generated after a driver completes a load. Follows real oilfield ticket
conventions: branded header, ticket meta, load details, product & volumes,
a hazards checklist with tick boxes, a backup photo of the load, and the
completion/signature block.

Same two-layer design as the invoice module:

  render_field_ticket_pdf(data) -> bytes    # pure layout, plain dict, no DB
  generate_field_ticket_pdf(ticket_id, company_id) -> (filename, bytes)

To restyle, edit only render_field_ticket_pdf — colors and section titles
are near the top.
"""
import io
import logging

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, HRFlowable,
)

from db import fetch_one

log = logging.getLogger("ticketdrop.field_ticket")

# The standard hazards checklist shown on every ticket (and in the driver form).
# Keep the wording short — these print as a 2-column checklist.
HAZARD_ITEMS = [
    "H2S present",
    "High pressure lines",
    "Slippery surfaces / spills",
    "Heavy equipment movement",
    "Chemical / fluid exposure",
    "Fire / explosion risk",
    "Overhead power lines",
    "Confined space",
    "Lease road traffic",
    "Overweight load risk",
    "Other (see notes)",
]

GREY = colors.HexColor("#6B7280")
LIGHT = colors.HexColor("#F4F4F6")
LINE = colors.HexColor("#E5E7EB")


def _brand_color(hexstr):
    try:
        return colors.HexColor(hexstr or "#8B5CF6")
    except Exception:
        return colors.HexColor("#8B5CF6")


def _fmt(v, dash="—"):
    if v is None or v == "":
        return dash
    return str(v)


def _ts(v):
    """Format a timestamp column for print; pass strings through unchanged."""
    if v is None or v == "":
        return None
    if hasattr(v, "strftime"):
        return v.strftime("%Y-%m-%d %H:%M")
    return str(v)


# --------------------------------------------------------------- pure renderer
def render_field_ticket_pdf(data) -> bytes:
    """Build the field ticket PDF from a plain dict (no database).

    Expected keys (all optional except company/ticket_number):
      company: {name, address, phone, primary_color}
      ticket_number, customer_ticket_number, ticket_date, load_id, status
      customer_name, operator_name (driver), truck_number, trailer_number
      pickup, delivery, arrive_load, depart_load, arrive_offload, depart_offload
      product, commodity, placard, density, bsw, est_volume, actual_volume, hours
      hazards: [list of ticked labels from HAZARD_ITEMS]
      hazard_notes: str
      photo_bytes: bytes|None   (jpeg/png of the load)
      signature, signature_datetime, notes
    """
    company = data.get("company", {})
    brand = _brand_color(company.get("primary_color"))
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        leftMargin=0.6 * inch, rightMargin=0.6 * inch,
        topMargin=0.45 * inch, bottomMargin=0.45 * inch,
        title=f"Field Ticket {data.get('ticket_number', '')}",
    )
    styles = getSampleStyleSheet()
    normal = ParagraphStyle("n", parent=styles["Normal"], fontSize=9, leading=12)
    small = ParagraphStyle("s", parent=normal, fontSize=7.5, leading=10, textColor=GREY)
    label = ParagraphStyle("lb", parent=small, textColor=colors.HexColor("#9CA3AF"))
    value = ParagraphStyle("v", parent=normal, fontSize=9.5)
    story = []
    W = doc.width  # usable width

    def section(title):
        t = Table([[Paragraph(f"<b>{title}</b>",
                              ParagraphStyle("st", parent=normal, fontSize=9,
                                             textColor=colors.white))]],
                  colWidths=[W])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), brand),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 3.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
        ]))
        story.append(t)
        story.append(Spacer(1, 6))

    # ---- header band ----
    co_style = ParagraphStyle("co", parent=styles["Title"], fontSize=18,
                              textColor=colors.white, leading=21)
    ft_style = ParagraphStyle("ft", parent=styles["Title"], fontSize=15,
                              textColor=colors.white, alignment=TA_RIGHT, leading=18)
    header = Table([[
        Paragraph(company.get("name", "Company"), co_style),
        Paragraph(f"FIELD TICKET<br/><font size=11>#{_fmt(data.get('ticket_number'))}</font>", ft_style),
    ]], colWidths=[W * 0.62, W * 0.38])
    header.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), brand),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(header)

    # thin contact strip under the band
    contact = " · ".join(x for x in [company.get("address"), company.get("phone")] if x)
    strip = Table([[Paragraph(contact or "&nbsp;", small),
                    Paragraph(f"Date: <b>{_fmt(data.get('ticket_date'))}</b> &nbsp;&nbsp; "
                              f"Load #: <b>{_fmt(data.get('load_id'))}</b> &nbsp;&nbsp; "
                              f"Customer Ticket #: <b>{_fmt(data.get('customer_ticket_number'))}</b>",
                              ParagraphStyle("m", parent=small, alignment=TA_RIGHT))]],
                  colWidths=[W * 0.45, W * 0.55])
    strip.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(strip)
    story.append(Spacer(1, 9))

    # ---- load details: two-column grid ----
    section("LOAD DETAILS")

    def kv(k, v):
        return [Paragraph(k, label), Paragraph(f"<b>{_fmt(v)}</b>", value)]

    grid = Table([
        kv("Customer", data.get("customer_name")) + kv("Driver / Operator", data.get("operator_name")),
        kv("Origin (loaded at)", data.get("pickup")) + kv("Destination (offloaded at)", data.get("delivery")),
        kv("Truck", data.get("truck_number")) + kv("Trailer", data.get("trailer_number")),
        kv("Arrive load", data.get("arrive_load")) + kv("Depart load", data.get("depart_load")),
        kv("Arrive offload", data.get("arrive_offload")) + kv("Depart offload", data.get("depart_offload")),
    ], colWidths=[W * 0.16, W * 0.34, W * 0.16, W * 0.34])
    grid.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LINEBELOW", (0, 0), (-1, -2), 0.4, LINE),
    ]))
    story.append(grid)
    story.append(Spacer(1, 7))

    # ---- product & volumes ----
    section("PRODUCT &amp; VOLUMES")
    prod = Table([
        [Paragraph("Product", label), Paragraph("Placard", label), Paragraph("Density", label),
         Paragraph("BS&amp;W", label), Paragraph("Est. Vol (m³)", label),
         Paragraph("Actual Vol (m³)", label), Paragraph("Hours", label)],
        [Paragraph(f"<b>{_fmt(data.get('product'))}</b>", value),
         Paragraph(_fmt(data.get("placard")), value),
         Paragraph(_fmt(data.get("density")), value),
         Paragraph(_fmt(data.get("bsw")), value),
         Paragraph(_fmt(data.get("est_volume")), value),
         Paragraph(f"<b>{_fmt(data.get('actual_volume'))}</b>", value),
         Paragraph(_fmt(data.get("hours")), value)],
    ], colWidths=[W * 0.28, W * 0.13, W * 0.11, W * 0.10, W * 0.13, W * 0.14, W * 0.11])
    prod.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), LIGHT),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("BOX", (0, 0), (-1, -1), 0.4, LINE),
        ("LINEBELOW", (0, 0), (-1, 0), 0.4, LINE),
    ]))
    story.append(prod)
    story.append(Spacer(1, 7))

    # ---- hazards checklist with tick boxes ----
    section("SITE &amp; LOAD HAZARDS")
    ticked = set(data.get("hazards") or [])

    def hazard_cell(item):
        """A tick box + label. Checked boxes are brand-colored with a white X."""
        checked = item in ticked
        box = Table([[Paragraph("<b>X</b>" if checked else "",
                                ParagraphStyle("bx", parent=normal, fontSize=8,
                                               textColor=colors.white, alignment=1,
                                               leading=8))]],
                    colWidths=[0.16 * inch], rowHeights=[0.16 * inch])
        box.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.9, brand if checked else GREY),
            ("BACKGROUND", (0, 0), (-1, -1), brand if checked else colors.white),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 1),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]))
        text = Paragraph(f"<b>{item}</b>" if checked else item, normal)
        cell = Table([[box, text]], colWidths=[0.24 * inch, W / 2 - 0.42 * inch])
        cell.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (0, 0), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))
        return cell

    half = (len(HAZARD_ITEMS) + 1) // 2
    col_a, col_b = HAZARD_ITEMS[:half], HAZARD_ITEMS[half:]
    rows = []
    for i in range(half):
        left_cell = hazard_cell(col_a[i])
        right_cell = hazard_cell(col_b[i]) if i < len(col_b) else ""
        rows.append([left_cell, right_cell])
    hz = Table(rows, colWidths=[W / 2, W / 2])
    hz.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(hz)
    if data.get("hazard_notes"):
        story.append(Spacer(1, 4))
        story.append(Paragraph(f"<b>Hazard notes:</b> {data['hazard_notes']}", normal))
    story.append(Spacer(1, 7))

    # ---- backup photo of the load ----
    section("BACKUP PHOTO — LOAD")
    photo_bytes = data.get("photo_bytes")
    if photo_bytes:
        try:
            img_reader = ImageReader(io.BytesIO(photo_bytes))
            iw, ih = img_reader.getSize()
            max_w, max_h = W * 0.55, 1.7 * inch
            scale = min(max_w / iw, max_h / ih)
            img = Image(io.BytesIO(photo_bytes), width=iw * scale, height=ih * scale)
            frame = Table([[img]], colWidths=[iw * scale + 10])
            frame.setStyle(TableStyle([
                ("BOX", (0, 0), (-1, -1), 0.8, LINE),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ]))
            story.append(frame)
            story.append(Paragraph("Photo captured by driver at completion.", small))
        except Exception:
            log.warning("Could not embed load photo; falling back to placeholder", exc_info=True)
            photo_bytes = None
    if not photo_bytes:
        ph = Table([[Paragraph("No photo attached", ParagraphStyle(
            "ph", parent=small, alignment=1, fontSize=9))]],
            colWidths=[W], rowHeights=[0.9 * inch])
        ph.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.8, LINE),
            ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(ph)
    story.append(Spacer(1, 7))

    # ---- completion ----
    section("COMPLETION")
    comp = Table([
        kv("Driver signature", data.get("signature")) + kv("Signed at", data.get("signature_datetime")),
    ], colWidths=[W * 0.16, W * 0.34, W * 0.16, W * 0.34])
    comp.setStyle(TableStyle([
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(comp)
    if data.get("notes"):
        story.append(Spacer(1, 3))
        story.append(Paragraph(f"<b>Notes:</b> {data['notes']}", normal))
    story.append(Spacer(1, 6))

    # ---- footer ----
    story.append(HRFlowable(width="100%", thickness=0.5, color=LINE))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        f"{company.get('name','')} — official field ticket record. "
        f"Generated by TicketDrop.", small))

    doc.build(story)
    return buf.getvalue()


# --------------------------------------------------------------- DB-backed
def generate_field_ticket_pdf(ticket_id, company_id):
    """Load a ticket + its company branding and return (filename, pdf_bytes)."""
    t = fetch_one(
        "SELECT t.ticket_number, t.customer_ticket_number, t.ticket_date, t.load_id, "
        "t.customer_name, t.operator_name, t.truck_number, t.trailer_number, "
        "t.loaded_at, t.offloaded_at, t.arrive_load_datetime, t.depart_load_datetime, "
        "t.arrive_offload_datetime, t.depart_offload_datetime, "
        "t.product_description, t.transport_placard, t.density, t.bsw_cut, "
        "t.estimated_volume, t.actual_volume, t.hours_charged, "
        "t.hazards, t.hazard_notes, t.load_photo, "
        "t.driver_signature, t.signature_datetime, t.status "
        "FROM tickets t WHERE t.id=:tid AND t.company_id=:cid",
        {"tid": ticket_id, "cid": company_id},
    )
    if not t:
        raise ValueError(f"Ticket {ticket_id} not found for this company")
    c = fetch_one(
        "SELECT name, address, phone, primary_color FROM companies WHERE id=:id",
        {"id": company_id},
    )
    company = {"name": c[0], "address": c[1] or "", "phone": c[2] or "",
               "primary_color": c[3] or "#8B5CF6"} if c else {"name": "Company"}

    data = {
        "company": company,
        "ticket_number": t[0], "customer_ticket_number": t[1],
        "ticket_date": t[2], "load_id": t[3],
        "customer_name": t[4], "operator_name": t[5],
        "truck_number": t[6], "trailer_number": t[7],
        "pickup": t[8], "delivery": t[9],
        "arrive_load": _ts(t[10]), "depart_load": _ts(t[11]),
        "arrive_offload": _ts(t[12]), "depart_offload": _ts(t[13]),
        "product": t[14], "placard": t[15], "density": t[16], "bsw": t[17],
        "est_volume": t[18], "actual_volume": t[19], "hours": t[20],
        "hazards": list(t[21] or []), "hazard_notes": t[22],
        "photo_bytes": bytes(t[23]) if t[23] else None,
        "signature": t[24],
        "signature_datetime": t[25].strftime("%Y-%m-%d %H:%M") if t[25] else None,
    }
    pdf = render_field_ticket_pdf(data)
    filename = f"FieldTicket_{t[0] or ticket_id}.pdf".replace("/", "-").replace(" ", "_")
    log.info("Generated field ticket PDF for ticket %s (company %s)", ticket_id, company_id)
    return filename, pdf
