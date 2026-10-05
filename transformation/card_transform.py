import pandas as pd

def transform_cards(good_df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans and standardizes card records:
    - Standardizes text fields (card_type, status)
    - Formats dates to YYYY-MM-DD
    - Sets clean numeric types
    """
    df = good_df.copy()

    df["card_type"] = df["card_type"].astype(str).str.strip().str.title()
    df["status"] = df["status"].astype(str).str.strip().str.capitalize()

    df["issue_date"] = pd.to_datetime(df["issue_date"], errors="coerce").dt.strftime("%Y-%m-%d")
    df["expiry_date"] = pd.to_datetime(df["expiry_date"], errors="coerce").dt.strftime("%Y-%m-%d")

    df["card_id"] = df["card_id"].astype(int)
    df["customer_id"] = df["customer_id"].astype(int)
    df["account_id"] = df["account_id"].astype(int)
    df["credit_limit"] = df["credit_limit"].astype(float).round(2)

    return df
