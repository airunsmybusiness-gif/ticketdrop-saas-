import logging
import streamlit as st
import pandas as pd
from db import fetch_all, fetch_one
from services.status import update_ticket_status, StatusError
from services.invoice import build_invoice_data, generate_invoice_pdf
from workers.axon_export import generate_axon_csv, get_export_history
import auth
import branding
st.set_page_config(page_title="AR / Billing · TicketDrop", page_icon="💰", layout="wide")
log = logging.getLogger("ticketdrop.ar")

branding.apply_branding(auth.current_user()["company_id"] if auth.current_user() else None)
user = auth.require("ar", "admin")
company_id = user["company_id"]
user_id, user_name, role = user["user_id"], user["user_name"], user["role"]
branding.apply_branding(company_id)
auth.sidebar_account()

st.title("💰 AR / Billing")
tab1, tab2, tab5, tab3, tab4 = st.tabs(
    ["📋 Review Tickets", "✅ Ready for Invoice", "🧾 Create Invoice", "📤 Export to AXON", "📊 Export History"]
)
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
                except StatusError as e:
                    log.warning("Ticket %s not marked ready: %s", t[0], e)
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
with tab5:
    st.markdown("### 🧾 Create a PDF Invoice")
    st.caption("Groups your 'Ready for Invoice' tickets by customer. Pick a customer, confirm the rates, and download a branded PDF.")
    ready = fetch_all(
        "SELECT id, ticket_number, customer_name, actual_volume, hours_charged, ticket_date "
        "FROM tickets WHERE company_id=:cid AND status='READY_FOR_INVOICE' "
        "ORDER BY customer_name, ticket_date",
        {"cid": company_id},
    )
    if not ready:
        st.info("No tickets ready to invoice. Verify tickets and mark them 'Ready for Invoice' first.")
    else:
        customers = sorted({(r[2] or "Unknown") for r in ready})
        cust = st.selectbox("Customer", customers)
        cust_tickets = [r for r in ready if (r[2] or "Unknown") == cust]
        st.dataframe(
            pd.DataFrame([(r[1] or f"#{r[0]}", r[3], r[4], r[5]) for r in cust_tickets],
                         columns=["Ticket #", "Volume m³", "Hours", "Date"]),
            use_container_width=True, hide_index=True,
        )
        comp = fetch_one("SELECT rate_per_m3, rate_per_hour FROM companies WHERE id=:id", {"id": company_id})
        d_m3, d_hr = (float(comp[0] or 0), float(comp[1] or 0)) if comp else (0.0, 0.0)
        cc1, cc2 = st.columns(2)
        r_m3 = cc1.number_input("Rate per m³ ($)", value=d_m3, step=5.0, min_value=0.0, key="inv_rm3")
        r_hr = cc2.number_input("Rate per hour ($)", value=d_hr, step=5.0, min_value=0.0, key="inv_rhr")
        if d_m3 == 0 and d_hr == 0 and r_m3 == 0 and r_hr == 0:
            st.warning("No rates set. Enter them above, or set defaults in Settings → Company.")

        ids = [r[0] for r in cust_tickets]
        try:
            preview = build_invoice_data(company_id, ids, rate_per_m3=r_m3, rate_per_hour=r_hr)
            p1, p2, p3 = st.columns(3)
            p1.metric("Subtotal", f"${preview['subtotal']:,.2f}")
            p2.metric(f"{preview['tax_label']} ({preview['tax_rate']:g}%)", f"${preview['tax']:,.2f}")
            p3.metric("Total", f"${preview['total']:,.2f}")
        except Exception as e:
            log.exception("Invoice preview failed")
            st.error("Could not build the preview.")
            st.caption(f"Details: {e}")

        mark_invoiced = st.checkbox("Mark these tickets as INVOICED after generating", value=True)
        if st.button("🧾 Generate PDF Invoice", type="primary", use_container_width=True):
            try:
                number, filename, pdf_bytes, data = generate_invoice_pdf(
                    company_id, ids, rate_per_m3=r_m3, rate_per_hour=r_hr, user_id=user_id)
                if mark_invoiced:
                    for tid in ids:
                        try:
                            update_ticket_status(tid, 'INVOICED', user_id, user_name, role, f"Invoice {number}")
                        except StatusError as e:
                            log.warning("Ticket %s not marked invoiced: %s", tid, e)
                st.session_state["last_invoice"] = {
                    "filename": filename, "pdf": pdf_bytes, "number": number, "total": data["total"]}
            except Exception as e:
                log.exception("Invoice generation failed")
                st.error("Could not generate the invoice. Please try again.")
                st.caption(f"Details: {e}")

    # Persistent download of the most recently generated invoice (survives reruns)
    li = st.session_state.get("last_invoice")
    if li:
        st.success(f"✅ Invoice {li['number']} ready — ${li['total']:,.2f} total")
        st.download_button(f"📥 Download {li['filename']}", data=li["pdf"], file_name=li["filename"],
                           mime="application/pdf", type="primary", use_container_width=True)
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
            try:
                result = generate_axon_csv(company_id, user_id, user_name)
            except Exception as e:
                log.exception("AXON export failed for company %s", company_id)
                st.error("Export failed. No tickets were marked as invoiced — please try again.")
                st.caption(f"Details: {e}")
                result = None
            if result and result[0]:
                filename, csv_content, ticket_count, total_vol, checksum = result
                st.success(f"✅ Exported {ticket_count} tickets ({total_vol:,.2f} m³)")
                st.download_button(label=f"📥 Download {filename}", data=csv_content, file_name=filename, mime="text/csv", type="primary", use_container_width=True)
                st.code(f"Checksum (SHA256): {checksum}")
            elif result is not None:
                st.error("Nothing to export.")
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
