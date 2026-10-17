import os
import sys
import argparse
from datetime import datetime

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import S3_BUCKET_NAME, AWS_DEFAULT_REGION
from utils.logger import get_logger
from cloud_aws.s3_uploader import upload_all_raw_csvs, upload_file_to_s3, get_s3_client, ensure_bucket_exists
from cloud_aws.glue_banking_etl import run_cloud_glue_etl
from cloud_aws.flink_transaction_processor import run_flink_stream_simulation

logger = get_logger("cloud_master_orchestrator")

def run_end_to_end_aws_pipeline(single_file: str = None, run_flink: bool = False):
    """
    Executes the complete AWS Cloud Banking Data Pipeline:
    1. Ingestion: Uploads local CSVs -> AWS S3 Bronze Data Lake.
    2. Processing: Executes AWS Glue PySpark ETL (Data Quality, DLQ, S3 Silver).
    3. Serving: Loads curated datasets into the target Database.
    4. (Optional) Streaming: Runs Apache Flink real-time transaction processing.
    """
    pipeline_start = datetime.now()
    logger.info("=" * 70)
    logger.info("LEDGERFLOW ENTERPRISE AWS DATA PIPELINE (S3 + GLUE + DB)")
    logger.info("=" * 70)
    logger.info(f"Target S3 Bucket : {S3_BUCKET_NAME}")
    logger.info(f"AWS Region       : {AWS_DEFAULT_REGION}")

    # Stage 1: Upload to S3
    logger.info("\n>>> STAGE 1: INGESTION TO AWS S3 DATA LAKE (BRONZE)")
    s3_client = get_s3_client()
    ensure_bucket_exists(s3_client, S3_BUCKET_NAME, AWS_DEFAULT_REGION)

    if single_file:
        logger.info(f"Uploading single file: {single_file}")
        s3_key = f"bronze/raw/{os.path.basename(single_file)}"
        upload_file_to_s3(s3_client, single_file, S3_BUCKET_NAME, s3_key)
    else:
        upload_all_raw_csvs(S3_BUCKET_NAME, "bronze/raw")

    # Stage 2: AWS Glue Job
    logger.info("\n>>> STAGE 2: AWS GLUE DISTRIBUTED ETL & DATABASE LOADING")
    run_cloud_glue_etl(S3_BUCKET_NAME, "bronze/raw")

    # Stage 3: Apache Flink (if requested)
    if run_flink:
        logger.info("\n>>> STAGE 3: APACHE FLINK REAL-TIME STREAMING")
        run_flink_stream_simulation()

    total_time = round((datetime.now() - pipeline_start).total_seconds(), 2)
    logger.info("\n" + "=" * 70)
    logger.info(f"END-TO-END AWS PIPELINE COMPLETED IN {total_time} SECONDS!")
    logger.info("=" * 70)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run LedgerFlow AWS Cloud Pipeline")
    parser.add_argument("--file", help="Upload and process a single CSV file")
    parser.add_argument("--flink", action="store_true", help="Also execute Apache Flink stream simulation")
    args = parser.parse_args()

    run_end_to_end_aws_pipeline(single_file=args.file, run_flink=args.flink)
