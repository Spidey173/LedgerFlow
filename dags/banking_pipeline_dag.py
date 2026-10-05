"""
Apache Airflow DAG demonstrating scheduled dependency orchestration for the
10-dataset LedgerFlow Data Platform.

Pipeline Dependency Architecture:
1. Master / Dimension lookups: Branches, Customers
2. Dependent Dimensions: Employees (depends on Branches), Accounts (depends on Customers)
3. Transactional & Product Fact Tables:
   - Transactions (depends on Accounts)
   - Loans (depends on Customers) -> Loan Payments (depends on Loans)
   - Cards (depends on Customers, Accounts) -> Card Transactions (depends on Cards)
   - Support Tickets (depends on Customers)
4. Database Load / Warehouse Ingestion & Completion verification
"""

from datetime import datetime, timedelta
import os
import sys

# Ensure project root is available in Python path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator

# Import pipeline runner functions
from scripts.process_branches import run_branches_pipeline
from scripts.process_employees import run_employees_pipeline
from scripts.process_customers import run_customers_pipeline
from scripts.process_accounts import run_accounts_pipeline
from scripts.process_transactions import run_transactions_pipeline
from scripts.process_loans import run_loans_pipeline
from scripts.process_loan_payments import run_loan_payments_pipeline
from scripts.process_cards import run_cards_pipeline
from scripts.process_card_transactions import run_card_transactions_pipeline
from scripts.process_support_tickets import run_support_tickets_pipeline

default_args = {
    "owner": "data_engineering",
    "depends_on_past": False,
    "start_date": datetime(2026, 1, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="banking_data_engineering_pipeline",
    default_args=default_args,
    description="Orchestrates ingestion, DQ validation, and curation for all 10 banking datasets",
    schedule_interval="@daily",
    catchup=False,
    tags=["banking", "etl", "dq_validation", "curation"],
) as dag:

    start_pipeline = EmptyOperator(
        task_id="start_pipeline",
    )

    # 1. Independent Core Dimensions
    process_branches = PythonOperator(
        task_id="process_branches",
        python_callable=run_branches_pipeline,
    )

    process_customers = PythonOperator(
        task_id="process_customers",
        python_callable=run_customers_pipeline,
    )

    # 2. Level 1 Downstream Entities
    process_employees = PythonOperator(
        task_id="process_employees",
        python_callable=run_employees_pipeline,
    )

    process_accounts = PythonOperator(
        task_id="process_accounts",
        python_callable=run_accounts_pipeline,
    )

    process_loans = PythonOperator(
        task_id="process_loans",
        python_callable=run_loans_pipeline,
    )

    process_support_tickets = PythonOperator(
        task_id="process_support_tickets",
        python_callable=run_support_tickets_pipeline,
    )

    # 3. Level 2 Downstream Entities
    process_transactions = PythonOperator(
        task_id="process_transactions",
        python_callable=run_transactions_pipeline,
    )

    process_loan_payments = PythonOperator(
        task_id="process_loan_payments",
        python_callable=run_loan_payments_pipeline,
    )

    process_cards = PythonOperator(
        task_id="process_cards",
        python_callable=run_cards_pipeline,
    )

    # 4. Level 3 Downstream Entities
    process_card_transactions = PythonOperator(
        task_id="process_card_transactions",
        python_callable=run_card_transactions_pipeline,
    )

    end_pipeline = EmptyOperator(
        task_id="end_pipeline",
    )

    # --- Dependency Graph ---
    start_pipeline >> [process_branches, process_customers]

    # Branch lineage
    process_branches >> process_employees

    # Customer lineage
    process_customers >> [process_accounts, process_loans, process_support_tickets]

    # Accounts lineage
    process_accounts >> process_transactions

    # Multi-parent dependencies (Cards requires both Customers and Accounts)
    [process_customers, process_accounts] >> process_cards

    # Loan Payments requires Loans
    process_loans >> process_loan_payments

    # Card transactions requires Cards
    process_cards >> process_card_transactions

    # Pipeline Completion
    [
        process_employees,
        process_transactions,
        process_loan_payments,
        process_card_transactions,
        process_support_tickets,
    ] >> end_pipeline
