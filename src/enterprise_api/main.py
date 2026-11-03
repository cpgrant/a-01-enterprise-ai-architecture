
import os
from contextlib import contextmanager
from datetime import date
from decimal import Decimal

import psycopg
from psycopg.rows import dict_row
from fastapi import FastAPI, HTTPException

app = FastAPI(
    title="AI-A01 Enterprise Integration API",
    version="0.1.0",
    description="Read-only synthetic enterprise data API",
)


@contextmanager
def db_connection():
    password = os.getenv("POSTGRES_PASSWORD")
    if not password:
        raise RuntimeError("POSTGRES_PASSWORD is not configured")

    with psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "127.0.0.1"),
        port=int(os.getenv("POSTGRES_PORT", "5433")),
        dbname="ai_a01",
        user="ai_a01",
        password=password,
        row_factory=dict_row,
    ) as conn:
        yield conn


def serialize(row):
    return {
        key: (
            value.isoformat() if isinstance(value, date)
            else float(value) if isinstance(value, Decimal)
            else value
        )
        for key, value in row.items()
    }


@app.get("/health")
def health():
    try:
        with db_connection() as conn:
            conn.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Database unavailable",
        )


@app.get("/orders")
def orders():
    with db_connection() as conn:
        rows = conn.execute("""
            SELECT o.order_id, c.customer_name, c.priority,
                   s.supplier_name, s.reliability_score,
                   o.order_value, o.promised_date,
                   o.expected_date,
                   o.expected_date - o.promised_date AS delay_days,
                   o.status
            FROM orders o
            JOIN customers c ON c.customer_id = o.customer_id
            JOIN suppliers s ON s.supplier_id = o.supplier_id
            ORDER BY o.order_id
        """).fetchall()
    return [serialize(row) for row in rows]


@app.get("/orders/at-risk")
def orders_at_risk():
    with db_connection() as conn:
        rows = conn.execute("""
            SELECT o.order_id, c.customer_name, c.priority,
                   s.supplier_name, s.reliability_score,
                   o.order_value, o.promised_date,
                   o.expected_date,
                   o.expected_date - o.promised_date AS delay_days,
                   o.status
            FROM orders o
            JOIN customers c ON c.customer_id = o.customer_id
            JOIN suppliers s ON s.supplier_id = o.supplier_id
            WHERE o.expected_date > o.promised_date
              AND o.status NOT IN ('delivered')
            ORDER BY
                CASE c.priority
                    WHEN 'critical' THEN 1
                    WHEN 'high' THEN 2
                    ELSE 3
                END,
                (o.expected_date - o.promised_date) DESC
        """).fetchall()
    return [serialize(row) for row in rows]


@app.get("/knowledge")
def knowledge():
    with db_connection() as conn:
        rows = conn.execute("""
            SELECT document_id, title, content
            FROM knowledge_documents
            ORDER BY document_id
        """).fetchall()
    return rows
