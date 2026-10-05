import sys
import os
from datetime import datetime
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import (
    LOAN_PAYMENTS_RAW, LOAN_PAYMENTS_CURATED, LOAN_PAYMENTS_BAD,
    LOANS_CURATED
)
from utils.logger import get_logger, log_pipeline_summary
from utils.file_handler import read_csv_safe
from validation.loan_payment_validation import validate_loan_payments
from transformation.loan_payment_transform import transform_loan_payments

logger = get_logger("process_loan_payments")

def run_loan_payments_pipeline(raw_path: str = LOAN_PAYMENTS_RAW,
                               loans_curated_path: str = LOANS_CURATED,
                               curated_path: str = LOAN_PAYMENTS_CURATED,
                               bad_path: str = LOAN_PAYMENTS_BAD,
                               chunksize: int = 200000):
    start_time = datetime.now()
    logger.info(f"Starting Loan Payments ETL. Reading from {raw_path}...")

    if not os.path.exists(loans_curated_path):
        raise FileNotFoundError(
            f"Curated loans file not found at: {loans_curated_path}. "
            "Please run process_loans.py first!"
        )

    # Load valid loan IDs
    logger.info(f"Loading curated loan IDs from {loans_curated_path}...")
    loan_df = pd.read_csv(loans_curated_path, usecols=["loan_id"])
    valid_loan_ids = set(loan_df["loan_id"].astype(int))
    logger.info(f"Loaded {len(valid_loan_ids):,} valid loan IDs.")

    os.makedirs(os.path.dirname(curated_path), exist_ok=True)
    os.makedirs(os.path.dirname(bad_path), exist_ok=True)

    total_raw = 0
    total_curated = 0
    total_bad = 0

    first_good = True
    first_bad = True

    chunk_idx = 0
    for chunk in pd.read_csv(raw_path, chunksize=chunksize):
        chunk_idx += 1
        total_raw += len(chunk)

        good_chunk, bad_chunk = validate_loan_payments(chunk, valid_loan_ids)
        clean_good_chunk = transform_loan_payments(good_chunk)

        total_curated += len(clean_good_chunk)
        total_bad += len(bad_chunk)

        if not clean_good_chunk.empty:
            clean_good_chunk.to_csv(
                curated_path,
                mode="w" if first_good else "a",
                index=False,
                header=first_good
            )
            first_good = False

        if not bad_chunk.empty:
            bad_chunk.to_csv(
                bad_path,
                mode="w" if first_bad else "a",
                index=False,
                header=first_bad
            )
            first_bad = False

        logger.info(
            f"Chunk {chunk_idx}: processed {len(chunk):,} rows | "
            f"Curated so far: {total_curated:,} | Bad so far: {total_bad:,}"
        )

    end_time = datetime.now()
    summary = log_pipeline_summary(
        pipeline_name="process_loan_payments",
        start_time=start_time,
        end_time=end_time,
        total_records=total_raw,
        curated_records=total_curated,
        bad_records=total_bad
    )

    return summary

if __name__ == "__main__":
    run_loan_payments_pipeline()
