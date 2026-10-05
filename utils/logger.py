import os
import logging
from datetime import datetime
from utils.config import LOGS_DIR

def get_logger(name: str) -> logging.Logger:
    """Returns a configured logger writing to both console and daily log file."""
    os.makedirs(LOGS_DIR, exist_ok=True)
    log_file = os.path.join(LOGS_DIR, f"pipeline_{datetime.now().strftime('%Y%m%d')}.log")

    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] [%(name)s] %(message)s")

        # File Handler
        fh = logging.FileHandler(log_file)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

        # Console Handler
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
    return logger

def log_pipeline_summary(pipeline_name: str, start_time: datetime, end_time: datetime,
                         total_records: int, curated_records: int, bad_records: int) -> dict:
    """Logs and returns a structured execution summary."""
    duration_sec = round((end_time - start_time).total_seconds(), 2)
    success_rate = round((curated_records / total_records * 100), 2) if total_records else 0.0
    failure_rate = round((bad_records / total_records * 100), 2) if total_records else 0.0

    summary_str = f"""
============================================================
Pipeline Run Report: {pipeline_name}
------------------------------------------------------------
Started        : {start_time.strftime('%Y-%m-%d %H:%M:%S')}
Ended          : {end_time.strftime('%Y-%m-%d %H:%M:%S')}
Duration       : {duration_sec}s
Total Records  : {total_records:,}
Curated (Good) : {curated_records:,} ({success_rate}%)
Rejected (DLQ) : {bad_records:,} ({failure_rate}%)
============================================================
"""
    logger = get_logger(pipeline_name)
    logger.info(summary_str)

    summary_data = {
        "pipeline_name": pipeline_name,
        "started_at": start_time.strftime("%Y-%m-%d %H:%M:%S"),
        "ended_at": end_time.strftime("%Y-%m-%d %H:%M:%S"),
        "duration_seconds": duration_sec,
        "total_records": total_records,
        "curated_records": curated_records,
        "bad_records": bad_records,
        "success_rate_pct": success_rate,
        "failure_rate_pct": failure_rate
    }
    return summary_data
