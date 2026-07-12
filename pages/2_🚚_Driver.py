import logging
import streamlit as st
from datetime import date, datetime
from db import execute, fetch_all, fetch_one
from services.status import update_load_status, StatusError
from services.field_ticket import HAZARD_ITEMS, generate_field_ticket_pdf
import auth
import branding

st.set_page_config(page_title="Driver · TicketDrop", page_icon="🚚", layout="wide")
log = logging.getLogger("ticketdrop.driver")

branding.apply_branding(auth.current_user()["company_id"] if auth.current_user() else None)
# Drivers sign in with their Name + PIN on the shared login screen.
user = auth.require("driver")
company_id = user["company_id"]
driver_id, driver_name, role = user["user_id"], user["user_name"], "driver"
branding.apply_branding(company_id)
auth.sidebar_account()

st.title("🚚 Driver Portal")

tab1, tab2, tab3 = st.tabs(["📬 New Requests", "🚛 My Active Load", "📄 History"])

with tab1:
    st.markdown("### 📬 New Load Requests")
    st.caption("Acknowledge to confirm you received the request")
    
    new_loads = fetch_all("""
        SELECT id, customer, pickup_location, delivery_location, truck, trailer, notes, created_at
        FROM loads 
        WHERE company_id = :cid AND driver_id = :did AND status = 'ASSIGNED'
        ORDER BY created_at DESC
    """, {"cid": company_id, "did": driver_id})
    
    if new_loads:
        for l in new_loads:
            lid, cust, pickup, delivery, truck, trailer, notes, created = l
            
            st.markdown(f"### 🚛 Load #{lid}")
            st.markdown(f"**Customer:** {cust}")
            st.markdown(f"**Pickup:** {pickup}")
            st.markdown(f"**Deliver:** {delivery}")
            st.markdown(f"**Truck:** {truck} / {trailer}")
            st.caption(f"Received: {created}")
            if notes:
                st.info(f"📝 Notes: {notes}")
            
            c1, c2 = st.columns(2)
            
            # Acknowledgment with optional note
            ack_note = st.text_input("Add note (optional)", key=f"note_{lid}", placeholder="e.g., ETA 2 hours")
            
            if c1.button("✅ ACKNOWLEDGE & ACCEPT", key=f"ack_{lid}", type="primary", use_container_width=True):
                try:
                    reason = f"Driver acknowledged at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    if ack_note:
                        reason += f" | Note: {ack_note}"
                    update_load_status(lid, 'ACCEPTED', driver_id, driver_name, role, reason)
                    st.success("✅ Acknowledged! Load moved to 'My Active Load'")
                    st.rerun()
                except StatusError as e:
                    st.error(str(e))
            
            if c2.button("❌ Decline", key=f"dec_{lid}"):
                decline_reason = st.text_input("Reason for declining", key=f"decline_reason_{lid}")
                try:
                    update_load_status(lid, 'DECLINED', driver_id, driver_name, role, decline_reason or "Declined by driver")
                    st.rerun()
                except StatusError as e:
                    st.error(str(e))
            
            st.markdown("---")
    else:
        st.info("✅ No new load requests")

