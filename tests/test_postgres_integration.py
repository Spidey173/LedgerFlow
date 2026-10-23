import os
import getpass
import pytest
import psycopg2
from psycopg2.extras import RealDictCursor

import scripts.load_postgres as loader

# Configuration for local test database
TEST_DB_NAME = "ledgerflow_test_db"
CURRENT_USER = getpass.getuser()

def get_test_db_conn():
    try:
        return psycopg2.connect(
            host="localhost",
            port=5432,
            dbname=TEST_DB_NAME,
            user=CURRENT_USER,
            connect_timeout=2
        )
    except Exception:
        return None

# Mark tests to skip if local test database is unreachable
conn_check = get_test_db_conn()
POSTGRES_AVAILABLE = conn_check is not None
if conn_check:
    conn_check.close()

pytestmark = pytest.mark.skipif(
    not POSTGRES_AVAILABLE,
    reason="Local PostgreSQL ledgerflow_test_db is not accessible"
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

def test_real_postgres_staged_refresh_and_rollback():
    """
    Verifies against a live PostgreSQL server that:
    1. Pre-existing records exist in a live table.
    2. Staging tables load new data.
    3. An intentional failure during the swap triggers a complete ROLLBACK.
    4. The original pre-existing records remain 100% intact without data loss.
    """
    conn = get_test_db_conn()
    cur = conn.cursor()

    try:
        # Seed initial existing record
        cur.execute("DELETE FROM branches;")
        cur.execute(
            "INSERT INTO branches (branch_id, branch_name, city, state, opened_date, ifsc_code) "
            "VALUES (1, 'Initial Branch', 'Mumbai', 'MH', '2020-01-01', 'BNK0001');"
        )
        conn.commit()

        # Verify initial state
        cur.execute("SELECT COUNT(*) FROM branches;")
        assert cur.fetchone()[0] == 1

        # Simulate staged load with a transaction that fails midway
        conn.autocommit = False
        loader.create_staging_tables(cur, ["branches"])

        # Insert new data into staging table
        cur.execute(
            "INSERT INTO stg_branches (branch_id, branch_name, city, state, opened_date, ifsc_code) "
            "VALUES (2, 'New Staged Branch', 'Delhi', 'DL', '2021-01-01', 'BNK0002');"
        )

        # Begin atomic swap simulation: truncate live, insert from staging, but raise error before commit
        cur.execute("TRUNCATE TABLE branches CASCADE;")
        cur.execute("INSERT INTO branches SELECT * FROM stg_branches;")

        # Simulate failure (e.g. constraint violation or crash)
        cur.execute("SELECT * FROM non_existent_table_triggering_syntax_error;")
        conn.commit()

    except Exception:
        # Roll back on error as production pipeline does
        conn.rollback()
    finally:
        # Ensure staging tables are cleaned up
        try:
            loader.drop_staging_tables(cur, ["branches"])
            conn.commit()
        except Exception:
            conn.rollback()

    # Re-verify that rollback preserved the original state!
    cur.execute("SELECT branch_id, branch_name FROM branches;")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    assert len(rows) == 1
    assert rows[0][0] == 1
    assert rows[0][1] == "Initial Branch"
