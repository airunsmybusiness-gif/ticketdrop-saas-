import streamlit as st
import sys
sys.path.insert(0, '/Users/lilibethsejera/Downloads/ticketdrop_saas')
from db import execute, fetch_all
st.set_page_config(page_title="Settings", page_icon="⚙️", layout="wide")
st.title("⚙️ Settings")
password = st.sidebar.text_input("Admin Password", type="password")
if password != st.secrets.get("ADMIN_PASSWORD", "admin123"):
    st.warning("Enter admin password")
    st.stop()
company_id = st.session_state.get('company_id', 1)
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
def manage_drivers():
    st.markdown("### 👷 Drivers")
    drivers = fetch_all("SELECT id, name, email, active FROM users WHERE company_id=:cid AND role='driver' ORDER BY name", {"cid": company_id})
    c1, c2, c3 = st.columns([2, 2, 1])
    new_name = c1.text_input("Driver Name")
    new_email = c2.text_input("Email (optional)")
    if c3.button("Add Driver"):
        if new_name:
            execute("INSERT INTO users (company_id, name, email, role, pin) VALUES (:cid, :name, :email, 'driver', '1234')", {"cid": company_id, "name": new_name, "email": new_email or None})
            st.rerun()
    for d in (drivers or []):
        c1, c2 = st.columns([4, 1])
        c1.write(f"{'✅' if d[3] else '❌'} {d[1]} ({d[2] or 'no email'})")
        if c2.button("🗑️", key=f"del_driver_{d[0]}"):
            execute("UPDATE users SET active=FALSE WHERE id=:id", {"id": d[0]})
            st.rerun()
tab1, tab2, tab3, tab4 = st.tabs(["👷 Drivers", "🚛 Trucks", "📦 Trailers", "🏢 Customers"])
with tab1:
    manage_drivers()
with tab2:
    manage_setting("trucks", "Trucks")
with tab3:
    manage_setting("trailers", "Trailers")
with tab4:
    manage_setting("customers", "Customers")
