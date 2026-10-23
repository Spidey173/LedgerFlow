import sys
import os
import psycopg2
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import (
    DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, DATABASE_URL,
    validate_db_credentials,
    BRANCHES_CURATED, EMPLOYEES_CURATED, CUSTOMERS_CURATED,
    ACCOUNTS_CURATED, TRANSACTIONS_CURATED, LOANS_CURATED,
    LOAN_PAYMENTS_CURATED, CARDS_CURATED, CARD_TRANSACTIONS_CURATED,
    SUPPORT_TICKETS_CURATED
)
from utils.logger import get_logger

logger = get_logger("db_loader")

def get_connection():
    validate_db_credentials(raise_on_missing=True)
    if DATABASE_URL:
        return psycopg2.connect(DATABASE_URL)
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

def copy_csv_to_table(cursor, table_name: str, csv_path: str):
    logger.info(f"Loading {csv_path} into staging '{table_name}' via COPY...")
    start = datetime.now()
    with open(csv_path, "r", encoding="utf-8") as f:
        header = f.readline().strip()
        f.seek(0)
        copy_sql = f"COPY {table_name} ({header}) FROM STDIN WITH CSV HEADER"
        cursor.copy_expert(copy_sql, f)
    elapsed = round((datetime.now() - start).total_seconds(), 2)
    logger.info(f"Loaded '{table_name}' in {elapsed}s.")

def create_staging_tables(cursor, tables):
    """Creates unlogged staging tables matching the structure of target tables."""
    for table in tables:
        staging_table = f"stg_{table}"
        cursor.execute(f"DROP TABLE IF EXISTS {staging_table} CASCADE;")
        cursor.execute(f"CREATE UNLOGGED TABLE {staging_table} (LIKE {table} INCLUDING DEFAULTS);")

def drop_staging_tables(cursor, tables):
    """Cleans up staging tables."""
    for table in tables:
        cursor.execute(f"DROP TABLE IF EXISTS stg_{table} CASCADE;")

def atomic_swap_tables(cursor, tables, use_truncate: bool = False):
    """
    Performs atomic data swap from staging into target warehouse tables inside an active transaction.

    Concurrency, Locking & Scale Architecture:
    - Non-Blocking by Default (use_truncate=False):
      Executes `DELETE FROM {table}` in reverse topological order. Under PostgreSQL MVCC,
      DELETE acquires a ROW EXCLUSIVE lock, which does NOT conflict with concurrent readers
      acquiring ACCESS SHARE locks (SELECT queries). Concurrent API callers and analytical
      dashboards continue reading the pre-refresh snapshot uninterrupted during the refresh.
      
      *Scale Trade-Off Note*: While readers are not blocked, full table replacement via DELETE
      writes a replacement set of rows, generates significant Write-Ahead Logging (WAL),
      leaves dead tuples in the heap, and requires updating all indexes across tables. Post-commit
      VACUUM ANALYZE is triggered to reclaim space and refresh optimizer statistics.
      
    - Truncate Mode (use_truncate=True):
      Executes `TRUNCATE TABLE {table} CASCADE`. This instantly deallocates pages without
      dead-tuple bloat, but acquires an ACCESS EXCLUSIVE lock on every table. This lock blocks
      ALL concurrent readers until transaction commit, and will queue behind active readers,
      potentially causing reader connection timeouts in production.

    - Production Blueprint for Large-Scale Data Platforms:
      For multi-gigabyte or terabyte financial warehouses, full replacement should be evolved into:
      1) Blue-Green Schema Swapping: Staged tables pre-indexed in a shadow schema and swapped
         instantaneously via DDL schema rename or View pointer switching (microseconds duration).
      2) Declarative Partition Swapping: Attaching new date partitions with ALTER TABLE ... ATTACH PARTITION.
      3) Incremental Upsert / Merge: Delta ingestion using watermark timestamps (INSERT ... ON CONFLICT).

    Atomicity & Rollback:
    - Executed within a single transaction (BEGIN ... COMMIT).
    - If any step fails, the entire transaction rolls back cleanly, leaving original data untouched.
    """
    swap_method = "TRUNCATE (exclusive lock; blocks readers)" if use_truncate else "DELETE (non-blocking MVCC; writes replacement rows)"
    logger.info(f"Executing atomic transactional data swap from staging to live warehouse via {swap_method}...")

    # Step 1: Clear live tables in reverse topological order to respect foreign key constraints
    for table in reversed(tables):
        if use_truncate:
            cursor.execute(f"TRUNCATE TABLE {table} CASCADE;")
        else:
            cursor.execute(f"DELETE FROM {table};")

    # Step 2: Insert into live tables in topological forward order
    for table in tables:
        staging_table = f"stg_{table}"
        cursor.execute(f"INSERT INTO {table} SELECT * FROM {staging_table};")
        logger.info(f"  ✓ Swapped staging data into '{table}'")

