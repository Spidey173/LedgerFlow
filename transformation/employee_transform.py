import pandas as pd

def transform_employees(good_df: pd.DataFrame) -> pd.DataFrame:
    df = good_df.copy()
    df["name"] = df["name"].astype(str).str.strip().str.title()
    df["role"] = df["role"].astype(str).str.strip().str.title()
    df["hire_date"] = pd.to_datetime(df["hire_date"], errors="coerce").dt.strftime("%Y-%m-%d")
    df["employee_id"] = df["employee_id"].astype(int)
    df["branch_id"] = df["branch_id"].astype(int)
    df["salary"] = df["salary"].astype(float).round(2)
    return df
