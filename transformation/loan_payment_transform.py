import pandas as pd

def transform_loan_payments(good_df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans and standardizes loan payment records:
    - Formats payment_date to YYYY-MM-DD
    - Standardizes amounts (amount_paid, principal_component, interest_component) to 2 decimals
    - Casts integer identifiers and flags
    """
    df = good_df.copy()

    df["payment_date"] = pd.to_datetime(df["payment_date"], errors="coerce").dt.strftime("%Y-%m-%d")

    df["payment_id"] = df["payment_id"].astype(int)
    df["loan_id"] = df["loan_id"].astype(int)
    df["late_payment_flag"] = df["late_payment_flag"].astype(int)

    df["amount_paid"] = df["amount_paid"].astype(float).round(2)
    df["principal_component"] = df["principal_component"].astype(float).round(2)
    df["interest_component"] = df["interest_component"].astype(float).round(2)

    return df
