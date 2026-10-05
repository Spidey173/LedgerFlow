import pytest
import pandas as pd
import numpy as np

from validation.customer_validation import validate_customers
from validation.branch_validation import validate_branches
from validation.account_validation import validate_accounts
from validation.employee_validation import validate_employees
from validation.loan_validation import validate_loans
from validation.loan_payment_validation import validate_loan_payments
from validation.card_validation import validate_cards
from validation.card_transaction_validation import validate_card_transactions
from validation.transaction_validation import validate_transactions
from validation.support_ticket_validation import validate_support_tickets


# ==========================================
# 1. Customer Validation Tests
# ==========================================
def test_validate_customers_valid():
    """Verify valid customer records pass successfully."""
    df = pd.DataFrame([{
        "customer_id": 101,
        "first_name": "Jane",
        "last_name": "Doe",
        "email": "jane.doe@example.com",
        "credit_score": 720,
        "annual_income": 85000.0
    }])
    good, bad = validate_customers(df)
    assert len(good) == 1
    assert len(bad) == 0


def test_validate_customers_invalid_credit_and_email():
    """Verify invalid credit score boundary and malformed email trigger rejections."""
    df = pd.DataFrame([
        {
            "customer_id": 102,
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "bad-email-format",
            "credit_score": 700,
            "annual_income": 50000.0
        },
        {
            "customer_id": 103,
            "first_name": "Bob",
            "last_name": "Brown",
            "email": "bob@example.com",
            "credit_score": 250,  # Below minimum (300)
            "annual_income": 40000.0
        }
    ])
    good, bad = validate_customers(df)
    assert len(good) == 0
    assert len(bad) == 2
    assert "Invalid Email" in bad.loc[0, "rejection_reason"]
    assert "Invalid Credit Score" in bad.loc[1, "rejection_reason"]


# ==========================================
# 2. Branch Validation Tests
# ==========================================
def test_validate_branches_valid():
    """Verify branch record with valid attributes passes validation."""
    df = pd.DataFrame([{
        "branch_id": 1,
        "branch_name": "Downtown Central",
        "city": "New York",
        "state": "NY",
        "opened_date": "2020-05-15",
        "ifsc_code": "BNK000101"
    }])
    good, bad = validate_branches(df)
    assert len(good) == 1
    assert len(bad) == 0


def test_validate_branches_missing_fields_and_duplicates():
    """Verify missing required branch fields and duplicate IDs are caught."""
    df = pd.DataFrame([
        {
            "branch_id": 2,
            "branch_name": "",
            "city": "Boston",
            "state": "MA",
            "opened_date": "2021-01-01",
            "ifsc_code": "BNK000102"
        },
        {
            "branch_id": 3,
            "branch_name": "North Branch",
            "city": "Boston",
            "state": "MA",
            "opened_date": "invalid-date",
            "ifsc_code": "BNK000103"
        }
    ])
    good, bad = validate_branches(df)
    assert len(good) == 0
    assert len(bad) == 2


# ==========================================
# 3. Account Validation Tests
# ==========================================
def test_validate_accounts_valid():
    """Verify valid account with recognized type and status passes."""
    df = pd.DataFrame([{
        "account_id": 1001,
        "customer_id": 101,
        "account_type": "Savings",
        "balance": 1500.50,
        "status": "Active"
    }])
    good, bad = validate_accounts(df, valid_customer_ids={101})
    assert len(good) == 1
    assert len(bad) == 0


def test_validate_accounts_orphan_customer():
    """Verify referential integrity failure when customer_id does not exist."""
    df = pd.DataFrame([{
        "account_id": 1002,
        "customer_id": 99999,  # Orphan
        "account_type": "Current",
        "balance": 2000.0,
        "status": "Active"
    }])
    good, bad = validate_accounts(df, valid_customer_ids={101})
    assert len(good) == 0
    assert len(bad) == 1
    assert "not found in Curated Customers" in bad.iloc[0]["rejection_reason"]


def test_validate_accounts_negative_balance_and_invalid_type():
    """Verify negative balance and unapproved account types are rejected."""
    df = pd.DataFrame([
        {
            "account_id": 1003,
            "customer_id": 101,
            "account_type": "CryptoWallet",  # Invalid type
            "balance": 500.0,
            "status": "Active"
        },
        {
            "account_id": 1004,
            "customer_id": 101,
            "account_type": "Savings",
            "balance": -50.0,  # Negative balance
            "status": "Active"
        }
    ])
    good, bad = validate_accounts(df, valid_customer_ids={101})
    assert len(good) == 0
    assert len(bad) == 2


# ==========================================
# 4. Employee Validation Tests
# ==========================================
def test_validate_employees_valid():
    """Verify valid employee record attached to curated branch passes."""
    df = pd.DataFrame([{
        "employee_id": 501,
        "branch_id": 1,
        "role": "Loan Officer",
        "salary": 75000.0,
        "hire_date": "2022-03-01"
    }])
    good, bad = validate_employees(df, valid_branch_ids={1})
    assert len(good) == 1
    assert len(bad) == 0


