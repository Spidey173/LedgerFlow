import sys
import os
from datetime import datetime
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import get_logger
from scripts.process_branches import run_branches_pipeline
from scripts.process_employees import run_employees_pipeline
from scripts.process_customers import run_customers_pipeline
from scripts.process_accounts import run_accounts_pipeline
from scripts.process_transactions import run_transactions_pipeline
from scripts.process_loans import run_loans_pipeline
from scripts.process_loan_payments import run_loan_payments_pipeline
from scripts.process_cards import run_cards_pipeline
from scripts.process_card_transactions import run_card_transactions_pipeline
from scripts.process_support_tickets import run_support_tickets_pipeline

logger = get_logger("master_orchestrator")

def run_all_pipelines():
    """
    Executes all 10 banking pipelines in strict dependency order:
    1. branches (Master Lookup)
    2. employees (depends on branches)
    3. customers (Core Root)
    4. accounts (depends on customers)
    5. transactions (depends on accounts)
    6. loans (depends on customers)
    7. loan_payments (depends on loans)
    8. cards (depends on customers & accounts)
    9. card_transactions (depends on cards)
    10. support_tickets (depends on customers)
    """
    master_start = datetime.now()
    logger.info("=" * 65)
    logger.info("STARTING LEDGERFLOW MASTER BANKING ETL ORCHESTRATOR (10 DATASETS)")
    logger.info("=" * 65)

    pipeline_sequence = [
        ("Branches Pipeline", run_branches_pipeline),
        ("Employees Pipeline", run_employees_pipeline),
        ("Customers Pipeline", run_customers_pipeline),
        ("Accounts Pipeline", run_accounts_pipeline),
        ("Transactions Pipeline", run_transactions_pipeline),
        ("Loans Pipeline", run_loans_pipeline),
        ("Loan Payments Pipeline", run_loan_payments_pipeline),
        ("Cards Pipeline", run_cards_pipeline),
        ("Card Transactions Pipeline", run_card_transactions_pipeline),
        ("Support Tickets Pipeline", run_support_tickets_pipeline),
    ]

    summaries = []

    for name, pipeline_fn in pipeline_sequence:
        logger.info(f"\n>>> Running {name}...")
        try:
            summary = pipeline_fn()
            summaries.append(summary)
            logger.info(f">>> {name} completed successfully.")
        except Exception as e:
            logger.error(f">>> Error in {name}: {str(e)}", exc_info=True)
            raise e

    master_end = datetime.now()
    total_elapsed = round((master_end - master_start).total_seconds(), 2)

    total_records_processed = sum(s.get("total", s.get("total_records", 0)) for s in summaries)
    total_curated_records = sum(s.get("curated", s.get("curated_records", 0)) for s in summaries)
    total_rejected_records = sum(s.get("bad", s.get("bad_records", 0)) for s in summaries)

    logger.info("\n" + "=" * 65)
    logger.info("MASTER ORCHESTRATION COMPLETE (ALL 10 DATASETS)")
    logger.info(f"Total Pipelines Executed: {len(summaries)}")
    logger.info(f"Total Execution Time    : {total_elapsed}s")
    logger.info(f"Total Records Ingested  : {total_records_processed:,}")
    logger.info(f"Total Curated Records   : {total_curated_records:,}")
    logger.info(f"Total Rejected (DLQ)    : {total_rejected_records:,}")
    logger.info("=" * 65)

    return summaries

if __name__ == "__main__":
    run_all_pipelines()
