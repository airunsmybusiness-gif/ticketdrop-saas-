import streamlit as st
import pandas as pd
from db import fetch_all
from services.status import update_ticket_status, StatusError
from workers.axon_export import generate_axon_csv, get_export_history
st.set_page_config(page_title="AR / Billing", page_icon="💰", layout="wide")
st.title("💰 AR / Billing")
password = st.sidebar.text_input("Password", type="password")
if password != st.secrets.get("AR_PASSWORD", "billing123"):
    st.warning("Enter AR password")
    st.stop()
company_id = st.session_state.get('company_id', 1)
user_id, user_name, role = 3, "AR", "ar"
st.sidebar.success("✓ Logged in as AR")
tab1, tab2, tab3, tab4 = st.tabs(["📋 Review Tickets", "✅ Ready for AXON", "📤 Export to AXON", "📊 Export History"])
with tab1:
    st.markdown("### Submitted Tickets (Need Verification)")
    tickets = fetch_all("SELECT t.id, t.ticket_number, t.customer_name, t.operator_name, t.actual_volume, t.ticket_date, t.status FROM tickets t WHERE t.company_id = :cid AND t.status = 'SUBMITTED' ORDER BY t.ticket_date DESC", {"cid": company_id})
    if tickets:
        for t in tickets:
            tid, tnum, cust, driver, vol, tdate, status = t
            c1, c2, c3 = st.columns([3, 1, 1])
            c1.markdown(f"**#{tid}** Ticket: {tnum or 'N/A'} | {cust} | {driver} | {vol}m³")
            c1.caption(f"Date: {tdate} | Status: `{status}`")
            if c2.button("✅ Verify", key=f"verify_{tid}"):
                try:
                    update_ticket_status(tid, 'VERIFIED', user_id, user_name, role)
                    st.rerun()
                except StatusError as e:
                    st.error(str(e))
            if c3.button("⚠️ Dispute", key=f"dispute_{tid}"):
                try:
                    update_ticket_status(tid, 'DISPUTED', user_id, user_name, role, "Needs review")
                    st.rerun()
                except StatusError as e:
                    st.error(str(e))
    else:
        st.info("No tickets awaiting verification")
with tab2:
    st.markdown("### Verified Tickets (Mark Ready for Invoice)")
    verified = fetch_all("SELECT t.id, t.ticket_number, t.customer_name, t.actual_volume, t.ticket_date FROM tickets t WHERE t.company_id = :cid AND t.status = 'VERIFIED' ORDER BY t.ticket_date", {"cid": company_id})
    if verified:
        if st.button("Mark ALL as Ready for Invoice", type="primary"):
            for t in verified:
                try:
                    update_ticket_status(t[0], 'READY_FOR_INVOICE', user_id, user_name, role)
                except:
                    pass
            st.rerun()
        for t in verified:
            tid, tnum, cust, vol, tdate = t
            c1, c2 = st.columns([4, 1])
            c1.markdown(f"**#{tid}** {tnum or 'N/A'} | {cust} | {vol}m³ | {tdate}")
            if c2.button("✅ Ready", key=f"ready_{tid}"):
                try:
                    update_ticket_status(tid, 'READY_FOR_INVOICE', user_id, user_name, role)
                    st.rerun()
                except StatusError as e:
                    st.error(str(e))
    else:
        st.info("No verified tickets")
with tab3:
    st.markdown("### 📤 AXON Export")
    st.markdown("Generate CSV file for AXON import. Only exports tickets marked 'Ready for Invoice'.")
    ready_count = fetch_all("SELECT COUNT(*), COALESCE(SUM(actual_volume), 0) FROM tickets WHERE company_id = :cid AND status = 'READY_FOR_INVOICE'", {"cid": company_id})
    count = ready_count[0][0] if ready_count else 0
    volume = ready_count[0][1] if ready_count else 0
    c1, c2 = st.columns(2)
    c1.metric("Tickets Ready", count)
    c2.metric("Total Volume (m³)", f"{volume:,.2f}")
    if count > 0:
        st.warning(f"⚠️ This will mark {count} tickets as INVOICED. This cannot be undone.")
        if st.button("🚀 Generate AXON CSV", type="primary", use_container_width=True):
            result = generate_axon_csv(company_id, user_id, user_name)
            if result and result[0]:
                filename, csv_content, ticket_count, total_vol, checksum = result
                st.success(f"✅ Exported {ticket_count} tickets ({total_vol:,.2f} m³)")
                st.download_button(label=f"📥 Download {filename}", data=csv_content, file_name=filename, mime="text/csv", type="primary", use_container_width=True)
                st.code(f"Checksum (SHA256): {checksum}")
            else:
                st.error("Export failed")
    else:
        st.info("No tickets ready for export. Verify tickets and mark them 'Ready for Invoice' first.")
with tab4:
    st.markdown("### Export History")
    history = get_export_history(company_id)
    if history:
        df = pd.DataFrame(history, columns=['ID', 'Filename', 'Tickets', 'Volume', 'Checksum', 'Exported At', 'Status'])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No exports yet")