def test_validate_employees_invalid_role_and_salary():
    """Verify invalid role or non-positive salary are flagged."""
    df = pd.DataFrame([
        {
            "employee_id": 502,
            "branch_id": 1,
            "role": "Astronaut",  # Invalid role
            "salary": 60000.0,
            "hire_date": "2023-01-01"
        },
        {
            "employee_id": 503,
            "branch_id": 1,
            "role": "Teller",
            "salary": -100.0,  # Non-positive salary
            "hire_date": "2023-01-01"
        }
    ])
    good, bad = validate_employees(df, valid_branch_ids={1})
    assert len(good) == 0
    assert len(bad) == 2


# ==========================================
# 5. Transaction Validation Tests
# ==========================================
def test_validate_transactions_valid():
    """Verify valid deposit transaction passes validation."""
    df = pd.DataFrame([{
        "transaction_id": 5001,
        "account_id": 1001,
        "amount": 250.0,
        "txn_type": "Deposit",
        "channel": "Mobile App",
        "txn_date": "2026-03-10"
    }])
    good, bad = validate_transactions(df, valid_account_ids={1001})
    assert len(good) == 1
    assert len(bad) == 0


def test_validate_transactions_negative_amount_and_orphan():
    """Verify non-positive amount and orphan account_id are rejected."""
    df = pd.DataFrame([
        {
            "transaction_id": 5002,
            "account_id": 1001,
            "amount": -50.0,  # <= 0
            "txn_type": "Withdrawal",
            "channel": "ATM",
            "txn_date": "2026-03-11"
        },
        {
            "transaction_id": 5003,
            "account_id": 8888,  # Orphan
            "amount": 100.0,
            "txn_type": "Deposit",
            "channel": "ATM",
            "txn_date": "2026-03-11"
        }
    ])
    good, bad = validate_transactions(df, valid_account_ids={1001})
    assert len(good) == 0
    assert len(bad) == 2


# ==========================================
# 6. Loan Validation Tests
# ==========================================
def test_validate_loans_valid():
    """Verify valid loan record passes validation."""
    df = pd.DataFrame([{
        "loan_id": 201,
        "customer_id": 101,
        "loan_amount": 250000.0,
        "interest_rate": 6.5,
        "term_months": 180,
        "loan_type": "Home Loan",
        "status": "Active",
        "start_date": "2024-01-10"
    }])
    good, bad = validate_loans(df, valid_customer_ids={101})
    assert len(good) == 1
    assert len(bad) == 0


def test_validate_loans_rate_and_term_bounds():
    """Verify interest rate out-of-bounds (>50) or negative term is caught."""
    df = pd.DataFrame([
        {
            "loan_id": 202,
            "customer_id": 101,
            "loan_amount": 10000.0,
            "interest_rate": 95.0,  # Exceeds max 50%
            "term_months": 12,
            "loan_type": "Personal Loan",
            "status": "Active",
            "start_date": "2024-01-10"
        },
        {
            "loan_id": 203,
            "customer_id": 101,
            "loan_amount": 10000.0,
            "interest_rate": 8.0,
            "term_months": -5,  # Non-positive term
            "loan_type": "Personal Loan",
            "status": "Active",
            "start_date": "2024-01-10"
        }
    ])
    good, bad = validate_loans(df, valid_customer_ids={101})
    assert len(good) == 0
    assert len(bad) == 2


# ==========================================
# 7. Loan Payment Validation Tests
# ==========================================
def test_validate_loan_payments_valid():
    """Verify valid payment where principal + interest matches amount_paid."""
    df = pd.DataFrame([{
        "payment_id": 801,
        "loan_id": 201,
        "amount_paid": 500.0,
        "principal_component": 350.0,
        "interest_component": 150.0,
        "late_payment_flag": 0,
        "payment_date": "2024-02-10"
    }])
    good, bad = validate_loan_payments(df, valid_loan_ids={201})
    assert len(good) == 1
    assert len(bad) == 0


def test_validate_loan_payments_mismatched_components():
    """Verify rejection when principal + interest does not equal amount_paid."""
    df = pd.DataFrame([{
        "payment_id": 802,
        "loan_id": 201,
        "amount_paid": 500.0,
        "principal_component": 200.0,
        "interest_component": 100.0,  # Sum = 300 != 500
        "late_payment_flag": 0,
        "payment_date": "2024-02-10"
    }])
    good, bad = validate_loan_payments(df, valid_loan_ids={201})
    assert len(good) == 0
    assert len(bad) == 1


