import sys
import os
from datetime import datetime
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import (
    CARD_TRANSACTIONS_RAW, CARD_TRANSACTIONS_CURATED, CARD_TRANSACTIONS_BAD,
    CARDS_CURATED
)
from utils.logger import get_logger, log_pipeline_summary
from utils.file_handler import read_csv_safe
from validation.card_transaction_validation import validate_card_transactions
from transformation.card_transaction_transform import transform_card_transactions

logger = get_logger("process_card_transactions")

def run_card_transactions_pipeline(raw_path: str = CARD_TRANSACTIONS_RAW,
                                   cards_curated_path: str = CARDS_CURATED,
                                   curated_path: str = CARD_TRANSACTIONS_CURATED,
                                   bad_path: str = CARD_TRANSACTIONS_BAD,
                                   chunksize: int = 300000):
    start_time = datetime.now()
    logger.info(f"Starting Card Transactions ETL. Reading from {raw_path}...")

    if not os.path.exists(cards_curated_path):
        raise FileNotFoundError(
            f"Curated cards file not found at: {cards_curated_path}. "
            "Please run process_cards.py first!"
        )

    # Load valid card IDs
    logger.info(f"Loading curated card IDs from {cards_curated_path}...")
    card_df = pd.read_csv(cards_curated_path, usecols=["card_id"])
    valid_card_ids = set(card_df["card_id"].astype(int))
    logger.info(f"Loaded {len(valid_card_ids):,} valid card IDs.")

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

        good_chunk, bad_chunk = validate_card_transactions(chunk, valid_card_ids)
        clean_good_chunk = transform_card_transactions(good_chunk)

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
        pipeline_name="process_card_transactions",
        start_time=start_time,
        end_time=end_time,
        total_records=total_raw,
        curated_records=total_curated,
        bad_records=total_bad
    )

    return summary

if __name__ == "__main__":
    run_card_transactions_pipeline()
