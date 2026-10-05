import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import CUSTOMERS_RAW, CUSTOMERS_CURATED, CUSTOMERS_BAD
from utils.logger import get_logger
from utils.file_handler import read_csv_safe, save_curated_and_bad
from validation.customer_validation import validate_customers
from transformation.customer_transform import transform_customers

logger = get_logger("process_customers")

def run_customers_pipeline(raw_path: str = CUSTOMERS_RAW,
                           curated_path: str = CUSTOMERS_CURATED,
                           bad_path: str = CUSTOMERS_BAD):
    logger.info(f"Starting Customers ETL. Reading from {raw_path}...")
    df_raw = read_csv_safe(raw_path)
    total_raw = len(df_raw)
    logger.info(f"Loaded {total_raw:,} records.")

    # Validation
    good_df, bad_df = validate_customers(df_raw)
    logger.info(f"Validation complete: {len(good_df):,} passed, {len(bad_df):,} failed.")

    # Transformation
    clean_df = transform_customers(good_df)
    logger.info(f"Transformation complete.")

    # Persist
    save_curated_and_bad(clean_df, bad_df, curated_path, bad_path)
    logger.info(f"Outputs written: Curated -> {curated_path}, DLQ -> {bad_path}")

    return {"total": total_raw, "curated": len(clean_df), "bad": len(bad_df)}

if __name__ == "__main__":
    run_customers_pipeline()
