from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
import sys
import os

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

app = FastAPI(
    title="LedgerFlow — Banking Data Warehouse API",
    description="REST API exposing curated banking entities, customer 360, and executive analytics for LedgerFlow.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Curated Fallback Demonstration Data (Used when deployed in serverless mode without direct PostgreSQL ingress)
DEMO_KPIS = {
    "total_customers": 55050,
    "total_accounts": 87177,
    "total_deposits": 3988526118.95,
    "total_active_loans": 13098,
    "active_loan_portfolio": 5462884935.72,
    "active_cards": 48143,
    "lifetime_transactions": 1835551,
    "lifetime_card_transactions": 2521980,
    "total_fraud_transactions": 12634
}

DEMO_SEGMENTS = [
    {"customer_segment": "Premium / Low Risk", "count": 5058},
    {"customer_segment": "Standard / Moderate Risk", "count": 15121},
    {"customer_segment": "Subprime / High Risk", "count": 34871}
]

DEMO_CUSTOMERS = [
    {"customer_id": 101, "name": "Jane Doe", "gender": "Female", "date_of_birth": "1990-04-12", "city": "New York", "state": "NY", "email": "jane.doe@example.com", "occupation": "Software Engineer", "annual_income": 85000.0, "credit_score": 720, "customer_segment": "Premium / Low Risk"},
    {"customer_id": 102, "name": "Alexander Smith", "gender": "Male", "date_of_birth": "1985-08-22", "city": "Chicago", "state": "IL", "email": "a.smith@example.com", "occupation": "Financial Analyst", "annual_income": 95000.0, "credit_score": 765, "customer_segment": "Premium / Low Risk"},
    {"customer_id": 103, "name": "Maria Garcia", "gender": "Female", "date_of_birth": "1993-11-05", "city": "Austin", "state": "TX", "email": "m.garcia@example.com", "occupation": "Marketing Director", "annual_income": 68000.0, "credit_score": 680, "customer_segment": "Standard / Moderate Risk"},
    {"customer_id": 104, "name": "David Chen", "gender": "Male", "date_of_birth": "1988-02-18", "city": "San Francisco", "state": "CA", "email": "d.chen@example.com", "occupation": "Data Architect", "annual_income": 125000.0, "credit_score": 790, "customer_segment": "Premium / Low Risk"},
    {"customer_id": 105, "name": "Sarah Jenkins", "gender": "Female", "date_of_birth": "1996-07-30", "city": "Seattle", "state": "WA", "email": "s.jenkins@example.com", "occupation": "Product Manager", "annual_income": 58000.0, "credit_score": 640, "customer_segment": "Subprime / High Risk"}
]

DEMO_ACCOUNTS = [
    {"account_id": 1001, "customer_id": 101, "branch_id": 1, "account_type": "Savings", "balance": 15450.50, "open_date": "2020-03-15", "status": "Active"},
    {"account_id": 1002, "customer_id": 101, "branch_id": 1, "account_type": "Current", "balance": 4820.00, "open_date": "2021-06-20", "status": "Active"},
    {"account_id": 1003, "customer_id": 102, "branch_id": 2, "account_type": "Salary", "balance": 28900.75, "open_date": "2019-11-01", "status": "Active"},
    {"account_id": 1004, "customer_id": 103, "branch_id": 3, "account_type": "Savings", "balance": 12400.00, "open_date": "2022-01-10", "status": "Active"},
    {"account_id": 1005, "customer_id": 104, "branch_id": 1, "account_type": "Fixed Deposit", "balance": 75000.00, "open_date": "2020-08-14", "status": "Active"}
]

DEMO_TRANSACTIONS = [
    {"transaction_id": 5001, "account_id": 1001, "txn_date": "2026-03-15 14:22:00", "txn_type": "Deposit", "amount": 1500.0, "channel": "Mobile App", "merchant_category": "Direct Deposit"},
    {"transaction_id": 5002, "account_id": 1001, "txn_date": "2026-03-16 09:15:00", "txn_type": "Withdrawal", "amount": 120.0, "channel": "ATM", "merchant_category": "Cash Withdrawal"},
    {"transaction_id": 5003, "account_id": 1001, "txn_date": "2026-03-17 19:40:00", "txn_type": "Transfer Out", "amount": 350.0, "channel": "UPI", "merchant_category": "Peer-to-Peer Transfer"},
    {"transaction_id": 5004, "account_id": 1002, "txn_date": "2026-03-18 11:05:00", "txn_type": "Deposit", "amount": 2500.0, "channel": "Online Banking", "merchant_category": "Salary Credit"},
    {"transaction_id": 5005, "account_id": 1003, "txn_date": "2026-03-19 16:30:00", "txn_type": "Fee Debit", "amount": 15.0, "channel": "Branch", "merchant_category": "Account Maintenance"}
]

DEMO_LOANS = [
    {"loan_id": 201, "customer_id": 101, "branch_id": 1, "loan_type": "Home Loan", "loan_amount": 250000.0, "interest_rate": 6.5, "term_months": 180, "start_date": "2024-01-10", "status": "Active"},
    {"loan_id": 202, "customer_id": 102, "branch_id": 2, "loan_type": "Auto Loan", "loan_amount": 32000.0, "interest_rate": 5.8, "term_months": 60, "start_date": "2023-05-15", "status": "Active"},
    {"loan_id": 203, "customer_id": 104, "branch_id": 1, "loan_type": "Personal Loan", "loan_amount": 15000.0, "interest_rate": 9.2, "term_months": 36, "start_date": "2025-02-01", "status": "Active"}
]

DEMO_CARDS = [
    {"card_id": 301, "customer_id": 101, "account_id": 1001, "card_type": "Credit - Platinum", "issue_date": "2023-01-01", "expiry_date": "2028-01-01", "credit_limit": 10000.0, "status": "Active"},
    {"card_id": 302, "customer_id": 101, "account_id": 1002, "card_type": "Debit", "issue_date": "2022-06-15", "expiry_date": "2027-06-15", "credit_limit": 0.0, "status": "Active"},
    {"card_id": 303, "customer_id": 102, "account_id": 1003, "card_type": "Credit - Gold", "issue_date": "2023-09-10", "expiry_date": "2028-09-10", "credit_limit": 7500.0, "status": "Active"}
]

DEMO_C360 = [
    {
        "customer_id": 101,
        "name": "Jane Doe",
        "annual_income": 85000.0,
        "credit_score": 720,
        "total_accounts": 2,
        "total_deposit_balance": 20270.50,
        "total_loans": 1,
        "active_loan_amount": 250000.0,
        "total_cards": 2,
        "total_credit_limit": 10000.0,
        "lifetime_transactions": 34,
        "lifetime_transaction_volume": 12850.0,
        "customer_segment": "Premium / Low Risk"
    },
    {
        "customer_id": 102,
        "name": "Alexander Smith",
        "annual_income": 95000.0,
        "credit_score": 765,
        "total_accounts": 1,
        "total_deposit_balance": 28900.75,
        "total_loans": 1,
        "active_loan_amount": 32000.0,
        "total_cards": 1,
        "total_credit_limit": 7500.0,
        "lifetime_transactions": 28,
        "lifetime_transaction_volume": 14200.0,
        "customer_segment": "Premium / Low Risk"
    }
]

def get_db():
    if not PSYCOPG2_AVAILABLE:
        return None
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            connect_timeout=2,
            cursor_factory=RealDictCursor
        )
        return conn
    except Exception:
        return None

