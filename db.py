import streamlit as st
from sqlalchemy import create_engine, text
from contextlib import contextmanager

_engine = None

def get_engine():
    global _engine
    if _engine is None:
        url = st.secrets["DATABASE_URL"]
        _engine = create_engine(url, pool_pre_ping=True)
    return _engine

@contextmanager
def get_connection():
    engine = get_engine()
    conn = engine.connect()
    try:
        yield conn
        conn.commit()
    except:
        conn.rollback()
        raise
    finally:
        conn.close()

def execute(query, params=None):
    with get_connection() as conn:
        conn.execute(text(query), params or {})

def fetch_all(query, params=None):
    with get_connection() as conn:
        result = conn.execute(text(query), params or {})
        return result.fetchall()

def fetch_one(query, params=None):
    with get_connection() as conn:
        result = conn.execute(text(query), params or {})
        return result.fetchone()

def fetch_scalar(query, params=None):
    with get_connection() as conn:
        result = conn.execute(text(query), params or {})
        row = result.fetchone()
        return row[0] if row else None
