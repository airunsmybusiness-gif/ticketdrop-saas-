import streamlit as st
st.set_page_config(page_title="TicketDrop", page_icon="🚛", layout="wide")
if 'company_id' not in st.session_state:
    st.session_state.company_id = 1
st.title("🚛 TicketDrop")
st.markdown("### Enterprise Field Ticket System")
st.markdown("""---
**Select Your Role:**
- 📋 **Dispatch** - Create & assign loads
- 🚚 **Driver** - Accept loads & complete tickets
- 💰 **AR/Billing** - Verify tickets & export to AXON
- ⚙️ **Settings** - Manage drivers, trucks, customers
---""")
try:
    from db import fetch_scalar
    pending = fetch_scalar("SELECT COUNT(*) FROM loads WHERE status IN ('REQUESTED','ASSIGNED','ACCEPTED','IN_PROGRESS') AND company_id = :cid", {"cid": st.session_state.company_id}) or 0
    ready = fetch_scalar("SELECT COUNT(*) FROM tickets WHERE status = 'READY_FOR_INVOICE' AND company_id = :cid", {"cid": st.session_state.company_id}) or 0
    c1, c2, c3 = st.columns(3)
    c1.metric("Active Loads", pending)
    c2.metric("Ready for AXON", ready)
    c3.metric("System", "🟢 Online")
except Exception as e:
    st.error(f"Database error: {e}")
st.sidebar.success("Select a page above")