# ==========================================
# 8. Card Validation Tests
# ==========================================
def test_validate_cards_valid():
    """Verify valid card passes validation."""
    df = pd.DataFrame([{
        "card_id": 301,
        "customer_id": 101,
        "account_id": 1001,
        "card_type": "Credit - Platinum",
        "status": "Active",
        "issue_date": "2023-01-01",
        "expiry_date": "2028-01-01",
        "credit_limit": 10000.0
    }])
    good, bad = validate_cards(df, valid_customer_ids={101}, valid_account_ids={1001})
    assert len(good) == 1
    assert len(bad) == 0


def test_validate_cards_expiry_before_issue():
    """Verify cards with expiry date earlier than issue date are rejected."""
    df = pd.DataFrame([{
        "card_id": 302,
        "customer_id": 101,
        "account_id": 1001,
        "card_type": "Debit",
        "status": "Active",
        "issue_date": "2025-01-01",
        "expiry_date": "2022-01-01",  # Before issue date
        "credit_limit": 0.0
    }])
    good, bad = validate_cards(df, valid_customer_ids={101}, valid_account_ids={1001})
    assert len(good) == 0
    assert len(bad) == 1


# ==========================================
# 9. Card Transactions Validation Tests
# ==========================================
def test_validate_card_transactions_valid():
    """Verify valid card transaction passes validation."""
    df = pd.DataFrame([{
        "card_txn_id": 7001,
        "card_id": 301,
        "amount": 42.50,
        "merchant_category": "Groceries",
        "txn_date": "2024-03-01 14:30:00",
        "is_fraud": 0
    }])
    good, bad = validate_card_transactions(df, valid_card_ids={301})
    assert len(good) == 1
    assert len(bad) == 0


def test_validate_card_transactions_invalid_fraud_flag():
    """Verify non-binary fraud flags are rejected."""
    df = pd.DataFrame([{
        "card_txn_id": 7002,
        "card_id": 301,
        "amount": 99.0,
        "merchant_category": "Electronics",
        "txn_date": "2024-03-01 14:35:00",
        "is_fraud": 5  # Must be 0 or 1
    }])
    good, bad = validate_card_transactions(df, valid_card_ids={301})
    assert len(good) == 0
    assert len(bad) == 1


# ==========================================
# 10. Support Ticket Validation Tests
# ==========================================
def test_validate_support_tickets_valid():
    """Verify valid support ticket record passes validation."""
    df = pd.DataFrame([{
        "ticket_id": 901,
        "customer_id": 101,
        "issue_type": "Billing Inquiry",
        "status": "Resolved",
        "date_opened": "2025-02-01",
        "date_resolved": "2025-02-03",
        "satisfaction_score": 4
    }])
    good, bad = validate_support_tickets(df, valid_customer_ids={101})
    assert len(good) == 1
    assert len(bad) == 0


def test_validate_support_tickets_chronology_and_score():
    """Verify chronology error (resolved before opened) and invalid satisfaction score."""
    df = pd.DataFrame([
        {
            "ticket_id": 902,
            "customer_id": 101,
            "issue_type": "Card Replacement",
            "status": "Resolved",
            "date_opened": "2025-02-10",
            "date_resolved": "2025-02-05",  # Before date_opened
            "satisfaction_score": 5
        },
        {
            "ticket_id": 903,
            "customer_id": 101,
            "issue_type": "Login Issue",
            "status": "Open",
            "date_opened": "2025-02-10",
            "date_resolved": np.nan,
            "satisfaction_score": 10  # Out of range 1..5
        }
    ])
    good, bad = validate_support_tickets(df, valid_customer_ids={101})
    assert len(good) == 0
    assert len(bad) == 2


# ==========================================
# 11. Additional Customer Tests (Boundaries & PKs)
# ==========================================
def test_validate_customers_duplicate_and_missing_id():
    """Verify missing Customer ID and duplicate Customer IDs are quarantined."""
    df = pd.DataFrame([
        {
            "customer_id": np.nan,
            "first_name": "Ghost",
            "last_name": "User",
            "email": "ghost@example.com",
            "credit_score": 750,
            "annual_income": 60000.0,
        },
        {
            "customer_id": 105,
            "first_name": "First",
            "last_name": "Clone",
            "email": "first@example.com",
            "credit_score": 700,
            "annual_income": 70000.0,
        },
        {
            "customer_id": 105,
            "first_name": "Second",
            "last_name": "Clone",
            "email": "second@example.com",
            "credit_score": 710,
            "annual_income": 72000.0,
        },
    ])
    good, bad = validate_customers(df)
    assert len(good) == 0
    assert len(bad) == 3
    reasons = bad["rejection_reason"].tolist()
    stages = bad["validation_stage"].tolist()
    assert any("Missing Customer ID" in r for r in reasons)
    assert any("Duplicate Customer ID" in r for r in reasons)
    assert any("Schema Integrity" in s for s in stages)
    assert any("Primary Key Constraint" in s for s in stages)


