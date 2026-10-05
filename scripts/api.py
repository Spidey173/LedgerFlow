from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

app = FastAPI(
    title="LedgerFlow — Banking Data Warehouse API",
    description="REST API exposing curated banking entities, customer 360, and executive analytics for LedgerFlow.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        cursor_factory=RealDictCursor
    )
    return conn

@app.get("/")
def root():
    return {
        "status": "online",
        "service": "LedgerFlow Data Warehouse API",
        "docs": "/docs",
        "entities": ["/customers", "/accounts", "/transactions", "/loans", "/cards", "/customer-360", "/dashboard"]
    }

@app.get("/customers")
def get_customers(limit: int = 50, offset: int = 0, city: Optional[str] = None):
    conn = get_db()
    cursor = conn.cursor()
    query = "SELECT * FROM customers WHERE 1=1"
    params = []
    if city:
        query += " AND LOWER(city) = LOWER(%s)"
        params.append(city)
    query += " ORDER BY customer_id LIMIT %s OFFSET %s"
    params.extend([limit, offset])
    cursor.execute(query, params)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return {"total": len(rows), "data": rows}

@app.get("/customer/{customer_id}")
def get_customer_detail(customer_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM customers WHERE customer_id = %s", (customer_id,))
    customer = cursor.fetchone()
    if not customer:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")

    cursor.execute("SELECT * FROM accounts WHERE customer_id = %s", (customer_id,))
    accounts = cursor.fetchall()

    cursor.execute("SELECT * FROM loans WHERE customer_id = %s", (customer_id,))
    loans = cursor.fetchall()

    cursor.execute("SELECT * FROM cards WHERE customer_id = %s", (customer_id,))
    cards = cursor.fetchall()

    cursor.execute("SELECT * FROM customer_360 WHERE customer_id = %s", (customer_id,))
    c360 = cursor.fetchone()

    cursor.close()
    conn.close()
    return {
        "customer": customer,
        "customer_360": c360,
        "accounts": accounts,
        "loans": loans,
        "cards": cards
    }

@app.get("/accounts")
def get_accounts(customer_id: Optional[int] = None, account_type: Optional[str] = None, limit: int = 50):
    conn = get_db()
    cursor = conn.cursor()
    query = "SELECT * FROM accounts WHERE 1=1"
    params = []
    if customer_id:
        query += " AND customer_id = %s"
        params.append(customer_id)
    if account_type:
        query += " AND LOWER(account_type) = LOWER(%s)"
        params.append(account_type)
    query += " ORDER BY account_id LIMIT %s"
    params.append(limit)
    cursor.execute(query, params)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return {"total": len(rows), "data": rows}

@app.get("/transactions")
def get_transactions(account_id: Optional[int] = None, limit: int = 50):
    conn = get_db()
    cursor = conn.cursor()
    query = "SELECT * FROM transactions WHERE 1=1"
    params = []
    if account_id:
        query += " AND account_id = %s"
        params.append(account_id)
    query += " ORDER BY txn_date DESC, transaction_id DESC LIMIT %s"
    params.append(limit)
    cursor.execute(query, params)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return {"total": len(rows), "data": rows}

@app.get("/loans")
def get_loans(customer_id: Optional[int] = None, status: Optional[str] = None, limit: int = 50):
    conn = get_db()
    cursor = conn.cursor()
    query = "SELECT * FROM loans WHERE 1=1"
    params = []
    if customer_id:
        query += " AND customer_id = %s"
        params.append(customer_id)
    if status:
        query += " AND LOWER(status) = LOWER(%s)"
        params.append(status)
    query += " ORDER BY loan_id LIMIT %s"
    params.append(limit)
    cursor.execute(query, params)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return {"total": len(rows), "data": rows}

@app.get("/customer-360")
def get_customer_360(segment: Optional[str] = None, limit: int = 50):
    conn = get_db()
    cursor = conn.cursor()
    query = "SELECT * FROM customer_360 WHERE 1=1"
    params = []
    if segment:
        query += " AND customer_segment ILIKE %s"
        params.append(f"%{segment}%")
    query += " ORDER BY total_deposit_balance DESC LIMIT %s"
    params.append(limit)
    cursor.execute(query, params)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return {"total": len(rows), "data": rows}

@app.get("/dashboard")
def get_dashboard_summary():
    """Returns executive dashboard KPIs across the entire warehouse."""
    conn = get_db()
    cursor = conn.cursor()
    query = """
    SELECT 
        (SELECT COUNT(*) FROM customers) AS total_customers,
        (SELECT COUNT(*) FROM accounts) AS total_accounts,
        (SELECT ROUND(SUM(balance), 2) FROM accounts) AS total_deposits,
        (SELECT COUNT(*) FROM loans WHERE status = 'Active') AS total_active_loans,
        (SELECT ROUND(SUM(loan_amount), 2) FROM loans WHERE status = 'Active') AS active_loan_portfolio,
        (SELECT COUNT(*) FROM cards WHERE status = 'Active') AS active_cards,
        (SELECT COUNT(*) FROM transactions) AS lifetime_transactions,
        (SELECT COUNT(*) FROM card_transactions) AS lifetime_card_transactions,
        (SELECT SUM(is_fraud) FROM card_transactions) AS total_fraud_transactions
    """
    cursor.execute(query)
    kpis = cursor.fetchone()

    # Segment breakdown
    cursor.execute("SELECT customer_segment, COUNT(*) AS count FROM customer_360 GROUP BY customer_segment")
    segments = cursor.fetchall()

    cursor.close()
    conn.close()
    return {
        "kpis": kpis,
        "customer_segments": segments
    }
