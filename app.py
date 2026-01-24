import streamlit as st

st.set_page_config(
    page_title="Rick's TicketDrop",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load CSS
try:
    with open("style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except:
    pass

if 'company_id' not in st.session_state:
    st.session_state.company_id = 1

# Premium Header
st.markdown("""
<div style="display: flex; align-items: center; justify-content: space-between; padding: 30px 0; margin-bottom: 20px;">
    <div style="display: flex; align-items: center;">
        <div style="position: relative;">
            <h1 style="
                margin: 0; 
                padding: 0; 
                font-family: 'Russo One', sans-serif;
                font-size: 4rem; 
                font-weight: 400;
                font-style: italic;
                background: linear-gradient(135deg, #C4B5FD 0%, #A78BFA 25%, #8B5CF6 50%, #7C3AED 75%, #6D28D9 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                text-shadow: 0 0 60px rgba(139, 92, 246, 0.5);
                letter-spacing: -2px;
            ">Rick's</h1>
            <div style="
                position: absolute;
                bottom: -5px;
                left: 0;
                right: 0;
                height: 3px;
                background: linear-gradient(90deg, #7C3AED, #8B5CF6, #A78BFA);
                border-radius: 2px;
                box-shadow: 0 0 20px rgba(139, 92, 246, 0.6);
            "></div>
        </div>
        <div style="margin-left: 25px;">
            <p style="
                margin: 0; 
                font-family: 'Oswald', sans-serif;
                color: #FFFFFF; 
                font-size: 1.6rem; 
                font-weight: 700; 
                letter-spacing: 4px;
                text-shadow: 0 2px 10px rgba(0,0,0,0.3);
            ">OILFIELD HAULING</p>
            <p style="
                margin: 5px 0 0 0; 
                font-family: 'Inter', sans-serif;
                color: #6B7280; 
                font-size: 0.85rem; 
                letter-spacing: 3px;
                text-transform: uppercase;
            ">Digital Field Ticket System</p>
        </div>
    </div>
    <div style="text-align: right; padding: 15px 25px; background: linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(20, 20, 20, 0.8)); border-radius: 16px; border: 1px solid rgba(139, 92, 246, 0.2);">
        <p style="margin: 0; font-family: 'Oswald', sans-serif; color: #6B7280; font-size: 0.7rem; letter-spacing: 2px; text-transform: uppercase;">24HR Emergency</p>
        <p style="margin: 5px 0 0 0; font-family: 'Russo One', sans-serif; color: #A78BFA; font-size: 1.4rem; letter-spacing: 1px;">(780) 942-2932</p>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# Role Selection
st.markdown("""
<p style="font-family: 'Oswald', sans-serif; font-size: 1.1rem; color: #9CA3AF; letter-spacing: 3px; text-transform: uppercase; margin-bottom: 25px;">Select Your Role</p>
""", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    <div style="
        background: linear-gradient(145deg, #141414 0%, #0F0F0F 100%);
        border-radius: 20px;
        padding: 35px 25px;
        text-align: center;
        border: 1px solid #2A2A2A;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    ">
        <div style="
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, transparent, #8B5CF6, transparent);
        "></div>
        <div style="font-size: 3.5rem; margin-bottom: 20px; filter: drop-shadow(0 0 20px rgba(139, 92, 246, 0.3));">📋</div>
        <h3 style="margin: 0; font-family: 'Oswald', sans-serif; color: #FFFFFF; font-size: 1.4rem; font-weight: 600; letter-spacing: 2px;">DISPATCH</h3>
        <p style="font-family: 'Inter', sans-serif; color: #6B7280; font-size: 0.85rem; margin-top: 12px; line-height: 1.5;">Send load requests to drivers</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("OPEN DISPATCH", key="btn_dispatch", use_container_width=True):
        st.switch_page("pages/1_📋_Dispatch.py")

with col2:
    st.markdown("""
    <div style="
        background: linear-gradient(145deg, #141414 0%, #0F0F0F 100%);
        border-radius: 20px;
        padding: 35px 25px;
        text-align: center;
        border: 1px solid #2A2A2A;
        position: relative;
        overflow: hidden;
    ">
        <div style="
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, transparent, #8B5CF6, transparent);
        "></div>
        <div style="font-size: 3.5rem; margin-bottom: 20px; filter: drop-shadow(0 0 20px rgba(139, 92, 246, 0.3));">🚚</div>
        <h3 style="margin: 0; font-family: 'Oswald', sans-serif; color: #FFFFFF; font-size: 1.4rem; font-weight: 600; letter-spacing: 2px;">DRIVER</h3>
        <p style="font-family: 'Inter', sans-serif; color: #6B7280; font-size: 0.85rem; margin-top: 12px; line-height: 1.5;">Accept & complete tickets</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("OPEN DRIVER", key="btn_driver", use_container_width=True):
        st.switch_page("pages/2_🚚_Driver.py")

with col3:
    st.markdown("""
    <div style="
        background: linear-gradient(145deg, #141414 0%, #0F0F0F 100%);
        border-radius: 20px;
        padding: 35px 25px;
        text-align: center;
        border: 1px solid #2A2A2A;
        position: relative;
        overflow: hidden;
    ">
        <div style="
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, transparent, #8B5CF6, transparent);
        "></div>
        <div style="font-size: 3.5rem; margin-bottom: 20px; filter: drop-shadow(0 0 20px rgba(139, 92, 246, 0.3));">💰</div>
        <h3 style="margin: 0; font-family: 'Oswald', sans-serif; color: #FFFFFF; font-size: 1.4rem; font-weight: 600; letter-spacing: 2px;">AR / BILLING</h3>
        <p style="font-family: 'Inter', sans-serif; color: #6B7280; font-size: 0.85rem; margin-top: 12px; line-height: 1.5;">Verify & export to AXON</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("OPEN AR", key="btn_ar", use_container_width=True):
        st.switch_page("pages/3_💰_AR.py")

with col4:
    st.markdown("""
    <div style="
        background: linear-gradient(145deg, #141414 0%, #0F0F0F 100%);
        border-radius: 20px;
        padding: 35px 25px;
        text-align: center;
        border: 1px solid #2A2A2A;
        position: relative;
        overflow: hidden;
    ">
        <div style="
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, transparent, #8B5CF6, transparent);
        "></div>
        <div style="font-size: 3.5rem; margin-bottom: 20px; filter: drop-shadow(0 0 20px rgba(139, 92, 246, 0.3));">⚙️</div>
        <h3 style="margin: 0; font-family: 'Oswald', sans-serif; color: #FFFFFF; font-size: 1.4rem; font-weight: 600; letter-spacing: 2px;">SETTINGS</h3>
        <p style="font-family: 'Inter', sans-serif; color: #6B7280; font-size: 0.85rem; margin-top: 12px; line-height: 1.5;">Manage company data</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("OPEN SETTINGS", key="btn_settings", use_container_width=True):
        st.switch_page("pages/4_⚙️_Settings.py")

st.markdown("---")

# Dashboard
st.markdown("""
<p style="font-family: 'Oswald', sans-serif; font-size: 1.1rem; color: #9CA3AF; letter-spacing: 3px; text-transform: uppercase; margin-bottom: 25px;">Live Dashboard</p>
""", unsafe_allow_html=True)

try:
    from db import fetch_scalar
    cid = st.session_state.company_id
    
    pending = fetch_scalar("SELECT COUNT(*) FROM loads WHERE status = 'ASSIGNED' AND company_id = :cid", {"cid": cid}) or 0
    acknowledged = fetch_scalar("SELECT COUNT(*) FROM loads WHERE status = 'ACCEPTED' AND company_id = :cid", {"cid": cid}) or 0
    in_progress = fetch_scalar("SELECT COUNT(*) FROM loads WHERE status = 'IN_PROGRESS' AND company_id = :cid", {"cid": cid}) or 0
    completed_today = fetch_scalar("SELECT COUNT(*) FROM loads WHERE status = 'COMPLETED' AND DATE(status_changed_at) = CURRENT_DATE AND company_id = :cid", {"cid": cid}) or 0
    ready_axon = fetch_scalar("SELECT COUNT(*) FROM tickets WHERE status = 'READY_FOR_INVOICE' AND company_id = :cid", {"cid": cid}) or 0
    
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("⏳ AWAITING", pending)
    m2.metric("✅ ACKNOWLEDGED", acknowledged)
    m3.metric("🚛 IN PROGRESS", in_progress)
    m4.metric("✔️ COMPLETED", completed_today)
    m5.metric("📤 AXON READY", ready_axon)
    
    st.markdown("---")
    
    st.markdown("""
    <div style="
        display: flex; 
        justify-content: center; 
        align-items: center; 
        padding: 25px; 
        background: linear-gradient(135deg, rgba(34, 197, 94, 0.1), rgba(34, 197, 94, 0.02));
        border-radius: 16px; 
        border: 1px solid rgba(34, 197, 94, 0.2);
        box-shadow: 0 0 40px rgba(34, 197, 94, 0.1);
    ">
        <div style="
            width: 12px;
            height: 12px;
            background: #22C55E;
            border-radius: 50%;
            margin-right: 15px;
            box-shadow: 0 0 20px #22C55E, 0 0 40px #22C55E;
            animation: pulse 2s infinite;
        "></div>
        <span style="font-family: 'Oswald', sans-serif; color: #22C55E; font-weight: 600; font-size: 1rem; letter-spacing: 3px; text-transform: uppercase;">All Systems Operational</span>
    </div>
    <style>
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
    </style>
    """, unsafe_allow_html=True)
    
except Exception as e:
    st.error(f"Database error: {e}")

# Sidebar
st.sidebar.markdown("""
<div style="text-align: center; padding: 30px 0; border-bottom: 1px solid #2A2A2A; margin-bottom: 25px;">
    <h2 style="
        margin: 0; 
        font-family: 'Russo One', sans-serif;
        font-size: 2.2rem; 
        font-style: italic;
        background: linear-gradient(135deg, #C4B5FD, #A78BFA, #8B5CF6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    ">Rick's</h2>
    <p style="
        margin: 8px 0 0 0; 
        font-family: 'Oswald', sans-serif;
        color: #6B7280; 
        font-size: 0.65rem; 
        letter-spacing: 3px;
        text-transform: uppercase;
    ">TicketDrop v2.0</p>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("""
<div style="padding: 20px; background: linear-gradient(135deg, rgba(139, 92, 246, 0.05), transparent); border-radius: 12px; border: 1px solid #2A2A2A;">
    <p style="font-family: 'Oswald', sans-serif; color: #6B7280; font-size: 0.7rem; letter-spacing: 2px; margin: 0 0 10px 0; text-transform: uppercase;">24HR Support</p>
    <p style="font-family: 'Russo One', sans-serif; color: #A78BFA; font-size: 1.1rem; margin: 0;">(780) 942-2932</p>
    <p style="font-family: 'Inter', sans-serif; color: #4B5563; font-size: 0.75rem; margin: 10px 0 0 0;">4606 51 Ave, Redwater AB</p>
</div>
""", unsafe_allow_html=True)
