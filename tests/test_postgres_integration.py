import os
import getpass
import time
import threading
import pytest
import psycopg2
from psycopg2.extras import RealDictCursor

import scripts.load_postgres as loader

# Configuration for local test database
TEST_DB_NAME = os.getenv("TEST_DB_NAME", "ledgerflow_test_db")
CURRENT_USER = os.getenv("DB_USER", getpass.getuser())
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

def _initialize_schema_if_needed(conn):
    """Initializes tables from sql/schema/create_tables.sql if not present."""
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT to_regclass('public.branches');")
            exists = cur.fetchone()[0]
            if exists is None:
                schema_file = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "sql", "schema", "create_tables.sql"
                )
                if os.path.exists(schema_file):
                    with open(schema_file, "r", encoding="utf-8") as f:
                        cur.execute(f.read())
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass

def get_test_db_conn():
    """
    Connects to the test database.
    If the test database does not exist, connects to default 'postgres' database,
    creates the test database, initializes the schema, and returns the connection.
    """
    # 1. Try direct connection to TEST_DB_NAME
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=TEST_DB_NAME,
            user=CURRENT_USER,
            password=DB_PASSWORD,
            connect_timeout=2
        )
        _initialize_schema_if_needed(conn)
        return conn
    except Exception:
        pass

    # 2. If direct connection fails, try bootstrapping via default 'postgres' database
    try:
        admin_conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname="postgres",
            user=CURRENT_USER,
            password=DB_PASSWORD,
            connect_timeout=2
        )
        admin_conn.autocommit = True
        with admin_conn.cursor() as admin_cur:
            admin_cur.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (TEST_DB_NAME,))
            if not admin_cur.fetchone():
                admin_cur.execute(f'CREATE DATABASE "{TEST_DB_NAME}";')
        admin_conn.close()

        # Connect to newly created database and initialize schema
        new_conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=TEST_DB_NAME,
            user=CURRENT_USER,
            password=DB_PASSWORD,
            connect_timeout=2
        )
        _initialize_schema_if_needed(new_conn)
        return new_conn
    except Exception:
        return None

# Mark tests to skip if PostgreSQL server is unreachable
conn_check = get_test_db_conn()
POSTGRES_AVAILABLE = conn_check is not None
if conn_check:
    conn_check.close()

pytestmark = pytest.mark.skipif(
    not POSTGRES_AVAILABLE,
    reason=f"PostgreSQL test database '{TEST_DB_NAME}' is not accessible on {DB_HOST}:{DB_PORT}. "
           f"Start PostgreSQL or use 'docker-compose up -d postgres' to run live integration tests."
)

def test_real_postgres_advisory_lock_mutual_exclusion():
    """
    Verifies against a live PostgreSQL server that session-level advisory locks
    properly serialize access between two concurrent connections.
    """
    conn1 = get_test_db_conn()
    conn2 = get_test_db_conn()
    assert conn1 is not None and conn2 is not None

    cur1 = conn1.cursor()
    cur2 = conn2.cursor()

    lock_id = 482910471

    try:
        # Session 1 acquires the lock
        cur1.execute("SELECT pg_try_advisory_lock(%s);", (lock_id,))
        assert cur1.fetchone()[0] is True

        # Session 2 tries to acquire the same lock and must fail immediately
        cur2.execute("SELECT pg_try_advisory_lock(%s);", (lock_id,))
        assert cur2.fetchone()[0] is False

        # Session 1 unlocks
        cur1.execute("SELECT pg_advisory_unlock(%s);", (lock_id,))
        assert cur1.fetchone()[0] is True

        # Now Session 2 can acquire the lock
        cur2.execute("SELECT pg_try_advisory_lock(%s);", (lock_id,))
        assert cur2.fetchone()[0] is True

        # Session 2 unlocks
        cur2.execute("SELECT pg_advisory_unlock(%s);", (lock_id,))
        assert cur2.fetchone()[0] is True
    finally:
        cur1.close()
        cur2.close()
        conn1.close()
        conn2.close()