with tab2:
    st.markdown("### 🚛 My Active Load")
    
    # Get accepted or in-progress load
    active_load = fetch_one("""
        SELECT id, customer, pickup_location, delivery_location, truck, trailer, notes, status
        FROM loads 
        WHERE company_id = :cid AND driver_id = :did AND status IN ('ACCEPTED', 'IN_PROGRESS')
        ORDER BY status_changed_at DESC LIMIT 1
    """, {"cid": company_id, "did": driver_id})
    
    if not active_load:
        st.info("No active load. Accept a load request first.")
        st.stop()
    
    lid, cust, pickup, delivery, truck, trailer, notes, status = active_load
    
    st.markdown(f"### Load #{lid}: {cust}")
    st.markdown(f"**Pickup:** {pickup}")
    st.markdown(f"**Deliver:** {delivery}")
    st.markdown(f"**Truck:** {truck} / {trailer}")
    st.markdown(f"**Status:** `{status}`")
    
    if status == 'ACCEPTED':
        if st.button("🚛 START LOAD - I'm on my way", type="primary", use_container_width=True):
            try:
                update_load_status(lid, 'IN_PROGRESS', driver_id, driver_name, role, f"Driver started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                st.rerun()
            except StatusError as e:
                st.error(str(e))
    
    elif status == 'IN_PROGRESS':
        st.markdown("---")
        st.markdown("### ✍️ Complete Field Ticket")
        st.caption("Fill in ALL details - this replaces the paper ticket")
        
        with st.form("ticket_form"):
            st.markdown("#### 📋 Ticket Info")
            h1, h2, h3 = st.columns(3)
            ticket_num = h1.text_input("Ticket #", placeholder="361334")
            cust_ticket = h2.text_input("Customer Ticket #", placeholder="268169")
            ticket_date = h3.date_input("Date", value=date.today())
            po_number = h1.text_input("PO # (if applicable)", placeholder="Optional")
            safety_number = h2.text_input("Safety #", placeholder="Optional")
            hours = h3.number_input("Hours Charged", value=1.0, step=0.25)
            
            st.markdown("---")
            st.markdown("#### ⬆️ Loading Details")
            l1, l2 = st.columns(2)
            loaded_at = l1.text_input("Loaded At", value=pickup)
            load_tank = l1.text_input("Loaded from Tank #")
            load_riser = l1.text_input("Load Riser")
            arrive_load = l2.text_input("Arrive Load", placeholder="2025-01-10 08:30")
            depart_load = l2.text_input("Depart Load", placeholder="2025-01-10 09:15")
            load_start = l2.number_input("Load Start Vol (m³)", value=0.0)
            load_end = l2.number_input("Load End Vol (m³)", value=0.0)
            
            st.markdown("---")
            st.markdown("#### ⬇️ Offloading Details")
            o1, o2 = st.columns(2)
            offload_at = o1.text_input("Offloaded At", value=delivery or "")
            offload_tank = o1.text_input("Offloaded into Tank #")
            offload_riser = o1.text_input("Offload Riser")
            arrive_offload = o2.text_input("Arrive Offload", placeholder="2025-01-10 14:30")
            depart_offload = o2.text_input("Depart Offload", placeholder="2025-01-10 15:45")
            
            st.markdown("---")
            st.markdown("#### 🛢️ Product Details")
            p1, p2, p3 = st.columns(3)
            product = p1.text_input("Product", placeholder="UN1267-Petroleum crude oil")
            commodity = p1.text_input("Commodity")
            placard = p2.text_input("Transport Placard", placeholder="8 X UN1267")
            last_contained = p2.text_input("Last Contained")
            density = p3.number_input("Density", value=948.0)
            bsw = p3.number_input("BS+W (Cut)", value=0.20, step=0.01)
            
            st.markdown("---")
            st.markdown("#### 📊 Volumes")
            v1, v2, v3 = st.columns(3)
            est_vol = v1.number_input("Estimated Volume (m³)", value=40.0)
            actual_vol = v2.number_input("Actual Volume (m³)", value=0.0)
            road_ban = v3.checkbox("Road Ban")

            st.markdown("---")
            st.markdown("#### ⚠️ Site & Load Hazards")
            st.caption("Tick every hazard present on this job — these print on the field ticket")
            hz1, hz2 = st.columns(2)
            hazard_checked = []
            half = (len(HAZARD_ITEMS) + 1) // 2
            for i, item in enumerate(HAZARD_ITEMS):
                col = hz1 if i < half else hz2
                if col.checkbox(item, key=f"hz_{lid}_{i}"):
                    hazard_checked.append(item)
            hazard_notes = st.text_input("Hazard notes (required if 'Other' is ticked)",
                                         placeholder="Describe any other hazard...")

            st.markdown("---")
            st.markdown("#### 📸 Backup Photo of the Load")
            st.caption("Take or upload one photo of the loaded product / paperwork (JPG or PNG)")
            load_photo = st.file_uploader("Load photo", type=["jpg", "jpeg", "png"],
                                          key=f"photo_{lid}", label_visibility="collapsed")

            st.markdown("---")
            st.markdown("#### ✍️ Signature")
            signature = st.text_input("Driver Signature (type full name)", placeholder=driver_name)
            
            if st.form_submit_button("✅ SUBMIT COMPLETED TICKET", type="primary", use_container_width=True):
                if not signature:
                    st.error("Signature required")
                elif actual_vol <= 0:
                    st.error("Enter actual volume")
                elif not ticket_num:
                    st.error("Enter your Ticket #")
                elif "Other (see notes)" in hazard_checked and not hazard_notes:
                    st.error("You ticked 'Other' — describe the hazard in the notes field")
                else:
                  try:
                    execute("""
                        INSERT INTO tickets (
                            company_id, load_id, ticket_number, customer_ticket_number, ticket_date,
                            operator_name, truck_number, trailer_number, customer_name,
                            loaded_at, load_tank, load_riser, arrive_load_datetime, depart_load_datetime,
                            load_start_volume, load_end_volume,
                            offloaded_at, offload_tank, offload_riser, arrive_offload_datetime, depart_offload_datetime,
                            product_description, commodity, transport_placard, last_contained, density, bsw_cut,
                            estimated_volume, actual_volume, hours_charged, road_ban,
                            hazards, hazard_notes, load_photo, load_photo_mime,
                            driver_signature, signature_datetime, status
                        ) VALUES (
                            :cid, :lid, :tnum, :ctnum, :tdate,
                            :op, :truck, :trailer, :cust,
                            :loaded, :ltank, :lriser, :arr_l, :dep_l,
                            :start_vol, :end_vol,
                            :offloaded, :otank, :oriser, :arr_o, :dep_o,
                            :product, :commodity, :placard, :last, :density, :bsw,
                            :est, :actual, :hours, :road,
                            :hazards, :haznotes, :photo, :photomime,
                            :sig, NOW(), 'SUBMITTED'
                        )
                    """, {
                        "cid": company_id, "lid": lid, "tnum": ticket_num, "ctnum": cust_ticket, "tdate": ticket_date,
                        "op": driver_name, "truck": truck, "trailer": trailer, "cust": cust,
                        "loaded": loaded_at, "ltank": load_tank, "lriser": load_riser, 
                        "arr_l": arrive_load or None, "dep_l": depart_load or None,
                        "start_vol": load_start, "end_vol": load_end,
                        "offloaded": offload_at, "otank": offload_tank, "oriser": offload_riser,
                        "arr_o": arrive_offload or None, "dep_o": depart_offload or None,
                        "product": product, "commodity": commodity, "placard": placard, "last": last_contained,
                        "density": density, "bsw": bsw,
                        "est": est_vol, "actual": actual_vol, "hours": hours, "road": road_ban,
                        "hazards": hazard_checked or None, "haznotes": hazard_notes or None,
                        "photo": load_photo.getvalue() if load_photo else None,
                        "photomime": load_photo.type if load_photo else None,
                        "sig": signature
                    })
                    
                    # Update load and PO if provided
                    if po_number:
                        execute("UPDATE loads SET po_number = :po WHERE id = :id", {"po": po_number, "id": lid})
                    if safety_number:
                        execute("UPDATE loads SET safety_number = :sn WHERE id = :id", {"sn": safety_number, "id": lid})

                    try:
                        update_load_status(lid, 'COMPLETED', driver_id, driver_name, role, f"Ticket #{ticket_num} submitted")
                    except StatusError as e:
                        # Ticket saved; load status couldn't advance. Log it, don't lose the ticket.
                        log.warning("Load %s status not advanced after ticket submit: %s", lid, e)

                    st.success("✅ Ticket submitted successfully!")
                    st.balloons()
                    st.rerun()
                  except Exception as e:
                    log.exception("Failed to submit ticket for load %s", lid)
                    st.error("Could not submit the ticket. Nothing was saved — please try again.")
                    st.caption(f"Details: {e}")

with tab3:
    st.markdown("### 📄 My Completed Tickets")
    
    tickets = fetch_all("""
        SELECT t.id, t.ticket_number, l.customer, t.actual_volume, t.status, t.created_at
        FROM tickets t
        JOIN loads l ON t.load_id = l.id
        WHERE t.company_id = :cid AND t.operator_name = :name
        ORDER BY t.created_at DESC LIMIT 20
    """, {"cid": company_id, "name": driver_name})
    
    if tickets:
        for t in tickets:
            tid, tnum, cust, vol, status, created = t
            c1, c2 = st.columns([4, 1])
            c1.markdown(f"**Ticket #{tnum or 'N/A'}** | {cust} | {vol}m³")
            c1.caption(f"Status: `{status}` | Submitted: {created}")
            if c2.button("📄 PDF", key=f"ftpdf_{tid}"):
                try:
                    fname, pdf = generate_field_ticket_pdf(tid, company_id)
                    st.session_state["ft_pdf"] = {"filename": fname, "pdf": pdf, "tnum": tnum or tid}
                except Exception as e:
                    log.exception("Field ticket PDF failed for ticket %s", tid)
                    st.error("Could not generate the PDF. Please try again.")
                    st.caption(f"Details: {e}")
        ft = st.session_state.get("ft_pdf")
        if ft:
            st.success(f"✅ Field Ticket #{ft['tnum']} PDF ready")
            st.download_button(f"📥 Download {ft['filename']}", data=ft["pdf"],
                               file_name=ft["filename"], mime="application/pdf",
                               type="primary", use_container_width=True)
    else:
        st.info("No completed tickets yet")
