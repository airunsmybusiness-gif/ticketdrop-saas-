import streamlit as st

st.set_page_config(
    page_title="Rick's TicketDrop",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
def load_css():
    with open("style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

try:
    load_css()
except:
    pass

if 'company_id' not in st.session_state:
    st.session_state.company_id = 1

# Header with Rick's branding
st.markdown("""
<div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 2rem; padding: 20px 0;">
    <div style="display: flex; align-items: center;">
        <div style="margin-right: 20px;">
            <h1 style="margin: 0; padding: 0; font-size: 3rem; font-weight: 900; font-style: italic; background: linear-gradient(135deg, #7C3AED, #8B5CF6, #A78BFA); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Rick's</h1>
        </div>
        <div>
            <p style="margin: 0; color: #FFFFFF; font-size: 1.4rem; font-weight: 800; letter-spacing: 2px;">OILFIELD HAULING</p>
            <p style="margin: 0; color: #9CA3AF; font-size: 0.9rem; letter-spacing: 1px;">Digital Field Ticket System</p>
        </div>
    </div>
    <div style="text-align: right;">
        <p style="margin: 0; color: #9CA3AF; font-size: 0.8rem;">24HR EMERGENCY</p>
        <p style="margin: 0; color: #8B5CF6; font-size: 1.1rem; font-weight: 700;">(780) 942-2932</p>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# Role selection cards
st.markdown("### Select Your Role")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1A1A1A, #252525); border-radius: 16px; padding: 28px; text-align: center; border: 1px solid #333333; transition: all 0.3s ease; cursor: pointer;">
        <div style="font-size: 3rem; margin-bottom: 16px;">📋</div>
        <h3 style="margin: 0; color: #FFFFFF; font-size: 1.3rem; font-weight: 700;">Dispatch</h3>
        <p style="color: #9CA3AF; font-size: 0.85rem; margin-top: 10px;">Send load requests to drivers</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1A1A1A, #252525); border-radius: 16px; padding: 28px; text-align: center; border: 1px solid #333333;">
        <div style="font-size: 3rem; margin-bottom: 16px;">🚚</div>
        <h3 style="margin: 0; color: #FFFFFF; font-size: 1.3rem; font-weight: 700;">Driver</h3>
        <p style="color: #9CA3AF; font-size: 0.85rem; margin-top: 10px;">Accept loads & complete tickets</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1A1A1A, #252525); border-radius: 16px; padding: 28px; text-align: center; border: 1px solid #333333;">
        <div style="font-size: 3rem; margin-bottom: 16px;">💰</div>
        <h3 style="margin: 0; color: #FFFFFF; font-size: 1.3rem; font-weight: 700;">AR / Billing</h3>
        <p style="color: #9CA3AF; font-size: 0.85rem; margin-top: 10px;">Verify & export to AXON</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1A1A1A, #252525); border-radius: 16px; padding: 28px; text-align: center; border: 1px solid #333333;">
        <div style="font-size: 3rem; margin-bottom: 16px;">⚙️</div>
        <h3 style="margin: 0; color: #FFFFFF; font-size: 1.3rem; font-weight: 700;">Settings</h3>
        <p style="color: #9CA3AF; font-size: 0.85rem; margin-top: 10px;">Manage company data</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Dashboard
st.markdown("### Live Dashboard")

try:
    from db import fetch_scalar
    cid = st.session_state.company_id
    
    pending = fetch_scalar("SELECT COUNT(*) FROM loads WHERE status = 'ASSIGNED' AND company_id = :cid", {"cid": cid}) or 0
    acknowledged = fetch_scalar("SELECT COUNT(*) FROM loads WHERE status = 'ACCEPTED' AND company_id = :cid", {"cid": cid}) or 0
    in_progress = fetch_scalar("SELECT COUNT(*) FROM loads WHERE status = 'IN_PROGRESS' AND company_id = :cid", {"cid": cid}) or 0
    completed_today = fetch_scalar("SELECT COUNT(*) FROM loads WHERE status = 'COMPLETED' AND DATE(status_changed_at) = CURRENT_DATE AND company_id = :cid", {"cid": cid}) or 0
    ready_axon = fetch_scalar("SELECT COUNT(*) FROM tickets WHERE status = 'READY_FOR_INVOICE' AND company_id = :cid", {"cid": cid}) or 0
    
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("⏳ Awaiting", pending)
    m2.metric("✅ Acknowledged", acknowledged)
    m3.metric("🚛 In Progress", in_progress)
    m4.metric("✔️ Completed Today", completed_today)
    m5.metric("📤 Ready for AXON", ready_axon)
    
    st.markdown("---")
    
    # System status
    st.markdown("""
    <div style="display: flex; justify-content: center; align-items: center; padding: 20px; background: linear-gradient(135deg, rgba(34, 197, 94, 0.1), rgba(34, 197, 94, 0.05)); border-radius: 12px; border: 1px solid rgba(34, 197, 94, 0.3);">
        <span style="font-size: 1.5rem; margin-right: 12px;">🟢</span>
        <span style="color: #22C55E; font-weight: 700; font-size: 1.1rem;">All Systems Operational</span>
    </div>
    """, unsafe_allow_html=True)
    
except Exception as e:
    st.error(f"Database connection error: {e}")

# Sidebar
st.sidebar.markdown("""
<div style="text-align: center; padding: 24px 0; border-bottom: 1px solid #333333; margin-bottom: 20px;">
    <h2 style="margin: 0; font-size: 1.8rem; font-weight: 900; font-style: italic; background: linear-gradient(135deg, #7C3AED, #8B5CF6, #A78BFA); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Rick's</h2>
    <p style="margin: 5px 0 0 0; color: #9CA3AF; font-size: 0.75rem; letter-spacing: 2px; font-weight: 600;">TICKETDROP v2.0</p>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("**📍 Navigation**")
st.sidebar.caption("Select a page from the menu above")

st.sidebar.markdown("---")
st.sidebar.markdown("**📞 Support**")
st.sidebar.caption("24HR: (780) 942-2932")
st.sidebar.caption("4606 51 Ave, Redwater AB")
