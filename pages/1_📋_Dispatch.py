import streamlit as st
from db import execute, fetch_all, fetch_scalar
from services.status import update_load_status, StatusError
from datetime import datetime

st.set_page_config(page_title="Dispatch - Rick's TicketDrop", page_icon="📋", layout="wide")

# Load CSS
try:
    with open("style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except:
    pass

st.markdown("""
<h1 style="font-size: 2rem; margin-bottom: 0;">📋 Dispatch Board</h1>
<p style="color: #9CA3AF; margin-top: 5px;">Send load requests to drivers</p>
""", unsafe_allow_html=True)

password = st.sidebar.text_input("Password", type="password")
if password != st.secrets.get("DISPATCH_PASSWORD", "dispatch123"):
    st.warning("🔒 Enter dispatch password in sidebar")
    st.stop()

company_id = st.session_state.get('company_id', 1)
user_id, user_name, role = 2, "Dispatch", "dispatch"
st.sidebar.success("✓ Authenticated")

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

st.markdown("---")

# New Load Form
st.markdown("### 📤 New Load Request")
st.caption("Driver will complete all ticket details")

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
    
    notes = st.text_area("Notes for Driver (optional)", placeholder="Special instructions...", height=80)
    
    if st.form_submit_button("📤 SEND TO DRIVER", type="primary", use_container_width=True):
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
            execute("INSERT INTO load_status_history (load_id, new_status, changed_by, changed_by_name, reason) VALUES (:lid, 'ASSIGNED', :uid, :name, 'Load request sent')", {"lid": load_id, "uid": user_id, "name": user_name})
            
            st.success(f"✅ Load #{load_id} sent to {driver_name_sel}")
            
            sms = f"""🚛 LOAD REQUEST #{load_id}

Customer: {customer}
Pickup: {pickup}
Deliver: {delivery}
Truck: {truck}/{trailer}
{f"Notes: {notes}" if notes else ""}

Open TicketDrop to acknowledge."""
            
            st.code(sms)
            st.info("📱 Copy and text to driver")

st.markdown("---")

# Status Board
st.markdown("### 📊 Load Status Board")

tab1, tab2, tab3, tab4 = st.tabs(["⏳ Awaiting", "✅ Acknowledged", "🚛 In Progress", "✔️ Completed"])

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
            st.markdown(f"""
            <div style="background: #1A1A1A; border: 1px solid #333; border-left: 4px solid #8B5CF6; border-radius: 8px; padding: 16px; margin-bottom: 12px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="color: #8B5CF6; font-weight: 700;">#{lid}</span>
                        <span style="color: #FFF; font-weight: 600; margin-left: 10px;">{cust}</span>
                    </div>
                    <span style="color: #9CA3AF; font-size: 0.85rem;">⏳ Awaiting acknowledgment</span>
                </div>
                <p style="color: #9CA3AF; margin: 8px 0 0 0; font-size: 0.9rem;">📍 {pickup} → {driver}</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("❌ Cancel", key=f"cancel_{lid}"):
                try:
                    update_load_status(lid, 'CANCELLED', user_id, user_name, role, "Cancelled by dispatch")
                    st.rerun()
                except StatusError as e:
                    st.error(str(e))
    else:
        st.info("No loads awaiting acknowledgment")

with tab2:
    loads = fetch_all("""
        SELECT l.id, l.customer, l.pickup_location, u.name, l.status_changed_at
        FROM loads l LEFT JOIN users u ON l.driver_id = u.id
        WHERE l.company_id = :cid AND l.status = 'ACCEPTED'
        ORDER BY l.status_changed_at DESC
    """, {"cid": company_id})
    if loads:
        for l in loads:
            lid, cust, pickup, driver, ack_time = l
            st.markdown(f"""
            <div style="background: #1A1A1A; border: 1px solid #333; border-left: 4px solid #22C55E; border-radius: 8px; padding: 16px; margin-bottom: 12px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="color: #22C55E; font-weight: 700;">#{lid}</span>
                        <span style="color: #FFF; font-weight: 600; margin-left: 10px;">{cust}</span>
                    </div>
                    <span style="color: #22C55E; font-size: 0.85rem;">✅ Acknowledged</span>
                </div>
                <p style="color: #9CA3AF; margin: 8px 0 0 0; font-size: 0.9rem;">📍 {pickup} → {driver} | {ack_time}</p>
            </div>
            """, unsafe_allow_html=True)
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
            st.markdown(f"""
            <div style="background: #1A1A1A; border: 1px solid #333; border-left: 4px solid #F59E0B; border-radius: 8px; padding: 16px; margin-bottom: 12px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="color: #F59E0B; font-weight: 700;">#{lid}</span>
                        <span style="color: #FFF; font-weight: 600; margin-left: 10px;">{cust}</span>
                    </div>
                    <span style="color: #F59E0B; font-size: 0.85rem;">🚛 In Progress</span>
                </div>
                <p style="color: #9CA3AF; margin: 8px 0 0 0; font-size: 0.9rem;">📍 {pickup} → {driver} | Started: {started}</p>
            </div>
            """, unsafe_allow_html=True)
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
            st.markdown(f"""
            <div style="background: #1A1A1A; border: 1px solid #333; border-left: 4px solid #10B981; border-radius: 8px; padding: 16px; margin-bottom: 12px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="color: #10B981; font-weight: 700;">#{lid}</span>
                        <span style="color: #FFF; font-weight: 600; margin-left: 10px;">{cust}</span>
                    </div>
                    <span style="color: #10B981; font-size: 0.85rem;">✔️ Completed</span>
                </div>
                <p style="color: #9CA3AF; margin: 8px 0 0 0; font-size: 0.9rem;">📍 {pickup} → {driver} | {completed}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No loads completed today")