def load_all_curated_data(staged: bool = True, use_truncate: bool = False, vacuum_analyze: bool = True):
    """
    Staged, Transactional Database Refresh:
    1. Validates presence of all curated datasets before modifying database state.
    2. Acquires PostgreSQL session-level advisory lock (`pg_try_advisory_lock`) on the dedicated connection
       to serialize pipeline executions and prevent concurrent loaders. The lock is held across the session
       and released explicitly in the finally block via `pg_advisory_unlock`.
    3. Loads CSVs into temporary staging tables (`stg_*`).
    4. Validates staging row counts.
    5. Atomically replaces data in target tables inside a single committed transaction without blocking readers.
    6. Automatically rolls back on any error, preserving the prior dataset intact.
    7. Optionally executes post-commit VACUUM ANALYZE to clean dead tuples and update planner stats.
    """
    logger.info("Connecting to PostgreSQL warehouse...")
    conn = get_connection()
    conn.autocommit = False
    cursor = conn.cursor()

    load_plan = [
        ("branches", BRANCHES_CURATED),
        ("employees", EMPLOYEES_CURATED),
        ("customers", CUSTOMERS_CURATED),
        ("accounts", ACCOUNTS_CURATED),
        ("transactions", TRANSACTIONS_CURATED),
        ("loans", LOANS_CURATED),
        ("loan_payments", LOAN_PAYMENTS_CURATED),
        ("cards", CARDS_CURATED),
        ("card_transactions", CARD_TRANSACTIONS_CURATED),
        ("support_tickets", SUPPORT_TICKETS_CURATED),
    ]
    tables = [t[0] for t in load_plan]

    # Pre-flight check: ensure all files exist before touching database
    for table, path in load_plan:
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"Curated file {path} for table '{table}' not found. "
                "Aborting load to protect warehouse integrity."
            )

    ADVISORY_LOCK_ID = 482910471  # Arbitrary unique ID for pipeline concurrency lock
    try:
        # Acquire session-level advisory lock to serialize pipeline executions
        logger.info("Acquiring database refresh session advisory lock...")
        cursor.execute("SELECT pg_try_advisory_lock(%s);", (ADVISORY_LOCK_ID,))
        acquired = cursor.fetchone()[0]
        if not acquired:
            raise RuntimeError(
                "Another pipeline refresh operation is currently in progress. "
                "Aborting to avoid concurrent data corruption."
            )

        if staged:
            logger.info("Setting up staging tables for non-destructive load...")
            create_staging_tables(cursor, tables)

            # Load into staging tables
            staging_counts = {}
            for table, path in load_plan:
                staging_table = f"stg_{table}"
                copy_csv_to_table(cursor, staging_table, path)
                cursor.execute(f"SELECT COUNT(*) FROM {staging_table};")
                staging_counts[table] = cursor.fetchone()[0]

            logger.info("Staging load verification complete:")
            for table, count in staging_counts.items():
                logger.info(f"  • stg_{table:<18}: {count:,} rows")
                if count == 0 and os.path.getsize(dict(load_plan)[table]) > 50:
                    raise ValueError(f"Staged table 'stg_{table}' has 0 rows despite non-empty CSV.")

            # Atomically swap staging data into live tables
            atomic_swap_tables(cursor, tables, use_truncate=use_truncate)
            drop_staging_tables(cursor, tables)
        else:
            # Direct load fallback if staging is disabled
            for table in reversed(tables):
                if use_truncate:
                    cursor.execute(f"TRUNCATE TABLE {table} CASCADE;")
                else:
                    cursor.execute(f"DELETE FROM {table};")
            for table, path in load_plan:
                copy_csv_to_table(cursor, table, path)

        conn.commit()
        logger.info("Warehouse refresh committed successfully! All 10 tables updated.")

        # Post-load maintenance: Reclaim dead tuples from DELETE and refresh query planner statistics
        if vacuum_analyze and not use_truncate:
            logger.info("Executing post-refresh VACUUM ANALYZE to reclaim dead tuples and refresh planner statistics...")
            try:
                # In PostgreSQL, VACUUM cannot run inside an active transaction block; use autocommit connection.
                vac_conn = get_connection()
                vac_conn.autocommit = True
                with vac_conn.cursor() as vac_cur:
                    for table in tables:
                        vac_cur.execute(f"VACUUM ANALYZE {table};")
                vac_conn.close()
                logger.info("Post-refresh VACUUM ANALYZE completed successfully.")
            except Exception as vac_err:
                logger.warning(f"Non-fatal warning: Post-refresh VACUUM ANALYZE encountered an issue: {vac_err}")

        # Post-load verification
        logger.info("\n--- Live Warehouse Table Record Verification (10 Tables) ---")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table};")
            count = cursor.fetchone()[0]
            logger.info(f"  • {table:<22}: {count:,} rows")

    except Exception as e:
        conn.rollback()
        logger.error(f"Error during warehouse load: {e}. Rolled back transaction; existing data preserved.", exc_info=True)
        raise e
    finally:
        try:
            cursor.execute("SELECT pg_advisory_unlock(%s);", (ADVISORY_LOCK_ID,))
        except Exception:
            pass
        cursor.close()
        conn.close()

if __name__ == "__main__":
    load_all_curated_data()

