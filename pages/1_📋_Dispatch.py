import streamlit as st
import sys
sys.path.insert(0, '/Users/lilibethsejera/Downloads/ticketdrop_saas')
from db import execute, fetch_all, fetch_scalar
from services.status import update_load_status, StatusError
from datetime import datetime

st.set_page_config(page_title="Dispatch", page_icon="📋", layout="wide")
st.title("📋 Dispatch Board")

password = st.sidebar.text_input("Password", type="password")
if password != st.secrets.get("DISPATCH_PASSWORD", "dispatch123"):
    st.warning("Enter dispatch password")
    st.stop()

company_id = st.session_state.get('company_id', 1)
user_id, user_name, role = 2, "Dispatch", "dispatch"
st.sidebar.success("✓ Logged in as Dispatch")

def get_options(category):
    items = fetch_all("SELECT value FROM settings WHERE company_id=:cid AND category=:cat AND active=TRUE ORDER BY value", {"cid": company_id, "cat": category})
    return [i[0] for i in items] if items else ["Add in Settings"]

def get_drivers():
    drivers = fetch_all("SELECT id, name FROM users WHERE company_id=:cid AND role='driver' AND active=TRUE ORDER BY name", {"cid": company_id})
    return {d[1]: d[0] for d in drivers} if drivers else {}

drivers = get_drivers()
customers = get_options("customers")
trucks = get_options("trucks") if get_options("trucks")[0] != "Add in Settings" else ["Truck 1", "Truck 2"]
trailers = get_options("trailers") if get_options("trailers")[0] != "Add in Settings" else ["T196", "T197"]

st.markdown("### 📤 Send Load Request")
st.caption("Minimal info only - driver completes all details")

with st.form("new_load"):
    c1, c2 = st.columns(2)
    with c1:
        customer = st.selectbox("Customer", customers)
        pickup = st.text_input("Pickup Location", placeholder="Well site or facility")
        delivery = st.text_input("Delivery Location", placeholder="Destination")
    with c2:
        driver_name_sel = st.selectbox("Assign Driver", list(drivers.keys()) if drivers else ["Add drivers first"])
        truck = st.selectbox("Truck", trucks)
        trailer = st.selectbox("Trailer", trailers)
    
    notes = st.text_input("Notes (optional)")
    
    if st.form_submit_button("📤 Send to Driver", type="primary", use_container_width=True):
        if not drivers or driver_name_sel == "Add drivers first":
            st.error("Add drivers in Settings first")
        elif "Add in Settings" in customer:
            st.error("Add customers in Settings first")
        else:
            driver_id = drivers.get(driver_name_sel)
            execute("""
                INSERT INTO loads (company_id, customer, pickup_location, delivery_location, driver_id, truck, trailer, notes, status, created_by)
                VALUES (:cid, :cust, :pickup, :delivery, :driver, :truck, :trailer, :notes, 'ASSIGNED', :user)
            """, {"cid": company_id, "cust": customer, "pickup": pickup, "delivery": delivery, "driver": driver_id, "truck": truck, "trailer": trailer, "notes": notes, "user": user_id})
            load_id = fetch_scalar("SELECT MAX(id) FROM loads WHERE company_id = :cid", {"cid": company_id})
            execute("INSERT INTO load_status_history (load_id, new_status, changed_by, changed_by_name, reason) VALUES (:lid, 'ASSIGNED', :uid, :name, 'Load request sent to driver')", {"lid": load_id, "uid": user_id, "name": user_name})
            
            st.success(f"✅ Load #{load_id} sent to {driver_name_sel}")
            
            sms = f"""🚛 LOAD REQUEST #{load_id}

Customer: {customer}
Pickup: {pickup}
Deliver: {delivery}
Truck: {truck}/{trailer}
{f"Notes: {notes}" if notes else ""}

Open TicketDrop to acknowledge & complete."""
            
            st.code(sms)
            st.info("👆 Copy and text to driver")

st.markdown("---")

# Load Status Board
st.markdown("### 📊 Load Status Board")

tab1, tab2, tab3, tab4 = st.tabs(["⏳ Awaiting Acknowledgment", "✅ Acknowledged", "🚛 In Progress", "✔️ Completed Today"])

with tab1:
    loads = fetch_all("""
        SELECT l.id, l.customer, l.pickup_location, u.name, l.created_at
        FROM loads l LEFT JOIN users u ON l.driver_id = u.id
        WHERE l.company_id = :cid AND l.status = 'ASSIGNED'
        ORDER BY l.created_at DESC
    """, {"cid": company_id})
    if loads:
        for l in loads:
            lid, cust, pickup, driver, created = l
            c1, c2 = st.columns([4, 1])
            c1.markdown(f"**#{lid}** {cust}")
            c1.caption(f"📍 {pickup} | Driver: {driver} | Sent: {created}")
            if c2.button("❌", key=f"cancel_{lid}"):
                try:
                    update_load_status(lid, 'CANCELLED', user_id, user_name, role, "Cancelled by dispatch")
                    st.rerun()
                except StatusError as e:
                    st.error(str(e))
    else:
        st.info("No loads awaiting acknowledgment")

with tab2:
    loads = fetch_all("""
        SELECT l.id, l.customer, l.pickup_location, u.name, l.status_changed_at,
               (SELECT reason FROM load_status_history WHERE load_id = l.id AND new_status = 'ACCEPTED' ORDER BY changed_at DESC LIMIT 1) as ack_note
        FROM loads l LEFT JOIN users u ON l.driver_id = u.id
        WHERE l.company_id = :cid AND l.status = 'ACCEPTED'
        ORDER BY l.status_changed_at DESC
    """, {"cid": company_id})
    if loads:
        for l in loads:
            lid, cust, pickup, driver, ack_time, ack_note = l
            st.markdown(f"**#{lid}** {cust} | {driver}")
            st.caption(f"📍 {pickup} | ✅ Acknowledged: {ack_time}")
            if ack_note:
                st.caption(f"📝 Driver note: {ack_note}")
            st.markdown("---")
    else:
        st.info("No acknowledged loads")

with tab3:
    loads = fetch_all("""
        SELECT l.id, l.customer, l.pickup_location, u.name, l.status_changed_at
        FROM loads l LEFT JOIN users u ON l.driver_id = u.id
        WHERE l.company_id = :cid AND l.status = 'IN_PROGRESS'
        ORDER BY l.status_changed_at DESC
    """, {"cid": company_id})
    if loads:
        for l in loads:
            lid, cust, pickup, driver, started = l
            st.markdown(f"**#{lid}** {cust} | {driver}")
            st.caption(f"📍 {pickup} | 🚛 Started: {started}")
    else:
        st.info("No loads in progress")

with tab4:
    loads = fetch_all("""
        SELECT l.id, l.customer, l.pickup_location, u.name, l.status_changed_at
        FROM loads l LEFT JOIN users u ON l.driver_id = u.id
        WHERE l.company_id = :cid AND l.status = 'COMPLETED' AND DATE(l.status_changed_at) = CURRENT_DATE
        ORDER BY l.status_changed_at DESC
    """, {"cid": company_id})
    if loads:
        for l in loads:
            lid, cust, pickup, driver, completed = l
            st.markdown(f"**#{lid}** {cust} | {driver}")
            st.caption(f"📍 {pickup} | ✔️ Completed: {completed}")
    else:
        st.info("No loads completed today")
