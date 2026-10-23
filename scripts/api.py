from fastapi import FastAPI, HTTPException, Query, Request, Depends, status, Security
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional, Dict, Any
import sys
import os

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

import utils.config as app_config
from utils.logger import get_logger
from scripts.dashboard_view import render_dashboard_html
from scripts.generate_audit_report import generate_audit_report_html

logger = get_logger("api_service")

app = FastAPI(
    title="LedgerFlow — Banking Data Warehouse API",
    description="REST API exposing curated banking entities, customer 360, and executive analytics for LedgerFlow.",
    version="1.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Restrict CORS to configured origins (no wildcard in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=app_config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

# Authentication & RBAC setup
bearer_security = HTTPBearer(auto_error=False)

ROLE_PERMISSIONS = {
    "read_only": ["read"],
    "analyst": ["read", "analytics"],
    "admin": ["read", "analytics", "admin"],
}

def require_role(min_role: str = "read_only"):
    """
    Enforces Bearer authentication and role-based authorization when API_AUTH_ENABLED is True.
    When API_AUTH_ENABLED is False (e.g. local dev), requests pass with 'admin' role.
    """
    def dependency(credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_security)):
        if not app_config.API_AUTH_ENABLED:
            return {"role": "admin", "token": "local-dev-bypass"}

        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required. Provide Bearer token in Authorization header.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = credentials.credentials
        user_role = None

        # Constant-time comparison across configured API keys to prevent timing attack side channels
        import hmac
        for valid_token, role in app_config.API_KEYS.items():
            if hmac.compare_digest(token, valid_token):
                user_role = role
                break

        if not user_role:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired API token.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        allowed_perms = ROLE_PERMISSIONS.get(user_role, [])
        required_perm = "admin" if min_role == "admin" else ("analytics" if min_role == "analyst" else "read")

        if required_perm not in allowed_perms:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden. Role '{user_role}' lacks '{min_role}' privileges.",
            )

        return {"role": user_role, "token": token[:6] + "..."}

    return dependency

# Explicit Demo Demonstration Data (Used ONLY when DEMO_MODE=true)
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
        db_url = os.getenv("DATABASE_URL") or app_config.DATABASE_URL
        if db_url:
            return psycopg2.connect(db_url, connect_timeout=5, cursor_factory=RealDictCursor)
        if not app_config.DB_PASSWORD and not os.getenv("DB_PASSWORD"):
            return None
        return psycopg2.connect(
            host=app_config.DB_HOST,
            port=app_config.DB_PORT,
            dbname=app_config.DB_NAME,
            user=app_config.DB_USER,
            password=app_config.DB_PASSWORD,
            connect_timeout=3,
            cursor_factory=RealDictCursor
        )
    except Exception as e:
        logger.warning(f"Database connection attempt failed: {e}")
        return None

def handle_db_error(error_msg: str):
    """
    Called when a database query or connection fails.
    If DEMO_MODE is explicitly enabled, allows fallback with warning.
    Otherwise, raises HTTP 503 Service Unavailable so failures are never silently masked.
    """
    if app_config.DEMO_MODE:
        logger.warning(f"[DEMO MODE FALLBACK] Database query failed ({error_msg}). Serving sanitized demo cache.")
        return
    logger.error(f"[DATABASE FAILURE] Live query failed ({error_msg}). Raising HTTP 503.")
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=f"Database warehouse is currently unavailable: {error_msg}. Live query aborted."
    )

@app.get("/")
def root(request: Request, format: Optional[str] = Query(None)):
    accept_header = request.headers.get("accept", "")
    if format == "json" or ("application/json" in accept_header and "text/html" not in accept_header):
        return JSONResponse({
            "status": "online",
            "service": "LedgerFlow Data Warehouse & AWS Lakehouse API",
            "docs": "/docs",
            "redoc": "/redoc",
            "dashboard_ui": "/",
            "audit_report": "/audit-report",
            "auth_enabled": app_config.API_AUTH_ENABLED,
            "demo_mode": app_config.DEMO_MODE,
            "architecture": "Medallion Lakehouse (S3 Bronze -> S3 Silver -> PostgreSQL Warehouse Marts)",
            "entities": ["/customers", "/accounts", "/transactions", "/loans", "/cards", "/customer-360", "/dashboard"]
        })
    return HTMLResponse(render_dashboard_html())

@app.get("/dashboard-ui", response_class=HTMLResponse)
def dashboard_ui():
    """Serves the interactive Glassmorphic Executive Banking Dashboard."""
    return HTMLResponse(render_dashboard_html())

@app.get("/audit-report", response_class=HTMLResponse)
def audit_report():
    """Serves the comprehensive Data Quality & Dead Letter Queue (DLQ) Audit Report."""
    return HTMLResponse(generate_audit_report_html())

