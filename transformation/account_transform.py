import pandas as pd

def transform_accounts(good_df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans and standardizes account records:
    - Strips whitespace
    - Title-cases account_type
    - Capitalizes status
    - Standardizes open_date to YYYY-MM-DD
    - Standardizes balance rounding to 2 decimal places
    - Casts integer types
    """
    df = good_df.copy()

    def format_account_type(val):
        s = str(val).strip()
        return "NRI" if s.upper() == "NRI" else s.title()

    df["account_type"] = df["account_type"].apply(format_account_type)
    df["status"] = df["status"].astype(str).str.strip().str.capitalize()

    if "open_date" in df.columns:
        df["open_date"] = pd.to_datetime(df["open_date"], errors="coerce").dt.strftime("%Y-%m-%d")

    df["account_id"] = df["account_id"].astype(int)
    df["customer_id"] = df["customer_id"].astype(int)
    df["branch_id"] = df["branch_id"].astype(int)
    df["balance"] = df["balance"].astype(float).round(2)

    return df
