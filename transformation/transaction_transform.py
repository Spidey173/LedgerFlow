import pandas as pd

def transform_transactions(good_df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans and standardizes transaction records:
    - Strips whitespace from strings
    - Standardizes txn_type, channel, merchant_category casing
    - Standardizes txn_date to YYYY-MM-DD
    - Standardizes amount to 2 decimal places
    - Enforces proper integer and float types
    """
    df = good_df.copy()

    # Standardize string fields
    for col in ["txn_type", "channel", "merchant_category"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.title()

    # Format date
    df["txn_date"] = pd.to_datetime(df["txn_date"], errors="coerce").dt.strftime("%Y-%m-%d")

    # Clean numeric types
    df["transaction_id"] = df["transaction_id"].astype(int)
    df["account_id"] = df["account_id"].astype(int)
    df["amount"] = df["amount"].astype(float).round(2)

    return df
