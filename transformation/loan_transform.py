import pandas as pd

def transform_loans(good_df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans and standardizes loan records:
    - Standardizes text fields (loan_type title case, status capitalized)
    - Formats start_date to YYYY-MM-DD
    - Standardizes loan_amount and interest_rate rounding
    - Casts integer identifiers
    """
    df = good_df.copy()

    df["loan_type"] = df["loan_type"].astype(str).str.strip().str.title()
    df["status"] = df["status"].astype(str).str.strip().str.title()

    df["start_date"] = pd.to_datetime(df["start_date"], errors="coerce").dt.strftime("%Y-%m-%d")

    df["loan_id"] = df["loan_id"].astype(int)
    df["customer_id"] = df["customer_id"].astype(int)
    df["branch_id"] = df["branch_id"].astype(int)
    df["term_months"] = df["term_months"].astype(int)
    df["loan_amount"] = df["loan_amount"].astype(float).round(2)
    df["interest_rate"] = df["interest_rate"].astype(float).round(2)

    return df
