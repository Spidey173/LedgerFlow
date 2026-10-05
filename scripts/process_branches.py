import sys
import os
from datetime import datetime
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import BRANCHES_RAW, BRANCHES_CURATED, BRANCHES_BAD
from utils.logger import get_logger, log_pipeline_summary
from utils.file_handler import read_csv_safe, save_curated_and_bad
from validation.branch_validation import validate_branches
from transformation.branch_transform import transform_branches

logger = get_logger("process_branches")

def run_branches_pipeline(raw_path: str = BRANCHES_RAW,
                          curated_path: str = BRANCHES_CURATED,
                          bad_path: str = BRANCHES_BAD):
    start_time = datetime.now()
    logger.info(f"Starting Branches ETL. Reading from {raw_path}...")

    df_raw = read_csv_safe(raw_path)
    total_raw = len(df_raw)

    good_df, bad_df = validate_branches(df_raw)
    clean_df = transform_branches(good_df)

    save_curated_and_bad(clean_df, bad_df, curated_path, bad_path)

    end_time = datetime.now()
    summary = log_pipeline_summary(
        pipeline_name="process_branches",
        start_time=start_time,
        end_time=end_time,
        total_records=total_raw,
        curated_records=len(clean_df),
        bad_records=len(bad_df)
    )
    return summary

if __name__ == "__main__":
    run_branches_pipeline()
