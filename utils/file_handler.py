import os
import pandas as pd
from typing import Tuple

def read_csv_safe(file_path: str) -> pd.DataFrame:
    """Reads CSV safely, raising clear error if missing."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Input file not found at: {file_path}")
    return pd.read_csv(file_path)

def save_curated_and_bad(good_df: pd.DataFrame, bad_df: pd.DataFrame,
                         curated_path: str, bad_path: str) -> None:
    """Saves good records to curated path and bad records to dead letter queue."""
    os.makedirs(os.path.dirname(curated_path), exist_ok=True)
    os.makedirs(os.path.dirname(bad_path), exist_ok=True)

    good_df.to_csv(curated_path, index=False)
    bad_df.to_csv(bad_path, index=False)
