import sys
import os
from datetime import datetime
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import (
    EMPLOYEES_RAW, EMPLOYEES_CURATED, EMPLOYEES_BAD,
    BRANCHES_CURATED
)
from utils.logger import get_logger, log_pipeline_summary
from utils.file_handler import read_csv_safe, save_curated_and_bad
from validation.employee_validation import validate_employees
from transformation.employee_transform import transform_employees

logger = get_logger("process_employees")

def run_employees_pipeline(raw_path: str = EMPLOYEES_RAW,
                           branches_curated_path: str = BRANCHES_CURATED,
                           curated_path: str = EMPLOYEES_CURATED,
                           bad_path: str = EMPLOYEES_BAD):
    start_time = datetime.now()
    logger.info(f"Starting Employees ETL. Reading from {raw_path}...")

    if not os.path.exists(branches_curated_path):
        raise FileNotFoundError(f"Curated branches not found at: {branches_curated_path}")

    branch_df = read_csv_safe(branches_curated_path)
    valid_branch_ids = set(branch_df["branch_id"].astype(int))

    df_raw = read_csv_safe(raw_path)
    total_raw = len(df_raw)

    good_df, bad_df = validate_employees(df_raw, valid_branch_ids)
    clean_df = transform_employees(good_df)

    save_curated_and_bad(clean_df, bad_df, curated_path, bad_path)

    end_time = datetime.now()
    summary = log_pipeline_summary(
        pipeline_name="process_employees",
        start_time=start_time,
        end_time=end_time,
        total_records=total_raw,
        curated_records=len(clean_df),
        bad_records=len(bad_df)
    )
    return summary

if __name__ == "__main__":
    run_employees_pipeline()
