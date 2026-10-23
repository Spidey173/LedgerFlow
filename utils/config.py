import os
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

# Root directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")
CURATED_DIR = os.path.join(DATA_DIR, "curated")
BAD_RECORDS_DIR = os.path.join(DATA_DIR, "bad_records")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# AWS Configuration
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION", "ap-south-1")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "ledgerflow-banking-511492912610")

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_NAME = os.getenv("DB_NAME", "bank_dwh")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

# API Security & Operations
# Comma-separated list of allowed origins. Defaults to local UI/API origins if not provided.
_default_origins = "http://localhost:3000,http://localhost:8000,http://127.0.0.1:8000,https://ledgerflow17.vercel.app"
raw_origins = os.getenv("ALLOWED_ORIGINS", _default_origins).strip()
ALLOWED_ORIGINS = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]

# API Authentication & RBAC
# API_AUTH_ENABLED: when True, all data-serving endpoints require valid Bearer token
API_AUTH_ENABLED = os.getenv("API_AUTH_ENABLED", "false").lower() in ("true", "1", "yes")

# API_KEYS parsed into a mapping of {token: role}
# Supported roles: 'admin', 'analyst', 'read_only'
API_KEYS = {}
_raw_keys = os.getenv("API_KEYS", "")
if _raw_keys:
    for entry in _raw_keys.split(","):
        if ":" in entry:
            token, role = entry.split(":", 1)
            API_KEYS[token.strip()] = role.strip().lower()
        elif entry.strip():
            API_KEYS[entry.strip()] = "read_only"

# Explicit Demo Mode: When True, endpoints can serve sanitized demo datasets
# When False (default for production), failed live queries return HTTP 503 instead of masking errors
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() in ("true", "1", "yes")

# Secret Decryption Key (for encrypted zip ingestion)
ZIP_DECRYPTION_PASSWORD = os.getenv("ZIP_DECRYPTION_PASSWORD", "")

def validate_db_credentials(raise_on_missing: bool = False) -> bool:
    """Verifies that database credentials are provided before attempting connection."""
    if DATABASE_URL:
        return True
    if not DB_PASSWORD:
        if raise_on_missing:
            raise ValueError(
                "Missing required DB_PASSWORD environment variable. "
                "Set DB_PASSWORD or DATABASE_URL in your environment."
            )
        return False
    return True


# File paths
CUSTOMERS_RAW = os.path.join(RAW_DIR, "customers.csv")
CUSTOMERS_CURATED = os.path.join(CURATED_DIR, "customers.csv")
CUSTOMERS_BAD = os.path.join(BAD_RECORDS_DIR, "customers_bad.csv")

ACCOUNTS_RAW = os.path.join(RAW_DIR, "accounts.csv")
ACCOUNTS_CURATED = os.path.join(CURATED_DIR, "accounts.csv")
ACCOUNTS_BAD = os.path.join(BAD_RECORDS_DIR, "accounts_bad.csv")

TRANSACTIONS_RAW = os.path.join(RAW_DIR, "transactions.csv")
TRANSACTIONS_CURATED = os.path.join(CURATED_DIR, "transactions.csv")
TRANSACTIONS_BAD = os.path.join(BAD_RECORDS_DIR, "transactions_bad.csv")

LOANS_RAW = os.path.join(RAW_DIR, "loans.csv")
LOANS_CURATED = os.path.join(CURATED_DIR, "loans.csv")
LOANS_BAD = os.path.join(BAD_RECORDS_DIR, "loans_bad.csv")

LOAN_PAYMENTS_RAW = os.path.join(RAW_DIR, "loan_payments.csv")
LOAN_PAYMENTS_CURATED = os.path.join(CURATED_DIR, "loan_payments.csv")
LOAN_PAYMENTS_BAD = os.path.join(BAD_RECORDS_DIR, "loan_payments_bad.csv")

CARDS_RAW = os.path.join(RAW_DIR, "cards.csv")
CARDS_CURATED = os.path.join(CURATED_DIR, "cards.csv")
CARDS_BAD = os.path.join(BAD_RECORDS_DIR, "cards_bad.csv")

CARD_TRANSACTIONS_RAW = os.path.join(RAW_DIR, "card_transactions.csv")
CARD_TRANSACTIONS_CURATED = os.path.join(CURATED_DIR, "card_transactions.csv")
CARD_TRANSACTIONS_BAD = os.path.join(BAD_RECORDS_DIR, "card_transactions_bad.csv")

BRANCHES_RAW = os.path.join(RAW_DIR, "branches.csv")
BRANCHES_CURATED = os.path.join(CURATED_DIR, "branches.csv")
BRANCHES_BAD = os.path.join(BAD_RECORDS_DIR, "branches_bad.csv")

EMPLOYEES_RAW = os.path.join(RAW_DIR, "employees.csv")
EMPLOYEES_CURATED = os.path.join(CURATED_DIR, "employees.csv")
EMPLOYEES_BAD = os.path.join(BAD_RECORDS_DIR, "employees_bad.csv")

SUPPORT_TICKETS_RAW = os.path.join(RAW_DIR, "support_tickets.csv")
SUPPORT_TICKETS_CURATED = os.path.join(CURATED_DIR, "support_tickets.csv")
SUPPORT_TICKETS_BAD = os.path.join(BAD_RECORDS_DIR, "support_tickets_bad.csv")

# Validation constants
EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
CREDIT_SCORE_MIN = 300
CREDIT_SCORE_MAX = 850

VALID_ACCOUNT_TYPES = {"Savings", "Current", "Salary", "Fixed Deposit", "NRI"}
VALID_ACCOUNT_STATUSES = {"Active", "Dormant", "Closed"}

VALID_TXN_TYPES = {
    "Deposit", "Withdrawal", "Transfer Out", "Transfer In", "Fee Debit", "Interest Credit"
}
VALID_CHANNELS = {
    "Mobile App", "Branch", "ATM", "UPI", "POS", "Online Banking"
}

VALID_LOAN_TYPES = {
    "Auto Loan", "Business Loan", "Education Loan", "Gold Loan", "Home Loan", "Personal Loan"
}
VALID_LOAN_STATUSES = {"Active", "Closed", "Defaulted", "Written Off"}

VALID_CARD_TYPES = {"Debit", "Credit - Classic", "Credit - Gold", "Credit - Platinum"}
VALID_CARD_STATUSES = {"Active", "Blocked", "Expired"}

VALID_EMPLOYEE_ROLES = {
    "Teller", "Customer Service", "Relationship Manager", "Loan Officer", "Branch Manager", "Compliance Officer"
}
VALID_TICKET_STATUSES = {"Resolved", "Open", "Escalated"}
