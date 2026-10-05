import pandas as pd

def transform_card_transactions(good_df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans and standardizes card transaction records:
    - Strips whitespace and title-cases merchant_category
    - Standardizes txn_date to YYYY-MM-DD
    - Enforces numeric types and 2 decimal place rounding on amount
    """
    df = good_df.copy()

    df["merchant_category"] = df["merchant_category"].astype(str).str.strip().str.title()
    df["txn_date"] = pd.to_datetime(df["txn_date"], errors="coerce").dt.strftime("%Y-%m-%d")

    df["card_txn_id"] = df["card_txn_id"].astype(int)
    df["card_id"] = df["card_id"].astype(int)
    df["is_fraud"] = df["is_fraud"].astype(int)
    df["amount"] = df["amount"].astype(float).round(2)

    return df
