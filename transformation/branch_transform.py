import pandas as pd

def transform_branches(good_df: pd.DataFrame) -> pd.DataFrame:
    df = good_df.copy()
    df["branch_name"] = df["branch_name"].astype(str).str.strip().str.title()
    df["city"] = df["city"].astype(str).str.strip().str.title()
    df["state"] = df["state"].astype(str).str.strip().str.title()
    df["ifsc_code"] = df["ifsc_code"].astype(str).str.strip().str.upper()
    df["opened_date"] = pd.to_datetime(df["opened_date"], errors="coerce").dt.strftime("%Y-%m-%d")
    df["branch_id"] = df["branch_id"].astype(int)
    return df
