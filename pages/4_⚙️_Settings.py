import logging
import streamlit as st
from db import execute, fetch_all, fetch_one
import auth
import branding

st.set_page_config(page_title="Settings · TicketDrop", page_icon="⚙️", layout="wide")
log = logging.getLogger("ticketdrop.settings")

branding.apply_branding(auth.current_user()["company_id"] if auth.current_user() else None)
user = auth.require("admin")
company_id = user["company_id"]
branding.apply_branding(company_id)
auth.sidebar_account()

st.title("⚙️ Settings")


# ---------------------------------------------------------------- company branding
def manage_company():
    st.markdown("### 🏢 Company & Branding")
    st.caption("These control the name, tagline, and color shown across the whole app.")
    row = fetch_one(
        "SELECT name, tagline, primary_color, phone, address FROM companies WHERE id=:id",
        {"id": company_id},
    )
    name, tagline, color, phone, address = (row or ("TicketDrop", "Dispatch & Field Ticketing", "#8B5CF6", "", ""))

    with st.form("company_form"):
        c1, c2 = st.columns(2)
        name = c1.text_input("Company Name", value=name or "")
        tagline = c2.text_input("Tagline", value=tagline or "")
        color = c1.color_picker("Brand Color", value=color or "#8B5CF6")
        phone = c2.text_input("Phone", value=phone or "")
        address = st.text_input("Address", value=address or "")
        if st.form_submit_button("💾 Save Branding", type="primary"):
            try:
                execute(
                    "UPDATE companies SET name=:n, tagline=:t, primary_color=:c, phone=:p, address=:a WHERE id=:id",
                    {"n": name, "t": tagline, "c": color, "p": phone or None, "a": address or None, "id": company_id},
                )
                branding.get_branding.clear()  # drop cached branding so changes show now
                st.success("✅ Branding saved. Refresh to see it everywhere.")
                st.rerun()
            except Exception as e:
                log.exception("Failed to save branding")
                st.error("Could not save branding. Please try again.")
                st.caption(f"Details: {e}")

    st.info("Preview:")
    branding.get_branding.clear()
    branding.render_header(company_id)


# ---------------------------------------------------------------- users + PINs
def manage_users():
    st.markdown("### 👥 Users & Logins")
    st.caption("Each person signs in with their Name + PIN. PINs are stored securely (hashed).")

    with st.form("add_user", clear_on_submit=True):
        st.markdown("**Add a person**")
        c1, c2, c3, c4 = st.columns([2, 2, 1.3, 1.2])
        new_name = c1.text_input("Name")
        new_email = c2.text_input("Email (optional)")
        new_role = c3.selectbox("Role", auth.ROLES, format_func=lambda r: auth.ROLE_LABELS[r])
        new_pin = c4.text_input("PIN", type="password", max_chars=8)
        if st.form_submit_button("➕ Add User", type="primary"):
            if not new_name or not new_pin:
                st.error("Name and PIN are required.")
            elif len(new_pin) < 4:
                st.error("Use a PIN of at least 4 digits.")
            else:
                try:
                    auth.create_user(company_id, new_name, new_role, new_pin, new_email)
                    st.success(f"✅ Added {new_name} ({auth.ROLE_LABELS[new_role]})")
                    st.rerun()
                except Exception as e:
                    log.exception("Failed to add user")
                    st.error("Could not add user. Please try again.")
                    st.caption(f"Details: {e}")

    st.markdown("---")
    users = auth.list_all_users(company_id)
    for uid, uname, uemail, urole, active, has_pin in users:
        c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
        status_icon = "✅" if active else "❌"
        pin_icon = "🔑" if has_pin else "⚠️ no PIN"
        c1.write(f"{status_icon} **{uname}** · {auth.ROLE_LABELS.get(urole, urole)}")
        c1.caption(f"{uemail or 'no email'} · {pin_icon}")
        reset_pin = c2.text_input("New PIN", key=f"pin_{uid}", type="password", max_chars=8, label_visibility="collapsed", placeholder="New PIN")
        if c3.button("Reset PIN", key=f"reset_{uid}"):
            if reset_pin and len(reset_pin) >= 4:
                auth.set_user_pin(uid, reset_pin)
                st.success(f"PIN updated for {uname}")
                st.rerun()
            else:
                st.error("PIN must be at least 4 digits.")
        if active and c4.button("🗑️", key=f"deact_{uid}"):
            auth.deactivate_user(uid)
            st.rerun()


# ---------------------------------------------------------------- trucks/trailers/customers
def manage_setting(category, label):
    st.markdown(f"### {label}")
    items = fetch_all("SELECT id, value, active FROM settings WHERE company_id=:cid AND category=:cat ORDER BY value", {"cid": company_id, "cat": category})
    c1, c2 = st.columns([3, 1])
    new_val = c1.text_input(f"Add {label}", key=f"new_{category}")
    if c2.button("Add", key=f"add_{category}"):
        if new_val:
            execute("INSERT INTO settings (company_id, category, value) VALUES (:cid, :cat, :val)", {"cid": company_id, "cat": category, "val": new_val})
            st.rerun()
    for item in (items or []):
        c1, c2 = st.columns([4, 1])
        c1.write(f"{'✅' if item[2] else '❌'} {item[1]}")
        if c2.button("🗑️", key=f"del_{item[0]}"):
            execute("DELETE FROM settings WHERE id=:id", {"id": item[0]})
            st.rerun()


tab0, tab1, tab2, tab3, tab4 = st.tabs(
    ["🏢 Company", "👥 Users", "🚛 Trucks", "📦 Trailers", "🏢 Customers"]
)
with tab0:
    manage_company()
with tab1:
    manage_users()
with tab2:
    manage_setting("trucks", "Trucks")
with tab3:
    manage_setting("trailers", "Trailers")
with tab4:
    manage_setting("customers", "Customers")
