import streamlit as st
import sys
sys.path.insert(0, '/Users/lilibethsejera/Downloads/ticketdrop_saas')
from datetime import date
from db import execute, fetch_all, fetch_one, fetch_scalar
from services.status import update_load_status, StatusError
st.set_page_config(page_title="Driver", page_icon="🚚", layout="wide")
st.title("🚚 Driver Portal")
company_id = st.session_state.get('company_id', 1)
drivers = fetch_all("SELECT id, name FROM users WHERE company_id=:cid AND role='driver' AND active=TRUE", {"cid": company_id})
driver_options = {d[1]: d[0] for d in drivers} if drivers else {}
if not driver_options:
    st.warning("No drivers configured. Add drivers in Settings.")
    st.stop()
driver_name = st.sidebar.selectbox("Your Name", list(driver_options.keys()))
pin = st.sidebar.text_input("PIN", type="password", max_chars=4)
if pin != st.secrets.get("DRIVER_PIN", "1234"):
    st.warning("Enter your 4-digit PIN")
    st.stop()
driver_id = driver_options[driver_name]
role = "driver"
st.sidebar.success(f"✓ {driver_name}")
tab1, tab2, tab3 = st.tabs(["📋 My Loads", "✍️ Complete Ticket", "📄 History"])
with tab1:
    loads = fetch_all("SELECT id, customer, pickup_location, delivery_location, truck, trailer, notes, status FROM loads WHERE company_id = :cid AND driver_id = :did AND status IN ('ASSIGNED', 'ACCEPTED', 'IN_PROGRESS') ORDER BY created_at DESC", {"cid": company_id, "did": driver_id})
    if loads:
        for l in loads:
            lid, cust, pickup, delivery, truck, trailer, notes, status = l
            st.markdown(f"### Load #{lid}: {cust}")
            st.markdown(f"**Pickup:** {pickup}")
            st.markdown(f"**Deliver:** {delivery}")
            st.markdown(f"**Truck:** {truck} / {trailer}")
            if notes:
                st.caption(f"Notes: {notes}")
            st.markdown(f"Status: `{status}`")
            c1, c2, c3 = st.columns(3)
            if status == 'ASSIGNED':
                if c1.button("✅ Accept", key=f"acc_{lid}", type="primary"):
                    try:
                        update_load_status(lid, 'ACCEPTED', driver_id, driver_name, role)
                        st.rerun()
                    except StatusError as e:
                        st.error(str(e))
                if c2.button("❌ Decline", key=f"dec_{lid}"):
                    try:
                        update_load_status(lid, 'DECLINED', driver_id, driver_name, role)
                        st.rerun()
                    except StatusError as e:
                        st.error(str(e))
            elif status == 'ACCEPTED':
                if c1.button("🚛 Start Load", key=f"start_{lid}", type="primary"):
                    try:
                        update_load_status(lid, 'IN_PROGRESS', driver_id, driver_name, role)
                        st.rerun()
                    except StatusError as e:
                        st.error(str(e))
            elif status == 'IN_PROGRESS':
                if c1.button("📝 Complete Ticket", key=f"ticket_{lid}", type="primary"):
                    st.session_state['active_load'] = lid
                    st.info("Go to 'Complete Ticket' tab")
            st.markdown("---")
    else:
        st.info("No loads assigned to you")
