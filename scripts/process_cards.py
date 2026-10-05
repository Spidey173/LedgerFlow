import sys
import os
from datetime import datetime
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import (
    CARDS_RAW, CARDS_CURATED, CARDS_BAD,
    CUSTOMERS_CURATED, ACCOUNTS_CURATED
)
from utils.logger import get_logger, log_pipeline_summary
from utils.file_handler import read_csv_safe, save_curated_and_bad
from validation.card_validation import validate_cards
from transformation.card_transform import transform_cards

logger = get_logger("process_cards")

def run_cards_pipeline(raw_path: str = CARDS_RAW,
                       customers_curated_path: str = CUSTOMERS_CURATED,
                       accounts_curated_path: str = ACCOUNTS_CURATED,
                       curated_path: str = CARDS_CURATED,
                       bad_path: str = CARDS_BAD):
    start_time = datetime.now()
    logger.info(f"Starting Cards ETL. Reading from {raw_path}...")

    if not os.path.exists(customers_curated_path):
        raise FileNotFoundError(f"Curated customers not found: {customers_curated_path}")
    if not os.path.exists(accounts_curated_path):
        raise FileNotFoundError(f"Curated accounts not found: {accounts_curated_path}")

    # Load valid customers and accounts for dual referential integrity
    cust_df = read_csv_safe(customers_curated_path)
    valid_customer_ids = set(cust_df["customer_id"].astype(int))

    acc_df = read_csv_safe(accounts_curated_path)
    valid_account_ids = set(acc_df["account_id"].astype(int))

    logger.info(f"Loaded {len(valid_customer_ids):,} valid customers and {len(valid_account_ids):,} valid accounts.")

    df_raw = read_csv_safe(raw_path)
    total_raw = len(df_raw)

    # Validate
    good_df, bad_df = validate_cards(df_raw, valid_customer_ids, valid_account_ids)

    # Transform
    clean_df = transform_cards(good_df)

    # Persist
    save_curated_and_bad(clean_df, bad_df, curated_path, bad_path)

    end_time = datetime.now()
    summary = log_pipeline_summary(
        pipeline_name="process_cards",
        start_time=start_time,
        end_time=end_time,
        total_records=total_raw,
        curated_records=len(clean_df),
        bad_records=len(bad_df)
    )

    return summary

if __name__ == "__main__":
    run_cards_pipeline()
