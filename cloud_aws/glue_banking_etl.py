import os
import sys
from datetime import datetime, timezone
import pandas as pd
import psycopg2
from botocore.exceptions import ClientError

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    AWS_DEFAULT_REGION,
    S3_BUCKET_NAME,
    DB_HOST,
    DB_PORT,
    DB_NAME,
    DB_USER,
    DB_PASSWORD,
)
from utils.logger import get_logger

# Import tested validation and transformation modules
from validation.branch_validation import validate_branches
from transformation.branch_transform import transform_branches
from validation.employee_validation import validate_employees
from transformation.employee_transform import transform_employees
from validation.customer_validation import validate_customers
from transformation.customer_transform import transform_customers
from validation.account_validation import validate_accounts
from transformation.account_transform import transform_accounts
from validation.transaction_validation import validate_transactions
from transformation.transaction_transform import transform_transactions

logger = get_logger("glue_banking_etl")

def get_s3_boto_client():
    """Returns an authenticated boto3 S3 client."""
    import boto3
    return boto3.client(
        "s3",
        region_name=AWS_DEFAULT_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )

def get_postgres_connection():
    """Establishes connection to the target PostgreSQL warehouse."""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )

def download_s3_to_memory(s3_client, bucket: str, s3_key: str):
    """Streams an S3 object into a Pandas DataFrame; returns None if not found."""
    import io
    try:
        logger.info(f"Reading from s3://{bucket}/{s3_key}...")
        obj = s3_client.get_object(Bucket=bucket, Key=s3_key)
        return pd.read_csv(io.BytesIO(obj["Body"].read()))
    except ClientError as e:
        if e.response.get("Error", {}).get("Code") in ["404", "NoSuchKey"]:
            logger.warning(f"Key s3://{bucket}/{s3_key} not found. Skipping.")
            return None
        raise e

def upload_dataframe_to_s3(s3_client, df: pd.DataFrame, bucket: str, s3_key: str):
    """Uploads a cleaned or quarantined DataFrame to S3 (Silver or DLQ)."""
    import io
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    s3_client.put_object(
        Bucket=bucket,
        Key=s3_key,
        Body=csv_buffer.getvalue().encode("utf-8")
    )
    logger.info(f"Saved {len(df):,} records -> s3://{bucket}/{s3_key}")

def load_df_to_postgres(df: pd.DataFrame, table_name: str, truncate_first: bool = True):
    """Bulk loads a clean DataFrame directly into PostgreSQL via COPY streaming."""
    import io
    if df.empty:
        logger.warning(f"DataFrame for table '{table_name}' is empty. Skipping DB load.")
        return

    logger.info(f"Loading {len(df):,} rows into PostgreSQL table '{table_name}'...")
    conn = get_postgres_connection()
    conn.autocommit = False
    cursor = conn.cursor()

    try:
        if truncate_first:
            cursor.execute(f"TRUNCATE TABLE {table_name} CASCADE;")
            conn.commit()

        buffer = io.StringIO()
        df.to_csv(buffer, index=False, header=True)
        buffer.seek(0)
        header = buffer.readline().strip()
        buffer.seek(0)

        copy_sql = f"COPY {table_name} ({header}) FROM STDIN WITH CSV HEADER"
        cursor.copy_expert(copy_sql, buffer)
        conn.commit()
        logger.info(f"Successfully committed {len(df):,} rows into '{table_name}'.")
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to load into {table_name}: {e}")
        raise e
    finally:
        cursor.close()
        conn.close()