@app.get("/health")
def health_check():
    """Liveness probe: verifies service process is running."""
    return {
        "status": "healthy",
        "service": "LedgerFlow Banking Platform",
        "auth_enabled": app_config.API_AUTH_ENABLED,
        "demo_mode": app_config.DEMO_MODE
    }

@app.get("/health/ready")
def readiness_check():
    """Readiness probe: validates database connectivity and warehouse operational status."""
    conn = get_db()
    db_connected = False
    table_counts = {}
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT 1;")
            db_connected = True
            for tbl in ["customers", "accounts", "transactions"]:
                try:
                    cur.execute(f"SELECT COUNT(*) FROM {tbl};")
                    table_counts[tbl] = cur.fetchone()["count"]
                except Exception:
                    pass
            cur.close()
            conn.close()
        except Exception:
            db_connected = False

    latest_summary = None
    summary_path = os.path.join(app_config.LOGS_DIR, "latest_pipeline_run.json")
    if os.path.exists(summary_path):
        try:
            import json
            with open(summary_path, "r", encoding="utf-8") as f:
                latest_summary = json.load(f)
        except Exception:
            pass

    return {
        "status": "ready" if (db_connected or app_config.DEMO_MODE) else "degraded",
        "database_connected": db_connected,
        "mode": "live_warehouse" if db_connected else ("demo_mode" if app_config.DEMO_MODE else "disconnected"),
        "table_counts": table_counts,
        "latest_pipeline_run": latest_summary,
        "cloud_lakehouse": {
            "provider": "AWS",
            "region": app_config.AWS_DEFAULT_REGION,
            "s3_bucket": app_config.S3_BUCKET_NAME
        }
    }

@app.get("/customers")
def get_customers(
    limit: int = Query(50, ge=1, le=200, description="Page size limit (1 to 200)"),
    offset: int = Query(0, ge=0, description="Offset index"),
    city: Optional[str] = Query(None, max_length=100),
    user_context: dict = Depends(require_role("read_only"))
):
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor()
            query = "SELECT customer_id, name, gender, city, state, email, occupation, annual_income, credit_score, join_date FROM customers WHERE 1=1"
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
            return {"total": len(rows), "data": rows, "source": "live_postgres", "limit": limit, "offset": offset}
        except Exception as e:
            handle_db_error(str(e))
    else:
        handle_db_error("PostgreSQL connection unavailable")

    # Demo fallback only reached if DEMO_MODE=True
    filtered = DEMO_CUSTOMERS
    if city:
        filtered = [c for c in filtered if c["city"].lower() == city.lower()]
    sliced = filtered[offset : offset + limit]
    return {"total": len(sliced), "data": sliced, "source": "demo_mode_cache", "limit": limit, "offset": offset}

@app.get("/customer/{customer_id}")
def get_customer_detail(
    customer_id: int,
    user_context: dict = Depends(require_role("read_only"))
):
    if customer_id <= 0:
        raise HTTPException(status_code=400, detail="Invalid customer_id. Must be positive integer.")

    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM customers WHERE customer_id = %s", (customer_id,))
            customer = cursor.fetchone()
            if not customer:
                cursor.close()
                conn.close()
                raise HTTPException(status_code=404, detail=f"Customer #{customer_id} not found.")

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
        except HTTPException:
            raise
        except Exception as e:
            handle_db_error(str(e))
    else:
        handle_db_error("PostgreSQL connection unavailable")

    cust = next((c for c in DEMO_CUSTOMERS if c["customer_id"] == customer_id), None)
    if not cust:
        raise HTTPException(status_code=404, detail=f"Customer #{customer_id} not found in demo data.")
    accs = [a for a in DEMO_ACCOUNTS if a["customer_id"] == cust["customer_id"]]
    lns = [l for l in DEMO_LOANS if l["customer_id"] == cust["customer_id"]]
    crds = [cd for cd in DEMO_CARDS if cd["customer_id"] == cust["customer_id"]]
    c360 = next((c for c in DEMO_C360 if c["customer_id"] == cust["customer_id"]), None)

    return {
        "customer": cust,
        "customer_360": c360,
        "accounts": accs,
        "loans": lns,
        "cards": crds,
        "source": "demo_mode_cache"
    }

@app.get("/accounts")
def get_accounts(
    customer_id: Optional[int] = Query(None, gt=0),
    account_type: Optional[str] = Query(None, max_length=50),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user_context: dict = Depends(require_role("read_only"))
):
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
            query += " ORDER BY account_id LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            cursor.execute(query, params)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            return {"total": len(rows), "data": rows, "source": "live_postgres", "limit": limit, "offset": offset}
        except Exception as e:
            handle_db_error(str(e))
    else:
        handle_db_error("PostgreSQL connection unavailable")

    filtered = DEMO_ACCOUNTS
    if customer_id:
        filtered = [a for a in filtered if a["customer_id"] == customer_id]
    if account_type:
        filtered = [a for a in filtered if a["account_type"].lower() == account_type.lower()]
    sliced = filtered[offset : offset + limit]
    return {"total": len(sliced), "data": sliced, "source": "demo_mode_cache", "limit": limit, "offset": offset}

