import os
import re
import json
import logging
from datetime import datetime
from utils.config import LOGS_DIR

SENSITIVE_PATTERNS = [
    (re.compile(r'(password[:=]\s*)([^\s,;&]+)', re.IGNORECASE), r'\1[REDACTED]'),
    (re.compile(r'(secret[:=]\s*)([^\s,;&]+)', re.IGNORECASE), r'\1[REDACTED]'),
    (re.compile(r'(token[:=]\s*)([^\s,;&]+)', re.IGNORECASE), r'\1[REDACTED]'),
    (re.compile(r'(api[-_]?key[:=]\s*)([^\s,;&]+)', re.IGNORECASE), r'\1[REDACTED]'),
    (re.compile(r'(aws_secret_access_key[:=]\s*)([^\s,;&]+)', re.IGNORECASE), r'\1[REDACTED]'),
    (re.compile(r'(postgres://[^\s:]+:)([^@]+)(@)', re.IGNORECASE), r'\1[REDACTED]\3'),
    (re.compile(r'(postgresql://[^\s:]+:)([^@]+)(@)', re.IGNORECASE), r'\1[REDACTED]\3'),
]

class SensitiveDataFilter(logging.Filter):
    """Redacts passwords, tokens, API keys, and sensitive customer identifiers from logs."""
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            msg = record.msg
            for pattern, repl in SENSITIVE_PATTERNS:
                msg = pattern.sub(repl, msg)
            record.msg = msg
        return True

class JsonFormatter(logging.Formatter):
    """Outputs structured JSON log records for production observability."""
    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)

def get_logger(name: str) -> logging.Logger:
    """Returns a configured logger writing structured JSON to daily log file and readable text to console."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        redaction_filter = SensitiveDataFilter()
        logger.addFilter(redaction_filter)

        # Console Handler (always enabled for container/serverless stdout)
        ch = logging.StreamHandler()
        ch.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] [%(name)s] %(message)s"))
        logger.addHandler(ch)

        # File Handlers (attempt local file logging; gracefully skip if filesystem is read-only)
        try:
            os.makedirs(LOGS_DIR, exist_ok=True)
            today = datetime.now().strftime('%Y%m%d')
            json_log_file = os.path.join(LOGS_DIR, f"pipeline_{today}.json.log")
            text_log_file = os.path.join(LOGS_DIR, f"pipeline_{today}.log")

            # Standard Text File Handler
            fh = logging.FileHandler(text_log_file)
            fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] [%(name)s] %(message)s"))
            logger.addHandler(fh)

            # Structured JSON File Handler
            jfh = logging.FileHandler(json_log_file)
            jfh.setFormatter(JsonFormatter())
            logger.addHandler(jfh)
        except (OSError, PermissionError):
            # Filesystem is read-only (e.g. Vercel serverless / AWS Lambda).
            # Fall back cleanly to console stream handler.
            pass

    return logger


def log_pipeline_summary(pipeline_name: str, start_time: datetime, end_time: datetime,
                         total_records: int, curated_records: int, bad_records: int,
                         rejection_reasons: dict = None, status: str = "SUCCESS") -> dict:
    """Logs and returns a structured execution summary and persists to a JSON manifest."""
    duration_sec = round((end_time - start_time).total_seconds(), 2)
    success_rate = round((curated_records / total_records * 100), 2) if total_records else 0.0
    failure_rate = round((bad_records / total_records * 100), 2) if total_records else 0.0

    summary_str = f"""
============================================================
Pipeline Run Report: {pipeline_name}
------------------------------------------------------------
Status         : {status}
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
        "status": status,
        "started_at": start_time.strftime("%Y-%m-%d %H:%M:%S"),
        "ended_at": end_time.strftime("%Y-%m-%d %H:%M:%S"),
        "duration_seconds": duration_sec,
        "total_records": total_records,
        "curated_records": curated_records,
        "bad_records": bad_records,
        "success_rate_pct": success_rate,
        "failure_rate_pct": failure_rate,
        "rejection_reasons": rejection_reasons or {}
    }

    # Persist summary snapshot
    summary_path = os.path.join(LOGS_DIR, "latest_pipeline_run.json")
    try:
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary_data, f, indent=2)
    except Exception as e:
        logger.warning(f"Could not persist latest_pipeline_run.json: {e}")

    return summary_data