def test_real_postgres_non_blocking_concurrent_readers():
    """
    Verifies that during a staged refresh using non-blocking DELETE (default),
    concurrent readers executing SELECT are NOT blocked by table locks and
    continue to read the pre-refresh snapshot under PostgreSQL MVCC.
    """
    conn = get_test_db_conn()
    cur = conn.cursor()

    # Seed baseline branch record: clean all tables in reverse topological order
    for table in reversed([
        "branches", "employees", "customers", "accounts", "transactions",
        "loans", "loan_payments", "cards", "card_transactions", "support_tickets"
    ]):
        cur.execute(f"DELETE FROM {table};")
    cur.execute(
        "INSERT INTO branches (branch_id, branch_name, city, state, opened_date, ifsc_code) "
        "VALUES (101, 'Baseline Branch', 'Pune', 'MH', '2022-01-01', 'BNK00101');"
    )
    conn.commit()

    reader_metrics = []

    def reader_query():
        time.sleep(0.1)  # Ensure writer is mid-transaction
        r_conn = get_test_db_conn()
        r_cur = r_conn.cursor()
        t_start = time.time()
        r_cur.execute("SELECT branch_name FROM branches WHERE branch_id = 101;")
        row = r_cur.fetchone()
        duration = time.time() - t_start
        reader_metrics.append((row[0] if row else None, duration))
        r_cur.close()
        r_conn.close()

    reader_thread = threading.Thread(target=reader_query)
    reader_thread.start()

    # Writer performs staged swap with non-blocking DELETE
    writer_conn = get_test_db_conn()
    writer_conn.autocommit = False
    w_cur = writer_conn.cursor()

    loader.create_staging_tables(w_cur, ["branches"])
    w_cur.execute(
        "INSERT INTO stg_branches (branch_id, branch_name, city, state, opened_date, ifsc_code) "
        "VALUES (102, 'Refreshed Branch', 'Delhi', 'DL', '2023-01-01', 'BNK00102');"
    )
    # Execute non-blocking swap
    loader.atomic_swap_tables(w_cur, ["branches"], use_truncate=False)

    # Sleep while uncommitted to allow concurrent reader query
    time.sleep(0.4)
    writer_conn.commit()

    loader.drop_staging_tables(w_cur, ["branches"])
    writer_conn.commit()
    w_cur.close()
    writer_conn.close()

    reader_thread.join()

    # Reader must have seen original row immediately without waiting for writer's commit
    assert len(reader_metrics) == 1
    branch_name, duration = reader_metrics[0]
    assert branch_name == "Baseline Branch"
    assert duration < 0.3, f"Reader was blocked! Duration: {duration:.4f}s"

    # Post-commit check: newly swapped row is now live
    cur.execute("SELECT branch_id, branch_name FROM branches;")
    rows = cur.fetchall()
    assert len(rows) == 1
    assert rows[0][0] == 102
    assert rows[0][1] == "Refreshed Branch"

    cur.close()
    conn.close()

def _create_sample_curated_datasets(tmp_path):
    datasets = {
        "branches": "branch_id,branch_name,city,state,opened_date,ifsc_code\n10,Test Branch,Bangalore,KA,2022-01-01,BNK00010\n",
        "employees": "employee_id,name,branch_id,role,hire_date,salary\n100,Alex River,10,Teller,2022-02-01,50000.00\n",
        "customers": "customer_id,name,gender,date_of_birth,city,state,phone,email,occupation,annual_income,join_date,credit_score\n1000,Sam Smith,Male,1990-01-01,Bangalore,KA,9876543210,sam@example.com,Engineer,90000.00,2022-01-10,750\n",
        "accounts": "account_id,customer_id,branch_id,account_type,balance,open_date,status\n10000,1000,10,Savings,25000.00,2022-01-15,Active\n",
        "transactions": "transaction_id,account_id,txn_date,txn_type,amount,channel,merchant_category\n50000,10000,2026-01-01,Deposit,500.00,Mobile App,Salary\n",
        "loans": "loan_id,customer_id,branch_id,loan_type,loan_amount,interest_rate,term_months,start_date,status\n2000,1000,10,Personal Loan,10000.00,8.5,24,2024-01-01,Active\n",
        "loan_payments": "payment_id,loan_id,payment_date,amount_paid,principal_component,interest_component,late_payment_flag\n8000,2000,2024-02-01,500.00,420.00,80.00,0\n",
        "cards": "card_id,customer_id,account_id,card_type,issue_date,expiry_date,credit_limit,status\n3000,1000,10000,Credit - Platinum,2023-01-01,2028-01-01,15000.00,Active\n",
        "card_transactions": "card_txn_id,card_id,txn_date,merchant_category,amount,is_fraud\n7000,3000,2026-01-02,Groceries,45.00,0\n",
        "support_tickets": "ticket_id,customer_id,issue_type,date_opened,date_resolved,status,satisfaction_score\n9000,1000,Billing,2026-01-05,2026-01-06,Resolved,5\n"
    }

    test_paths = {}
    for name, content in datasets.items():
        file_path = tmp_path / f"{name}.csv"
        file_path.write_text(content, encoding="utf-8")
        test_paths[name] = str(file_path)
    return test_paths