@app.get("/")
def root():
    return {
        "status": "online",
        "service": "LedgerFlow Data Warehouse API",
        "docs": "/docs",
        "redoc": "/redoc",
        "architecture": "Medallion Layer (Raw -> DLQ Quarantine -> Curated -> Warehouse Marts)",
        "entities": ["/customers", "/accounts", "/transactions", "/loans", "/cards", "/customer-360", "/dashboard"]
    }

@app.get("/health")
def health_check():
    conn = get_db()
    db_connected = False
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT 1;")
            db_connected = True
            cur.close()
            conn.close()
        except Exception:
            db_connected = False
    return {
        "status": "healthy",
        "platform": "LedgerFlow",
        "database_connected": db_connected,
        "mode": "live_warehouse" if db_connected else "curated_cache_demo"
    }

@app.get("/customers")
def get_customers(limit: int = 50, offset: int = 0, city: Optional[str] = None):
    conn = get_db()
    if conn:
        try:
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
            return {"total": len(rows), "data": rows, "source": "live_postgres"}
        except Exception:
            pass

    # Demo fallback
    filtered = DEMO_CUSTOMERS
    if city:
        filtered = [c for c in filtered if c["city"].lower() == city.lower()]
    sliced = filtered[offset : offset + limit]
    return {"total": len(sliced), "data": sliced, "source": "curated_cache"}

