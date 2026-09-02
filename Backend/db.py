"""Postgres/Supabase connection layer. Every other backend module goes
through here — nothing else opens a raw connection itself.
"""
from __future__ import annotations
import os
import psycopg2
import psycopg2.extras

try:
    from dotenv import load_dotenv
    load_dotenv()  # loads .env if present; harmless no-op if it isn't
except ImportError:
    pass

DATABASE_URL = os.environ.get("DATABASE_URL")


def get_conn():
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL is not set. Export your Supabase connection string, e.g.\n"
            '  export DATABASE_URL="postgresql://postgres:[password]@[host]:5432/postgres"'
        )
    return psycopg2.connect(DATABASE_URL)


def query(sql: str, params: tuple = ()) -> list[dict]:
    """Read query -> list of dict rows."""
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return [dict(r) for r in cur.fetchall()]


def execute(sql: str, params: tuple = ()) -> None:
    """Write query, no return value expected."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
        conn.commit()


def execute_returning(sql: str, params: tuple = ()) -> dict | None:
    """Write query with a RETURNING clause -> single dict row."""
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
        conn.commit()
        return dict(row) if row else None
