import pandas as pd
from typing import Tuple, Set

def validate_loan_payments(df_raw: pd.DataFrame, valid_loan_ids: Set[int]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Validates loan_payments dataframe:
    1. Primary Key: payment_id is not null and unique.
    2. Referential Integrity: loan_id exists in curated loans.
    3. Amount Paid: numeric and strictly positive (> 0).
    4. Principal & Interest components: non-negative and sum equals amount_paid (within tolerance).
    5. Late payment flag: must be 0 or 1.
    6. Payment Date: valid parseable date.

    Returns: (good_df, bad_df with rejection_reason, validation_stage, pipeline_name, processed_at)
    """
    # 1. Primary Key
    is_missing_id = df_raw["payment_id"].isna() | (df_raw["payment_id"].astype(str).str.strip() == "")
    is_duplicate_id = df_raw.duplicated(subset=["payment_id"], keep=False)

    # 2. Referential integrity: loan_id in valid_loan_ids
    loan_id_numeric = pd.to_numeric(df_raw["loan_id"], errors="coerce")
    is_orphan_loan = ~loan_id_numeric.isin(valid_loan_ids)

    # 3. Amount Paid > 0
    amount_numeric = pd.to_numeric(df_raw["amount_paid"], errors="coerce")
    is_invalid_amount = amount_numeric.isna() | (amount_numeric <= 0)

    # 4. Principal & Interest components consistency
    principal_numeric = pd.to_numeric(df_raw["principal_component"], errors="coerce")
    interest_numeric = pd.to_numeric(df_raw["interest_component"], errors="coerce")
    component_diff = (principal_numeric + interest_numeric - amount_numeric).abs()
    is_invalid_components = (
        principal_numeric.isna()
        | interest_numeric.isna()
        | (principal_numeric < 0)
        | (interest_numeric < 0)
        | (component_diff > 0.05)  # 5 cents rounding tolerance
    )

    # 5. Late payment flag (0 or 1)
    flag_numeric = pd.to_numeric(df_raw["late_payment_flag"], errors="coerce")
    is_invalid_flag = flag_numeric.isna() | (~flag_numeric.isin([0, 1]))

    # 6. Payment date valid
    parsed_dates = pd.to_datetime(df_raw["payment_date"], errors="coerce")
    is_invalid_date = parsed_dates.isna()

    # Consolidate
    is_bad = (
        is_missing_id
        | is_duplicate_id
        | is_orphan_loan
        | is_invalid_amount
        | is_invalid_components
        | is_invalid_flag
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
                reasons.append("Missing Payment ID")
                stages.append("Schema Integrity")
            if is_duplicate_id.loc[i]:
                reasons.append("Duplicate Payment ID")
                stages.append("Primary Key Constraint")
            if is_orphan_loan.loc[i]:
                reasons.append(f"Loan ID {loan_id_numeric.loc[i]} not found in Curated Loans")
                stages.append("Referential Integrity")
            if is_invalid_amount.loc[i]:
                reasons.append(f"Invalid Amount Paid ({amount_numeric.loc[i]})")
                stages.append("Domain Boundary Check")
            if is_invalid_components.loc[i]:
                reasons.append("Principal and Interest components do not balance to Amount Paid")
                stages.append("Accounting Reconciliation")
            if is_invalid_flag.loc[i]:
                reasons.append(f"Invalid Late Payment Flag ({df_raw['late_payment_flag'].loc[i]})")
                stages.append("Domain Boundary Check")
            if is_invalid_date.loc[i]:
                reasons.append(f"Invalid Payment Date ({df_raw['payment_date'].loc[i]})")
                stages.append("Format Validation")

            reasons_list.append("; ".join(reasons))
            stages_list.append("; ".join(dict.fromkeys(stages)))

        bad_df["rejection_reason"] = reasons_list
        bad_df["validation_stage"] = stages_list
        bad_df["pipeline_name"] = "process_loan_payments"
        bad_df["processed_at"] = now_str

    return good_df, bad_df