def test_validate_customers_credit_score_boundaries_and_negative_income():
    """Verify exact min/max credit score boundaries (300, 850) and reject non-positive income."""
    # Valid boundaries
    df_valid = pd.DataFrame([
        {"customer_id": 201, "first_name": "Min", "last_name": "Score", "email": "min@example.com", "credit_score": 300, "annual_income": 30000.0},
        {"customer_id": 202, "first_name": "Max", "last_name": "Score", "email": "max@example.com", "credit_score": 850, "annual_income": 120000.0},
    ])
    good_v, bad_v = validate_customers(df_valid)
    assert len(good_v) == 2
    assert len(bad_v) == 0

    # Invalid boundary + non-positive income
    df_invalid = pd.DataFrame([
        {"customer_id": 203, "first_name": "Under", "last_name": "Score", "email": "u@example.com", "credit_score": 299, "annual_income": 50000.0},
        {"customer_id": 204, "first_name": "Over", "last_name": "Score", "email": "o@example.com", "credit_score": 851, "annual_income": 50000.0},
        {"customer_id": 205, "first_name": "Zero", "last_name": "Income", "email": "z@example.com", "credit_score": 720, "annual_income": 0.0},
        {"customer_id": 206, "first_name": "Negative", "last_name": "Income", "email": "n@example.com", "credit_score": 720, "annual_income": -5000.0},
    ])
    good_inv, bad_inv = validate_customers(df_invalid)
    assert len(good_inv) == 0
    assert len(bad_inv) == 4
    assert all("Domain Boundary Check" in s for s in bad_inv["validation_stage"])


# ==========================================
# 12. Additional Branch Tests (IFSC & Duplicates)
# ==========================================
def test_validate_branches_missing_ifsc_and_blank_names():
    """Verify branches with missing IFSC code or blank branch_name are rejected."""
    df = pd.DataFrame([
        {
            "branch_id": 11,
            "branch_name": "Westside Branch",
            "city": "Chicago",
            "state": "IL",
            "opened_date": "2021-06-01",
            "ifsc_code": "",  # Missing IFSC
        },
        {
            "branch_id": 12,
            "branch_name": "   ",  # Blank name
            "city": "Chicago",
            "state": "IL",
            "opened_date": "2021-06-01",
            "ifsc_code": "BNK000112",
        },
    ])
    good, bad = validate_branches(df)
    assert len(good) == 0
    assert len(bad) == 2
    assert "Missing IFSC Code" in bad.loc[0, "rejection_reason"]
    assert "Missing Branch Name" in bad.loc[1, "rejection_reason"]


def test_validate_branches_duplicate_ids():
    """Verify duplicate branch IDs are caught and attributed to Primary Key Constraint."""
    df = pd.DataFrame([
        {"branch_id": 20, "branch_name": "Alpha", "city": "Dallas", "state": "TX", "opened_date": "2020-01-01", "ifsc_code": "BNK000020"},
        {"branch_id": 20, "branch_name": "Beta", "city": "Austin", "state": "TX", "opened_date": "2020-01-01", "ifsc_code": "BNK000021"},
    ])
    good, bad = validate_branches(df)
    assert len(good) == 0
    assert len(bad) == 2
    assert all("Duplicate Branch ID" in r for r in bad["rejection_reason"])
    assert all("Primary Key Constraint" in s for s in bad["validation_stage"])


# ==========================================
# 13. Additional Account Tests (Case & Zero Balance)
# ==========================================
def test_validate_accounts_case_insensitive_types_and_zero_balance():
    """Verify case-insensitive account types and zero balances (valid initial balance) pass."""
    df = pd.DataFrame([
        {"account_id": 2001, "customer_id": 101, "account_type": "savings", "balance": 0.0, "status": "Active"},
        {"account_id": 2002, "customer_id": 101, "account_type": "CURRENT", "balance": 100.0, "status": "active"},
        {"account_id": 2003, "customer_id": 101, "account_type": "Fixed Deposit", "balance": 50000.0, "status": "Dormant"},
    ])
    good, bad = validate_accounts(df, valid_customer_ids={101})
    assert len(good) == 3
    assert len(bad) == 0


def test_validate_accounts_missing_id_and_duplicate_id():
    """Verify missing account_id and duplicate account_id are quarantined."""
    df = pd.DataFrame([
        {"account_id": "", "customer_id": 101, "account_type": "Savings", "balance": 500.0, "status": "Active"},
        {"account_id": 3001, "customer_id": 101, "account_type": "Savings", "balance": 500.0, "status": "Active"},
        {"account_id": 3001, "customer_id": 101, "account_type": "Savings", "balance": 600.0, "status": "Active"},
    ])
    good, bad = validate_accounts(df, valid_customer_ids={101})
    assert len(good) == 0
    assert len(bad) == 3
    assert any("Missing Account ID" in r for r in bad["rejection_reason"])
    assert any("Duplicate Account ID" in r for r in bad["rejection_reason"])


