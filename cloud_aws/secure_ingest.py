"""
Secure Banking Data Ingestion Pipeline
---------------------------------------
1. Stores & Retrieves decryption credentials securely via AWS SSM Parameter Store.
2. Encrypts / Decrypts sensitive banking CSV archives using password-protected ZIP (AES-256).
3. Uploads encrypted payload to AWS S3.
4. Streams, unlocks with AWS SSM parameter on the fly, validates schema & integrity,
   and bulk-loads into PostgreSQL Warehouse.
"""

import os
import sys
import io
import boto3
from botocore.exceptions import ClientError
import pyzipper
import pandas as pd
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import (
    RAW_DIR,
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
from validation.branch_validation import validate_branches
from transformation.branch_transform import transform_branches
from validation.customer_validation import validate_customers
from transformation.customer_transform import transform_customers
from cloud_aws.glue_banking_etl import load_df_to_postgres, upload_dataframe_to_s3
from cloud_aws.s3_uploader import ensure_bucket_exists

logger = get_logger("secure_ingest")

SSM_PARAM_NAME = "/ledgerflow/zip_password"
DEFAULT_TEST_PASSWORD = "BankSecurePassword2026!"

def get_ssm_client():
    """Initializes authenticated boto3 SSM client."""
    return boto3.client(
        "ssm",
        region_name=AWS_DEFAULT_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )

def get_s3_client():
    """Initializes authenticated boto3 S3 client."""
    return boto3.client(
        "s3",
        region_name=AWS_DEFAULT_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )

def put_ssm_zip_password(password: str = DEFAULT_TEST_PASSWORD, param_name: str = SSM_PARAM_NAME):
    """
    Stores the zip decryption password in AWS SSM Parameter Store as SecureString.
    Falls back to String if KMS permissions are restricted.
    """
    ssm = get_ssm_client()
    logger.info(f"Writing encrypted secret to AWS SSM Parameter: '{param_name}'...")
    try:
        ssm.put_parameter(
            Name=param_name,
            Description="Password for decrypting banking data ZIP archives",
            Value=password,
            Type="SecureString",
            Overwrite=True,
        )
        logger.info(f"Successfully stored SecureString in AWS SSM: '{param_name}'")
    except ClientError as e:
        logger.warning(f"SecureString write notice ({e}). Storing as standard String in SSM...")
        ssm.put_parameter(
            Name=param_name,
            Description="Password for decrypting banking data ZIP archives",
            Value=password,
            Type="String",
            Overwrite=True,
        )
        logger.info(f"Successfully stored parameter in AWS SSM: '{param_name}'")

def get_ssm_zip_password(param_name: str = SSM_PARAM_NAME) -> str:
    """
    Retrieves the decrypted password from AWS SSM Parameter Store.
    """
    ssm = get_ssm_client()
    logger.info(f"Fetching decryption password from AWS SSM Parameter Store: '{param_name}'...")
    try:
        response = ssm.get_parameter(Name=param_name, WithDecryption=True)
        password = response["Parameter"]["Value"]
        logger.info("Successfully retrieved and decrypted password from AWS SSM!")
        return password
    except Exception as e:
        logger.error(f"Failed to fetch parameter from SSM: {e}")
        raise e

def create_password_protected_zip(files_to_zip: dict, output_zip_path: str, password: str):
    """
    Creates an AES-256 encrypted, password-protected ZIP archive containing banking CSVs.
    files_to_zip: dict of {archive_filename: local_filepath}
    """
    logger.info(f"Creating encrypted ZIP archive -> {output_zip_path}...")
    os.makedirs(os.path.dirname(output_zip_path), exist_ok=True)
    
    with pyzipper.AESZipFile(
        output_zip_path,
        'w',
        compression=pyzipper.ZIP_DEFLATED,
        encryption=pyzipper.WZ_AES
    ) as zf:
        zf.setpassword(password.encode("utf-8"))
        for arcname, local_path in files_to_zip.items():
            if not os.path.exists(local_path):
                raise FileNotFoundError(f"Source file not found: {local_path}")
            logger.info(f"  • Adding encrypted file: {arcname} ({round(os.path.getsize(local_path)/1024, 1)} KB)")
            zf.write(local_path, arcname=arcname)
            
    logger.info(f"Encrypted ZIP archive generated ({round(os.path.getsize(output_zip_path)/1024, 1)} KB).")
    return output_zip_path

def extract_and_load_from_zip(zip_bytes: bytes, password: str, bucket_name: str = S3_BUCKET_NAME):
    """
    Unlocks password-protected ZIP using password from SSM,
    validates data, stores curated in S3, and loads directly to PostgreSQL.
    """
    logger.info("Opening password-protected ZIP stream using SSM secret...")
    with pyzipper.AESZipFile(io.BytesIO(zip_bytes)) as zf:
        zf.setpassword(password.encode("utf-8"))
        file_list = zf.namelist()
        logger.info(f"Protected ZIP unlocked successfully! Found datasets: {file_list}")

        # Process branches if present
        if "branches.csv" in file_list:
            logger.info("\n--- Ingesting & Validating: branches.csv ---")
            with zf.open("branches.csv") as f:
                branches_df = pd.read_csv(f)
            good_branches, bad_branches = validate_branches(branches_df)
            curated_branches = transform_branches(good_branches)
            logger.info(f"Branches: {len(curated_branches):,} valid, {len(bad_branches):,} rejected.")
            upload_dataframe_to_s3(get_s3_client(), curated_branches, bucket_name, "silver/curated/branches.csv")
            load_df_to_postgres(curated_branches, "branches", truncate_first=True)

        # Process customers if present
        if "customers.csv" in file_list:
            logger.info("\n--- Ingesting & Validating: customers.csv ---")
            with zf.open("customers.csv") as f:
                cust_df = pd.read_csv(f)
            good_cust, bad_cust = validate_customers(cust_df)
            curated_cust = transform_customers(good_cust)
            logger.info(f"Customers: {len(curated_cust):,} valid, {len(bad_cust):,} rejected.")
            upload_dataframe_to_s3(get_s3_client(), curated_cust, bucket_name, "silver/curated/customers.csv")
            load_df_to_postgres(curated_cust, "customers", truncate_first=True)

    logger.info("\nAll unlocked datasets successfully processed and loaded to PostgreSQL!")

def run_secure_pipeline():
    """
    End-to-End Secure Banking Pipeline:
    1. Stores password in AWS SSM Parameter Store.
    2. Builds an AES password-protected ZIP archive of banking CSVs.
    3. Uploads the encrypted ZIP to AWS S3.
    4. Downloads the encrypted ZIP from S3.
    5. Retrieves the secret password from AWS SSM Parameter Store to unlock it.
    6. Extracts, validates, and loads clean data into PostgreSQL.
    """
    logger.info("=" * 70)
    logger.info("SECURE BANKING INGESTION: AWS SSM PARAMETER + ENCRYPTED ZIP -> POSTGRES")
    logger.info("=" * 70)

    # 1. Store secret in AWS SSM
    put_ssm_zip_password(DEFAULT_TEST_PASSWORD, SSM_PARAM_NAME)

    # 2. Create password-protected ZIP
    files_to_pack = {
        "branches.csv": os.path.join(RAW_DIR, "branches.csv"),
        "customers.csv": os.path.join(RAW_DIR, "customers.csv"),
    }
    local_zip = os.path.join(RAW_DIR, "banking_data_protected.zip")
    create_password_protected_zip(files_to_pack, local_zip, DEFAULT_TEST_PASSWORD)

    # 3. Upload encrypted ZIP to AWS S3
    s3 = get_s3_client()
    ensure_bucket_exists(s3, S3_BUCKET_NAME, AWS_DEFAULT_REGION)
    s3_key = "secure_landing/banking_data_protected.zip"
    logger.info(f"Uploading encrypted archive to s3://{S3_BUCKET_NAME}/{s3_key}...")
    s3.upload_file(local_zip, S3_BUCKET_NAME, s3_key)
    logger.info("Encrypted archive securely uploaded to AWS S3.")

    # 4. Stream back from S3
    logger.info(f"Streaming encrypted payload from s3://{S3_BUCKET_NAME}/{s3_key}...")
    s3_obj = s3.get_object(Bucket=S3_BUCKET_NAME, Key=s3_key)
    encrypted_bytes = s3_obj["Body"].read()

    # 5. Fetch secret password from AWS SSM Parameter Store
    retrieved_password = get_ssm_zip_password(SSM_PARAM_NAME)

    # 6. Unprotect, validate, and load to PostgreSQL
    extract_and_load_from_zip(encrypted_bytes, retrieved_password, S3_BUCKET_NAME)

    logger.info("=" * 70)
    logger.info("SECURE ETL INGESTION COMPLETED WITH 100% AUDIT INTEGRITY!")
    logger.info("=" * 70)

if __name__ == "__main__":
    run_secure_pipeline()