with tab2:
    load_id = st.session_state.get('active_load')
    if not load_id:
        in_progress = fetch_all("SELECT id, customer, pickup_location FROM loads WHERE company_id=:cid AND driver_id=:did AND status='IN_PROGRESS'", {"cid": company_id, "did": driver_id})
        if in_progress:
            options = {f"#{l[0]}: {l[1]} - {l[2]}": l[0] for l in in_progress}
            selected = st.selectbox("Select Load to Complete", list(options.keys()))
            load_id = options[selected]
        else:
            st.warning("No loads in progress. Accept and start a load first.")
            st.stop()
    load = fetch_one("SELECT customer, pickup_location, delivery_location, truck, trailer FROM loads WHERE id = :id", {"id": load_id})
    if not load:
        st.error("Load not found")
        st.stop()
    cust, pickup, delivery, truck, trailer = load
    st.markdown(f"### Completing Ticket for Load #{load_id}")
    st.markdown(f"**{cust}** | {pickup} → {delivery}")
    with st.form("ticket_form"):
        st.markdown("#### Header")
        h1, h2, h3 = st.columns(3)
        ticket_num = h1.text_input("Rick's Ticket #")
        cust_ticket = h2.text_input("Customer Ticket #")
        ticket_date = h3.date_input("Date", value=date.today())
        st.markdown("#### Loading")
        l1, l2 = st.columns(2)
        loaded_at = l1.text_input("Loaded At", value=pickup)
        load_tank = l1.text_input("Tank #")
        arrive_load = l1.text_input("Arrive Load (datetime)", placeholder="2025-01-10 08:30")
        depart_load = l1.text_input("Depart Load (datetime)", placeholder="2025-01-10 09:15")
        load_start = l2.number_input("Load Start Vol (m³)", value=0.0)
        load_end = l2.number_input("Load End Vol (m³)", value=0.0)
        st.markdown("#### Offloading")
        o1, o2 = st.columns(2)
        offload_at = o1.text_input("Offloaded At", value=delivery or "")
        offload_tank = o1.text_input("Offload Tank #")
        arrive_offload = o1.text_input("Arrive Offload (datetime)")
        depart_offload = o1.text_input("Depart Offload (datetime)")
        st.markdown("#### Product & Billing")
        p1, p2, p3 = st.columns(3)
        product = p1.text_input("Product", placeholder="Crude Oil")
        density = p1.number_input("Density", value=948.0)
        bsw = p2.number_input("BS+W", value=0.20, step=0.01)
        est_vol = p2.number_input("Est Volume (m³)", value=40.0)
        actual_vol = p3.number_input("Actual Volume (m³)", value=0.0)
        hours = p3.number_input("Hours Charged", value=1.0, step=0.25)
        road_ban = st.checkbox("Road Ban")
        st.markdown("#### Signature")
        signature = st.text_input("Driver Signature (type full name)")
        if st.form_submit_button("✅ SUBMIT TICKET", type="primary", use_container_width=True):
            if not signature:
                st.error("Signature required")
            elif actual_vol <= 0:
                st.error("Enter actual volume")
            else:
                execute("""INSERT INTO tickets (company_id, load_id, ticket_number, customer_ticket_number, ticket_date, operator_name, truck_number, trailer_number, customer_name, loaded_at, offloaded_at, load_tank, arrive_load_datetime, depart_load_datetime, load_start_volume, load_end_volume, offload_tank, arrive_offload_datetime, depart_offload_datetime, product_description, density, bsw_cut, estimated_volume, actual_volume, hours_charged, road_ban, driver_signature, signature_datetime, status) VALUES (:cid, :lid, :tnum, :ctnum, :tdate, :op, :truck, :trailer, :cust, :loaded, :offloaded, :ltank, :arr_l, :dep_l, :start_vol, :end_vol, :otank, :arr_o, :dep_o, :product, :density, :bsw, :est, :actual, :hours, :road, :sig, NOW(), 'SUBMITTED')""",
                        {"cid": company_id, "lid": load_id, "tnum": ticket_num, "ctnum": cust_ticket, "tdate": ticket_date, "op": driver_name, "truck": truck, "trailer": trailer, "cust": cust, "loaded": loaded_at, "offloaded": offload_at, "ltank": load_tank, "arr_l": arrive_load or None, "dep_l": depart_load or None, "start_vol": load_start, "end_vol": load_end, "otank": offload_tank, "arr_o": arrive_offload or None, "dep_o": depart_offload or None, "product": product, "density": density, "bsw": bsw, "est": est_vol, "actual": actual_vol, "hours": hours, "road": road_ban, "sig": signature})
                try:
                    update_load_status(load_id, 'COMPLETED', driver_id, driver_name, role)
                except:
                    pass
                if 'active_load' in st.session_state:
                    del st.session_state['active_load']
                st.success("✅ Ticket submitted!")
                st.balloons()
with tab3:
    tickets = fetch_all("SELECT t.id, t.ticket_number, t.customer_name, t.actual_volume, t.status, t.created_at FROM tickets t WHERE t.company_id = :cid AND t.operator_name = :name ORDER BY t.created_at DESC LIMIT 20", {"cid": company_id, "name": driver_name})
    if tickets:
        for t in tickets:
            st.markdown(f"**#{t[0]}** {t[1] or 'No ticket#'} | {t[2]} | {t[3]}m³ | `{t[4]}`")
    else:
        st.info("No completed tickets")
