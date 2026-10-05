import pandas as pd
from typing import Tuple
from utils.config import EMAIL_REGEX, CREDIT_SCORE_MIN, CREDIT_SCORE_MAX

def validate_customers(df_raw: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Validates customers dataframe:
    - customer_id is not null
    - customer_id is unique
    - email is valid
    - credit_score between 300 and 850
    - annual_income is positive (> 0)

    Returns: (good_df, bad_df with rejection_reason)
    """
    is_missing_id = df_raw["customer_id"].isna() | (df_raw["customer_id"].astype(str).str.strip() == "")
    is_duplicate_id = df_raw.duplicated(subset=["customer_id"], keep=False)

    is_invalid_email = df_raw["email"].isna() | (
        ~df_raw["email"].astype(str).str.strip().str.match(EMAIL_REGEX)
    )

    credit_numeric = pd.to_numeric(df_raw["credit_score"], errors="coerce")
    is_invalid_credit = credit_numeric.isna() | (credit_numeric < CREDIT_SCORE_MIN) | (credit_numeric > CREDIT_SCORE_MAX)

    income_numeric = pd.to_numeric(df_raw["annual_income"], errors="coerce")
    is_invalid_income = income_numeric.isna() | (income_numeric <= 0)

    is_bad = is_missing_id | is_duplicate_id | is_invalid_email | is_invalid_credit | is_invalid_income

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
                reasons.append("Missing Customer ID")
                stages.append("Schema Integrity")
            if is_duplicate_id.loc[i]:
                reasons.append("Duplicate Customer ID")
                stages.append("Primary Key Constraint")
            if is_invalid_email.loc[i]:
                reasons.append("Invalid Email")
                stages.append("Format Validation")
            if is_invalid_credit.loc[i]:
                reasons.append(f"Invalid Credit Score ({credit_numeric.loc[i]})")
                stages.append("Domain Boundary Check")
            if is_invalid_income.loc[i]:
                reasons.append("Non-positive Annual Income")
                stages.append("Domain Boundary Check")

            reasons_list.append("; ".join(reasons))
            stages_list.append("; ".join(dict.fromkeys(stages)))

        bad_df["rejection_reason"] = reasons_list
        bad_df["validation_stage"] = stages_list
        bad_df["pipeline_name"] = "process_customers"
        bad_df["processed_at"] = now_str

    return good_df, bad_df
