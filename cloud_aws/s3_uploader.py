import os
import sys
import boto3
from botocore.exceptions import ClientError
from datetime import datetime

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import (
    RAW_DIR,
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    AWS_DEFAULT_REGION,
    S3_BUCKET_NAME,
)
from utils.logger import get_logger

logger = get_logger("s3_uploader")

def get_s3_client():
    """Initializes and returns a boto3 S3 client using environment credentials."""
    if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
        raise ValueError(
            "AWS credentials not configured! Please ensure AWS_ACCESS_KEY_ID and "
            "AWS_SECRET_ACCESS_KEY are set in your .env file."
        )
    return boto3.client(
        "s3",
        region_name=AWS_DEFAULT_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )

def ensure_bucket_exists(s3_client, bucket_name: str, region: str = AWS_DEFAULT_REGION):
    """Checks if the S3 bucket exists; if not, creates it in the specified region."""
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        logger.info(f"S3 bucket '{bucket_name}' already exists and is accessible.")
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code")
        if error_code in ["404", "NoSuchBucket"]:
            logger.info(f"Bucket '{bucket_name}' does not exist. Creating in region '{region}'...")
            try:
                if region == "us-east-1":
                    s3_client.create_bucket(Bucket=bucket_name)
                else:
                    s3_client.create_bucket(
                        Bucket=bucket_name,
                        CreateBucketConfiguration={"LocationConstraint": region},
                    )
                logger.info(f"Bucket '{bucket_name}' created successfully in {region}.")
            except Exception as create_err:
                logger.error(f"Failed to create bucket '{bucket_name}': {create_err}")
                raise create_err
        elif error_code == "403":
            logger.error(f"Access denied to bucket '{bucket_name}'. It may be owned by another account.")
            raise e
        else:
            logger.error(f"Error checking bucket '{bucket_name}': {e}")
            raise e

def upload_file_to_s3(s3_client, local_path: str, bucket_name: str, s3_key: str):
    """Uploads a single local file to S3 with size and timing metrics."""
    if not os.path.exists(local_path):
        raise FileNotFoundError(f"Local file not found: {local_path}")

    file_size_mb = round(os.path.getsize(local_path) / (1024 * 1024), 2)
    logger.info(f"Uploading {os.path.basename(local_path)} ({file_size_mb} MB) -> s3://{bucket_name}/{s3_key}...")
    
    start_time = datetime.now()
    try:
        s3_client.upload_file(local_path, bucket_name, s3_key)
        elapsed = round((datetime.now() - start_time).total_seconds(), 2)
        logger.info(f"Successfully uploaded {s3_key} in {elapsed}s.")
        return {
            "file": os.path.basename(local_path),
            "s3_uri": f"s3://{bucket_name}/{s3_key}",
            "size_mb": file_size_mb,
            "status": "SUCCESS",
            "duration_sec": elapsed,
        }
    except Exception as e:
        logger.error(f"Failed to upload {local_path} to s3://{bucket_name}/{s3_key}: {e}")
        return {
            "file": os.path.basename(local_path),
            "s3_uri": f"s3://{bucket_name}/{s3_key}",
            "size_mb": file_size_mb,
            "status": f"FAILED: {e}",
            "duration_sec": 0,
        }

def upload_all_raw_csvs(bucket_name: str = S3_BUCKET_NAME, s3_prefix: str = "bronze/raw"):
    """
    Uploads all 10 banking raw CSV datasets from data/raw to the AWS S3 bronze layer.
    """
    logger.info("=" * 65)
    logger.info("AWS S3 INGESTION: BANKING RAW DATASETS -> DATA LAKE (BRONZE)")
    logger.info("=" * 65)
    logger.info(f"Target Bucket: {bucket_name}")
    logger.info(f"S3 Prefix    : {s3_prefix}")
    logger.info(f"Region       : {AWS_DEFAULT_REGION}")

    s3 = get_s3_client()
    ensure_bucket_exists(s3, bucket_name, AWS_DEFAULT_REGION)

    raw_files = [f for f in sorted(os.listdir(RAW_DIR)) if f.endswith(".csv")]
    if not raw_files:
        raise FileNotFoundError(f"No CSV files found in {RAW_DIR}")

    logger.info(f"Found {len(raw_files)} raw CSV datasets to upload: {', '.join(raw_files)}")

    results = []
    total_start = datetime.now()

    for file_name in raw_files:
        local_file_path = os.path.join(RAW_DIR, file_name)
        s3_key = f"{s3_prefix}/{file_name}"
        res = upload_file_to_s3(s3, local_file_path, bucket_name, s3_key)
        results.append(res)

    total_elapsed = round((datetime.now() - total_start).total_seconds(), 2)
    successful = [r for r in results if r["status"] == "SUCCESS"]

    logger.info("\n" + "=" * 65)
    logger.info("S3 INGESTION SUMMARY")
    logger.info(f"Total Files Processed : {len(results)}")
    logger.info(f"Successfully Uploaded : {len(successful)}/{len(results)}")
    logger.info(f"Total Time Elapsed    : {total_elapsed}s")
    logger.info("Uploaded S3 URIs:")
    for r in successful:
        logger.info(f"  • {r['file']:<25} ({r['size_mb']} MB) -> {r['s3_uri']}")
    logger.info("=" * 65)

    return results

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Upload banking raw CSVs to AWS S3")
    parser.add_argument("--file", help="Specific CSV filename in data/raw to upload (optional)")
    parser.add_argument("--bucket", default=S3_BUCKET_NAME, help="S3 bucket name")
    parser.add_argument("--prefix", default="bronze/raw", help="S3 prefix folder")
    args = parser.parse_args()

    s3_client = get_s3_client()
    ensure_bucket_exists(s3_client, args.bucket, AWS_DEFAULT_REGION)

    if args.file:
        full_path = args.file if os.path.isabs(args.file) else os.path.join(RAW_DIR, os.path.basename(args.file))
        key = f"{args.prefix}/{os.path.basename(full_path)}"
        upload_file_to_s3(s3_client, full_path, args.bucket, key)
    else:
        upload_all_raw_csvs(args.bucket, args.prefix)
