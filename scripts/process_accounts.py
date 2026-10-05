import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import (
    ACCOUNTS_RAW, ACCOUNTS_CURATED, ACCOUNTS_BAD,
    CUSTOMERS_CURATED
)
from utils.logger import get_logger
from utils.file_handler import read_csv_safe, save_curated_and_bad
from validation.account_validation import validate_accounts
from transformation.account_transform import transform_accounts

logger = get_logger("process_accounts")

def run_accounts_pipeline(raw_path: str = ACCOUNTS_RAW,
                          customers_curated_path: str = CUSTOMERS_CURATED,
                          curated_path: str = ACCOUNTS_CURATED,
                          bad_path: str = ACCOUNTS_BAD):
    logger.info(f"Starting Accounts ETL. Reading from {raw_path}...")

    # Ensure curated customers exist for referential integrity
    if not os.path.exists(customers_curated_path):
        raise FileNotFoundError(
            f"Curated customers file not found at: {customers_curated_path}. "
            "Please run process_customers.py first!"
        )

    # Load valid customer IDs
    logger.info(f"Loading curated customer IDs from {customers_curated_path} for referential integrity...")
    cust_df = read_csv_safe(customers_curated_path)
    valid_customer_ids = set(cust_df["customer_id"].astype(int))
    logger.info(f"Loaded {len(valid_customer_ids):,} valid customer IDs.")

    # Read raw accounts
    df_raw = read_csv_safe(raw_path)
    total_raw = len(df_raw)
    logger.info(f"Loaded {total_raw:,} raw account records.")

    # Validation
    good_df, bad_df = validate_accounts(df_raw, valid_customer_ids)
    logger.info(f"Validation complete: {len(good_df):,} passed, {len(bad_df):,} failed.")

    # Transformation
    clean_df = transform_accounts(good_df)
    logger.info(f"Transformation complete.")

    # Persist
    save_curated_and_bad(clean_df, bad_df, curated_path, bad_path)
    logger.info(f"Outputs written: Curated -> {curated_path}, DLQ -> {bad_path}")

    return {"total": total_raw, "curated": len(clean_df), "bad": len(bad_df)}

if __name__ == "__main__":
    run_accounts_pipeline()
