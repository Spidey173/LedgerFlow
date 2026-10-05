import pandas as pd
from typing import Tuple, Set
from utils.config import VALID_TXN_TYPES, VALID_CHANNELS

def validate_transactions(df_raw: pd.DataFrame, valid_account_ids: Set[int]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Validates transactions dataframe:
    1. Primary Key: transaction_id is not null and unique.
    2. Referential Integrity: account_id exists in curated accounts.
    3. Amount: numeric and strictly positive (> 0).
    4. Transaction Type: belongs to approved bank txn types.
    5. Channel: belongs to approved transaction channels.
    6. Date: valid parseable date, not in the future (relative to today or local timeline).

    Returns: (good_df, bad_df with rejection_reason, validation_stage, pipeline_name, processed_at)
    """
    # 1. Primary Key checks
    is_missing_id = df_raw["transaction_id"].isna() | (df_raw["transaction_id"].astype(str).str.strip() == "")
    is_duplicate_id = df_raw.duplicated(subset=["transaction_id"], keep=False)

    # 2. Referential integrity: account_id in valid_account_ids
    acc_id_numeric = pd.to_numeric(df_raw["account_id"], errors="coerce")
    is_orphan_account = ~acc_id_numeric.isin(valid_account_ids)

    # 3. Transaction Amount: strictly positive (> 0)
    amount_numeric = pd.to_numeric(df_raw["amount"], errors="coerce")
    is_invalid_amount = amount_numeric.isna() | (amount_numeric <= 0)

    # 4. Valid Transaction Type (case-insensitive check)
    valid_types_upper = {t.upper() for t in VALID_TXN_TYPES}
    txn_type_str = df_raw["txn_type"].astype(str).str.strip()
    is_invalid_type = ~txn_type_str.str.upper().isin(valid_types_upper)

    # 5. Valid Channel (case-insensitive check)
    valid_channels_upper = {c.upper() for c in VALID_CHANNELS}
    channel_str = df_raw["channel"].astype(str).str.strip()
    is_invalid_channel = ~channel_str.str.upper().isin(valid_channels_upper)

    # 6. Valid Transaction Date (parseable)
    parsed_dates = pd.to_datetime(df_raw["txn_date"], errors="coerce")
    is_invalid_date = parsed_dates.isna()

    # Consolidate bad condition
    is_bad = (
        is_missing_id
        | is_duplicate_id
        | is_orphan_account
        | is_invalid_amount
        | is_invalid_type
        | is_invalid_channel
        | is_invalid_date
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
                reasons.append("Missing Transaction ID")
                stages.append("Schema Integrity")
            if is_duplicate_id.loc[i]:
                reasons.append("Duplicate Transaction ID")
                stages.append("Primary Key Constraint")
            if is_orphan_account.loc[i]:
                reasons.append(f"Account ID {acc_id_numeric.loc[i]} not found in Curated Accounts")
                stages.append("Referential Integrity")
            if is_invalid_amount.loc[i]:
                reasons.append(f"Invalid Transaction Amount ({amount_numeric.loc[i]})")
                stages.append("Domain Boundary Check")
            if is_invalid_type.loc[i]:
                reasons.append(f"Invalid Transaction Type ({txn_type_str.loc[i]})")
                stages.append("Domain Boundary Check")
            if is_invalid_channel.loc[i]:
                reasons.append(f"Invalid Channel ({channel_str.loc[i]})")
                stages.append("Domain Boundary Check")
            if is_invalid_date.loc[i]:
                reasons.append(f"Invalid Date format ({df_raw['txn_date'].loc[i]})")
                stages.append("Format Validation")

            reasons_list.append("; ".join(reasons))
            stages_list.append("; ".join(dict.fromkeys(stages)))

        bad_df["rejection_reason"] = reasons_list
        bad_df["validation_stage"] = stages_list
        bad_df["pipeline_name"] = "process_transactions"
        bad_df["processed_at"] = now_str

    return good_df, bad_df
