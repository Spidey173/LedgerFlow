import pandas as pd
from typing import Tuple, Set
from utils.config import VALID_EMPLOYEE_ROLES

def validate_employees(df_raw: pd.DataFrame, valid_branch_ids: Set[int]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Validates employees dataset:
    - employee_id is not null and unique
    - branch_id exists in curated branches
    - role in valid roles
    - salary is numeric and > 0
    - hire_date is valid date
    """
    is_missing_id = df_raw["employee_id"].isna() | (df_raw["employee_id"].astype(str).str.strip() == "")
    is_duplicate_id = df_raw.duplicated(subset=["employee_id"], keep=False)

    branch_id_numeric = pd.to_numeric(df_raw["branch_id"], errors="coerce")
    is_orphan_branch = ~branch_id_numeric.isin(valid_branch_ids)

    role_str = df_raw["role"].astype(str).str.strip()
    valid_roles_upper = {r.upper() for r in VALID_EMPLOYEE_ROLES}
    is_invalid_role = ~role_str.str.upper().isin(valid_roles_upper)

    salary_numeric = pd.to_numeric(df_raw["salary"], errors="coerce")
    is_invalid_salary = salary_numeric.isna() | (salary_numeric <= 0)

    is_invalid_date = pd.to_datetime(df_raw["hire_date"], errors="coerce").isna()

    is_bad = (
        is_missing_id
        | is_duplicate_id
        | is_orphan_branch
        | is_invalid_role
        | is_invalid_salary
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
                reasons.append("Missing Employee ID")
                stages.append("Schema Integrity")
            if is_duplicate_id.loc[i]:
                reasons.append("Duplicate Employee ID")
                stages.append("Primary Key Constraint")
            if is_orphan_branch.loc[i]:
                reasons.append(f"Branch ID {branch_id_numeric.loc[i]} not found in Curated Branches")
                stages.append("Referential Integrity")
            if is_invalid_role.loc[i]:
                reasons.append(f"Invalid Employee Role ({role_str.loc[i]})")
                stages.append("Domain Boundary Check")
            if is_invalid_salary.loc[i]:
                reasons.append(f"Invalid Salary ({salary_numeric.loc[i]})")
                stages.append("Domain Boundary Check")
            if is_invalid_date.loc[i]:
                reasons.append("Invalid Hire Date")
                stages.append("Format Validation")

            reasons_list.append("; ".join(reasons))
            stages_list.append("; ".join(dict.fromkeys(stages)))

        bad_df["rejection_reason"] = reasons_list
        bad_df["validation_stage"] = stages_list
        bad_df["pipeline_name"] = "process_employees"
        bad_df["processed_at"] = now_str

    return good_df, bad_df
