import pandas as pd

def transform_customers(good_df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans validated customer records:
    - Strips whitespace
    - Title cases string columns (name, city, state, occupation)
    - Lowercases email
    - Standardizes dates to YYYY-MM-DD
    - Sets clean data types
    """
    df = good_df.copy()

    for col in ["name", "city", "state", "occupation"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.title()

    if "email" in df.columns:
        df["email"] = df["email"].astype(str).str.strip().str.lower()

    if "gender" in df.columns:
        df["gender"] = df["gender"].astype(str).str.strip().str.capitalize()

    for date_col in ["date_of_birth", "join_date"]:
        if date_col in df.columns:
            df[date_col] = pd.to_datetime(df[date_col], errors="coerce").dt.strftime("%Y-%m-%d")

    df["customer_id"] = df["customer_id"].astype(int)
    df["annual_income"] = df["annual_income"].astype(float)
    df["credit_score"] = df["credit_score"].astype(int)

    return df
