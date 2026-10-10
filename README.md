# LedgerFlow — Banking ETL Pipeline & PostgreSQL Warehouse

[![API Docs / Interactive Schema](https://img.shields.io/badge/API%20Docs-Interactive%20Schema-009688?style=for-the-badge&logo=fastapi)](https://ledgerflow17.vercel.app/docs)
[![Live Deployment](https://img.shields.io/badge/Live%20API-ledgerflow17.vercel.app-blue?style=for-the-badge&logo=vercel)](https://ledgerflow17.vercel.app/)
[![Database](https://img.shields.io/badge/Database-Neon%20PostgreSQL-00E599?style=for-the-badge&logo=postgresql&logoColor=white)](https://neon.tech)
[![Tests](https://img.shields.io/badge/Pytest-41%20Passed-brightgreen?style=for-the-badge&logo=pytest)](tests/test_validation.py)

> 🌐 **Live Interactive Schema & Swagger UI**: **[https://ledgerflow17.vercel.app/docs](https://ledgerflow17.vercel.app/docs)**  
> 📊 **Live Executive Dashboard API**: **[https://ledgerflow17.vercel.app/dashboard](https://ledgerflow17.vercel.app/dashboard)**  
> ⚡ **Cloud Warehouse**: Live Neon Serverless PostgreSQL cluster running ~1.9M curated & dimensional warehouse records.

**LedgerFlow** is an end-to-end banking data pipeline and relational data warehouse implemented in Python, PostgreSQL, and FastAPI. It processes 10 relational banking datasets (~5.8M raw records) with automated data quality checks, referential integrity validation, a Dead Letter Queue (DLQ) for auditability, high-speed PostgreSQL bulk ingestion via `COPY`, and analytical marts for reporting and APIs.

---

## ⚡ Quickstart

You can test and execute the end-to-end pipeline locally with a single script:

### Option A: Local CLI Execution
```bash
./run_all.sh
```
*Or using Make:*
```bash
make run
```
> **What this executes:**
> 1. Runs **41 Pytest validation tests** (verifying schema rules, domain checks, and integrity constraints).
> 2. Executes the **10-dataset pipeline in topological dependency order** (~5.8M raw rows -> ~5.15M curated rows + bad records routed to DLQ).
> 3. Connects to PostgreSQL, loads curated data via `COPY`, and refreshes analytical tables (when database connection is available).
> 4. Generates an execution summary report showing processed counts and runtimes.

### Option B: Dockerized Setup
```bash
docker-compose up --build -d
```
Spins up PostgreSQL 15 and the FastAPI service with auto-initialized schemas and health checks.

---

## 1. System Architecture

```mermaid
flowchart TD
    subgraph L1["1. Raw Layer (CSV)"]
        R1["customers.csv (60k)"]
        R2["accounts.csv (95k)"]
        R3["transactions.csv (2.0M)"]
        R4["loans.csv (22k)"]
        R5["loan_payments.csv (600k)"]
        R6["cards.csv (65k)"]
        R7["card_transactions.csv (3.0M)"]
        R8["branches.csv (150)"]
        R9["employees.csv (1.8k)"]
        R10["support_tickets.csv (25k)"]
    end

    subgraph L2["2. Validation & Quarantine"]
        V["Data Quality Rules & Referential Integrity Checks"]
        DLQ["Dead Letter Queue (DLQ)\ndata/bad_records/*\n(Audit Metadata: Reason, Stage, Timestamp)"]
    end

    subgraph L3["3. Curated Layer"]
        C1["curated/customers.csv (55k)"]
        C2["curated/accounts.csv (87k)"]
        C3["curated/transactions.csv (1.83M)"]
        C4["curated/loans.csv (20k)"]
        C5["curated/loan_payments.csv (549k)"]
        C6["curated/cards.csv (54k)"]
        C7["curated/card_transactions.csv (2.52M)"]
    end

    subgraph L4["4. Relational Warehouse"]
        PG["PostgreSQL (bank_dwh)\n- Foreign Key Enforcement\n- B-Tree Indexes\n- Bulk COPY Ingestion"]
    end

    subgraph L5["5. Analytical Marts & Service"]
        M1["customer_360"]
        M2["monthly_customer_summary"]
        M3["monthly_branch_summary"]
        API["FastAPI REST Service\n(/customers, /customer-360, /dashboard)"]
    end

    L1 --> V
    V -- Rejected Rows --> DLQ
    V -- Validated & Cleaned Rows --> L3
    L3 -->|psycopg2 Bulk COPY| PG
    PG --> M1
    PG --> M2
    PG --> M3
    M1 & M2 & M3 --> API
```

---

## 2. Architecture & Design Decisions

* **Tiered Data Storage Pattern**: Separates Raw ingestion data, Curated validated data, and Quarantined (bad) records to ensure traceability and prevent corrupt data from propagating downstream.
* **Pre-Load Foreign Key Validation**: Verifies parent-child relational constraints in Python before loading into PostgreSQL, ensuring high-throughput batch loads don't fail midway due to FK violations (e.g., rejecting transactions pointing to dropped accounts).
* **Chunked File Streaming**: High-volume files (2M transactions, 3M card transactions) are processed in chunks (`chunksize=250k-300k`), avoiding memory exhaustion and keeping memory usage predictable.
* **Audited Dead Letter Queue (DLQ)**: Rejected records are isolated into separate quarantine CSVs alongside audit metadata:
  * `rejection_reason` (e.g., `Customer ID not found in curated customers`)
  * `validation_stage` (`Primary Key Constraint`, `Referential Integrity`, `Domain Boundary Check`, `Format Validation`, `Accounting Reconciliation`)
  * `pipeline_name`
  * `processed_at`
* **Dependency-Aware Orchestration**: Executes datasets in strict topological order (`Branches` -> `Employees` -> `Customers` -> `Accounts` -> `Transactions` / `Loans` / `Cards` -> `Payments` / `Support`). Also includes an Airflow DAG definition (`dags/banking_pipeline_dag.py`) demonstrating production workflow orchestration.
* **Efficient Bulk Loading via `COPY`**: Leverages PostgreSQL's native `COPY` command via `psycopg2` rather than slow row-by-row `INSERT` statements, enabling multi-million row loads in seconds.
* **Analytical Serving Layer**: PostgreSQL aggregation scripts materialize dimensional summary tables (`customer_360`, branch metrics) served directly via indexed queries in a lightweight FastAPI application.

---

## 3. Dataset & Pipeline Summary

*(Metrics from a local execution run across the sample banking dataset)*

| Dataset / Entity | Raw Records | Curated (Clean) | Quarantined (DLQ) | Valid Pass Rate | Ingestion Method |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`branches`** | 150 | 150 | 0 | 100.0% | In-Memory (Master Lookup) |
| **`employees`** | 1,800 | 1,800 | 0 | 100.0% | In-Memory (FK: Branch) |
| **`customers`** | 60,000 | 55,050 | 4,950 | 91.75% | In-Memory (Cleanse & Rules) |
| **`accounts`** | 95,000 | 87,177 | 7,823 | 91.77% | In-Memory (FK: Customer) |
| **`transactions`** | 2,000,000 | 1,835,551 | 164,449 | 91.78% | Chunked Stream (250k rows/chunk) |
| **`loans`** | 22,000 | 20,137 | 1,863 | 91.53% | In-Memory (FK: Customer) |
| **`loan_payments`** | 600,000 | 549,015 | 50,985 | 91.50% | Chunked Stream (200k rows/chunk) |
| **`cards`** | 65,000 | 54,643 | 10,357 | 84.07% | In-Memory (Dual FK: Customer & Account) |
| **`card_transactions`**| 3,000,000 | 2,521,980 | 478,020 | 84.07% | Chunked Stream (300k rows/chunk) |
| **`support_tickets`** | 25,000 | 22,927 | 2,073 | 91.71% | In-Memory (FK: Customer) |
| **TOTAL** | **5,868,950** | **5,148,430** | **720,520** | **87.72%** | **Chunked ETL + Native COPY** |

---

## 4. Test Suite (41 Pytest Validator Tests)

The test suite in [`tests/test_validation.py`](tests/test_validation.py) contains **41 automated unit tests** verifying data quality rules, edge cases, boundaries, and referential constraints across all 10 banking entities:

| Category / Entity | Tests | Scenarios Covered |
| :--- | :---: | :--- |
| **Customers** | 4 | Valid customer schemas; email regex formats; credit score boundaries (min 300, max 850); non-positive income; duplicate customer IDs; null/blank customer IDs. |
| **Branches** | 4 | Valid branch schemas; missing IFSC code; blank branch names; missing city/state; duplicate branch IDs; date parsing. |
| **Accounts** | 4 | Valid account types (Savings, Current, Salary, FD, NRI); case insensitivity; initial zero balance; negative balance; orphan customer FK; duplicate account IDs; unapproved statuses. |
| **Employees** | 4 | Valid roles; case-insensitive role matching; non-positive salary; orphan branch FK; invalid hire date; duplicate employee IDs. |
| **Transactions** | 4 | Strictly positive amount (> 0); zero amount; channel case-insensitivity (ATM, UPI, Mobile App); invalid transaction types; unparseable dates; duplicate transaction IDs; orphan account FK. |
| **Loans** | 4 | Valid loans; interest rate boundaries (1.0% to 50.0%); zero/negative interest rate; zero/negative term months; unapproved loan statuses; orphan customer FK; duplicate loan IDs. |
| **Loan Payments** | 4 | Valid payments; 5-cent accounting reconciliation tolerance (`abs(principal + interest - amount) <= 0.05`); mismatched components; negative principal/interest; non-binary late payment flag; orphan loan FK; duplicate payment IDs. |
| **Cards** | 4 | Dual foreign key referential integrity (`customer_id` AND `account_id`); same-day expiry boundary (`expiry_date >= issue_date`); expiry before issue date; negative credit limit; zero limit (debit cards); duplicate card IDs. |
| **Card Transactions** | 4 | Valid card transactions; empty/whitespace merchant category; non-positive amount; binary fraud flag validation (`is_fraud` in [0, 1]); orphan card FK; duplicate transaction IDs. |
| **Support Tickets** | 4 | Valid tickets; open ticket null resolution date (`date_resolved = NaN`); same-day resolution; resolution before opened chronology error; satisfaction score boundaries (1 to 5); missing issue type; duplicate ticket IDs. |

### Run Tests:
```bash
pytest -v
```
*(Or via Make: `make test`)*

---

## 5. Project Structure

```text
ledgerflow/
├── run_all.sh                         # Master One-Command execution script
├── Makefile                           # Unified CLI shortcuts (run, test, etl, api, docker)
├── pytest.ini                         # Pytest configuration & pythonpath
├── requirements.txt                   # Complete project dependencies
├── Dockerfile                         # Container image definition
├── docker-compose.yml                 # PostgreSQL 15 + FastAPI container stack
├── dags/
│   └── banking_pipeline_dag.py        # Apache Airflow scheduled DAG definition
├── data/
│   ├── raw/                           # Raw bank CSV exports (~5.8M rows)
│   ├── curated/                       # Validated, cleansed files (~5.1M rows)
│   └── bad_records/                   # Quarantined DLQ with audit columns
├── scripts/
│   ├── run_pipeline.py                # Master DAG Orchestrator (10 pipelines)
│   ├── process_customers.py           # Customer ETL
│   ├── process_accounts.py            # Accounts ETL
│   ├── process_transactions.py        # Transactions ETL (Chunked streaming)
│   ├── process_loans.py               # Loans ETL
│   ├── process_loan_payments.py       # Loan Payments ETL (Reconciliation)
│   ├── process_cards.py               # Cards ETL (Dual FK check)
│   ├── process_card_transactions.py   # Card Txns ETL (Chunked streaming)
│   ├── process_branches.py            # Branches ETL
│   ├── process_employees.py           # Employees ETL
│   ├── process_support_tickets.py     # Support Tickets ETL
│   ├── load_postgres.py               # Native COPY Bulk Loader
│   └── api.py                         # FastAPI REST Endpoints & KPIs
├── validation/                        # 10 dedicated Data Quality validator modules
├── transformation/                    # 10 dedicated cleansing and normalization modules
├── sql/
│   ├── schema/create_tables.sql       # Relational DDL with FKs & Indexes
│   ├── analytics/create_analytics_tables.sql # Customer 360 & Summary Marts
│   └── queries/analytics_queries.sql  # 25 Financial & Business KPI queries
├── tests/
│   └── test_validation.py             # 41 Pytest unit tests for all validators
├── docs/
│   └── data_dictionary.md             # Full Enterprise Data Dictionary
└── logs/                              # Pipeline execution logs and audit reports
```

---

## 6. Step-by-Step Manual Execution (Alternative)

If you prefer executing each stage step-by-step:

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Run Unit Tests
```bash
pytest -v
```

### Step 3: Run the 10-Dataset Pipeline
```bash
python3 scripts/run_pipeline.py
```

### Step 4: Initialize PostgreSQL Warehouse & Bulk Load
```bash
# 1. Apply DDL schema with primary and foreign keys
psql -U postgres -d bank_dwh -f sql/schema/create_tables.sql

# 2. Bulk load 5.12M curated records via high-speed COPY
python3 scripts/load_postgres.py

# 3. Materialize analytical marts & Customer 360 view
psql -U postgres -d bank_dwh -f sql/analytics/create_analytics_tables.sql
```

### Step 5: Launch FastAPI REST Service
```bash
uvicorn scripts.api:app --host 0.0.0.0 --port 8000 --reload
```
Interactive Swagger API documentation available at **[http://localhost:8000/docs](http://localhost:8000/docs)**.

---

## 7. Sample API Responses

### `GET /dashboard`
Executive KPI summary aggregated across all 10 entities:
```json
{
  "kpis": {
    "total_customers": 55050,
    "total_accounts": 87177,
    "total_deposits": 3988526118.95,
    "total_active_loans": 13098,
    "active_loan_portfolio": 5462884935.72,
    "active_cards": 48143,
    "lifetime_transactions": 1835551,
    "lifetime_card_transactions": 2521980,
    "total_fraud_transactions": 12634
  },
  "customer_segments": [
    { "customer_segment": "Premium / Low Risk", "count": 5058 },
    { "customer_segment": "Standard / Moderate Risk", "count": 15121 },
    { "customer_segment": "Subprime / High Risk", "count": 34871 }
  ]
}
```

### `GET /customer/101`
Unified **Customer 360** profile containing linked accounts, loans, credit/debit cards, and monthly financial metrics:
```json
{
  "customer": {
    "customer_id": 101,
    "name": "Jane Doe",
    "email": "jane.doe@example.com",
    "credit_score": 720,
    "annual_income": 85000.0,
    "customer_segment": "Premium / Low Risk"
  },
  "accounts": [
    { "account_id": 1001, "account_type": "Savings", "balance": 1500.50, "status": "Active" }
  ],
  "loans": [
    { "loan_id": 201, "loan_amount": 250000.0, "interest_rate": 6.5, "status": "Active" }
  ],
  "cards": [
    { "card_id": 301, "card_type": "Credit - Platinum", "credit_limit": 10000.0, "status": "Active" }
  ]
}
```

---

## 8. CLI Command Quick Reference

| Command | Action |
| :--- | :--- |
| **`./run_all.sh`** | **One-command full run**: executes tests, 10 ETL pipelines, and DB load. |
| **`./run_all.sh --test-only`** | Runs only the 41 Pytest validator test suite. |
| **`./run_all.sh --api`** | Runs full pipeline and immediately spins up FastAPI server. |
| **`make test`** | Runs Pytest with verbose test descriptions. |
| **`make etl`** | Runs the 10-dataset master ETL pipeline. |
| **`make load`** | Loads curated CSVs into PostgreSQL via COPY streaming. |
| **`docker-compose up --build -d`** | Starts containerized PostgreSQL warehouse and FastAPI. |