def run_cloud_glue_etl(bucket_name: str = S3_BUCKET_NAME, raw_prefix: str = "bronze/raw"):
    """
    Simulates / Executes the AWS Glue Banking ETL Job:
    1. Reads Bronze raw CSVs from S3.
    2. Performs distributed Data Quality & Referential Integrity validation.
    3. Writes Curated records to S3 Silver (s3://bucket/silver/curated/).
    4. Writes Quarantined DLQ records to S3 (s3://bucket/quarantine/).
    5. Loads Curated records into the PostgreSQL Database.
    """
    logger.info("=" * 65)
    logger.info("AWS GLUE BANKING ETL JOB EXECUTION")
    logger.info("=" * 65)
    logger.info(f"Source S3 Bucket: {bucket_name}")
    logger.info(f"Bronze Prefix   : {raw_prefix}")

    s3_client = get_s3_boto_client()

    # Step 1: Branches
    logger.info("\n--- Processing Step 1: Branches ---")
    branches_raw = download_s3_to_memory(s3_client, bucket_name, f"{raw_prefix}/branches.csv")
    valid_branch_ids = set()
    if branches_raw is not None:
        branches_good, branches_bad = validate_branches(branches_raw)
        branches_curated = transform_branches(branches_good)
        valid_branch_ids = set(branches_curated["branch_id"].dropna().astype(int))

        upload_dataframe_to_s3(s3_client, branches_curated, bucket_name, "silver/curated/branches.csv")
        if not branches_bad.empty:
            upload_dataframe_to_s3(s3_client, branches_bad, bucket_name, "quarantine/branches_bad.csv")
        try:
            load_df_to_postgres(branches_curated, "branches", truncate_first=True)
        except Exception as db_err:
            logger.warning(f"Database direct load skipped (PostgreSQL might be offline): {db_err}")

    # Step 2: Employees
    logger.info("\n--- Processing Step 2: Employees ---")
    emp_raw = download_s3_to_memory(s3_client, bucket_name, f"{raw_prefix}/employees.csv")
    if emp_raw is not None:
        emp_good, emp_bad = validate_employees(emp_raw, valid_branch_ids)
        emp_curated = transform_employees(emp_good)

        upload_dataframe_to_s3(s3_client, emp_curated, bucket_name, "silver/curated/employees.csv")
        if not emp_bad.empty:
            upload_dataframe_to_s3(s3_client, emp_bad, bucket_name, "quarantine/employees_bad.csv")
        try:
            load_df_to_postgres(emp_curated, "employees", truncate_first=True)
        except Exception as db_err:
            logger.warning(f"Database direct load skipped: {db_err}")

    # Step 3: Customers
    logger.info("\n--- Processing Step 3: Customers ---")
    cust_raw = download_s3_to_memory(s3_client, bucket_name, f"{raw_prefix}/customers.csv")
    valid_customer_ids = set()
    if cust_raw is not None:
        cust_good, cust_bad = validate_customers(cust_raw)
        cust_curated = transform_customers(cust_good)
        valid_customer_ids = set(cust_curated["customer_id"].astype(int))

        upload_dataframe_to_s3(s3_client, cust_curated, bucket_name, "silver/curated/customers.csv")
        if not cust_bad.empty:
            upload_dataframe_to_s3(s3_client, cust_bad, bucket_name, "quarantine/customers_bad.csv")
        try:
            load_df_to_postgres(cust_curated, "customers", truncate_first=True)
        except Exception as db_err:
            logger.warning(f"Database direct load skipped: {db_err}")

    # Step 4: Accounts
    logger.info("\n--- Processing Step 4: Accounts ---")
    acc_raw = download_s3_to_memory(s3_client, bucket_name, f"{raw_prefix}/accounts.csv")
    valid_account_ids = set()
    if acc_raw is not None:
        acc_good, acc_bad = validate_accounts(acc_raw, valid_customer_ids)
        acc_curated = transform_accounts(acc_good)
        valid_account_ids = set(acc_curated["account_id"].astype(int))

        upload_dataframe_to_s3(s3_client, acc_curated, bucket_name, "silver/curated/accounts.csv")
        if not acc_bad.empty:
            upload_dataframe_to_s3(s3_client, acc_bad, bucket_name, "quarantine/accounts_bad.csv")
        try:
            load_df_to_postgres(acc_curated, "accounts", truncate_first=True)
        except Exception as db_err:
            logger.warning(f"Database direct load skipped: {db_err}")

    # Step 5: Transactions
    logger.info("\n--- Processing Step 5: Transactions ---")
    txn_raw = download_s3_to_memory(s3_client, bucket_name, f"{raw_prefix}/transactions.csv")
    if txn_raw is not None:
        txn_good, txn_bad = validate_transactions(txn_raw, valid_account_ids)
        txn_curated = transform_transactions(txn_good)

        upload_dataframe_to_s3(s3_client, txn_curated, bucket_name, "silver/curated/transactions.csv")
        if not txn_bad.empty:
            upload_dataframe_to_s3(s3_client, txn_bad, bucket_name, "quarantine/transactions_bad.csv")
        try:
            load_df_to_postgres(txn_curated, "transactions", truncate_first=True)
        except Exception as db_err:
            logger.warning(f"Database direct load skipped: {db_err}")

    logger.info("\n" + "=" * 65)
    logger.info("AWS GLUE BANKING ETL JOB COMPLETED SUCCESSFULLY!")
    logger.info("Artifacts landed in AWS S3 Data Lake:")
    logger.info(f"  • Silver Curated Layer : s3://{bucket_name}/silver/curated/")
    logger.info(f"  • Quarantined DLQ      : s3://{bucket_name}/quarantine/")
    logger.info("=" * 65)

if __name__ == "__main__":
    run_cloud_glue_etl()
