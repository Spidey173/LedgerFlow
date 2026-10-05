import pandas as pd
from typing import Tuple, Set
from utils.config import VALID_CARD_TYPES, VALID_CARD_STATUSES

def validate_cards(df_raw: pd.DataFrame,
                   valid_customer_ids: Set[int],
                   valid_account_ids: Set[int]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Validates cards dataframe:
    1. Primary Key: card_id is not null and unique.
    2. Referential Integrity:
       - customer_id in valid_customer_ids
       - account_id in valid_account_ids
    3. Card Type: belongs to approved bank card types.
    4. Status: belongs to approved card statuses (Active, Blocked, Expired).
    5. Dates: issue_date and expiry_date are parseable dates; expiry_date >= issue_date.
    6. Credit Limit: numeric and >= 0.

    Returns: (good_df, bad_df with rejection_reason, validation_stage, pipeline_name, processed_at)
    """
    # 1. Primary Key
    is_missing_id = df_raw["card_id"].isna() | (df_raw["card_id"].astype(str).str.strip() == "")
    is_duplicate_id = df_raw.duplicated(subset=["card_id"], keep=False)

    # 2. Referential integrity
    cust_id_numeric = pd.to_numeric(df_raw["customer_id"], errors="coerce")
    is_orphan_customer = ~cust_id_numeric.isin(valid_customer_ids)

    acc_id_numeric = pd.to_numeric(df_raw["account_id"], errors="coerce")
    is_orphan_account = ~acc_id_numeric.isin(valid_account_ids)

    # 3. Card Type (case-insensitive check)
    valid_types_upper = {t.upper() for t in VALID_CARD_TYPES}
    card_type_str = df_raw["card_type"].astype(str).str.strip()
    is_invalid_type = ~card_type_str.str.upper().isin(valid_types_upper)

    # 4. Status (case-insensitive check)
    valid_status_upper = {s.upper() for s in VALID_CARD_STATUSES}
    status_str = df_raw["status"].astype(str).str.strip()
    is_invalid_status = ~status_str.str.upper().isin(valid_status_upper)

    # 5. Dates
    issue_date_parsed = pd.to_datetime(df_raw["issue_date"], errors="coerce")
    expiry_date_parsed = pd.to_datetime(df_raw["expiry_date"], errors="coerce")
    is_invalid_dates = issue_date_parsed.isna() | expiry_date_parsed.isna()
    is_expiry_before_issue = (~is_invalid_dates) & (expiry_date_parsed < issue_date_parsed)

    # 6. Credit Limit
    limit_numeric = pd.to_numeric(df_raw["credit_limit"], errors="coerce")
    is_invalid_limit = limit_numeric.isna() | (limit_numeric < 0)

    # Consolidate
    is_bad = (
        is_missing_id
        | is_duplicate_id
        | is_orphan_customer
        | is_orphan_account
        | is_invalid_type
        | is_invalid_status
        | is_invalid_dates
        | is_expiry_before_issue
        | is_invalid_limit
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
                reasons.append("Missing Card ID")
                stages.append("Schema Integrity")
            if is_duplicate_id.loc[i]:
                reasons.append("Duplicate Card ID")
                stages.append("Primary Key Constraint")
            if is_orphan_customer.loc[i]:
                reasons.append(f"Customer ID {cust_id_numeric.loc[i]} not found in Curated Customers")
                stages.append("Referential Integrity")
            if is_orphan_account.loc[i]:
                reasons.append(f"Account ID {acc_id_numeric.loc[i]} not found in Curated Accounts")
                stages.append("Referential Integrity")
            if is_invalid_type.loc[i]:
                reasons.append(f"Invalid Card Type ({card_type_str.loc[i]})")
                stages.append("Domain Boundary Check")
            if is_invalid_status.loc[i]:
                reasons.append(f"Invalid Card Status ({status_str.loc[i]})")
                stages.append("Domain Boundary Check")
            if is_invalid_dates.loc[i]:
                reasons.append("Invalid date format in issue_date or expiry_date")
                stages.append("Format Validation")
            if is_expiry_before_issue.loc[i]:
                reasons.append(f"Expiry date ({expiry_date_parsed.loc[i]}) before issue date ({issue_date_parsed.loc[i]})")
                stages.append("Chronological Logic")
            if is_invalid_limit.loc[i]:
                reasons.append(f"Invalid Credit Limit ({limit_numeric.loc[i]})")
                stages.append("Domain Boundary Check")

            reasons_list.append("; ".join(reasons))
            stages_list.append("; ".join(dict.fromkeys(stages)))

        bad_df["rejection_reason"] = reasons_list
        bad_df["validation_stage"] = stages_list
        bad_df["pipeline_name"] = "process_cards"
        bad_df["processed_at"] = now_str

    return good_df, bad_df
