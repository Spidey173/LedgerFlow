import pandas as pd
from typing import Tuple, Set
from utils.config import VALID_ACCOUNT_TYPES, VALID_ACCOUNT_STATUSES

def validate_accounts(df_raw: pd.DataFrame, valid_customer_ids: Set[int]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Validates accounts dataframe:
    - account_id is not null
    - account_id is unique
    - customer_id exists in curated customers dataset (Referential Integrity)
    - balance is valid numeric and >= 0 (or valid overdraft according to bank policy)
    - account_type in approved bank account types
    - status in approved account statuses

    Returns: (good_df, bad_df with rejection_reason)
    """
    # 1. Missing account_id
    is_missing_id = df_raw["account_id"].isna() | (df_raw["account_id"].astype(str).str.strip() == "")

    # 2. Duplicate account_id
    is_duplicate_id = df_raw.duplicated(subset=["account_id"], keep=False)

    # 3. Referential integrity: customer_id exists in curated customers
    # Handle possible string/numeric mismatch safely
    cust_id_numeric = pd.to_numeric(df_raw["customer_id"], errors="coerce")
    is_orphan_customer = ~cust_id_numeric.isin(valid_customer_ids)

    # 4. Valid Balance: numeric and non-negative
    balance_numeric = pd.to_numeric(df_raw["balance"], errors="coerce")
    is_invalid_balance = balance_numeric.isna() | (balance_numeric < 0)

    # 5. Account type valid (case-insensitive check)
    valid_types_upper = {t.upper() for t in VALID_ACCOUNT_TYPES}
    account_type_clean = df_raw["account_type"].astype(str).str.strip()
    is_invalid_type = ~account_type_clean.str.upper().isin(valid_types_upper)

    # 6. Status valid
    status_clean = df_raw["status"].astype(str).str.strip().str.capitalize()
    is_invalid_status = ~status_clean.isin(VALID_ACCOUNT_STATUSES)

    # Overall bad records mask
    is_bad = (
        is_missing_id
        | is_duplicate_id
        | is_orphan_customer
        | is_invalid_balance
        | is_invalid_type
        | is_invalid_status
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
                reasons.append("Missing Account ID")
                stages.append("Schema Integrity")
            if is_duplicate_id.loc[i]:
                reasons.append("Duplicate Account ID")
                stages.append("Primary Key Constraint")
            if is_orphan_customer.loc[i]:
                reasons.append(f"Customer ID {cust_id_numeric.loc[i]} not found in Curated Customers")
                stages.append("Referential Integrity")
            if is_invalid_balance.loc[i]:
                reasons.append(f"Invalid Balance ({balance_numeric.loc[i]})")
                stages.append("Domain Boundary Check")
            if is_invalid_type.loc[i]:
                reasons.append(f"Invalid Account Type ({account_type_clean.loc[i]})")
                stages.append("Domain Boundary Check")
            if is_invalid_status.loc[i]:
                reasons.append(f"Invalid Status ({status_clean.loc[i]})")
                stages.append("Domain Boundary Check")

            reasons_list.append("; ".join(reasons))
            stages_list.append("; ".join(dict.fromkeys(stages)))

        bad_df["rejection_reason"] = reasons_list
        bad_df["validation_stage"] = stages_list
        bad_df["pipeline_name"] = "process_accounts"
        bad_df["processed_at"] = now_str

    return good_df, bad_df
