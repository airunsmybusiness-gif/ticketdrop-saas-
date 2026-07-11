"""Authentication: Name + PIN login with bcrypt-hashed PINs.

Every user belongs to a company and has a role. Signing in stores the user
in st.session_state and drives which company's data the app shows. This is
what makes the app both secure (no shared passwords) and multi-tenant (each
login is scoped to one company).
"""
import logging
import bcrypt
import streamlit as st

from db import fetch_all, fetch_one, execute, execute_returning

log = logging.getLogger("ticketdrop.auth")

ROLES = ["driver", "dispatch", "ar", "admin"]
ROLE_LABELS = {
    "driver": "Driver",
    "dispatch": "Dispatch",
    "ar": "AR / Billing",
    "admin": "Admin",
}


# ---------------------------------------------------------------- PIN hashing
def hash_pin(pin: str) -> str:
    return bcrypt.hashpw(str(pin).encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_pin(pin: str, pin_hash: str) -> bool:
    if not pin_hash:
        return False
    try:
        return bcrypt.checkpw(str(pin).encode("utf-8"), pin_hash.encode("utf-8"))
    except Exception:
        return False


# ---------------------------------------------------------------- lookups
def get_companies():
    return fetch_all("SELECT id, name FROM companies WHERE active = TRUE ORDER BY name")


def get_login_users(company_id, role=None):
    if role:
        return fetch_all(
            "SELECT id, name FROM users WHERE company_id=:cid AND active=TRUE AND role=:role ORDER BY name",
            {"cid": company_id, "role": role},
        )
    return fetch_all(
        "SELECT id, name, role FROM users WHERE company_id=:cid AND active=TRUE ORDER BY name",
        {"cid": company_id},
    )


def authenticate(company_id, user_id, pin):
    """Return a user dict on success, else None. Falls back to a legacy
    plaintext `pin` column only if no hash has been set yet (smooth migration)."""
    row = fetch_one(
        "SELECT id, name, role, pin_hash, pin FROM users "
        "WHERE id=:id AND company_id=:cid AND active=TRUE",
        {"id": user_id, "cid": company_id},
    )
    if not row:
        return None
    uid, name, role, pin_hash, legacy_pin = row
    if pin_hash:
        ok = verify_pin(pin, pin_hash)
    else:
        ok = bool(legacy_pin) and str(pin) == str(legacy_pin)
    if not ok:
        log.info("Failed login for user_id=%s company_id=%s", user_id, company_id)
        return None
    log.info("Login OK user=%s role=%s company=%s", name, role, company_id)
    return {"user_id": uid, "user_name": name, "role": role, "company_id": company_id}


# ---------------------------------------------------------------- user management
def create_user(company_id, name, role, pin, email=None):
    return execute_returning(
        "INSERT INTO users (company_id, name, email, role, pin_hash, active) "
        "VALUES (:cid, :name, :email, :role, :ph, TRUE) RETURNING id",
        {"cid": company_id, "name": name, "email": email or None,
         "role": role, "ph": hash_pin(pin)},
    )


def set_user_pin(user_id, pin):
    execute("UPDATE users SET pin_hash=:ph, pin=NULL WHERE id=:id",
            {"ph": hash_pin(pin), "id": user_id})


def deactivate_user(user_id):
    execute("UPDATE users SET active=FALSE WHERE id=:id", {"id": user_id})


def list_all_users(company_id):
    return fetch_all(
        "SELECT id, name, email, role, active, (pin_hash IS NOT NULL) AS has_pin "
        "FROM users WHERE company_id=:cid ORDER BY role, name",
        {"cid": company_id},
    )


# ---------------------------------------------------------------- session / gate
def current_user():
    return st.session_state.get("user")


def logout():
    st.session_state.pop("user", None)


def _login_form():
    st.markdown("### 🔐 Sign in")
    companies = get_companies()
    if not companies:
        st.error("No companies configured yet. Run `python seed.py` once to set up your company.")
        st.stop()

    if len(companies) == 1:
        company_id, company_name = companies[0]
        st.caption(f"Company: **{company_name}**")
    else:
        cmap = {c[1]: c[0] for c in companies}
        company_name = st.selectbox("Company", list(cmap.keys()))
        company_id = cmap[company_name]

    users = get_login_users(company_id)
    if not users:
        st.warning("No users for this company yet. Add them in Settings (or run seed.py).")
        st.stop()

    umap = {f"{u[1]}  ·  {ROLE_LABELS.get(u[2], u[2])}": u[0] for u in users}
    who = st.selectbox("Your name", list(umap.keys()))
    pin = st.text_input("PIN", type="password", max_chars=8)

    if st.button("Sign in", type="primary", use_container_width=True):
        user = authenticate(company_id, umap[who], pin)
        if user:
            st.session_state["user"] = user
            st.rerun()
        else:
            st.error("Wrong PIN. Please try again.")
    st.stop()


def require(*allowed_roles):
    """Gate a page. Renders the login form if needed, enforces role, and
    returns the logged-in user dict. Use at the top of every page."""
    user = current_user()
    if not user:
        _login_form()
    if allowed_roles and user["role"] not in allowed_roles and user["role"] != "admin":
        st.error(f"🚫 This page is for: {', '.join(ROLE_LABELS.get(r, r) for r in allowed_roles)}. "
                 f"You are signed in as {ROLE_LABELS.get(user['role'], user['role'])}.")
        sidebar_account()
        st.stop()
    return user


def sidebar_account():
    """Show who's signed in + a logout button in the sidebar."""
    user = current_user()
    if not user:
        return
    with st.sidebar:
        st.markdown(
            f"<div style='padding:12px 14px;border:1px solid #2A2A2A;border-radius:12px;"
            f"background:rgba(var(--brand-rgb,139,92,246),0.06);margin-bottom:14px;'>"
            f"<div style='font-size:0.7rem;letter-spacing:2px;color:#9CA3AF;text-transform:uppercase;'>Signed in</div>"
            f"<div style='font-weight:700;color:#fff;'>{user['user_name']}</div>"
            f"<div style='font-size:0.8rem;color:#9CA3AF;'>{ROLE_LABELS.get(user['role'], user['role'])}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
        if st.button("Sign out", use_container_width=True):
            logout()
            st.rerun()
