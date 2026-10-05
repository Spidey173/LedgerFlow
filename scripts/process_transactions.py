import sys
import os
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import (
    TRANSACTIONS_RAW, TRANSACTIONS_CURATED, TRANSACTIONS_BAD,
    ACCOUNTS_CURATED
)
from utils.logger import get_logger
from utils.file_handler import read_csv_safe
from validation.transaction_validation import validate_transactions
from transformation.transaction_transform import transform_transactions

logger = get_logger("process_transactions")

def run_transactions_pipeline(raw_path: str = TRANSACTIONS_RAW,
                              accounts_curated_path: str = ACCOUNTS_CURATED,
                              curated_path: str = TRANSACTIONS_CURATED,
                              bad_path: str = TRANSACTIONS_BAD,
                              chunksize: int = 250000):
    logger.info(f"Starting Transactions ETL. Reading from {raw_path}...")

    if not os.path.exists(accounts_curated_path):
        raise FileNotFoundError(
            f"Curated accounts not found at {accounts_curated_path}. "
            "Please run process_accounts.py first!"
        )

    # Load valid account IDs for referential integrity
    logger.info(f"Loading curated account IDs from {accounts_curated_path}...")
    acc_df = pd.read_csv(accounts_curated_path, usecols=["account_id"])
    valid_account_ids = set(acc_df["account_id"].astype(int))
    logger.info(f"Loaded {len(valid_account_ids):,} valid account IDs.")

    os.makedirs(os.path.dirname(curated_path), exist_ok=True)
    os.makedirs(os.path.dirname(bad_path), exist_ok=True)

    # Process in chunks to handle 2,000,000+ rows smoothly with low memory footprint
    total_raw = 0
    total_curated = 0
    total_bad = 0

    first_good = True
    first_bad = True

    chunk_idx = 0
    for chunk in pd.read_csv(raw_path, chunksize=chunksize):
        chunk_idx += 1
        total_raw += len(chunk)

        good_chunk, bad_chunk = validate_transactions(chunk, valid_account_ids)
        clean_good_chunk = transform_transactions(good_chunk)

        total_curated += len(clean_good_chunk)
        total_bad += len(bad_chunk)

        # Write good records
        if not clean_good_chunk.empty:
            clean_good_chunk.to_csv(
                curated_path,
                mode="w" if first_good else "a",
                index=False,
                header=first_good
            )
            first_good = False

        # Write bad records
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

    logger.info("Transactions ETL Completed Successfully!")
    logger.info(f"  • Total input transactions: {total_raw:,}")
    logger.info(f"  • Curated transactions:     {total_curated:,} -> {curated_path}")
    logger.info(f"  • Bad transactions (DLQ):   {total_bad:,} -> {bad_path}")

    return {"total": total_raw, "curated": total_curated, "bad": total_bad}

if __name__ == "__main__":
    run_transactions_pipeline()