# ==========================================
# 14. Additional Employee Tests (Roles & Salaries)
# ==========================================
def test_validate_employees_role_case_insensitivity_and_orphan_branch():
    """Verify employee role case insensitivity and branch referential integrity."""
    df_valid = pd.DataFrame([
        {"employee_id": 601, "branch_id": 1, "role": "branch manager", "salary": 95000.0, "hire_date": "2020-01-15"},
        {"employee_id": 602, "branch_id": 1, "role": "TELLER", "salary": 45000.0, "hire_date": "2021-05-10"},
    ])
    good_v, bad_v = validate_employees(df_valid, valid_branch_ids={1})
    assert len(good_v) == 2
    assert len(bad_v) == 0

    df_orphan = pd.DataFrame([{
        "employee_id": 603,
        "branch_id": 9999,  # Orphan
        "role": "Teller",
        "salary": 50000.0,
        "hire_date": "2021-01-01"
    }])
    good_o, bad_o = validate_employees(df_orphan, valid_branch_ids={1})
    assert len(good_o) == 0
    assert len(bad_o) == 1
    assert "not found in Curated Branches" in bad_o.iloc[0]["rejection_reason"]


def test_validate_employees_salary_boundaries_and_invalid_date():
    """Verify zero salary, invalid hire date, and duplicate employee_ids are caught."""
    df = pd.DataFrame([
        {"employee_id": 701, "branch_id": 1, "role": "Teller", "salary": 0.0, "hire_date": "2022-01-01"},
        {"employee_id": 702, "branch_id": 1, "role": "Teller", "salary": 50000.0, "hire_date": "2022-99-99"},
        {"employee_id": 703, "branch_id": 1, "role": "Teller", "salary": 50000.0, "hire_date": "2022-01-01"},
        {"employee_id": 703, "branch_id": 1, "role": "Teller", "salary": 52000.0, "hire_date": "2022-01-01"},
    ])
    good, bad = validate_employees(df, valid_branch_ids={1})
    assert len(good) == 0
    assert len(bad) == 4
    assert any("Invalid Salary" in r for r in bad["rejection_reason"])
    assert any("Invalid Hire Date" in r for r in bad["rejection_reason"])
    assert any("Duplicate Employee ID" in r for r in bad["rejection_reason"])


# ==========================================
# 15. Additional Transaction Tests (Zeros & Formats)
# ==========================================
def test_validate_transactions_zero_amount_and_duplicate_id():
    """Verify zero transaction amount and duplicate transaction IDs are rejected."""
    df = pd.DataFrame([
        {"transaction_id": 6001, "account_id": 1001, "amount": 0.0, "txn_type": "Deposit", "channel": "ATM", "txn_date": "2026-03-01"},
        {"transaction_id": 6002, "account_id": 1001, "amount": 100.0, "txn_type": "Deposit", "channel": "ATM", "txn_date": "2026-03-01"},
        {"transaction_id": 6002, "account_id": 1001, "amount": 200.0, "txn_type": "Deposit", "channel": "ATM", "txn_date": "2026-03-01"},
    ])
    good, bad = validate_transactions(df, valid_account_ids={1001})
    assert len(good) == 0
    assert len(bad) == 3
    assert any("Invalid Transaction Amount" in r for r in bad["rejection_reason"])
    assert any("Duplicate Transaction ID" in r for r in bad["rejection_reason"])


def test_validate_transactions_channel_and_type_case_insensitivity_and_bad_date():
    """Verify channel and type case insensitivity, and invalid date rejection."""
    df_valid = pd.DataFrame([{
        "transaction_id": 6003,
        "account_id": 1001,
        "amount": 75.0,
        "txn_type": "transfer in",
        "channel": "online banking",
        "txn_date": "2026-03-12 10:00:00"
    }])
    good_v, bad_v = validate_transactions(df_valid, valid_account_ids={1001})
    assert len(good_v) == 1
    assert len(bad_v) == 0

    df_invalid = pd.DataFrame([
        {"transaction_id": 6004, "account_id": 1001, "amount": 50.0, "txn_type": "Crypto Swap", "channel": "ATM", "txn_date": "2026-03-12"},
        {"transaction_id": 6005, "account_id": 1001, "amount": 50.0, "txn_type": "Deposit", "channel": "ATM", "txn_date": "invalid-date-format"},
    ])
    good_inv, bad_inv = validate_transactions(df_invalid, valid_account_ids={1001})
    assert len(good_inv) == 0
    assert len(bad_inv) == 2
    assert "Invalid Transaction Type" in bad_inv.loc[0, "rejection_reason"]
    assert "Invalid Date format" in bad_inv.loc[1, "rejection_reason"]


