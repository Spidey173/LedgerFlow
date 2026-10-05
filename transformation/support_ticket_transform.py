import pandas as pd

def transform_support_tickets(good_df: pd.DataFrame) -> pd.DataFrame:
    df = good_df.copy()
    df["issue_type"] = df["issue_type"].astype(str).str.strip().str.title()
    df["status"] = df["status"].astype(str).str.strip().str.capitalize()
    df["date_opened"] = pd.to_datetime(df["date_opened"], errors="coerce").dt.strftime("%Y-%m-%d")
    df["date_resolved"] = pd.to_datetime(df["date_resolved"], errors="coerce").dt.strftime("%Y-%m-%d")
    df["ticket_id"] = df["ticket_id"].astype(int)
    df["customer_id"] = df["customer_id"].astype(int)
    df["satisfaction_score"] = df["satisfaction_score"].astype(int)
    return df
