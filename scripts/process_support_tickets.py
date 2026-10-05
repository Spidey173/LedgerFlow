import sys
import os
from datetime import datetime
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import (
    SUPPORT_TICKETS_RAW, SUPPORT_TICKETS_CURATED, SUPPORT_TICKETS_BAD,
    CUSTOMERS_CURATED
)
from utils.logger import get_logger, log_pipeline_summary
from utils.file_handler import read_csv_safe, save_curated_and_bad
from validation.support_ticket_validation import validate_support_tickets
from transformation.support_ticket_transform import transform_support_tickets

logger = get_logger("process_support_tickets")

def run_support_tickets_pipeline(raw_path: str = SUPPORT_TICKETS_RAW,
                                 customers_curated_path: str = CUSTOMERS_CURATED,
                                 curated_path: str = SUPPORT_TICKETS_CURATED,
                                 bad_path: str = SUPPORT_TICKETS_BAD):
    start_time = datetime.now()
    logger.info(f"Starting Support Tickets ETL. Reading from {raw_path}...")

    if not os.path.exists(customers_curated_path):
        raise FileNotFoundError(f"Curated customers not found at: {customers_curated_path}")

    cust_df = read_csv_safe(customers_curated_path)
    valid_customer_ids = set(cust_df["customer_id"].astype(int))

    df_raw = read_csv_safe(raw_path)
    total_raw = len(df_raw)

    good_df, bad_df = validate_support_tickets(df_raw, valid_customer_ids)
    clean_df = transform_support_tickets(good_df)

    save_curated_and_bad(clean_df, bad_df, curated_path, bad_path)

    end_time = datetime.now()
    summary = log_pipeline_summary(
        pipeline_name="process_support_tickets",
        start_time=start_time,
        end_time=end_time,
        total_records=total_raw,
        curated_records=len(clean_df),
        bad_records=len(bad_df)
    )
    return summary

if __name__ == "__main__":
    run_support_tickets_pipeline()