# ==========================================
# 16. Additional Loan Tests (Boundaries & Status)
# ==========================================
def test_validate_loans_interest_rate_boundaries():
    """Verify loan interest rate boundary conditions (1.0% to 50.0%)."""
    df_valid = pd.DataFrame([
        {"loan_id": 210, "customer_id": 101, "loan_amount": 50000.0, "interest_rate": 1.0, "term_months": 36, "loan_type": "Personal Loan", "status": "Active", "start_date": "2024-01-01"},
        {"loan_id": 211, "customer_id": 101, "loan_amount": 50000.0, "interest_rate": 50.0, "term_months": 36, "loan_type": "Personal Loan", "status": "Active", "start_date": "2024-01-01"},
    ])
    good_v, bad_v = validate_loans(df_valid, valid_customer_ids={101})
    assert len(good_v) == 2
    assert len(bad_v) == 0

    df_invalid = pd.DataFrame([
        {"loan_id": 212, "customer_id": 101, "loan_amount": 50000.0, "interest_rate": 0.0, "term_months": 36, "loan_type": "Personal Loan", "status": "Active", "start_date": "2024-01-01"},
        {"loan_id": 213, "customer_id": 101, "loan_amount": 50000.0, "interest_rate": 50.1, "term_months": 36, "loan_type": "Personal Loan", "status": "Active", "start_date": "2024-01-01"},
    ])
    good_inv, bad_inv = validate_loans(df_invalid, valid_customer_ids={101})
    assert len(good_inv) == 0
    assert len(bad_inv) == 2
    assert all("Invalid Interest Rate" in r for r in bad_inv["rejection_reason"])


def test_validate_loans_zero_term_and_invalid_status():
    """Verify zero term months, zero loan amount, and unapproved status are rejected."""
    df = pd.DataFrame([
        {"loan_id": 214, "customer_id": 101, "loan_amount": 0.0, "interest_rate": 8.0, "term_months": 24, "loan_type": "Auto Loan", "status": "Active", "start_date": "2024-01-01"},
        {"loan_id": 215, "customer_id": 101, "loan_amount": 15000.0, "interest_rate": 8.0, "term_months": 0, "loan_type": "Auto Loan", "status": "Active", "start_date": "2024-01-01"},
        {"loan_id": 216, "customer_id": 101, "loan_amount": 15000.0, "interest_rate": 8.0, "term_months": 24, "loan_type": "Auto Loan", "status": "Under Review", "start_date": "2024-01-01"},
    ])
    good, bad = validate_loans(df, valid_customer_ids={101})
    assert len(good) == 0
    assert len(bad) == 3
    assert any("Invalid Loan Amount" in r for r in bad["rejection_reason"])
    assert any("Invalid Term Months" in r for r in bad["rejection_reason"])
    assert any("Invalid Loan Status" in r for r in bad["rejection_reason"])


# ==========================================
# 17. Additional Loan Payment Tests (Tolerance & Components)
# ==========================================
def test_validate_loan_payments_rounding_tolerance():
    """Verify 5-cent accounting rounding tolerance for loan payment reconciliation."""
    # Difference = |(300.02 + 100.00) - 400.00| = 0.02 <= 0.05 (Valid)
    df_valid = pd.DataFrame([{
        "payment_id": 810,
        "loan_id": 201,
        "amount_paid": 400.0,
        "principal_component": 300.02,
        "interest_component": 100.00,
        "late_payment_flag": 0,
        "payment_date": "2024-03-01"
    }])
    good_v, bad_v = validate_loan_payments(df_valid, valid_loan_ids={201})
    assert len(good_v) == 1
    assert len(bad_v) == 0

    # Difference = |(300.00 + 100.00) - 400.10| = 0.10 > 0.05 (Invalid)
    df_invalid = pd.DataFrame([{
        "payment_id": 811,
        "loan_id": 201,
        "amount_paid": 400.10,
        "principal_component": 300.00,
        "interest_component": 100.00,
        "late_payment_flag": 0,
        "payment_date": "2024-03-01"
    }])
    good_inv, bad_inv = validate_loan_payments(df_invalid, valid_loan_ids={201})
    assert len(good_inv) == 0
    assert len(bad_inv) == 1
    assert "Principal and Interest components do not balance" in bad_inv.iloc[0]["rejection_reason"]


def test_validate_loan_payments_negative_components_and_orphan():
    """Verify negative principal/interest, orphan loan IDs, and duplicates are rejected."""
    df = pd.DataFrame([
        {
            "payment_id": 812,
            "loan_id": 201,
            "amount_paid": 100.0,
            "principal_component": -20.0,
            "interest_component": 120.0,
            "late_payment_flag": 0,
            "payment_date": "2024-03-01"
        },
        {
            "payment_id": 813,
            "loan_id": 99999,  # Orphan loan
            "amount_paid": 100.0,
            "principal_component": 80.0,
            "interest_component": 20.0,
            "late_payment_flag": 0,
            "payment_date": "2024-03-01"
        },
        {
            "payment_id": 814,
            "loan_id": 201,
            "amount_paid": 100.0,
            "principal_component": 80.0,
            "interest_component": 20.0,
            "late_payment_flag": 0,
            "payment_date": "2024-03-01"
        },
        {
            "payment_id": 814,  # Duplicate
            "loan_id": 201,
            "amount_paid": 100.0,
            "principal_component": 80.0,
            "interest_component": 20.0,
            "late_payment_flag": 0,
            "payment_date": "2024-03-01"
        },
    ])
    good, bad = validate_loan_payments(df, valid_loan_ids={201})
    assert len(good) == 0
    assert len(bad) == 4
    assert any("Principal and Interest components do not balance" in r for r in bad["rejection_reason"])
    assert any("not found in Curated Loans" in r for r in bad["rejection_reason"])
    assert any("Duplicate Payment ID" in r for r in bad["rejection_reason"])