@app.get("/transactions")
def get_transactions(
    account_id: Optional[int] = Query(None, gt=0),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user_context: dict = Depends(require_role("read_only"))
):
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor()
            query = "SELECT * FROM transactions WHERE 1=1"
            params = []
            if account_id:
                query += " AND account_id = %s"
                params.append(account_id)
            query += " ORDER BY txn_date DESC, transaction_id DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            cursor.execute(query, params)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            return {"total": len(rows), "data": rows, "source": "live_postgres", "limit": limit, "offset": offset}
        except Exception as e:
            handle_db_error(str(e))
    else:
        handle_db_error("PostgreSQL connection unavailable")

    filtered = DEMO_TRANSACTIONS
    if account_id:
        filtered = [t for t in filtered if t["account_id"] == account_id]
    sliced = filtered[offset : offset + limit]
    return {"total": len(sliced), "data": sliced, "source": "demo_mode_cache", "limit": limit, "offset": offset}

@app.get("/loans")
def get_loans(
    customer_id: Optional[int] = Query(None, gt=0),
    status: Optional[str] = Query(None, max_length=50),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user_context: dict = Depends(require_role("read_only"))
):
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
            query += " ORDER BY loan_id LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            cursor.execute(query, params)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            return {"total": len(rows), "data": rows, "source": "live_postgres", "limit": limit, "offset": offset}
        except Exception as e:
            handle_db_error(str(e))
    else:
        handle_db_error("PostgreSQL connection unavailable")

    filtered = DEMO_LOANS
    if customer_id:
        filtered = [l for l in filtered if l["customer_id"] == customer_id]
    if status:
        filtered = [l for l in filtered if l["status"].lower() == status.lower()]
    sliced = filtered[offset : offset + limit]
    return {"total": len(sliced), "data": sliced, "source": "demo_mode_cache", "limit": limit, "offset": offset}

@app.get("/cards")
def get_cards(
    customer_id: Optional[int] = Query(None, gt=0),
    card_type: Optional[str] = Query(None, max_length=50),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user_context: dict = Depends(require_role("read_only"))
):
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor()
            query = "SELECT * FROM cards WHERE 1=1"
            params = []
            if customer_id:
                query += " AND customer_id = %s"
                params.append(customer_id)
            if card_type:
                query += " AND LOWER(card_type) = LOWER(%s)"
                params.append(card_type)
            query += " ORDER BY card_id LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            cursor.execute(query, params)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            return {"total": len(rows), "data": rows, "source": "live_postgres", "limit": limit, "offset": offset}
        except Exception as e:
            handle_db_error(str(e))
    else:
        handle_db_error("PostgreSQL connection unavailable")

    filtered = DEMO_CARDS
    if customer_id:
        filtered = [c for c in filtered if c["customer_id"] == customer_id]
    if card_type:
        filtered = [c for c in filtered if c["card_type"].lower() == card_type.lower()]
    sliced = filtered[offset : offset + limit]
    return {"total": len(sliced), "data": sliced, "source": "demo_mode_cache", "limit": limit, "offset": offset}

@app.get("/customer-360")
def get_customer_360(
    segment: Optional[str] = Query(None, max_length=100),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user_context: dict = Depends(require_role("analyst"))
):
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor()
            query = "SELECT * FROM customer_360 WHERE 1=1"
            params = []
            if segment:
                query += " AND customer_segment ILIKE %s"
                params.append(f"%{segment}%")
            query += " ORDER BY total_deposit_balance DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            cursor.execute(query, params)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            return {"total": len(rows), "data": rows, "source": "live_postgres", "limit": limit, "offset": offset}
        except Exception as e:
            handle_db_error(str(e))
    else:
        handle_db_error("PostgreSQL connection unavailable")

    filtered = DEMO_C360
    if segment:
        filtered = [c for c in filtered if segment.lower() in c["customer_segment"].lower()]
    sliced = filtered[offset : offset + limit]
    return {"total": len(sliced), "data": sliced, "source": "demo_mode_cache", "limit": limit, "offset": offset}

@app.get("/dashboard")
def get_dashboard_summary(
    user_context: dict = Depends(require_role("analyst"))
):
    """Returns executive dashboard KPIs across the warehouse."""
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
            if kpis and (kpis.get("total_accounts") or 0) > 0:
                return {
                    "kpis": kpis,
                    "customer_segments": segments or DEMO_SEGMENTS,
                    "source": "live_postgres"
                }
        except Exception as e:
            handle_db_error(str(e))
    else:
        handle_db_error("PostgreSQL connection unavailable")

    return {
        "kpis": DEMO_KPIS,
        "customer_segments": DEMO_SEGMENTS,
        "source": "demo_mode_cache"
    }
