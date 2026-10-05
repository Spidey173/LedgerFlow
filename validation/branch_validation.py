import pandas as pd
from typing import Tuple

def validate_branches(df_raw: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Validates branches dataset:
    - branch_id is not null and unique
    - branch_name, city, state are not empty
    - opened_date is a valid date
    - ifsc_code is non-empty string
    """
    is_missing_id = df_raw["branch_id"].isna() | (df_raw["branch_id"].astype(str).str.strip() == "")
    is_duplicate_id = df_raw.duplicated(subset=["branch_id"], keep=False)

    is_missing_name = df_raw["branch_name"].isna() | (df_raw["branch_name"].astype(str).str.strip() == "")
    is_missing_city = df_raw["city"].isna() | (df_raw["city"].astype(str).str.strip() == "")
    is_missing_state = df_raw["state"].isna() | (df_raw["state"].astype(str).str.strip() == "")
    is_invalid_date = pd.to_datetime(df_raw["opened_date"], errors="coerce").isna()
    is_missing_ifsc = df_raw["ifsc_code"].isna() | (df_raw["ifsc_code"].astype(str).str.strip() == "")

    is_bad = (
        is_missing_id
        | is_duplicate_id
        | is_missing_name
        | is_missing_city
        | is_missing_state
        | is_invalid_date
        | is_missing_ifsc
    )

    bad_df = df_raw[is_bad].copy()
    good_df = df_raw[~is_bad].copy()

    if not bad_df.empty:
        now_str = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        bad_indices = bad_df.index
        reasons_list = []
        stages_list = []
        for i in bad_indices:
            reasons = []
            stages = []
            if is_missing_id.loc[i]:
                reasons.append("Missing Branch ID")
                stages.append("Schema Integrity")
            if is_duplicate_id.loc[i]:
                reasons.append("Duplicate Branch ID")
                stages.append("Primary Key Constraint")
            if is_missing_name.loc[i]:
                reasons.append("Missing Branch Name")
                stages.append("Domain Boundary Check")
            if is_missing_city.loc[i] or is_missing_state.loc[i]:
                reasons.append("Missing City or State")
                stages.append("Domain Boundary Check")
            if is_invalid_date.loc[i]:
                reasons.append("Invalid Opened Date")
                stages.append("Format Validation")
            if is_missing_ifsc.loc[i]:
                reasons.append("Missing IFSC Code")
                stages.append("Domain Boundary Check")

            reasons_list.append("; ".join(reasons))
            stages_list.append("; ".join(dict.fromkeys(stages)))

        bad_df["rejection_reason"] = reasons_list
        bad_df["validation_stage"] = stages_list
        bad_df["pipeline_name"] = "process_branches"
        bad_df["processed_at"] = now_str

    return good_df, bad_df
