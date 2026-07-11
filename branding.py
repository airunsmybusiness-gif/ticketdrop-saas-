"""Per-company branding.

Each company row carries a name, tagline, and a primary color. This module
turns that into (1) a set of CSS variables so the whole theme follows the
company's color, and (2) a clean professional header wordmark that works for
any company name — no logo required.
"""
import streamlit as st
from db import fetch_one

DEFAULT_BRANDING = {
    "name": "TicketDrop",
    "tagline": "Dispatch & Field Ticketing",
    "primary_color": "#8B5CF6",
    "phone": "",
    "address": "",
    "logo_url": None,
}


# ---------------------------------------------------------------- color helpers
def _hex_to_rgb(h):
    h = (h or "#8B5CF6").lstrip("#")
    if len(h) != 6:
        h = "8B5CF6"
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _rgb_to_hex(r, g, b):
    return "#%02X%02X%02X" % (int(r), int(g), int(b))


def _clamp(x):
    return max(0, min(255, x))


def _mix(hexcolor, factor):
    """factor > 0 lightens toward white, < 0 darkens toward black."""
    r, g, b = _hex_to_rgb(hexcolor)
    if factor >= 0:
        r, g, b = r + (255 - r) * factor, g + (255 - g) * factor, b + (255 - b) * factor
    else:
        f = 1 + factor
        r, g, b = r * f, g * f, b * f
    return _rgb_to_hex(_clamp(r), _clamp(g), _clamp(b))


# ---------------------------------------------------------------- data
@st.cache_data(ttl=120)
def get_branding(company_id):
    if not company_id:
        return dict(DEFAULT_BRANDING)
    try:
        row = fetch_one(
            "SELECT name, tagline, primary_color, phone, address, logo_url "
            "FROM companies WHERE id=:id",
            {"id": company_id},
        )
    except Exception:
        row = None
    if not row:
        return dict(DEFAULT_BRANDING)
    b = dict(DEFAULT_BRANDING)
    b.update({
        "name": row[0] or DEFAULT_BRANDING["name"],
        "tagline": row[1] or DEFAULT_BRANDING["tagline"],
        "primary_color": row[2] or DEFAULT_BRANDING["primary_color"],
        "phone": row[3] or "",
        "address": row[4] or "",
        "logo_url": row[5],
    })
    return b


# ---------------------------------------------------------------- rendering
def _load_css():
    try:
        with open("style.css") as f:
            return f.read()
    except OSError:
        return ""


def apply_branding(company_id=None):
    """Inject brand color variables + the stylesheet. Call at the top of every page."""
    b = get_branding(company_id)
    primary = b["primary_color"]
    r, g, b_ = _hex_to_rgb(primary)
    css_vars = f"""
    <style>
    :root {{
        --brand: {primary};
        --brand-light: {_mix(primary, 0.30)};
        --brand-lighter: {_mix(primary, 0.55)};
        --brand-dark: {_mix(primary, -0.25)};
        --brand-rgb: {r}, {g}, {b_};
    }}
    </style>
    """
    st.markdown(css_vars, unsafe_allow_html=True)
    css = _load_css()
    if css:
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    return b


def render_header(company_id=None, right_label="24HR Dispatch"):
    """A clean, professional wordmark header that works for any company name."""
    b = get_branding(company_id)
    contact = ""
    if b["phone"]:
        contact = f"""
        <div style="text-align:right;padding:14px 22px;
             background:linear-gradient(135deg, rgba(var(--brand-rgb),0.12), rgba(20,20,20,0.8));
             border-radius:16px;border:1px solid rgba(var(--brand-rgb),0.25);">
            <p style="margin:0;font-family:'Oswald',sans-serif;color:#9CA3AF;font-size:0.65rem;
               letter-spacing:2px;text-transform:uppercase;">{right_label}</p>
            <p style="margin:4px 0 0 0;font-family:'Russo One',sans-serif;color:var(--brand-light);
               font-size:1.3rem;letter-spacing:1px;">{b['phone']}</p>
        </div>"""

    st.markdown(f"""
    <div style="display:flex;align-items:center;justify-content:space-between;
         padding:26px 0 16px 0;">
        <div>
            <h1 style="margin:0;font-family:'Russo One',sans-serif;font-size:3.4rem;
                font-weight:400;letter-spacing:-1px;line-height:1;
                background:linear-gradient(135deg, var(--brand-lighter), var(--brand-light), var(--brand), var(--brand-dark));
                -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                text-shadow:0 0 50px rgba(var(--brand-rgb),0.4);">{b['name']}</h1>
            <p style="margin:8px 0 0 2px;font-family:'Oswald',sans-serif;color:#E5E7EB;
               font-size:0.95rem;font-weight:600;letter-spacing:4px;text-transform:uppercase;">
               {b['tagline']}</p>
        </div>
        {contact}
    </div>
    <div style="height:3px;border-radius:2px;margin-bottom:8px;
         background:linear-gradient(90deg, var(--brand-dark), var(--brand), var(--brand-light), transparent);
         box-shadow:0 0 20px rgba(var(--brand-rgb),0.5);"></div>
    """, unsafe_allow_html=True)


def render_sidebar_brand(company_id=None):
    b = get_branding(company_id)
    addr = f"<p style='font-family:Inter,sans-serif;color:#4B5563;font-size:0.72rem;margin:8px 0 0 0;'>{b['address']}</p>" if b["address"] else ""
    phone = f"<p style='font-family:\"Russo One\",sans-serif;color:var(--brand-light);font-size:1rem;margin:0;'>{b['phone']}</p>" if b["phone"] else ""
    st.sidebar.markdown(f"""
    <div style="text-align:center;padding:22px 0;border-bottom:1px solid #2A2A2A;margin-bottom:18px;">
        <h2 style="margin:0;font-family:'Russo One',sans-serif;font-size:1.9rem;
            background:linear-gradient(135deg, var(--brand-lighter), var(--brand));
            -webkit-background-clip:text;-webkit-text-fill-color:transparent;">{b['name']}</h2>
        <p style="margin:6px 0 0 0;font-family:'Oswald',sans-serif;color:#6B7280;
           font-size:0.6rem;letter-spacing:3px;text-transform:uppercase;">TicketDrop</p>
        {phone}{addr}
    </div>
    """, unsafe_allow_html=True)