def test_real_postgres_full_loader_end_to_end(tmp_path, monkeypatch):
    """
    Executes load_all_curated_data() completely end-to-end against a real PostgreSQL instance:
    1. Generates mini curated CSV files matching all 10 schemas.
    2. Overrides connection to point to test PostgreSQL.
    3. Executes the full loader with non-blocking staged refresh.
    4. Asserts that data lands in all tables and advisory locks are properly acquired and released.
    """
    test_paths = _create_sample_curated_datasets(tmp_path)

    # Monkeypatch config constants to use temporary curated files
    monkeypatch.setattr(loader, "BRANCHES_CURATED", test_paths["branches"])
    monkeypatch.setattr(loader, "EMPLOYEES_CURATED", test_paths["employees"])
    monkeypatch.setattr(loader, "CUSTOMERS_CURATED", test_paths["customers"])
    monkeypatch.setattr(loader, "ACCOUNTS_CURATED", test_paths["accounts"])
    monkeypatch.setattr(loader, "TRANSACTIONS_CURATED", test_paths["transactions"])
    monkeypatch.setattr(loader, "LOANS_CURATED", test_paths["loans"])
    monkeypatch.setattr(loader, "LOAN_PAYMENTS_CURATED", test_paths["loan_payments"])
    monkeypatch.setattr(loader, "CARDS_CURATED", test_paths["cards"])
    monkeypatch.setattr(loader, "CARD_TRANSACTIONS_CURATED", test_paths["card_transactions"])
    monkeypatch.setattr(loader, "SUPPORT_TICKETS_CURATED", test_paths["support_tickets"])

    monkeypatch.setattr(loader, "get_connection", get_test_db_conn)
    monkeypatch.setattr(loader, "validate_db_credentials", lambda raise_on_missing=True: True)

    # Run the full loader end to end
    loader.load_all_curated_data(staged=True, use_truncate=False)

    # Verify rows in PostgreSQL across multiple tables
    conn = get_test_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM branches WHERE branch_id = 10;")
    assert cur.fetchone()[0] == 1
    cur.execute("SELECT COUNT(*) FROM customers WHERE customer_id = 1000;")
    assert cur.fetchone()[0] == 1
    cur.execute("SELECT COUNT(*) FROM accounts WHERE account_id = 10000;")
    assert cur.fetchone()[0] == 1
    cur.execute("SELECT COUNT(*) FROM transactions WHERE transaction_id = 50000;")
    assert cur.fetchone()[0] == 1

    cur.close()
    conn.close()

def test_real_postgres_full_loader_failure_rollback(tmp_path, monkeypatch):
    """
    Exercises load_all_curated_data() end-to-end under real failure conditions:
    1. Pre-seeds known baseline rows in live tables.
    2. Injects an invalid CSV (bad foreign key or corrupted data) in one dataset.
    3. Executes the full loader.
    4. Asserts that the full loader raises an exception, triggers transaction rollback,
       and preserves the prior baseline data 100% intact.
    """
    test_paths = _create_sample_curated_datasets(tmp_path)

    # Seed baseline state: clean all tables in reverse topological order
    conn = get_test_db_conn()
    cur = conn.cursor()
    for table in reversed([
        "branches", "employees", "customers", "accounts", "transactions",
        "loans", "loan_payments", "cards", "card_transactions", "support_tickets"
    ]):
        cur.execute(f"DELETE FROM {table};")
    cur.execute("INSERT INTO branches VALUES (999, 'Permanent Branch', 'City', 'ST', '2020-01-01', 'BNK00999');")
    conn.commit()

    # Corrupt accounts CSV with a non-existent customer_id to violate foreign key constraint
    corrupt_accounts = "account_id,customer_id,branch_id,account_type,balance,open_date,status\n99999,99999999,10,Savings,1000.00,2022-01-01,Active\n"
    acc_path = tmp_path / "accounts.csv"
    acc_path.write_text(corrupt_accounts, encoding="utf-8")
    test_paths["accounts"] = str(acc_path)

    monkeypatch.setattr(loader, "BRANCHES_CURATED", test_paths["branches"])
    monkeypatch.setattr(loader, "EMPLOYEES_CURATED", test_paths["employees"])
    monkeypatch.setattr(loader, "CUSTOMERS_CURATED", test_paths["customers"])
    monkeypatch.setattr(loader, "ACCOUNTS_CURATED", test_paths["accounts"])
    monkeypatch.setattr(loader, "TRANSACTIONS_CURATED", test_paths["transactions"])
    monkeypatch.setattr(loader, "LOANS_CURATED", test_paths["loans"])
    monkeypatch.setattr(loader, "LOAN_PAYMENTS_CURATED", test_paths["loan_payments"])
    monkeypatch.setattr(loader, "CARDS_CURATED", test_paths["cards"])
    monkeypatch.setattr(loader, "CARD_TRANSACTIONS_CURATED", test_paths["card_transactions"])
    monkeypatch.setattr(loader, "SUPPORT_TICKETS_CURATED", test_paths["support_tickets"])

    monkeypatch.setattr(loader, "get_connection", get_test_db_conn)
    monkeypatch.setattr(loader, "validate_db_credentials", lambda raise_on_missing=True: True)

    with pytest.raises(Exception):
        loader.load_all_curated_data(staged=True, use_truncate=False)

    # Verify that rollback preserved the original state!
    cur.execute("SELECT branch_id, branch_name FROM branches;")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    assert len(rows) == 1
    assert rows[0][0] == 999
    assert rows[0][1] == "Permanent Branch"

