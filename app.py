import logging
import streamlit as st

st.set_page_config(
    page_title="TicketDrop",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded",
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

import auth
import branding
from db import fetch_scalar

# Theme first (default colors until we know the company), then gate on login.
branding.apply_branding(auth.current_user()["company_id"] if auth.current_user() else None)
user = auth.require()

company_id = user["company_id"]
st.session_state.company_id = company_id  # keep existing pages working
branding.apply_branding(company_id)

branding.render_header(company_id)
auth.sidebar_account()
branding.render_sidebar_brand(company_id)

# ---------------------------------------------------------------- navigation
NAV = [
    ("📋", "DISPATCH", "Send load requests to drivers", "pages/1_📋_Dispatch.py", {"dispatch", "admin"}),
    ("🚚", "DRIVER", "Accept & complete tickets", "pages/2_🚚_Driver.py", {"driver", "admin"}),
    ("💰", "AR / BILLING", "Verify & export invoices", "pages/3_💰_AR.py", {"ar", "admin"}),
    ("⚙️", "SETTINGS", "Company, users & data", "pages/4_⚙️_Settings.py", {"admin"}),
]
visible = [n for n in NAV if user["role"] in n[4]]

st.markdown(
    "<p style=\"font-family:'Oswald',sans-serif;font-size:1rem;color:#9CA3AF;"
    "letter-spacing:3px;text-transform:uppercase;margin:10px 0 18px 0;\">Where do you want to go?</p>",
    unsafe_allow_html=True,
)

cols = st.columns(len(visible)) if visible else [st]
for col, (icon, title, desc, page, _roles) in zip(cols, visible):
    with col:
        st.markdown(f"""
        <div style="background:linear-gradient(145deg,#141414,#0F0F0F);border-radius:20px;
             padding:30px 22px;text-align:center;border:1px solid #2A2A2A;position:relative;overflow:hidden;">
            <div style="position:absolute;top:0;left:0;right:0;height:3px;
                 background:linear-gradient(90deg,transparent,var(--brand),transparent);"></div>
            <div style="font-size:3rem;margin-bottom:14px;
                 filter:drop-shadow(0 0 18px rgba(var(--brand-rgb),0.35));">{icon}</div>
            <h3 style="margin:0;font-family:'Oswald',sans-serif;color:#fff;font-size:1.25rem;
                 font-weight:600;letter-spacing:2px;">{title}</h3>
            <p style="font-family:'Inter',sans-serif;color:#6B7280;font-size:0.82rem;
                 margin-top:10px;line-height:1.5;">{desc}</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button(f"OPEN {title.split(' ')[0]}", key=f"nav_{page}", use_container_width=True):
            st.switch_page(page)

st.markdown("---")

# ---------------------------------------------------------------- live dashboard
st.markdown(
    "<p style=\"font-family:'Oswald',sans-serif;font-size:1rem;color:#9CA3AF;"
    "letter-spacing:3px;text-transform:uppercase;margin-bottom:18px;\">Live Dashboard</p>",
    unsafe_allow_html=True,
)

try:
    pending = fetch_scalar("SELECT COUNT(*) FROM loads WHERE status='ASSIGNED' AND company_id=:cid", {"cid": company_id}) or 0
    acknowledged = fetch_scalar("SELECT COUNT(*) FROM loads WHERE status='ACCEPTED' AND company_id=:cid", {"cid": company_id}) or 0
    in_progress = fetch_scalar("SELECT COUNT(*) FROM loads WHERE status='IN_PROGRESS' AND company_id=:cid", {"cid": company_id}) or 0
    completed_today = fetch_scalar("SELECT COUNT(*) FROM loads WHERE status='COMPLETED' AND DATE(status_changed_at)=CURRENT_DATE AND company_id=:cid", {"cid": company_id}) or 0
    ready_invoice = fetch_scalar("SELECT COUNT(*) FROM tickets WHERE status='READY_FOR_INVOICE' AND company_id=:cid", {"cid": company_id}) or 0

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("⏳ AWAITING", pending)
    m2.metric("✅ ACKNOWLEDGED", acknowledged)
    m3.metric("🚛 IN PROGRESS", in_progress)
    m4.metric("✔️ COMPLETED", completed_today)
    m5.metric("📤 READY TO BILL", ready_invoice)

    st.markdown("---")
    st.markdown("""
    <div style="display:flex;justify-content:center;align-items:center;padding:22px;
         background:linear-gradient(135deg,rgba(34,197,94,0.10),rgba(34,197,94,0.02));
         border-radius:16px;border:1px solid rgba(34,197,94,0.2);">
        <div style="width:11px;height:11px;background:#22C55E;border-radius:50%;margin-right:14px;
             box-shadow:0 0 18px #22C55E;animation:pulse 2s infinite;"></div>
        <span style="font-family:'Oswald',sans-serif;color:#22C55E;font-weight:600;
             letter-spacing:3px;text-transform:uppercase;">All Systems Operational</span>
    </div>
    <style>@keyframes pulse {0%,100%{opacity:1;}50%{opacity:0.5;}}</style>
    """, unsafe_allow_html=True)

except Exception as e:
    logging.getLogger("ticketdrop.app").exception("Dashboard query failed")
    st.error("Could not load the dashboard right now. Please refresh in a moment.")
    st.caption(f"Details: {e}")
