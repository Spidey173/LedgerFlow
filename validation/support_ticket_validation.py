import pandas as pd
from typing import Tuple, Set
from utils.config import VALID_TICKET_STATUSES

def validate_support_tickets(df_raw: pd.DataFrame, valid_customer_ids: Set[int]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Validates support_tickets dataset:
    - ticket_id is not null and unique
    - customer_id exists in curated customers
    - issue_type is non-empty
    - status in valid statuses
    - date_opened and date_resolved are valid dates
    - date_resolved >= date_opened
    - satisfaction_score between 1 and 5
    """
    is_missing_id = df_raw["ticket_id"].isna() | (df_raw["ticket_id"].astype(str).str.strip() == "")
    is_duplicate_id = df_raw.duplicated(subset=["ticket_id"], keep=False)

    cust_id_numeric = pd.to_numeric(df_raw["customer_id"], errors="coerce")
    is_orphan_customer = ~cust_id_numeric.isin(valid_customer_ids)

    is_missing_issue = df_raw["issue_type"].isna() | (df_raw["issue_type"].astype(str).str.strip() == "")

    status_str = df_raw["status"].astype(str).str.strip()
    valid_status_upper = {s.upper() for s in VALID_TICKET_STATUSES}
    is_invalid_status = ~status_str.str.upper().isin(valid_status_upper)

    opened_parsed = pd.to_datetime(df_raw["date_opened"], errors="coerce")
    resolved_parsed = pd.to_datetime(df_raw["date_resolved"], errors="coerce")
    is_invalid_opened = opened_parsed.isna()
    is_chronology_error = (~opened_parsed.isna()) & (~resolved_parsed.isna()) & (resolved_parsed < opened_parsed)

    score_numeric = pd.to_numeric(df_raw["satisfaction_score"], errors="coerce")
    is_invalid_score = score_numeric.isna() | (score_numeric < 1) | (score_numeric > 5)

    is_bad = (
        is_missing_id
        | is_duplicate_id
        | is_orphan_customer
        | is_missing_issue
        | is_invalid_status
        | is_invalid_opened
        | is_chronology_error
        | is_invalid_score
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
                reasons.append("Missing Ticket ID")
                stages.append("Schema Integrity")
            if is_duplicate_id.loc[i]:
                reasons.append("Duplicate Ticket ID")
                stages.append("Primary Key Constraint")
            if is_orphan_customer.loc[i]:
                reasons.append(f"Customer ID {cust_id_numeric.loc[i]} not found in Curated Customers")
                stages.append("Referential Integrity")
            if is_missing_issue.loc[i]:
                reasons.append("Missing Issue Type")
                stages.append("Domain Boundary Check")
            if is_invalid_status.loc[i]:
                reasons.append(f"Invalid Status ({status_str.loc[i]})")
                stages.append("Domain Boundary Check")
            if is_invalid_opened.loc[i]:
                reasons.append("Invalid Date Opened")
                stages.append("Format Validation")
            if is_chronology_error.loc[i]:
                reasons.append(f"Date resolved ({resolved_parsed.loc[i]}) before opened ({opened_parsed.loc[i]})")
                stages.append("Chronological Logic")
            if is_invalid_score.loc[i]:
                reasons.append(f"Invalid Satisfaction Score ({score_numeric.loc[i]})")
                stages.append("Domain Boundary Check")

            reasons_list.append("; ".join(reasons))
            stages_list.append("; ".join(dict.fromkeys(stages)))

        bad_df["rejection_reason"] = reasons_list
        bad_df["validation_stage"] = stages_list
        bad_df["pipeline_name"] = "process_support_tickets"
        bad_df["processed_at"] = now_str

    return good_df, bad_df
