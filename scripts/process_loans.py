import sys
import os
from datetime import datetime
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import (
    LOANS_RAW, LOANS_CURATED, LOANS_BAD,
    CUSTOMERS_CURATED
)
from utils.logger import get_logger, log_pipeline_summary
from utils.file_handler import read_csv_safe, save_curated_and_bad
from validation.loan_validation import validate_loans
from transformation.loan_transform import transform_loans

logger = get_logger("process_loans")

def run_loans_pipeline(raw_path: str = LOANS_RAW,
                       customers_curated_path: str = CUSTOMERS_CURATED,
                       curated_path: str = LOANS_CURATED,
                       bad_path: str = LOANS_BAD):
    start_time = datetime.now()
    logger.info(f"Starting Loans ETL. Reading from {raw_path}...")

    if not os.path.exists(customers_curated_path):
        raise FileNotFoundError(
            f"Curated customers file not found at: {customers_curated_path}. "
            "Please run process_customers.py first!"
        )

    # Load valid customer IDs
    logger.info(f"Loading curated customer IDs from {customers_curated_path}...")
    cust_df = read_csv_safe(customers_curated_path)
    valid_customer_ids = set(cust_df["customer_id"].astype(int))
    logger.info(f"Loaded {len(valid_customer_ids):,} valid customer IDs.")

    # Read raw loans
    df_raw = read_csv_safe(raw_path)
    total_raw = len(df_raw)
    logger.info(f"Loaded {total_raw:,} raw loan records.")

    # Validate
    good_df, bad_df = validate_loans(df_raw, valid_customer_ids)

    # Transform
    clean_df = transform_loans(good_df)

    # Persist
    save_curated_and_bad(clean_df, bad_df, curated_path, bad_path)

    end_time = datetime.now()
    summary = log_pipeline_summary(
        pipeline_name="process_loans",
        start_time=start_time,
        end_time=end_time,
        total_records=total_raw,
        curated_records=len(clean_df),
        bad_records=len(bad_df)
    )

    return summary

if __name__ == "__main__":
    run_loans_pipeline()