# ==========================================
# 18. Additional Card Tests (Dual FK & Expiry)
# ==========================================
def test_validate_cards_dual_referential_integrity():
    """Verify dual foreign key referential integrity (customer_id AND account_id)."""
    df = pd.DataFrame([
        {
            "card_id": 310,
            "customer_id": 101,
            "account_id": 9999,  # Orphan account
            "card_type": "Debit",
            "status": "Active",
            "issue_date": "2023-01-01",
            "expiry_date": "2028-01-01",
            "credit_limit": 0.0
        },
        {
            "card_id": 311,
            "customer_id": 8888,  # Orphan customer
            "account_id": 1001,
            "card_type": "Debit",
            "status": "Active",
            "issue_date": "2023-01-01",
            "expiry_date": "2028-01-01",
            "credit_limit": 0.0
        }
    ])
    good, bad = validate_cards(df, valid_customer_ids={101}, valid_account_ids={1001})
    assert len(good) == 0
    assert len(bad) == 2
    assert "Account ID 9999 not found in Curated Accounts" in bad.loc[0, "rejection_reason"]
    assert "Customer ID 8888 not found in Curated Customers" in bad.loc[1, "rejection_reason"]


def test_validate_cards_same_day_expiry_and_negative_limit():
    """Verify same-day expiry boundary is allowed and negative limits or duplicates are caught."""
    # Valid: expiry == issue date, credit_limit == 0.0
    df_valid = pd.DataFrame([{
        "card_id": 312,
        "customer_id": 101,
        "account_id": 1001,
        "card_type": "Debit",
        "status": "Active",
        "issue_date": "2024-05-01",
        "expiry_date": "2024-05-01",
        "credit_limit": 0.0
    }])
    good_v, bad_v = validate_cards(df_valid, valid_customer_ids={101}, valid_account_ids={1001})
    assert len(good_v) == 1
    assert len(bad_v) == 0

    # Invalid: negative credit limit and duplicate card IDs
    df_invalid = pd.DataFrame([
        {
            "card_id": 313,
            "customer_id": 101,
            "account_id": 1001,
            "card_type": "Credit - Gold",
            "status": "Active",
            "issue_date": "2024-01-01",
            "expiry_date": "2029-01-01",
            "credit_limit": -1000.0  # Invalid
        },
        {
            "card_id": 314,
            "customer_id": 101,
            "account_id": 1001,
            "card_type": "Credit - Gold",
            "status": "Active",
            "issue_date": "2024-01-01",
            "expiry_date": "2029-01-01",
            "credit_limit": 5000.0
        },
        {
            "card_id": 314,  # Duplicate
            "customer_id": 101,
            "account_id": 1001,
            "card_type": "Credit - Gold",
            "status": "Active",
            "issue_date": "2024-01-01",
            "expiry_date": "2029-01-01",
            "credit_limit": 5000.0
        }
    ])
    good_inv, bad_inv = validate_cards(df_invalid, valid_customer_ids={101}, valid_account_ids={1001})
    assert len(good_inv) == 0
    assert len(bad_inv) == 3
    assert any("Invalid Credit Limit" in r for r in bad_inv["rejection_reason"])
    assert any("Duplicate Card ID" in r for r in bad_inv["rejection_reason"])


# ==========================================
# 19. Additional Card Transaction Tests (Merchants & Fraud)
# ==========================================
def test_validate_card_transactions_empty_merchant_and_zero_amount():
    """Verify empty merchant category, zero amount, and duplicate txn IDs are rejected."""
    df = pd.DataFrame([
        {"card_txn_id": 7010, "card_id": 301, "amount": 0.0, "merchant_category": "Dining", "txn_date": "2024-03-01 12:00:00", "is_fraud": 0},
        {"card_txn_id": 7011, "card_id": 301, "amount": 25.0, "merchant_category": "   ", "txn_date": "2024-03-01 12:00:00", "is_fraud": 0},
        {"card_txn_id": 7012, "card_id": 301, "amount": 50.0, "merchant_category": "Travel", "txn_date": "2024-03-01 12:00:00", "is_fraud": 0},
        {"card_txn_id": 7012, "card_id": 301, "amount": 50.0, "merchant_category": "Travel", "txn_date": "2024-03-01 12:00:00", "is_fraud": 0},
    ])
    good, bad = validate_card_transactions(df, valid_card_ids={301})
    assert len(good) == 0
    assert len(bad) == 4
    assert any("Invalid Transaction Amount" in r for r in bad["rejection_reason"])
    assert any("Missing Merchant Category" in r for r in bad["rejection_reason"])
    assert any("Duplicate Card Txn ID" in r for r in bad["rejection_reason"])


