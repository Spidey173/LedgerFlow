import pandas as pd
from typing import Tuple, Set

def validate_card_transactions(df_raw: pd.DataFrame, valid_card_ids: Set[int]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Validates card_transactions dataframe:
    1. Primary Key: card_txn_id is not null and unique.
    2. Referential Integrity: card_id exists in curated cards.
    3. Amount: numeric and strictly positive (> 0).
    4. Merchant Category: non-empty string.
    5. Date: valid parseable date.
    6. Fraud Flag: binary (0 or 1).

    Returns: (good_df, bad_df with rejection_reason, validation_stage, pipeline_name, processed_at)
    """
    # 1. Primary Key
    is_missing_id = df_raw["card_txn_id"].isna() | (df_raw["card_txn_id"].astype(str).str.strip() == "")
    is_duplicate_id = df_raw.duplicated(subset=["card_txn_id"], keep=False)

    # 2. Referential integrity: card_id
    card_id_numeric = pd.to_numeric(df_raw["card_id"], errors="coerce")
    is_orphan_card = ~card_id_numeric.isin(valid_card_ids)

    # 3. Amount > 0
    amount_numeric = pd.to_numeric(df_raw["amount"], errors="coerce")
    is_invalid_amount = amount_numeric.isna() | (amount_numeric <= 0)

    # 4. Merchant Category
    is_invalid_merchant = df_raw["merchant_category"].isna() | (df_raw["merchant_category"].astype(str).str.strip() == "")

    # 5. Date
    date_parsed = pd.to_datetime(df_raw["txn_date"], errors="coerce")
    is_invalid_date = date_parsed.isna()

    # 6. Fraud flag in [0, 1]
    fraud_numeric = pd.to_numeric(df_raw["is_fraud"], errors="coerce")
    is_invalid_fraud = fraud_numeric.isna() | (~fraud_numeric.isin([0, 1]))

    # Consolidate
    is_bad = (
        is_missing_id
        | is_duplicate_id
        | is_orphan_card
        | is_invalid_amount
        | is_invalid_merchant
        | is_invalid_date
        | is_invalid_fraud
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
                reasons.append("Missing Card Txn ID")
                stages.append("Schema Integrity")
            if is_duplicate_id.loc[i]:
                reasons.append("Duplicate Card Txn ID")
                stages.append("Primary Key Constraint")
            if is_orphan_card.loc[i]:
                reasons.append(f"Card ID {card_id_numeric.loc[i]} not found in Curated Cards")
                stages.append("Referential Integrity")
            if is_invalid_amount.loc[i]:
                reasons.append(f"Invalid Transaction Amount ({amount_numeric.loc[i]})")
                stages.append("Domain Boundary Check")
            if is_invalid_merchant.loc[i]:
                reasons.append("Missing Merchant Category")
                stages.append("Domain Boundary Check")
            if is_invalid_date.loc[i]:
                reasons.append(f"Invalid Txn Date ({df_raw['txn_date'].loc[i]})")
                stages.append("Format Validation")
            if is_invalid_fraud.loc[i]:
                reasons.append(f"Invalid Fraud Flag ({df_raw['is_fraud'].loc[i]})")
                stages.append("Domain Boundary Check")

            reasons_list.append("; ".join(reasons))
            stages_list.append("; ".join(dict.fromkeys(stages)))

        bad_df["rejection_reason"] = reasons_list
        bad_df["validation_stage"] = stages_list
        bad_df["pipeline_name"] = "process_card_transactions"
        bad_df["processed_at"] = now_str

    return good_df, bad_df
