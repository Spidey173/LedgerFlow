import sys
import os
import psycopg2
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import (
    DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD,
    BRANCHES_CURATED, EMPLOYEES_CURATED, CUSTOMERS_CURATED,
    ACCOUNTS_CURATED, TRANSACTIONS_CURATED, LOANS_CURATED,
    LOAN_PAYMENTS_CURATED, CARDS_CURATED, CARD_TRANSACTIONS_CURATED,
    SUPPORT_TICKETS_CURATED
)
from utils.logger import get_logger

logger = get_logger("db_loader")

def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

def copy_csv_to_table(cursor, table_name: str, csv_path: str):
    logger.info(f"Loading {csv_path} into '{table_name}' via COPY...")
    start = datetime.now()
    with open(csv_path, "r", encoding="utf-8") as f:
        header = f.readline().strip()
        f.seek(0)
        copy_sql = f"COPY {table_name} ({header}) FROM STDIN WITH CSV HEADER"
        cursor.copy_expert(copy_sql, f)
    elapsed = round((datetime.now() - start).total_seconds(), 2)
    logger.info(f"Loaded '{table_name}' in {elapsed}s.")

def load_all_curated_data():
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

    try:
        logger.info("Truncating existing tables before refresh...")
        for table, _ in reversed(load_plan):
            cursor.execute(f"TRUNCATE TABLE {table} CASCADE;")

        for table, path in load_plan:
            if not os.path.exists(path):
                raise FileNotFoundError(f"Curated file {path} not found. Please run ETL first!")
            copy_csv_to_table(cursor, table, path)

        conn.commit()
        logger.info("All 10 curated tables loaded and committed successfully!")

        logger.info("\n--- Warehouse Table Record Verification (10 Tables) ---")
        for table, _ in load_plan:
            cursor.execute(f"SELECT COUNT(*) FROM {table};")
            count = cursor.fetchone()[0]
            logger.info(f"  • {table:<22}: {count:,} rows")

    except Exception as e:
        conn.rollback()
        logger.error(f"Error during bulk load: {e}", exc_info=True)
        raise e
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    load_all_curated_data()