def test_validate_card_transactions_orphan_card_and_valid_fraud_flags():
    """Verify orphan card_id rejection and both binary fraud flags (0 and 1) are accepted."""
    # Both 0 and 1 are accepted
    df_valid = pd.DataFrame([
        {"card_txn_id": 7020, "card_id": 301, "amount": 15.0, "merchant_category": "Coffee", "txn_date": "2024-03-02 08:30:00", "is_fraud": 0},
        {"card_txn_id": 7021, "card_id": 301, "amount": 450.0, "merchant_category": "Jewelry", "txn_date": "2024-03-02 08:35:00", "is_fraud": 1},
    ])
    good_v, bad_v = validate_card_transactions(df_valid, valid_card_ids={301})
    assert len(good_v) == 2
    assert len(bad_v) == 0

    # Orphan card
    df_orphan = pd.DataFrame([{
        "card_txn_id": 7022,
        "card_id": 99999,  # Orphan card
        "amount": 20.0,
        "merchant_category": "Fast Food",
        "txn_date": "2024-03-02 09:00:00",
        "is_fraud": 0
    }])
    good_o, bad_o = validate_card_transactions(df_orphan, valid_card_ids={301})
    assert len(good_o) == 0
    assert len(bad_o) == 1
    assert "not found in Curated Cards" in bad_o.iloc[0]["rejection_reason"]


# ==========================================
# 20. Additional Support Ticket Tests (Open Tickets & Satisfaction)
# ==========================================
def test_validate_support_tickets_open_status_null_resolved_date():
    """Verify open tickets with null resolution dates and same-day resolutions are valid."""
    df = pd.DataFrame([
        {
            "ticket_id": 910,
            "customer_id": 101,
            "issue_type": "Account Lock",
            "status": "Open",
            "date_opened": "2025-03-01",
            "date_resolved": np.nan,
            "satisfaction_score": 3
        },
        {
            "ticket_id": 911,
            "customer_id": 101,
            "issue_type": "PIN Reset",
            "status": "Resolved",
            "date_opened": "2025-03-01",
            "date_resolved": "2025-03-01",  # Same-day resolved
            "satisfaction_score": 5
        }
    ])
    good, bad = validate_support_tickets(df, valid_customer_ids={101})
    assert len(good) == 2
    assert len(bad) == 0


def test_validate_support_tickets_satisfaction_score_boundaries():
    """Verify satisfaction score boundaries (1 to 5), missing issue_type, and duplicates."""
    df_valid = pd.DataFrame([
        {"ticket_id": 912, "customer_id": 101, "issue_type": "Query", "status": "Resolved", "date_opened": "2025-01-01", "date_resolved": "2025-01-02", "satisfaction_score": 1},
        {"ticket_id": 913, "customer_id": 101, "issue_type": "Query", "status": "Resolved", "date_opened": "2025-01-01", "date_resolved": "2025-01-02", "satisfaction_score": 5},
    ])
    good_v, bad_v = validate_support_tickets(df_valid, valid_customer_ids={101})
    assert len(good_v) == 2
    assert len(bad_v) == 0

    df_invalid = pd.DataFrame([
        {"ticket_id": 914, "customer_id": 101, "issue_type": "Query", "status": "Resolved", "date_opened": "2025-01-01", "date_resolved": "2025-01-02", "satisfaction_score": 0},
        {"ticket_id": 915, "customer_id": 101, "issue_type": "Query", "status": "Resolved", "date_opened": "2025-01-01", "date_resolved": "2025-01-02", "satisfaction_score": 6},
        {"ticket_id": 916, "customer_id": 101, "issue_type": "", "status": "Resolved", "date_opened": "2025-01-01", "date_resolved": "2025-01-02", "satisfaction_score": 4},
        {"ticket_id": 917, "customer_id": 101, "issue_type": "Dispute", "status": "Resolved", "date_opened": "2025-01-01", "date_resolved": "2025-01-02", "satisfaction_score": 4},
        {"ticket_id": 917, "customer_id": 101, "issue_type": "Dispute", "status": "Resolved", "date_opened": "2025-01-01", "date_resolved": "2025-01-02", "satisfaction_score": 4},
    ])
    good_inv, bad_inv = validate_support_tickets(df_invalid, valid_customer_ids={101})
    assert len(good_inv) == 0
    assert len(bad_inv) == 5
    assert any("Invalid Satisfaction Score" in r for r in bad_inv["rejection_reason"])
    assert any("Missing Issue Type" in r for r in bad_inv["rejection_reason"])
    assert any("Duplicate Ticket ID" in r for r in bad_inv["rejection_reason"])

