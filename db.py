"""Database access layer.

Reads configuration from environment variables first (how Railway / Render
inject secrets), then falls back to Streamlit's secrets.toml for local dev.
Never hardcode credentials here.
"""
import os
import streamlit as st
from sqlalchemy import create_engine, text
from contextlib import contextmanager

_engine = None


def get_secret(key, default=None):
    """Return a config value from the OS environment, then Streamlit secrets."""
    val = os.environ.get(key)
    if val is not None:
        return val
    try:
        return st.secrets[key]
    except Exception:
        return default


def get_engine():
    global _engine
    if _engine is None:
        url = get_secret("DATABASE_URL")
        if not url:
            raise RuntimeError(
                "DATABASE_URL is not set. Add it as an environment variable "
                "(Railway/Render) or in .streamlit/secrets.toml for local dev."
            )
        _engine = create_engine(url, pool_pre_ping=True)
    return _engine


@contextmanager
def get_connection():
    engine = get_engine()
    conn = engine.connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def execute(query, params=None):
    with get_connection() as conn:
        conn.execute(text(query), params or {})


def execute_returning(query, params=None):
    """Run an INSERT/UPDATE ... RETURNING and return the first column of the first row."""
    with get_connection() as conn:
        result = conn.execute(text(query), params or {})
        row = result.fetchone()
        return row[0] if row else None


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
