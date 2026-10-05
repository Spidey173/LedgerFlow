import pandas as pd
from typing import Tuple, Set
from utils.config import VALID_LOAN_TYPES, VALID_LOAN_STATUSES

def validate_loans(df_raw: pd.DataFrame, valid_customer_ids: Set[int]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Validates loans dataframe:
    1. Primary Key: loan_id is not null and unique.
    2. Referential Integrity: customer_id exists in curated customers.
    3. Loan Amount: numeric and strictly positive (> 0).
    4. Interest Rate: numeric, positive, within realistic bounds (e.g. 1.0% to 50.0%).
    5. Term Months: integer > 0.
    6. Loan Type: belongs to approved bank loan types.
    7. Loan Status: belongs to approved loan statuses.
    8. Start Date: valid parseable date.

    Returns: (good_df, bad_df with rejection_reason, validation_stage, pipeline_name, processed_at)
    """
    # 1. Primary Key
    is_missing_id = df_raw["loan_id"].isna() | (df_raw["loan_id"].astype(str).str.strip() == "")
    is_duplicate_id = df_raw.duplicated(subset=["loan_id"], keep=False)

    # 2. Referential integrity: customer_id
    cust_id_numeric = pd.to_numeric(df_raw["customer_id"], errors="coerce")
    is_orphan_customer = ~cust_id_numeric.isin(valid_customer_ids)

    # 3. Loan Amount
    amount_numeric = pd.to_numeric(df_raw["loan_amount"], errors="coerce")
    is_invalid_amount = amount_numeric.isna() | (amount_numeric <= 0)

    # 4. Interest Rate (1.0% to 50.0%)
    rate_numeric = pd.to_numeric(df_raw["interest_rate"], errors="coerce")
    is_invalid_rate = rate_numeric.isna() | (rate_numeric <= 0) | (rate_numeric > 50)

    # 5. Term Months
    term_numeric = pd.to_numeric(df_raw["term_months"], errors="coerce")
    is_invalid_term = term_numeric.isna() | (term_numeric <= 0)

    # 6. Loan Type (case-insensitive)
    valid_types_upper = {t.upper() for t in VALID_LOAN_TYPES}
    loan_type_str = df_raw["loan_type"].astype(str).str.strip()
    is_invalid_type = ~loan_type_str.str.upper().isin(valid_types_upper)

    # 7. Status (case-insensitive)
    valid_status_upper = {s.upper() for s in VALID_LOAN_STATUSES}
    status_str = df_raw["status"].astype(str).str.strip()
    is_invalid_status = ~status_str.str.upper().isin(valid_status_upper)

    # 8. Start Date
    start_date_parsed = pd.to_datetime(df_raw["start_date"], errors="coerce")
    is_invalid_date = start_date_parsed.isna()

    # Consolidate bad rows
    is_bad = (
        is_missing_id
        | is_duplicate_id
        | is_orphan_customer
        | is_invalid_amount
        | is_invalid_rate
        | is_invalid_term
        | is_invalid_type
        | is_invalid_status
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
                reasons.append("Missing Loan ID")
                stages.append("Schema Integrity")
            if is_duplicate_id.loc[i]:
                reasons.append("Duplicate Loan ID")
                stages.append("Primary Key Constraint")
            if is_orphan_customer.loc[i]:
                reasons.append(f"Customer ID {cust_id_numeric.loc[i]} not found in Curated Customers")
                stages.append("Referential Integrity")
            if is_invalid_amount.loc[i]:
                reasons.append(f"Invalid Loan Amount ({amount_numeric.loc[i]})")
                stages.append("Domain Boundary Check")
            if is_invalid_rate.loc[i]:
                reasons.append(f"Invalid Interest Rate ({rate_numeric.loc[i]})")
                stages.append("Domain Boundary Check")
            if is_invalid_term.loc[i]:
                reasons.append(f"Invalid Term Months ({term_numeric.loc[i]})")
                stages.append("Domain Boundary Check")
            if is_invalid_type.loc[i]:
                reasons.append(f"Invalid Loan Type ({loan_type_str.loc[i]})")
                stages.append("Domain Boundary Check")
            if is_invalid_status.loc[i]:
                reasons.append(f"Invalid Loan Status ({status_str.loc[i]})")
                stages.append("Domain Boundary Check")
            if is_invalid_date.loc[i]:
                reasons.append(f"Invalid Start Date ({df_raw['start_date'].loc[i]})")
                stages.append("Format Validation")

            reasons_list.append("; ".join(reasons))
            stages_list.append("; ".join(dict.fromkeys(stages)))

        bad_df["rejection_reason"] = reasons_list
        bad_df["validation_stage"] = stages_list
        bad_df["pipeline_name"] = "process_loans"
        bad_df["processed_at"] = now_str

    return good_df, bad_df