@app.get("/customer/{customer_id}")
def get_customer_detail(customer_id: int):
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM customers WHERE customer_id = %s", (customer_id,))
            customer = cursor.fetchone()
            if customer:
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
                    "cards": cards,
                    "source": "live_postgres"
                }
            cursor.close()
            conn.close()
        except Exception:
            pass

    # Demo fallback
    cust = next((c for c in DEMO_CUSTOMERS if c["customer_id"] == customer_id), DEMO_CUSTOMERS[0])
    accs = [a for a in DEMO_ACCOUNTS if a["customer_id"] == cust["customer_id"]]
    lns = [l for l in DEMO_LOANS if l["customer_id"] == cust["customer_id"]]
    crds = [cd for cd in DEMO_CARDS if cd["customer_id"] == cust["customer_id"]]
    c360 = next((c for c in DEMO_C360 if c["customer_id"] == cust["customer_id"]), DEMO_C360[0])

    return {
        "customer": cust,
        "customer_360": c360,
        "accounts": accs,
        "loans": lns,
        "cards": crds,
        "source": "curated_cache"
    }

@app.get("/accounts")
def get_accounts(customer_id: Optional[int] = None, account_type: Optional[str] = None, limit: int = 50):
    conn = get_db()
    if conn:
        try:
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
            return {"total": len(rows), "data": rows, "source": "live_postgres"}
        except Exception:
            pass

    filtered = DEMO_ACCOUNTS
    if customer_id:
        filtered = [a for a in filtered if a["customer_id"] == customer_id]
    if account_type:
        filtered = [a for a in filtered if a["account_type"].lower() == account_type.lower()]
    sliced = filtered[:limit]
    return {"total": len(sliced), "data": sliced, "source": "curated_cache"}

@app.get("/transactions")
def get_transactions(account_id: Optional[int] = None, limit: int = 50):
    conn = get_db()
    if conn:
        try:
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
            return {"total": len(rows), "data": rows, "source": "live_postgres"}
        except Exception:
            pass

    filtered = DEMO_TRANSACTIONS
    if account_id:
        filtered = [t for t in filtered if t["account_id"] == account_id]
    sliced = filtered[:limit]
    return {"total": len(sliced), "data": sliced, "source": "curated_cache"}

@app.get("/loans")
def get_loans(customer_id: Optional[int] = None, status: Optional[str] = None, limit: int = 50):
    conn = get_db()
    if conn:
        try:
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
            return {"total": len(rows), "data": rows, "source": "live_postgres"}
        except Exception:
            pass

    filtered = DEMO_LOANS
    if customer_id:
        filtered = [l for l in filtered if l["customer_id"] == customer_id]
    if status:
        filtered = [l for l in filtered if l["status"].lower() == status.lower()]
    sliced = filtered[:limit]
    return {"total": len(sliced), "data": sliced, "source": "curated_cache"}

@app.get("/customer-360")
def get_customer_360(segment: Optional[str] = None, limit: int = 50):
    conn = get_db()
    if conn:
        try:
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
            return {"total": len(rows), "data": rows, "source": "live_postgres"}
        except Exception:
            pass

    filtered = DEMO_C360
    if segment:
        filtered = [c for c in filtered if segment.lower() in c["customer_segment"].lower()]
    sliced = filtered[:limit]
    return {"total": len(sliced), "data": sliced, "source": "curated_cache"}

@app.get("/dashboard")
def get_dashboard_summary():
    """Returns executive dashboard KPIs across the entire warehouse."""
    conn = get_db()
    if conn:
        try:
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

            cursor.execute("SELECT customer_segment, COUNT(*) AS count FROM customer_360 GROUP BY customer_segment")
            segments = cursor.fetchall()

            cursor.close()
            conn.close()
            return {
                "kpis": kpis,
                "customer_segments": segments,
                "source": "live_postgres"
            }
        except Exception:
            pass

    return {
        "kpis": DEMO_KPIS,
        "customer_segments": DEMO_SEGMENTS,
        "source": "curated_cache"
    }
